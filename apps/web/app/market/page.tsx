"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Newspaper,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Search,
  Filter,
  ExternalLink,
  ShieldAlert,
  Calendar,
  Layers,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Plus,
  X,
  ChevronLeft,
  ChevronRight,
  Bookmark,
  Bell,
  Eye,
  Trash2,
  Landmark,
  Percent,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  SlidersHorizontal,
} from "lucide-react";
import { DashboardLayout } from "@/components/DashboardLayout";
import {
  api,
  NewsArticle,
  PaginatedNewsArticles,
  SentimentTrendSummary,
  MacroSeries,
  Watchlist,
  UserAlert,
  AlertNotification,
  Instrument,
} from "@/lib/api";

type ActiveTab = "feed" | "macro" | "sentiment" | "watchlist";

export default function MarketPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("feed");

  // Global News Feed state
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [totalArticles, setTotalArticles] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [sentimentFilter, setSentimentFilter] = useState("All");
  const [selectedInstrumentFilter, setSelectedInstrumentFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);

  const [isLoadingNews, setIsLoadingNews] = useState(true);
  const [isSeeding, setIsSeeding] = useState(false);
  const [seedStatus, setSeedStatus] = useState<string | null>(null);

  // Macroeconomics state
  const [macroSeriesList, setMacroSeriesList] = useState<MacroSeries[]>([]);
  const [selectedMacroId, setSelectedMacroId] = useState<string>("IN_REPO_RATE");
  const [selectedMacroHistory, setSelectedMacroHistory] = useState<MacroSeries | null>(null);
  const [isLoadingMacro, setIsLoadingMacro] = useState(false);
  const [macroHoverPoint, setMacroHoverPoint] = useState<{ date: string; value: number } | null>(null);

  // Sentiment Analytics state
  const [sentimentDays, setSentimentDays] = useState<number>(30);
  const [sentimentSummary, setSentimentSummary] = useState<SentimentTrendSummary | null>(null);
  const [isLoadingSentiment, setIsLoadingSentiment] = useState(false);

  // Watchlists & Alerts state
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [activeWatchlistId, setActiveWatchlistId] = useState<string>("");
  const [activeWatchlist, setActiveWatchlist] = useState<Watchlist | null>(null);
  const [alerts, setAlerts] = useState<UserAlert[]>([]);
  const [notifications, setNotifications] = useState<AlertNotification[]>([]);
  const [newWatchlistName, setNewWatchlistName] = useState("");
  const [isCreatingWatchlist, setIsCreatingWatchlist] = useState(false);
  const [addInstrumentId, setAddInstrumentId] = useState("");
  const [newAlertKeyword, setNewAlertKeyword] = useState("");
  const [newAlertSentiment, setNewAlertSentiment] = useState("ALL");
  const [newAlertInstrumentId, setNewAlertInstrumentId] = useState("");
  const [isCreatingAlert, setIsCreatingAlert] = useState(false);

  // Initial load: Categories & Instruments
  useEffect(() => {
    api.getNewsCategories()
      .then((res) => setCategories(res.categories))
      .catch((err) => console.error("Failed to load categories:", err));

    api.listInstruments({ size: 50 })
      .then((res) => setInstruments(res.items))
      .catch((err) => console.error("Failed to load instruments:", err));
  }, []);

  // Load News Feed
  useEffect(() => {
    loadNews();
  }, [page, categoryFilter, sentimentFilter, selectedInstrumentFilter, searchQuery]);

  const loadNews = async () => {
    setIsLoadingNews(true);
    try {
      const resp = await api.listNews({
        page,
        size: pageSize,
        category: categoryFilter,
        sentiment: sentimentFilter,
        instrument_id: selectedInstrumentFilter || undefined,
        q: searchQuery || undefined,
      });
      setNews(resp.items);
      setTotalArticles(resp.total);
      setTotalPages(resp.pages);
    } catch (err) {
      console.error("Failed to load news articles:", err);
    } finally {
      setIsLoadingNews(false);
    }
  };

  // Seed MarketPulse demo data
  const handleSeedMarketPulse = async () => {
    setIsSeeding(true);
    setSeedStatus(null);
    try {
      const res = await api.seedMarketPulse();
      setSeedStatus(`Initialized MarketPulse: ${res.articles_ingested} articles, ${res.series_created} macro series.`);
      await loadNews();
      await loadMacroCatalog();
      await loadSentimentSummary();
    } catch (err: any) {
      setSeedStatus(err?.message || "Failed to seed MarketPulse data.");
    } finally {
      setIsSeeding(false);
    }
  };

  // Load Macroeconomic catalog & active series
  useEffect(() => {
    if (activeTab === "macro") {
      loadMacroCatalog();
    }
  }, [activeTab]);

  const loadMacroCatalog = async () => {
    setIsLoadingMacro(true);
    try {
      const list = await api.listMacroSeries();
      setMacroSeriesList(list);
      if (list.length > 0) {
        const targetId = selectedMacroId || list[0].series_id;
        setSelectedMacroId(targetId);
        const detail = await api.getMacroSeriesHistory(targetId);
        setSelectedMacroHistory(detail);
      }
    } catch (err) {
      console.error("Failed to load macro series:", err);
    } finally {
      setIsLoadingMacro(false);
    }
  };

  useEffect(() => {
    if (selectedMacroId && activeTab === "macro") {
      api.getMacroSeriesHistory(selectedMacroId)
        .then((detail) => setSelectedMacroHistory(detail))
        .catch((err) => console.error("Failed to load series history:", err));
    }
  }, [selectedMacroId]);

  // Load Sentiment Summary
  useEffect(() => {
    if (activeTab === "sentiment") {
      loadSentimentSummary();
    }
  }, [activeTab, sentimentDays]);

  const loadSentimentSummary = async () => {
    setIsLoadingSentiment(true);
    try {
      const sum = await api.getSentimentSummary({ days: sentimentDays });
      setSentimentSummary(sum);
    } catch (err) {
      console.error("Failed to load sentiment summary:", err);
    } finally {
      setIsLoadingSentiment(false);
    }
  };

  // Load Watchlists & Alerts
  useEffect(() => {
    if (activeTab === "watchlist") {
      loadWatchlists();
      loadAlertsAndNotifications();
    }
  }, [activeTab]);

  const loadWatchlists = async () => {
    try {
      const list = await api.listWatchlists();
      setWatchlists(list);
      if (list.length > 0) {
        const targetId = activeWatchlistId && list.some((w) => w.id === activeWatchlistId)
          ? activeWatchlistId
          : list[0].id;
        setActiveWatchlistId(targetId);
        const detail = await api.getWatchlist(targetId);
        setActiveWatchlist(detail);
      } else {
        setActiveWatchlist(null);
      }
    } catch (err) {
      console.error("Failed to load watchlists:", err);
    }
  };

  const loadAlertsAndNotifications = async () => {
    try {
      const [alertList, notifList] = await Promise.all([
        api.listAlerts(),
        api.listNotifications(20),
      ]);
      setAlerts(alertList);
      setNotifications(notifList);
    } catch (err) {
      console.error("Failed to load alerts:", err);
    }
  };

  const handleSelectWatchlist = async (id: string) => {
    setActiveWatchlistId(id);
    try {
      const detail = await api.getWatchlist(id);
      setActiveWatchlist(detail);
    } catch (err) {
      console.error("Failed to load watchlist details:", err);
    }
  };

  const handleCreateWatchlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWatchlistName.trim()) return;
    setIsCreatingWatchlist(true);
    try {
      const created = await api.createWatchlist({ name: newWatchlistName.trim() });
      setNewWatchlistName("");
      await loadWatchlists();
      setActiveWatchlistId(created.id);
      setActiveWatchlist(created);
    } catch (err: any) {
      alert(err?.message || "Failed to create watchlist.");
    } finally {
      setIsCreatingWatchlist(false);
    }
  };

  const handleAddInstrumentToWatchlist = async () => {
    if (!activeWatchlistId || !addInstrumentId) return;
    try {
      await api.addWatchlistItem(activeWatchlistId, { instrument_id: addInstrumentId });
      setAddInstrumentId("");
      const updated = await api.getWatchlist(activeWatchlistId);
      setActiveWatchlist(updated);
      await loadWatchlists();
    } catch (err: any) {
      alert(err?.message || "Failed to add instrument.");
    }
  };

  const handleRemoveInstrumentFromWatchlist = async (instId: string) => {
    if (!activeWatchlistId) return;
    try {
      await api.removeWatchlistItem(activeWatchlistId, instId);
      const updated = await api.getWatchlist(activeWatchlistId);
      setActiveWatchlist(updated);
      await loadWatchlists();
    } catch (err: any) {
      alert(err?.message || "Failed to remove instrument.");
    }
  };

  const handleDeleteWatchlist = async () => {
    if (!activeWatchlistId || !confirm("Are you sure you want to delete this watchlist?")) return;
    try {
      await api.deleteWatchlist(activeWatchlistId);
      setActiveWatchlistId("");
      await loadWatchlists();
    } catch (err: any) {
      alert(err?.message || "Failed to delete watchlist.");
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAlertKeyword && !newAlertInstrumentId) {
      alert("Please enter a keyword or select an instrument for the alert.");
      return;
    }
    setIsCreatingAlert(true);
    try {
      await api.createAlert({
        keyword: newAlertKeyword.trim() || undefined,
        instrument_id: newAlertInstrumentId || undefined,
        target_sentiment: newAlertSentiment !== "ALL" ? newAlertSentiment : undefined,
      });
      setNewAlertKeyword("");
      setNewAlertInstrumentId("");
      setNewAlertSentiment("ALL");
      await loadAlertsAndNotifications();
    } catch (err: any) {
      alert(err?.message || "Failed to create alert.");
    } finally {
      setIsCreatingAlert(false);
    }
  };

  const handleDeleteAlert = async (id: string) => {
    try {
      await api.deleteAlert(id);
      await loadAlertsAndNotifications();
    } catch (err: any) {
      alert(err?.message || "Failed to delete alert.");
    }
  };

  const handleMarkNotificationRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      console.error("Failed to mark notification read:", err);
    }
  };

  return (
    <DashboardLayout title="MarketPulse — Financial News & Macro Intelligence">
      <div className="space-y-6">
        {/* Header with Demo Badge and Quick Seed Button */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500/20 to-emerald-500/10 border border-teal-500/30 flex items-center justify-center text-[#71d5b3]">
                <Newspaper size={20} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-[#edf3fa]">MarketPulse</h1>
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-950/80 text-[#71d5b3] border border-emerald-600/40">
                    Market Intelligence Wire
                  </span>
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-950/80 text-amber-300 border border-amber-600/40 flex items-center gap-1">
                    <ShieldAlert size={10} />
                    Synthetic Demo Wire
                  </span>
                </div>
                <p className="text-xs text-[#91a0b3] mt-0.5">
                  Institutional financial news ingestion, domain-weighted sentiment NLP, macroeconomic indicator tracking, and custom watchlists.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/ai?explain=market"
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#15273b] hover:bg-[#1a334e] text-[#71d5b3] border border-[#1e3e4a] flex items-center gap-1.5 transition-all"
            >
              Explain with Copilot
            </Link>
            <button
              onClick={handleSeedMarketPulse}
              disabled={isSeeding}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#142233] hover:bg-[#1a2c42] text-[#71d5b3] border border-emerald-500/30 flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              {isSeeding ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
              {isSeeding ? "Seeding Wire..." : "Seed MarketPulse Wire"}
            </button>
          </div>
        </div>

        {/* Status Notification */}
        {seedStatus && (
          <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-600/40 text-xs text-emerald-300 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <CheckCircle2 size={14} className="text-[#71d5b3]" />
              {seedStatus}
            </span>
            <button onClick={() => setSeedStatus(null)} className="text-emerald-400 hover:text-white">
              <X size={14} />
            </button>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex border-b border-[#1e2d3e] gap-1 overflow-x-auto pb-0">
          <button
            onClick={() => setActiveTab("feed")}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg flex items-center gap-2 transition-all ${
              activeTab === "feed"
                ? "bg-[#0e1724] text-[#71d5b3] border-t-2 border-t-[#71d5b3] border-x border-[#1e2d3e]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#121d2d]"
            }`}
          >
            <Newspaper size={14} />
            Financial News Wire
            <span className="text-[10px] bg-[#142030] text-[#91a0b3] px-1.5 py-0.2 rounded-full ml-1">
              {totalArticles}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("macro")}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg flex items-center gap-2 transition-all ${
              activeTab === "macro"
                ? "bg-[#0e1724] text-[#71d5b3] border-t-2 border-t-[#71d5b3] border-x border-[#1e2d3e]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#121d2d]"
            }`}
          >
            <Landmark size={14} />
            Macroeconomic Intelligence
          </button>

          <button
            onClick={() => setActiveTab("sentiment")}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg flex items-center gap-2 transition-all ${
              activeTab === "sentiment"
                ? "bg-[#0e1724] text-[#71d5b3] border-t-2 border-t-[#71d5b3] border-x border-[#1e2d3e]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#121d2d]"
            }`}
          >
            <Activity size={14} />
            Sentiment Trends
          </button>

          <button
            onClick={() => setActiveTab("watchlist")}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg flex items-center gap-2 transition-all ${
              activeTab === "watchlist"
                ? "bg-[#0e1724] text-[#71d5b3] border-t-2 border-t-[#71d5b3] border-x border-[#1e2d3e]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#121d2d]"
            }`}
          >
            <Bookmark size={14} />
            Watchlists & Alerts
            {notifications.filter((n) => !n.is_read).length > 0 && (
              <span className="text-[10px] bg-emerald-500 text-[#080d16] font-bold px-1.5 py-0.2 rounded-full ml-1">
                {notifications.filter((n) => !n.is_read).length}
              </span>
            )}
          </button>
        </div>

        {/* TAB 1: FINANCIAL NEWS WIRE */}
        {activeTab === "feed" && (
          <div className="space-y-4">
            {/* Filter Bar */}
            <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
              <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
                {/* Search input */}
                <div className="relative flex-1">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#91a0b3]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setPage(1);
                    }}
                    placeholder="Search news by headline, keyword (e.g. RBI, TCS, 5G, inflation)..."
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] placeholder-[#556982] focus:outline-none focus:border-[#71d5b3]"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery("")}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#91a0b3] hover:text-white"
                    >
                      <X size={12} />
                    </button>
                  )}
                </div>

                {/* Filters */}
                <div className="flex flex-wrap items-center gap-2">
                  {/* Category Pills */}
                  <div className="flex rounded-lg bg-[#080d16] p-1 border border-[#1e2d3e]">
                    {["All", "MARKETS", "EQUITY", "ECONOMY", "BANKING"].map((cat) => (
                      <button
                        key={cat}
                        onClick={() => {
                          setCategoryFilter(cat);
                          setPage(1);
                        }}
                        className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                          categoryFilter === cat
                            ? "bg-[#1e2d3e] text-[#71d5b3] font-semibold"
                            : "text-[#91a0b3] hover:text-[#edf3fa]"
                        }`}
                      >
                        {cat === "All" ? "All Categories" : cat}
                      </button>
                    ))}
                  </div>

                  {/* Sentiment Filter */}
                  <select
                    value={sentimentFilter}
                    onChange={(e) => {
                      setSentimentFilter(e.target.value);
                      setPage(1);
                    }}
                    className="px-2.5 py-1.5 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  >
                    <option value="All">All Sentiments</option>
                    <option value="POSITIVE">Positive</option>
                    <option value="NEUTRAL">Neutral</option>
                    <option value="NEGATIVE">Negative</option>
                  </select>

                  {/* Company Filter */}
                  <select
                    value={selectedInstrumentFilter}
                    onChange={(e) => {
                      setSelectedInstrumentFilter(e.target.value);
                      setPage(1);
                    }}
                    className="px-2.5 py-1.5 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3] max-w-[160px] truncate"
                  >
                    <option value="">All Companies</option>
                    {instruments.map((inst) => (
                      <option key={inst.id} value={inst.id}>
                        {inst.symbol} - {inst.company_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Articles List */}
            {isLoadingNews ? (
              <div className="p-16 text-center rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
                <Loader2 size={24} className="animate-spin text-[#71d5b3] mx-auto mb-3" />
                <p className="text-xs text-[#91a0b3]">Ingesting news feed and computing domain sentiment...</p>
              </div>
            ) : news.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                <AlertCircle size={32} className="text-amber-400 mx-auto" />
                <h3 className="text-sm font-semibold text-[#edf3fa]">No News Articles Found</h3>
                <p className="text-xs text-[#91a0b3] max-w-md mx-auto">
                  No articles matched your filter criteria. Try resetting filters or seed the MarketPulse demo wire.
                </p>
                <button
                  onClick={handleSeedMarketPulse}
                  disabled={isSeeding}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#71d5b3] text-[#080d16] hover:bg-[#5bc29f] transition-all inline-flex items-center gap-1.5"
                >
                  <RefreshCw size={13} />
                  Initialize MarketPulse Wire
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {news.map((item) => {
                  const sentiment = item.sentiment?.sentiment_label || "NEUTRAL";
                  const sentimentColor =
                    sentiment === "POSITIVE"
                      ? "bg-emerald-950/60 text-[#71d5b3] border-emerald-600/40"
                      : sentiment === "NEGATIVE"
                      ? "bg-rose-950/60 text-rose-300 border-rose-600/40"
                      : "bg-[#142030] text-[#91a0b3] border-[#1e2d3e]";

                  return (
                    <div
                      key={item.id}
                      className="p-5 rounded-xl bg-[#0e1724] border border-[#1e2d3e] hover:border-[#2d425c] transition-all space-y-3"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          <span className="font-semibold text-[#71d5b3]">
                            {item.source_name || "QuantWeave Wire"}
                          </span>
                          <span className="text-[#556982]">•</span>
                          <span className="text-[#91a0b3]">
                            {new Date(item.published_at).toLocaleString("en-IN", {
                              dateStyle: "medium",
                              timeStyle: "short",
                            })}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-[#142233] text-[#91a0b3] border border-[#1e2d3e]">
                            {item.category}
                          </span>
                          {item.is_demo && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-600/30">
                              DEMO
                            </span>
                          )}
                        </div>

                        {/* Sentiment badge */}
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border flex items-center gap-1 ${sentimentColor}`}
                          >
                            {sentiment === "POSITIVE" && <ArrowUpRight size={12} />}
                            {sentiment === "NEGATIVE" && <ArrowDownRight size={12} />}
                            {sentiment} ({item.sentiment ? Math.round(item.sentiment.confidence * 100) : 50}%)
                          </span>
                        </div>
                      </div>

                      {/* Headline */}
                      <h3 className="text-base font-bold text-[#edf3fa] leading-snug">
                        {item.title}
                      </h3>

                      {/* Description */}
                      {item.short_description && (
                        <p className="text-xs text-[#91a0b3] leading-relaxed">
                          {item.short_description}
                        </p>
                      )}

                      {/* Footer: Linked Companies & Publisher Link */}
                      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[#1e2d3e]">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-[11px] text-[#556982]">Tagged Equities:</span>
                          {item.linked_instruments && item.linked_instruments.length > 0 ? (
                            item.linked_instruments.map((inst) => (
                              <Link
                                key={inst.id}
                                href={`/instruments/${inst.id}`}
                                className="text-[11px] font-semibold px-2 py-0.5 rounded bg-[#15273b] text-[#71d5b3] hover:underline border border-[#1e2d3e]"
                              >
                                {inst.symbol}
                              </Link>
                            ))
                          ) : (
                            <span className="text-[11px] text-[#556982]">Macro / Sector-wide</span>
                          )}
                        </div>

                        <a
                          href={item.canonical_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-[#71d5b3] hover:underline flex items-center gap-1 font-semibold"
                        >
                          Publisher Article <ExternalLink size={12} />
                        </a>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="p-3 rounded-xl bg-[#0e1724] border border-[#1e2d3e] flex items-center justify-between text-xs text-[#91a0b3]">
                <span>
                  Showing page {page} of {totalPages} ({totalArticles} articles)
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-1.5 rounded-lg bg-[#142030] text-[#edf3fa] disabled:opacity-30 hover:bg-[#1b2b40]"
                  >
                    <ChevronLeft size={14} />
                  </button>
                  <span className="px-3 font-semibold text-[#edf3fa]">{page}</span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-1.5 rounded-lg bg-[#142030] text-[#edf3fa] disabled:opacity-30 hover:bg-[#1b2b40]"
                  >
                    <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: MACROECONOMIC INTELLIGENCE */}
        {activeTab === "macro" && (
          <div className="space-y-6">
            {/* KPI Cards for Key Indian Macro Indicators */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {macroSeriesList.map((s) => {
                const isSelected = selectedMacroId === s.series_id;
                return (
                  <button
                    key={s.series_id}
                    onClick={() => setSelectedMacroId(s.series_id)}
                    className={`p-5 rounded-2xl border text-left transition-all ${
                      isSelected
                        ? "bg-[#142233] border-[#71d5b3] shadow-lg shadow-emerald-950/20"
                        : "bg-[#0e1724] border-[#1e2d3e] hover:border-[#2d425c]"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px] text-[#556982] mb-1">
                      <span className="truncate max-w-[150px]">{s.source}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#080d16] text-[#91a0b3]">
                        {s.frequency}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-[#edf3fa] line-clamp-1">{s.name}</h3>

                    <div className="mt-3 flex items-baseline justify-between">
                      <span className="text-2xl font-black text-[#71d5b3]">
                        {s.latest_observation ? `${s.latest_observation.value.toFixed(2)}${s.unit}` : "—"}
                      </span>
                      {s.latest_observation && (
                        <span className="text-[10px] text-[#556982]">
                          As of {s.latest_observation.observation_date}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Historical Macro Chart & Overview */}
            {selectedMacroHistory && (
              <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold text-[#71d5b3]">{selectedMacroHistory.source}</span>
                      <span className="text-xs text-[#556982]">•</span>
                      <span className="text-xs text-[#91a0b3]">Frequency: {selectedMacroHistory.frequency}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-600/30">
                        DEMO DATA
                      </span>
                    </div>
                    <h2 className="text-lg font-bold text-[#edf3fa]">{selectedMacroHistory.name}</h2>
                    <p className="text-xs text-[#556982] mt-0.5">{selectedMacroHistory.description}</p>
                  </div>

                  <div className="p-3 rounded-xl bg-[#080d16] border border-[#1e2d3e] text-right">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Latest Value</span>
                    <span className="text-xl font-black text-[#71d5b3]">
                      {selectedMacroHistory.latest_observation
                        ? `${selectedMacroHistory.latest_observation.value.toFixed(2)}${selectedMacroHistory.unit}`
                        : "—"}
                    </span>
                  </div>
                </div>

                {/* SVG Time-Series Chart */}
                <div className="h-64 w-full relative pt-2">
                  {selectedMacroHistory.observations.length >= 2 ? (
                    (() => {
                      const width = 800;
                      const height = 240;
                      const padL = 50;
                      const padR = 20;
                      const padT = 20;
                      const padB = 30;

                      const obs = selectedMacroHistory?.observations || [];
                      if (obs.length < 2) {
                        return (
                          <div className="h-full flex items-center justify-center text-xs text-[#556982]">
                            Insufficient historical observation points for charting.
                          </div>
                        );
                      }

                      const vals = obs.map((o) => Number(o.value)).filter((v) => Number.isFinite(v));
                      const minVal = vals.length > 0 ? Math.min(...vals) * 0.95 : 0;
                      const maxVal = vals.length > 0 ? Math.max(...vals) * 1.05 : 100;
                      const rangeVal = maxVal - minVal <= 0 ? 1 : maxVal - minVal;
                      const count = obs.length;
                      const divisor = count > 1 ? count - 1 : 1;

                      const points = obs.map((o, idx) => {
                        const val = Number.isFinite(Number(o.value)) ? Number(o.value) : minVal;
                        const rawX = padL + (idx / divisor) * (width - padL - padR);
                        const rawY = padT + (1 - (val - minVal) / rangeVal) * (height - padT - padB);
                        return {
                          x: Number.isFinite(rawX) ? rawX : padL,
                          y: Number.isFinite(rawY) ? rawY : padT,
                          data: o,
                        };
                      });

                      const validPoints = points.filter((pt) => Number.isFinite(pt.x) && Number.isFinite(pt.y));
                      if (validPoints.length === 0) {
                        return (
                          <div className="h-full flex items-center justify-center text-xs text-[#556982]">
                            No valid chart coordinates available.
                          </div>
                        );
                      }

                      const pathD = validPoints.reduce(
                        (acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`),
                        ""
                      );
                      const areaD = validPoints.length > 1
                        ? `${pathD} L ${validPoints[validPoints.length - 1].x} ${height - padB} L ${validPoints[0].x} ${height - padB} Z`
                        : "";

                      return (
                        <svg
                          viewBox={`0 0 ${width} ${height}`}
                          className="w-full h-full overflow-visible"
                          onMouseLeave={() => setMacroHoverPoint(null)}
                        >
                          <defs>
                            <linearGradient id="macroGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#71d5b3" stopOpacity="0.25" />
                              <stop offset="100%" stopColor="#71d5b3" stopOpacity="0.0" />
                            </linearGradient>
                          </defs>

                          {/* Grid lines */}
                          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                            const y = padT + pct * (height - padT - padB);
                            const val = maxVal - pct * rangeVal;
                            return (
                              <g key={i}>
                                <line x1={padL} y1={y} x2={width - padR} y2={y} stroke="#1e2d3e" strokeDasharray="4 4" />
                                <text x={padL - 8} y={y + 3} textAnchor="end" fill="#556982" fontSize="10">
                                  {val.toFixed(2)}{selectedMacroHistory.unit}
                                </text>
                              </g>
                            );
                          })}

                          {areaD && <path d={areaD} fill="url(#macroGrad)" />}
                          {pathD && <path d={pathD} fill="none" stroke="#71d5b3" strokeWidth="2.5" />}

                          {validPoints.map((pt, i) => (
                            <circle
                              key={i}
                              cx={pt.x}
                              cy={pt.y}
                              r={macroHoverPoint?.date === pt.data.observation_date ? 5 : 3}
                              fill="#71d5b3"
                              className="opacity-0 hover:opacity-100 cursor-pointer"
                              onMouseEnter={() =>
                                setMacroHoverPoint({ date: pt.data.observation_date, value: pt.data.value })
                              }
                            />
                          ))}

                          {/* Axis dates */}
                          <text x={padL} y={height - 8} textAnchor="start" fill="#556982" fontSize="10">
                            {obs[0]?.observation_date || ""}
                          </text>
                          <text x={width - padR} y={height - 8} textAnchor="end" fill="#556982" fontSize="10">
                            {obs[obs.length - 1]?.observation_date || ""}
                          </text>
                        </svg>
                      );
                    })()
                  ) : (
                    <div className="h-full flex items-center justify-center text-xs text-[#556982]">
                      Insufficient observations.
                    </div>
                  )}
                </div>

                {macroHoverPoint && (
                  <div className="p-2.5 rounded-lg bg-[#080d16] border border-[#1e2d3e] text-xs text-[#edf3fa] inline-block">
                    Observation on <strong>{macroHoverPoint.date}</strong>:{" "}
                    <span className="font-bold text-[#71d5b3]">
                      {macroHoverPoint.value.toFixed(2)}{selectedMacroHistory.unit}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: SENTIMENT TRENDS */}
        {activeTab === "sentiment" && (
          <div className="space-y-6">
            {/* Controls */}
            <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-bold text-[#edf3fa] flex items-center gap-2">
                  <Activity size={18} className="text-[#71d5b3]" />
                  Market Sentiment Barometer
                </h2>
                <p className="text-xs text-[#556982]">
                  Aggregated financial media sentiment scores computed via QuantWeave's domain NLP engine.
                </p>
              </div>

              {/* Time window selector */}
              <div className="flex rounded-lg bg-[#080d16] p-1 border border-[#1e2d3e]">
                {[7, 30, 90].map((d) => (
                  <button
                    key={d}
                    onClick={() => setSentimentDays(d)}
                    className={`px-3 py-1 text-xs rounded-md font-semibold transition-all ${
                      sentimentDays === d
                        ? "bg-[#1e2d3e] text-[#71d5b3]"
                        : "text-[#91a0b3] hover:text-[#edf3fa]"
                    }`}
                  >
                    {d} Days
                  </button>
                ))}
              </div>
            </div>

            {isLoadingSentiment ? (
              <div className="p-16 text-center rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
                <Loader2 size={24} className="animate-spin text-[#71d5b3] mx-auto mb-3" />
                <p className="text-xs text-[#91a0b3]">Aggregating article sentiment distributions...</p>
              </div>
            ) : sentimentSummary ? (
              <div className="space-y-6">
                {/* Sentiment Gauge KPI Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Overall Bias</span>
                    <span className={`text-2xl font-black mt-1 block ${
                      sentimentSummary.overall_classification === "BULLISH"
                        ? "text-[#71d5b3]"
                        : sentimentSummary.overall_classification === "BEARISH"
                        ? "text-rose-400"
                        : "text-sky-300"
                    }`}>
                      {sentimentSummary.overall_classification}
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      Net Score: {sentimentSummary.net_sentiment_score > 0 ? "+" : ""}{sentimentSummary.net_sentiment_score.toFixed(2)}
                    </span>
                  </div>

                  <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Positive Tone</span>
                    <span className="text-2xl font-black text-[#71d5b3] mt-1 block">
                      {sentimentSummary.positive_pct}%
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      {sentimentSummary.positive_count} articles
                    </span>
                  </div>

                  <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Negative Tone</span>
                    <span className="text-2xl font-black text-rose-400 mt-1 block">
                      {sentimentSummary.negative_pct}%
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      {sentimentSummary.negative_count} articles
                    </span>
                  </div>

                  <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Model Confidence</span>
                    <span className="text-2xl font-black text-sky-400 mt-1 block">
                      {Math.round(sentimentSummary.average_confidence * 100)}%
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      Based on {sentimentSummary.total_articles} articles
                    </span>
                  </div>
                </div>

                {/* Sentiment Distribution Bar */}
                <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                  <h3 className="text-sm font-bold text-[#edf3fa]">Sentiment Distribution Breakdown</h3>
                  <div className="h-4 w-full bg-[#080d16] rounded-full overflow-hidden flex border border-[#1e2d3e]">
                    <div
                      style={{ width: `${sentimentSummary.positive_pct}%` }}
                      className="bg-emerald-500 h-full"
                      title={`Positive: ${sentimentSummary.positive_pct}%`}
                    />
                    <div
                      style={{ width: `${sentimentSummary.neutral_pct}%` }}
                      className="bg-slate-500 h-full"
                      title={`Neutral: ${sentimentSummary.neutral_pct}%`}
                    />
                    <div
                      style={{ width: `${sentimentSummary.negative_pct}%` }}
                      className="bg-rose-500 h-full"
                      title={`Negative: ${sentimentSummary.negative_pct}%`}
                    />
                  </div>

                  <div className="flex items-center justify-between text-xs text-[#91a0b3]">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                      Positive ({sentimentSummary.positive_pct}%)
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-slate-500 inline-block" />
                      Neutral ({sentimentSummary.neutral_pct}%)
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
                      Negative ({sentimentSummary.negative_pct}%)
                    </span>
                  </div>
                </div>

                {/* Disclaimer */}
                <div className="p-4 rounded-xl bg-[#142030] border border-[#1e2d3e] text-xs text-[#91a0b3] flex items-center gap-2">
                  <ShieldAlert size={16} className="text-amber-400 shrink-0" />
                  <span>{sentimentSummary.disclaimer}</span>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* TAB 4: WATCHLISTS & ALERTS */}
        {activeTab === "watchlist" && (
          <div className="space-y-6">
            {/* Watchlist Management Header */}
            <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-[#91a0b3]">Active Watchlist:</span>
                  <select
                    value={activeWatchlistId}
                    onChange={(e) => handleSelectWatchlist(e.target.value)}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  >
                    {watchlists.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name} ({w.items.length} stocks)
                      </option>
                    ))}
                  </select>

                  {activeWatchlistId && (
                    <button
                      onClick={handleDeleteWatchlist}
                      className="p-1.5 text-xs text-rose-400 hover:text-white rounded bg-rose-950/40 border border-rose-600/30"
                      title="Delete Watchlist"
                    >
                      <Trash2 size={13} />
                    </button>
                  )}
                </div>

                {/* Create Watchlist Form */}
                <form onSubmit={handleCreateWatchlist} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={newWatchlistName}
                    onChange={(e) => setNewWatchlistName(e.target.value)}
                    placeholder="New watchlist name..."
                    className="px-3 py-1.5 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] placeholder-[#556982] focus:outline-none focus:border-[#71d5b3]"
                  />
                  <button
                    type="submit"
                    disabled={isCreatingWatchlist || !newWatchlistName.trim()}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#71d5b3] text-[#080d16] hover:bg-[#5bc29f] transition-all flex items-center gap-1 disabled:opacity-50"
                  >
                    <Plus size={13} />
                    Create
                  </button>
                </form>
              </div>

              {/* Add Instrument to Watchlist */}
              {activeWatchlist && (
                <div className="pt-3 border-t border-[#1e2d3e] flex flex-wrap items-center gap-3">
                  <span className="text-xs text-[#91a0b3]">Add Stock to Watchlist:</span>
                  <select
                    value={addInstrumentId}
                    onChange={(e) => setAddInstrumentId(e.target.value)}
                    className="px-3 py-1.5 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  >
                    <option value="">Select Company...</option>
                    {instruments
                      .filter((inst) => !activeWatchlist.items.some((itm) => itm.instrument_id === inst.id))
                      .map((inst) => (
                        <option key={inst.id} value={inst.id}>
                          {inst.symbol} - {inst.company_name}
                        </option>
                      ))}
                  </select>
                  <button
                    onClick={handleAddInstrumentToWatchlist}
                    disabled={!addInstrumentId}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#142030] hover:bg-[#1a2d42] text-[#71d5b3] border border-[#1e2d3e] disabled:opacity-50"
                  >
                    Add
                  </button>
                </div>
              )}
            </div>

            {/* Watchlist Items & Watched News Grid */}
            {activeWatchlist && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Watched Companies List */}
                <div className="lg:col-span-1 p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                  <h3 className="text-sm font-bold text-[#edf3fa] flex items-center justify-between">
                    <span>Monitored Stocks ({activeWatchlist.items.length})</span>
                  </h3>

                  {activeWatchlist.items.length === 0 ? (
                    <p className="text-xs text-[#556982] py-4 text-center">
                      No stocks in this watchlist yet. Add some above to track their news and events!
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {activeWatchlist.items.map((item) => (
                        <div
                          key={item.id}
                          className="p-3 rounded-xl bg-[#080d16] border border-[#1e2d3e] flex items-center justify-between"
                        >
                          <div>
                            <Link
                              href={`/instruments/${item.instrument_id}`}
                              className="text-xs font-bold text-[#71d5b3] hover:underline"
                            >
                              {item.symbol}
                            </Link>
                            <span className="text-[11px] text-[#91a0b3] block truncate max-w-[160px]">
                              {item.company_name}
                            </span>
                          </div>
                          <button
                            onClick={() => handleRemoveInstrumentFromWatchlist(item.instrument_id)}
                            className="text-[#556982] hover:text-rose-400 p-1"
                            title="Remove"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* News for Watched Companies */}
                <div className="lg:col-span-2 p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                  <h3 className="text-sm font-bold text-[#edf3fa]">
                    Curated News for Watched Equities
                  </h3>

                  {activeWatchlist.latest_news.length === 0 ? (
                    <p className="text-xs text-[#556982] py-4 text-center">
                      No recent headlines found for watched companies. Seed the demo news wire or add active tickers!
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {activeWatchlist.latest_news.map((item) => (
                        <div
                          key={item.id}
                          className="p-4 rounded-xl bg-[#080d16] border border-[#1e2d3e] space-y-2"
                        >
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-[#71d5b3] font-semibold">{item.source_name}</span>
                            <span className="text-[10px] text-[#556982]">
                              {new Date(item.published_at).toLocaleDateString("en-IN")}
                            </span>
                          </div>
                          <h4 className="text-xs font-bold text-[#edf3fa]">{item.title}</h4>
                          <p className="text-[11px] text-[#91a0b3] line-clamp-2">
                            {item.short_description}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* In-App Alerts Configuration & Notifications */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Alert Creation */}
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                <h3 className="text-sm font-bold text-[#edf3fa] flex items-center gap-2">
                  <Bell size={16} className="text-[#71d5b3]" />
                  Configure News & Sentiment Alert
                </h3>
                <p className="text-xs text-[#556982]">
                  Receive in-app alerts whenever headlines mention a keyword or ticker with specific sentiment.
                </p>

                <form onSubmit={handleCreateAlert} className="space-y-3">
                  <div>
                    <label className="text-[11px] text-[#91a0b3] block mb-1">Alert Keyword</label>
                    <input
                      type="text"
                      value={newAlertKeyword}
                      onChange={(e) => setNewAlertKeyword(e.target.value)}
                      placeholder="e.g. cloud, dividend, inflation..."
                      className="w-full px-3 py-2 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] text-[#91a0b3] block mb-1">Company (Optional)</label>
                      <select
                        value={newAlertInstrumentId}
                        onChange={(e) => setNewAlertInstrumentId(e.target.value)}
                        className="w-full px-2.5 py-2 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                      >
                        <option value="">Any Company</option>
                        {instruments.map((inst) => (
                          <option key={inst.id} value={inst.id}>
                            {inst.symbol}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="text-[11px] text-[#91a0b3] block mb-1">Sentiment Condition</label>
                      <select
                        value={newAlertSentiment}
                        onChange={(e) => setNewAlertSentiment(e.target.value)}
                        className="w-full px-2.5 py-2 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                      >
                        <option value="ALL">Any Sentiment</option>
                        <option value="POSITIVE">Only Positive</option>
                        <option value="NEGATIVE">Only Negative</option>
                      </select>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isCreatingAlert}
                    className="w-full py-2 text-xs font-bold rounded-lg bg-[#71d5b3] text-[#080d16] hover:bg-[#5bc29f] transition-all"
                  >
                    Save Alert Rule
                  </button>
                </form>

                {/* Active Alerts List */}
                <div className="pt-3 border-t border-[#1e2d3e] space-y-2">
                  <span className="text-[11px] text-[#556982] uppercase tracking-wider block">Active Rules</span>
                  {alerts.map((al) => (
                    <div
                      key={al.id}
                      className="p-2.5 rounded-lg bg-[#080d16] border border-[#1e2d3e] flex items-center justify-between text-xs"
                    >
                      <span className="text-[#edf3fa]">
                        Keyword: <strong>{al.keyword || "Any"}</strong>
                        {al.target_sentiment && ` • ${al.target_sentiment}`}
                      </span>
                      <button
                        onClick={() => handleDeleteAlert(al.id)}
                        className="text-[#556982] hover:text-rose-400"
                      >
                        <X size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* In-App Notifications Feed */}
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                <h3 className="text-sm font-bold text-[#edf3fa] flex items-center justify-between">
                  <span>In-App Event Notifications</span>
                  <span className="text-[10px] text-[#556982] font-normal">
                    {notifications.filter((n) => !n.is_read).length} unread
                  </span>
                </h3>

                {notifications.length === 0 ? (
                  <p className="text-xs text-[#556982] py-8 text-center">
                    No triggered notifications. Seed news or wait for incoming matching wire articles.
                  </p>
                ) : (
                  <div className="space-y-2.5 max-h-80 overflow-y-auto">
                    {notifications.map((notif) => (
                      <div
                        key={notif.id}
                        className={`p-3 rounded-xl border text-xs transition-all flex items-start justify-between gap-3 ${
                          notif.is_read
                            ? "bg-[#080d16] border-[#1e2d3e] opacity-60"
                            : "bg-[#142233] border-emerald-500/30"
                        }`}
                      >
                        <div>
                          <div className="flex items-center gap-1.5 font-bold text-[#edf3fa] mb-0.5">
                            {!notif.is_read && (
                              <span className="w-1.5 h-1.5 rounded-full bg-[#71d5b3] inline-block" />
                            )}
                            {notif.title}
                          </div>
                          <p className="text-[#91a0b3] text-[11px]">{notif.message}</p>
                          <span className="text-[9px] text-[#556982] mt-1 block">
                            {new Date(notif.created_at).toLocaleString("en-IN")}
                          </span>
                        </div>

                        {!notif.is_read && (
                          <button
                            onClick={() => handleMarkNotificationRead(notif.id)}
                            className="px-2 py-1 text-[10px] font-semibold rounded bg-[#1e2d3e] text-[#71d5b3] hover:bg-[#2a3e54] shrink-0"
                          >
                            Mark Read
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
