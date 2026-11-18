"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  PieChart,
  TrendingUp,
  Calculator,
  Scale,
  Search,
  Filter,
  ArrowRight,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  Layers,
  ShieldAlert,
  Info,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Plus,
  X,
  ChevronLeft,
  ChevronRight,
  Database,
  BarChart3,
  Award,
  DollarSign,
  TrendingDown,
} from "lucide-react";
import { DashboardLayout } from "@/components/DashboardLayout";
import {
  api,
  MutualFund,
  MutualFundDetail,
  FundNAVPoint,
  FundNAVHistoryResponse,
  FundAnalyticsResponse,
  SIPCalculatorResponse,
  LumpSumCalculatorResponse,
  FundComparisonResponse,
  FundCategoriesResponse,
} from "@/lib/api";

type ActiveTab = "directory" | "analytics" | "sip" | "compare";
type ChartPeriod = "1M" | "3M" | "6M" | "1Y" | "2Y" | "ALL";

const COMPARISON_COLORS = [
  { stroke: "#71d5b3", fill: "rgba(113, 213, 179, 0.15)", text: "text-[#71d5b3]", border: "border-emerald-600/40", bg: "bg-emerald-950/40" },
  { stroke: "#38bdf8", fill: "rgba(56, 189, 248, 0.15)", text: "text-sky-400", border: "border-sky-600/40", bg: "bg-sky-950/40" },
  { stroke: "#f59e0b", fill: "rgba(245, 158, 11, 0.15)", text: "text-amber-400", border: "border-amber-600/40", bg: "bg-amber-950/40" },
  { stroke: "#c084fc", fill: "rgba(192, 132, 252, 0.15)", text: "text-purple-400", border: "border-purple-600/40", bg: "bg-purple-950/40" },
];

export default function FundsPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("directory");

  // Global fund catalog state
  const [funds, setFunds] = useState<MutualFund[]>([]);
  const [totalFunds, setTotalFunds] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(12);
  const [totalPages, setTotalPages] = useState(1);
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [subcategoryFilter, setSubcategoryFilter] = useState("All");
  const [amcFilter, setAmcFilter] = useState("All");
  const [planFilter, setPlanFilter] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [categoriesData, setCategoriesData] = useState<FundCategoriesResponse>({
    categories: [],
    subcategories: [],
    amcs: [],
  });

  const [isLoadingDirectory, setIsLoadingDirectory] = useState(true);
  const [isSeeding, setIsSeeding] = useState(false);
  const [seedStatus, setSeedStatus] = useState<string | null>(null);

  // Selected Fund for Deep Dive
  const [selectedFundId, setSelectedFundId] = useState<string>("");
  const [fundDetail, setFundDetail] = useState<MutualFundDetail | null>(null);
  const [fundAnalytics, setFundAnalytics] = useState<FundAnalyticsResponse | null>(null);
  const [navHistory, setNavHistory] = useState<FundNAVPoint[]>([]);
  const [chartPeriod, setChartPeriod] = useState<ChartPeriod>("1Y");
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
  const [navChartHover, setNavChartHover] = useState<FundNAVPoint | null>(null);

  // SIP & Lump-Sum Calculator state
  const [calcMode, setCalcMode] = useState<"sip" | "lumpsum">("sip");
  const [sipFundId, setSipFundId] = useState<string>("");
  const [sipMonthlyAmount, setSipMonthlyAmount] = useState<number>(5000);
  const [sipStartDate, setSipStartDate] = useState<string>("2024-01-05");
  const [sipEndDate, setSipEndDate] = useState<string>("2025-01-05");
  const [sipDay, setSipDay] = useState<number>(5);
  const [sipResult, setSipResult] = useState<SIPCalculatorResponse | null>(null);
  const [isCalculatingSIP, setIsCalculatingSIP] = useState(false);
  const [sipError, setSipError] = useState<string | null>(null);
  const [sipTimelineHover, setSipTimelineHover] = useState<{ date: string; invested: number; value: number } | null>(null);

  // Lump-Sum state
  const [lumpAmount, setLumpAmount] = useState<number>(100000);
  const [lumpStartDate, setLumpStartDate] = useState<string>("2024-01-05");
  const [lumpEndDate, setLumpEndDate] = useState<string>("2025-01-05");
  const [lumpResult, setLumpResult] = useState<LumpSumCalculatorResponse | null>(null);
  const [isCalculatingLump, setIsCalculatingLump] = useState(false);
  const [lumpError, setLumpError] = useState<string | null>(null);

  // Fund Comparison state
  const [comparisonFundIds, setComparisonFundIds] = useState<string[]>([]);
  const [comparisonPeriod, setComparisonPeriod] = useState<string>("1Y");
  const [comparisonData, setComparisonData] = useState<FundComparisonResponse | null>(null);
  const [isLoadingComparison, setIsLoadingComparison] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const [comparisonHoverPoint, setComparisonHoverPoint] = useState<{ date: string; navs: Record<string, number | null> } | null>(null);

  // Load Categories & Filter Options
  useEffect(() => {
    api.getFundCategories()
      .then((data) => setCategoriesData(data))
      .catch((err) => console.error("Failed to load categories:", err));
  }, []);

  // Load Funds Directory
  useEffect(() => {
    loadFundsDirectory();
  }, [page, categoryFilter, subcategoryFilter, amcFilter, planFilter, searchQuery]);

  const loadFundsDirectory = async () => {
    setIsLoadingDirectory(true);
    try {
      const resp = await api.listFunds({
        page,
        size: pageSize,
        category: categoryFilter,
        subcategory: subcategoryFilter,
        amc: amcFilter,
        plan_type: planFilter,
        q: searchQuery,
      });
      setFunds(resp.items);
      setTotalFunds(resp.total);
      setTotalPages(resp.pages);

      // Auto-set selectedFundId for analytics & SIP if empty
      if (resp.items.length > 0) {
        if (!selectedFundId) {
          setSelectedFundId(resp.items[0].id);
        }
        if (!sipFundId) {
          setSipFundId(resp.items[0].id);
        }
        if (comparisonFundIds.length === 0 && resp.items.length >= 2) {
          setComparisonFundIds([resp.items[0].id, resp.items[1].id]);
        }
      }
    } catch (err) {
      console.error("Failed to load funds directory:", err);
    } finally {
      setIsLoadingDirectory(false);
    }
  };

  // Seed demo data handler
  const handleSeedDemoData = async () => {
    setIsSeeding(true);
    setSeedStatus(null);
    try {
      const res = await api.seedFunds();
      setSeedStatus(`Successfully initialized ${res.funds_created} funds with ${res.nav_rows_created} NAV entries.`);
      await loadFundsDirectory();
      const catData = await api.getFundCategories();
      setCategoriesData(catData);
    } catch (err: any) {
      setSeedStatus(err?.message || "Failed to seed demo mutual fund records.");
    } finally {
      setIsSeeding(false);
    }
  };

  // Load Fund Details & Analytics when selectedFundId changes
  useEffect(() => {
    if (!selectedFundId) return;

    let isMounted = true;
    setIsLoadingAnalytics(true);

    Promise.all([
      api.getFund(selectedFundId),
      api.getFundAnalytics(selectedFundId),
      api.getFundNAVHistory(selectedFundId, { limit: 600 }),
    ])
      .then(([detail, analytics, history]) => {
        if (!isMounted) return;
        setFundDetail(detail);
        setFundAnalytics(analytics);
        setNavHistory(history.navs);
        setNavChartHover(null);
      })
      .catch((err) => {
        console.error("Failed to load fund deep dive:", err);
      })
      .finally(() => {
        if (isMounted) setIsLoadingAnalytics(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedFundId]);

  // Filter NAV history by selected period for chart
  const filteredNavHistory = useMemo(() => {
    if (!navHistory || navHistory.length === 0) return [];
    if (chartPeriod === "ALL") return navHistory;

    const daysMap: Record<string, number> = {
      "1M": 30,
      "3M": 90,
      "6M": 180,
      "1Y": 365,
      "2Y": 730,
    };
    const days = daysMap[chartPeriod] || 365;
    const latest = new Date(navHistory[navHistory.length - 1].nav_date);
    const cutoff = new Date(latest.getTime() - days * 24 * 60 * 60 * 1000);

    const filtered = navHistory.filter((item) => new Date(item.nav_date) >= cutoff);
    return filtered.length > 0 ? filtered : navHistory;
  }, [navHistory, chartPeriod]);

  // Run SIP calculation
  const handleCalculateSIP = async () => {
    if (!sipFundId) return;
    setIsCalculatingSIP(true);
    setSipError(null);
    try {
      const res = await api.calculateSIP(sipFundId, {
        monthly_amount: sipMonthlyAmount,
        start_date: sipStartDate,
        end_date: sipEndDate || undefined,
        sip_day: sipDay,
      });
      setSipResult(res);
    } catch (err: any) {
      setSipError(err?.message || "Failed to calculate SIP");
    } finally {
      setIsCalculatingSIP(false);
    }
  };

  // Run Lump Sum calculation
  const handleCalculateLumpSum = async () => {
    if (!sipFundId) return;
    setIsCalculatingLump(true);
    setLumpError(null);
    try {
      const res = await api.calculateLumpSum(sipFundId, {
        amount: lumpAmount,
        start_date: lumpStartDate,
        end_date: lumpEndDate || undefined,
      });
      setLumpResult(res);
    } catch (err: any) {
      setLumpError(err?.message || "Failed to calculate lump sum");
    } finally {
      setIsCalculatingLump(false);
    }
  };

  // Run initial calculation when switching to SIP tab
  useEffect(() => {
    if (activeTab === "sip" && sipFundId && !sipResult && !isCalculatingSIP) {
      handleCalculateSIP();
    }
  }, [activeTab, sipFundId]);

  // Load Comparison Data
  useEffect(() => {
    if (comparisonFundIds.length === 0) {
      setComparisonData(null);
      return;
    }
    setIsLoadingComparison(true);
    setComparisonError(null);

    api.compareFunds(comparisonFundIds, comparisonPeriod)
      .then((data) => {
        setComparisonData(data);
      })
      .catch((err: any) => {
        setComparisonError(err?.message || "Failed to compare mutual funds");
      })
      .finally(() => {
        setIsLoadingComparison(false);
      });
  }, [comparisonFundIds, comparisonPeriod]);

  const toggleComparisonFund = (id: string) => {
    if (comparisonFundIds.includes(id)) {
      setComparisonFundIds(comparisonFundIds.filter((item) => item !== id));
    } else {
      if (comparisonFundIds.length >= 4) {
        alert("You can compare up to 4 funds simultaneously.");
        return;
      }
      setComparisonFundIds([...comparisonFundIds, id]);
    }
  };

  return (
    <DashboardLayout title="FundScope — Mutual Fund Intelligence">
      <div className="space-y-6">
        {/* Header with Demo Badge and Quick Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center text-[#71d5b3]">
                <PieChart size={20} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-[#edf3fa]">FundScope</h1>
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-950/80 text-[#71d5b3] border border-emerald-600/40">
                    FundScope Intelligence
                  </span>
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-950/80 text-amber-300 border border-amber-600/40 flex items-center gap-1">
                    <ShieldAlert size={10} />
                    Synthetic Demo Data
                  </span>
                </div>
                <p className="text-xs text-[#91a0b3] mt-0.5">
                  Institutional-grade Indian mutual fund analytics, historical NAV simulations, true XIRR SIP modeling & multi-fund comparison.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSeedDemoData}
              disabled={isSeeding}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#142233] hover:bg-[#1a2c42] text-[#71d5b3] border border-emerald-500/30 flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              {isSeeding ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
              {isSeeding ? "Seeding Catalog..." : "Seed Demo Catalog"}
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
            onClick={() => setActiveTab("directory")}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg flex items-center gap-2 transition-all ${
              activeTab === "directory"
                ? "bg-[#0e1724] text-[#71d5b3] border-t-2 border-t-[#71d5b3] border-x border-[#1e2d3e]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#121d2d]"
            }`}
          >
            <Database size={14} />
            Fund Catalog & Discovery
            <span className="text-[10px] bg-[#142030] text-[#91a0b3] px-1.5 py-0.2 rounded-full ml-1">
              {totalFunds}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg flex items-center gap-2 transition-all ${
              activeTab === "analytics"
                ? "bg-[#0e1724] text-[#71d5b3] border-t-2 border-t-[#71d5b3] border-x border-[#1e2d3e]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#121d2d]"
            }`}
          >
            <BarChart3 size={14} />
            Deep-Dive Analytics
          </button>

          <button
            onClick={() => setActiveTab("sip")}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg flex items-center gap-2 transition-all ${
              activeTab === "sip"
                ? "bg-[#0e1724] text-[#71d5b3] border-t-2 border-t-[#71d5b3] border-x border-[#1e2d3e]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#121d2d]"
            }`}
          >
            <Calculator size={14} />
            SIP & Wealth Calculator
          </button>

          <button
            onClick={() => setActiveTab("compare")}
            className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg flex items-center gap-2 transition-all ${
              activeTab === "compare"
                ? "bg-[#0e1724] text-[#71d5b3] border-t-2 border-t-[#71d5b3] border-x border-[#1e2d3e]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#121d2d]"
            }`}
          >
            <Scale size={14} />
            Fund Comparison
            {comparisonFundIds.length > 0 && (
              <span className="text-[10px] bg-[#15273b] text-[#71d5b3] px-1.5 py-0.2 rounded-full font-bold ml-1">
                {comparisonFundIds.length}
              </span>
            )}
          </button>

          <Link
            href="/ai?explain=funds"
            className="ml-auto px-3 py-1.5 text-xs font-semibold rounded-lg text-[#71d5b3] bg-[#15273b] hover:bg-[#1c3550] border border-[#1e3e4a] flex items-center gap-1.5 transition-all self-center"
          >
            Explain with Copilot
          </Link>
        </div>

        {/* TAB 1: FUND CATALOG & DISCOVERY */}
        {activeTab === "directory" && (
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
                    placeholder="Search by scheme name, code (e.g. PPFAS, NIFTY50), or fund house..."
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

                {/* Dropdowns */}
                <div className="flex flex-wrap items-center gap-2">
                  {/* Category Pill Filters */}
                  <div className="flex rounded-lg bg-[#080d16] p-1 border border-[#1e2d3e]">
                    {["All", "Equity", "Debt", "Hybrid"].map((cat) => (
                      <button
                        key={cat}
                        onClick={() => {
                          setCategoryFilter(cat);
                          setPage(1);
                        }}
                        className={`px-3 py-1 text-xs rounded-md font-medium transition-all ${
                          categoryFilter === cat
                            ? "bg-[#1e2d3e] text-[#71d5b3] font-semibold"
                            : "text-[#91a0b3] hover:text-[#edf3fa]"
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>

                  {/* AMC Filter */}
                  <select
                    value={amcFilter}
                    onChange={(e) => {
                      setAmcFilter(e.target.value);
                      setPage(1);
                    }}
                    className="px-2.5 py-1.5 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  >
                    <option value="All">All AMCs</option>
                    {categoriesData.amcs.map((amc) => (
                      <option key={amc} value={amc}>
                        {amc}
                      </option>
                    ))}
                  </select>

                  {/* Plan Type Filter */}
                  <select
                    value={planFilter}
                    onChange={(e) => {
                      setPlanFilter(e.target.value);
                      setPage(1);
                    }}
                    className="px-2.5 py-1.5 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  >
                    <option value="All">All Plans</option>
                    <option value="Direct">Direct Plan</option>
                    <option value="Regular">Regular Plan</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Scheme Cards Grid */}
            {isLoadingDirectory ? (
              <div className="p-12 text-center rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
                <Loader2 size={24} className="animate-spin text-[#71d5b3] mx-auto mb-3" />
                <p className="text-xs text-[#91a0b3]">Loading mutual funds catalog...</p>
              </div>
            ) : funds.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                <AlertCircle size={32} className="text-amber-400 mx-auto" />
                <h3 className="text-sm font-semibold text-[#edf3fa]">No Mutual Funds Found</h3>
                <p className="text-xs text-[#91a0b3] max-w-md mx-auto">
                  No funds match your selected filter criteria. Try resetting filters or seed the demo mutual fund catalog.
                </p>
                <button
                  onClick={handleSeedDemoData}
                  disabled={isSeeding}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#71d5b3] text-[#080d16] hover:bg-[#5bc29f] transition-all inline-flex items-center gap-1.5"
                >
                  <RefreshCw size={13} />
                  Initialize 6 Demo Funds
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {funds.map((fund) => {
                  const isCompared = comparisonFundIds.includes(fund.id);
                  return (
                    <div
                      key={fund.id}
                      className="p-5 rounded-xl bg-[#0e1724] border border-[#1e2d3e] hover:border-[#2d425c] transition-all flex flex-col justify-between group"
                    >
                      <div>
                        {/* AMC & Category Badges */}
                        <div className="flex items-center justify-between gap-2 mb-2.5">
                          <span className="text-[11px] font-semibold text-[#71d5b3] truncate max-w-[180px]">
                            {fund.amc_name}
                          </span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-[#142233] text-[#91a0b3] border border-[#1e2d3e]">
                              {fund.category} • {fund.subcategory}
                            </span>
                            {fund.crisil_rating && (
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-600/30 flex items-center gap-0.5">
                                <Award size={10} />
                                {fund.crisil_rating}★
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Scheme Name & Code */}
                        <h3 className="text-sm font-bold text-[#edf3fa] group-hover:text-[#71d5b3] transition-colors line-clamp-2">
                          {fund.scheme_name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1 text-[11px] text-[#556982]">
                          <span>Code: {fund.scheme_code}</span>
                          {fund.isin && <span>• {fund.isin}</span>}
                          <span>• {fund.plan_type}</span>
                        </div>

                        {/* Metrics Grid */}
                        <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-[#1e2d3e]">
                          <div>
                            <span className="text-[10px] text-[#556982] uppercase tracking-wider block">AUM</span>
                            <span className="text-xs font-semibold text-[#edf3fa]">
                              {fund.aum_crores ? `₹${fund.aum_crores.toLocaleString("en-IN")} Cr` : "—"}
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Expense Ratio</span>
                            <span className="text-xs font-semibold text-[#edf3fa]">
                              {fund.expense_ratio !== null ? `${fund.expense_ratio}%` : "—"}
                            </span>
                          </div>
                          <div className="col-span-2 pt-1 flex items-center justify-between text-[11px]">
                            <span className="text-[#556982]">Benchmark:</span>
                            <span className="text-[#91a0b3] truncate max-w-[180px]" title={fund.benchmark_name || ""}>
                              {fund.benchmark_name || "N/A"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Card Footer Actions */}
                      <div className="mt-5 pt-3 border-t border-[#1e2d3e] flex items-center justify-between gap-2">
                        <button
                          onClick={() => {
                            setSelectedFundId(fund.id);
                            setActiveTab("analytics");
                          }}
                          className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-[#142030] hover:bg-[#1a2d42] text-[#71d5b3] border border-[#1e2d3e] flex items-center gap-1 transition-all"
                        >
                          <BarChart3 size={12} />
                          Analyze
                        </button>

                        <button
                          onClick={() => {
                            setSipFundId(fund.id);
                            setActiveTab("sip");
                          }}
                          className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-[#142030] hover:bg-[#1a2d42] text-sky-400 border border-[#1e2d3e] flex items-center gap-1 transition-all"
                        >
                          <Calculator size={12} />
                          SIP Calc
                        </button>

                        <button
                          onClick={() => toggleComparisonFund(fund.id)}
                          className={`px-2.5 py-1.5 text-xs font-semibold rounded-lg border flex items-center gap-1 transition-all ${
                            isCompared
                              ? "bg-amber-950/60 text-amber-300 border-amber-600/40"
                              : "bg-[#142030] text-[#91a0b3] hover:text-white border-[#1e2d3e]"
                          }`}
                        >
                          <Scale size={12} />
                          {isCompared ? "Added" : "Compare"}
                        </button>
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
                  Showing page {page} of {totalPages} ({totalFunds} funds)
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

        {/* TAB 2: DEEP-DIVE ANALYTICS */}
        {activeTab === "analytics" && (
          <div className="space-y-6">
            {/* Fund Selector Dropdown */}
            <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-[#91a0b3]">Select Scheme:</span>
                <select
                  value={selectedFundId}
                  onChange={(e) => setSelectedFundId(e.target.value)}
                  className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3] max-w-md truncate"
                >
                  {funds.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.scheme_name} ({f.scheme_code})
                    </option>
                  ))}
                </select>
              </div>

              {fundDetail && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setSipFundId(fundDetail.id);
                      setActiveTab("sip");
                    }}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#142030] hover:bg-[#1a2d42] text-[#71d5b3] border border-[#1e2d3e] flex items-center gap-1.5"
                  >
                    <Calculator size={13} />
                    Run SIP on This Scheme
                  </button>
                  <button
                    onClick={() => toggleComparisonFund(fundDetail.id)}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#142030] hover:bg-[#1a2d42] text-amber-300 border border-[#1e2d3e] flex items-center gap-1.5"
                  >
                    <Scale size={13} />
                    {comparisonFundIds.includes(fundDetail.id) ? "Remove from Compare" : "Add to Compare"}
                  </button>
                </div>
              )}
            </div>

            {isLoadingAnalytics ? (
              <div className="p-16 text-center rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
                <Loader2 size={24} className="animate-spin text-[#71d5b3] mx-auto mb-3" />
                <p className="text-xs text-[#91a0b3]">Calculating trailing returns, rolling distributions and risk metrics...</p>
              </div>
            ) : fundDetail ? (
              <>
                {/* Scheme Profile & KPI Banner */}
                <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-[#71d5b3]">{fundDetail.amc_name}</span>
                        <span className="text-xs text-[#556982]">•</span>
                        <span className="text-xs text-[#91a0b3]">
                          {fundDetail.category} / {fundDetail.subcategory}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-[#142030] text-[#91a0b3] border border-[#1e2d3e]">
                          {fundDetail.plan_type} • {fundDetail.option_type}
                        </span>
                        {fundDetail.is_demo && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-600/30">
                            DEMO
                          </span>
                        )}
                      </div>
                      <h2 className="text-xl font-bold text-[#edf3fa]">{fundDetail.scheme_name}</h2>
                      <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-[#556982]">
                        <span>Scheme Code: <strong className="text-[#91a0b3]">{fundDetail.scheme_code}</strong></span>
                        {fundDetail.isin && <span>ISIN: <strong className="text-[#91a0b3]">{fundDetail.isin}</strong></span>}
                        {fundDetail.fund_manager && <span>Manager: <strong className="text-[#91a0b3]">{fundDetail.fund_manager}</strong></span>}
                        {fundDetail.benchmark_name && <span>Benchmark: <strong className="text-[#91a0b3]">{fundDetail.benchmark_name}</strong></span>}
                      </div>
                    </div>

                    {/* Latest NAV Badge */}
                    <div className="flex items-center gap-4 bg-[#080d16] p-4 rounded-xl border border-[#1e2d3e]">
                      <div>
                        <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Latest NAV</span>
                        <span className="text-2xl font-black text-[#edf3fa]">
                          {fundDetail.latest_nav ? `₹${fundDetail.latest_nav.nav.toFixed(4)}` : "—"}
                        </span>
                        {fundDetail.latest_nav && (
                          <span className="text-[10px] text-[#556982] block">
                            As of {fundDetail.latest_nav.nav_date}
                          </span>
                        )}
                      </div>
                      <div className="h-10 w-px bg-[#1e2d3e]" />
                      <div>
                        <span className="text-[10px] text-[#556982] uppercase tracking-wider block">1Y Return</span>
                        {fundAnalytics?.trailing_returns?.["1Y"] !== undefined && fundAnalytics.trailing_returns["1Y"] !== null ? (
                          <span className={`text-base font-bold flex items-center ${
                            fundAnalytics.trailing_returns["1Y"] >= 0 ? "text-[#71d5b3]" : "text-rose-400"
                          }`}>
                            {fundAnalytics.trailing_returns["1Y"] >= 0 ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                            {fundAnalytics.trailing_returns["1Y"].toFixed(2)}%
                          </span>
                        ) : (
                          <span className="text-xs text-[#556982]">N/A</span>
                        )}
                        <span className="text-[10px] text-[#556982] block">CAGR</span>
                      </div>
                    </div>
                  </div>

                  {/* Fund Details Bar */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-[#1e2d3e]">
                    <div className="p-3 rounded-lg bg-[#080d16] border border-[#1e2d3e]">
                      <span className="text-[10px] text-[#556982] uppercase tracking-wider block">AUM</span>
                      <span className="text-sm font-semibold text-[#edf3fa]">
                        {fundDetail.aum_crores ? `₹${fundDetail.aum_crores.toLocaleString("en-IN")} Cr` : "—"}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#080d16] border border-[#1e2d3e]">
                      <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Expense Ratio</span>
                      <span className="text-sm font-semibold text-[#edf3fa]">
                        {fundDetail.expense_ratio !== null ? `${fundDetail.expense_ratio}%` : "—"}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#080d16] border border-[#1e2d3e]">
                      <span className="text-[10px] text-[#556982] uppercase tracking-wider block">CRISIL Rating</span>
                      <span className="text-sm font-semibold text-amber-300 flex items-center gap-1">
                        {fundDetail.crisil_rating ? `${fundDetail.crisil_rating} Stars` : "Not Rated"}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#080d16] border border-[#1e2d3e]">
                      <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Annual Volatility</span>
                      <span className="text-sm font-semibold text-[#edf3fa]">
                        {fundAnalytics?.volatility_pct !== null && fundAnalytics?.volatility_pct !== undefined
                          ? `${fundAnalytics.volatility_pct.toFixed(2)}%`
                          : "—"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Historical NAV Chart */}
                <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-bold text-[#edf3fa] flex items-center gap-2">
                        <TrendingUp size={16} className="text-[#71d5b3]" />
                        Historical NAV Performance
                      </h3>
                      <p className="text-xs text-[#556982]">
                        {navChartHover
                          ? `NAV on ${navChartHover.nav_date}: ₹${navChartHover.nav.toFixed(4)}`
                          : filteredNavHistory.length > 0
                          ? `Showing ${filteredNavHistory.length} trading points (${filteredNavHistory[0].nav_date} to ${filteredNavHistory[filteredNavHistory.length - 1].nav_date})`
                          : "No NAV points"}
                      </p>
                    </div>

                    {/* Period Selector */}
                    <div className="flex rounded-lg bg-[#080d16] p-1 border border-[#1e2d3e]">
                      {(["1M", "3M", "6M", "1Y", "2Y", "ALL"] as ChartPeriod[]).map((p) => (
                        <button
                          key={p}
                          onClick={() => setChartPeriod(p)}
                          className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                            chartPeriod === p
                              ? "bg-[#1e2d3e] text-[#71d5b3] font-semibold"
                              : "text-[#91a0b3] hover:text-[#edf3fa]"
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* SVG Chart Rendering */}
                  <div className="h-64 w-full relative">
                    {filteredNavHistory.length >= 2 ? (
                      (() => {
                        const width = 800;
                        const height = 240;
                        const padL = 45;
                        const padR = 20;
                        const padT = 20;
                        const padB = 30;

                        const navs = filteredNavHistory.map((p) => Number(p.nav)).filter((v) => Number.isFinite(v));
                        if (navs.length < 2) {
                          return (
                            <div className="h-full flex items-center justify-center text-xs text-[#556982]">
                              Insufficient historical NAV data points for charting.
                            </div>
                          );
                        }

                        const minNav = Math.min(...navs) * 0.98;
                        const maxNav = Math.max(...navs) * 1.02;
                        const rangeNav = maxNav - minNav <= 0 ? 1 : maxNav - minNav;
                        const count = filteredNavHistory.length;
                        const divisor = count > 1 ? count - 1 : 1;

                        const points = filteredNavHistory.map((p, idx) => {
                          const navVal = Number(p.nav);
                          const safeNav = Number.isFinite(navVal) ? navVal : minNav;
                          const rawX = padL + (idx / divisor) * (width - padL - padR);
                          const rawY = padT + (1 - (safeNav - minNav) / rangeNav) * (height - padT - padB);
                          return {
                            x: Number.isFinite(rawX) ? rawX : padL,
                            y: Number.isFinite(rawY) ? rawY : padT,
                            point: p,
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
                          (acc, pt, i) => (i === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`),
                          ""
                        );
                        const areaD = validPoints.length > 1
                          ? `${pathD} L ${validPoints[validPoints.length - 1].x} ${height - padB} L ${validPoints[0].x} ${height - padB} Z`
                          : "";

                        return (
                          <svg
                            viewBox={`0 0 ${width} ${height}`}
                            className="w-full h-full overflow-visible"
                            onMouseLeave={() => setNavChartHover(null)}
                          >
                            <defs>
                              <linearGradient id="navGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#71d5b3" stopOpacity="0.25" />
                                <stop offset="100%" stopColor="#71d5b3" stopOpacity="0.0" />
                              </linearGradient>
                            </defs>

                            {/* Horizontal Grid lines */}
                            {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                              const y = padT + pct * (height - padT - padB);
                              const val = maxNav - pct * rangeNav;
                              return (
                                <g key={i}>
                                  <line
                                    x1={padL}
                                    y1={y}
                                    x2={width - padR}
                                    y2={y}
                                    stroke="#1e2d3e"
                                    strokeDasharray="4 4"
                                  />
                                  <text
                                    x={padL - 8}
                                    y={y + 3}
                                    textAnchor="end"
                                    fill="#556982"
                                    fontSize="10"
                                  >
                                    ₹{val.toFixed(1)}
                                  </text>
                                </g>
                              );
                            })}

                            {/* Area fill */}
                            {areaD && <path d={areaD} fill="url(#navGradient)" />}

                            {/* Line path */}
                            {pathD && (
                              <path
                                d={pathD}
                                fill="none"
                                stroke="#71d5b3"
                                strokeWidth="2.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              />
                            )}

                            {/* Date labels at bottom */}
                            <text
                              x={padL}
                              y={height - 8}
                              textAnchor="start"
                              fill="#556982"
                              fontSize="10"
                            >
                              {filteredNavHistory[0]?.nav_date || ""}
                            </text>
                            <text
                              x={width - padR}
                              y={height - 8}
                              textAnchor="end"
                              fill="#556982"
                              fontSize="10"
                            >
                              {filteredNavHistory[filteredNavHistory.length - 1]?.nav_date || ""}
                            </text>

                            {/* Interactive hover overlays */}
                            {validPoints.map((pt, i) => (
                              <circle
                                key={i}
                                cx={pt.x}
                                cy={pt.y}
                                r={navChartHover?.nav_date === pt.point.nav_date ? 5 : 3}
                                fill="#71d5b3"
                                className="opacity-0 hover:opacity-100 transition-opacity cursor-pointer"
                                onMouseEnter={() => setNavChartHover(pt.point)}
                              />
                            ))}

                            {/* Active cursor circle */}
                            {navChartHover && (() => {
                              const activePt = validPoints.find((p) => p.point.nav_date === navChartHover.nav_date);
                              if (!activePt || !Number.isFinite(activePt.x) || !Number.isFinite(activePt.y)) return null;
                              return (
                                <g>
                                  <line
                                    x1={activePt.x}
                                    y1={padT}
                                    x2={activePt.x}
                                    y2={height - padB}
                                    stroke="#71d5b3"
                                    strokeWidth="1"
                                    strokeDasharray="3 3"
                                  />
                                  <circle cx={activePt.x} cy={activePt.y} r="5" fill="#71d5b3" stroke="#080d16" strokeWidth="2" />
                                </g>
                              );
                            })()}
                          </svg>
                        );
                      })()
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-[#556982]">
                        Insufficient historical NAV data points for charting.
                      </div>
                    )}
                  </div>
                </div>

                {/* Trailing Returns Grid */}
                <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-[#edf3fa]">Trailing Returns</h3>
                      <p className="text-xs text-[#556982]">
                        Standardized point-to-point annualized returns (CAGR for periods ≥ 1 Year; Absolute for &lt; 1 Year).
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                    {[
                      { key: "1M", label: "1 Month", type: "Abs" },
                      { key: "3M", label: "3 Months", type: "Abs" },
                      { key: "6M", label: "6 Months", type: "Abs" },
                      { key: "1Y", label: "1 Year", type: "CAGR" },
                      { key: "3Y", label: "3 Years", type: "CAGR" },
                      { key: "5Y", label: "5 Years", type: "CAGR" },
                      { key: "Inception", label: "Inception", type: "CAGR" },
                    ].map((period) => {
                      const val = fundAnalytics?.trailing_returns?.[period.key];
                      const isPositive = val !== null && val !== undefined && val >= 0;
                      return (
                        <div key={period.key} className="p-3.5 rounded-xl bg-[#080d16] border border-[#1e2d3e]">
                          <div className="flex items-center justify-between text-[10px] text-[#556982] mb-1">
                            <span>{period.label}</span>
                            <span className="text-[9px] px-1 py-0.2 rounded bg-[#142030]">{period.type}</span>
                          </div>
                          {val !== null && val !== undefined ? (
                            <span className={`text-sm font-bold flex items-center ${
                              isPositive ? "text-[#71d5b3]" : "text-rose-400"
                            }`}>
                              {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                              {val.toFixed(2)}%
                            </span>
                          ) : (
                            <span className="text-xs text-[#556982]">N/A</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Rolling Returns Distributions & Risk Metrics */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* 1Y Rolling Returns */}
                  <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                    <h3 className="text-sm font-bold text-[#edf3fa] flex items-center justify-between">
                      <span>1-Year Rolling Returns</span>
                      <span className="text-[10px] text-[#556982] font-normal">
                        {fundAnalytics?.rolling_returns_1y?.samples || 0} overlapping windows
                      </span>
                    </h3>
                    <p className="text-xs text-[#556982]">
                      Measures return consistency across every 365-day holding period to eliminate starting-point bias.
                    </p>

                    <div className="grid grid-cols-3 gap-2 pt-2">
                      <div className="p-2.5 rounded-lg bg-[#080d16] border border-[#1e2d3e]">
                        <span className="text-[10px] text-[#556982] block">Mean (Average)</span>
                        <span className="text-xs font-bold text-[#edf3fa]">
                          {fundAnalytics?.rolling_returns_1y?.mean_pct !== null && fundAnalytics?.rolling_returns_1y?.mean_pct !== undefined
                            ? `${fundAnalytics.rolling_returns_1y.mean_pct.toFixed(2)}%`
                            : "—"}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#080d16] border border-[#1e2d3e]">
                        <span className="text-[10px] text-[#556982] block">Median</span>
                        <span className="text-xs font-bold text-[#edf3fa]">
                          {fundAnalytics?.rolling_returns_1y?.median_pct !== null && fundAnalytics?.rolling_returns_1y?.median_pct !== undefined
                            ? `${fundAnalytics.rolling_returns_1y.median_pct.toFixed(2)}%`
                            : "—"}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#080d16] border border-[#1e2d3e]">
                        <span className="text-[10px] text-[#556982] block">Positive %</span>
                        <span className="text-xs font-bold text-[#71d5b3]">
                          {fundAnalytics?.rolling_returns_1y?.positive_periods_pct !== null && fundAnalytics?.rolling_returns_1y?.positive_periods_pct !== undefined
                            ? `${fundAnalytics.rolling_returns_1y.positive_periods_pct.toFixed(1)}%`
                            : "—"}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-xs pt-2 border-t border-[#1e2d3e] text-[#91a0b3]">
                      <span>
                        Min: <strong className="text-rose-400">{fundAnalytics?.rolling_returns_1y?.min_pct?.toFixed(2) ?? "—"}%</strong>
                      </span>
                      <span>
                        Max: <strong className="text-[#71d5b3]">{fundAnalytics?.rolling_returns_1y?.max_pct?.toFixed(2) ?? "—"}%</strong>
                      </span>
                    </div>
                  </div>

                  {/* Risk Profile & Drawdown */}
                  <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                    <h3 className="text-sm font-bold text-[#edf3fa]">Risk & Drawdown Profile</h3>
                    <p className="text-xs text-[#556982]">
                      Volatility is annualized using standard 252 trading days; Maximum Drawdown measures peak-to-trough decline.
                    </p>

                    <div className="grid grid-cols-2 gap-3 pt-2">
                      <div className="p-3.5 rounded-xl bg-[#080d16] border border-[#1e2d3e]">
                        <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Annualized Volatility</span>
                        <span className="text-base font-bold text-[#edf3fa] mt-1 block">
                          {fundAnalytics?.volatility_pct !== null && fundAnalytics?.volatility_pct !== undefined
                            ? `${fundAnalytics.volatility_pct.toFixed(2)}%`
                            : "—"}
                        </span>
                        <span className="text-[10px] text-[#556982] mt-0.5 block">Standard deviation ($\sigma \times \sqrt{252}$)</span>
                      </div>

                      <div className="p-3.5 rounded-xl bg-[#080d16] border border-[#1e2d3e]">
                        <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Maximum Drawdown</span>
                        <span className="text-base font-bold text-rose-400 mt-1 block">
                          {fundAnalytics?.max_drawdown_pct !== undefined
                            ? `${fundAnalytics.max_drawdown_pct.toFixed(2)}%`
                            : "0.00%"}
                        </span>
                        <span className="text-[10px] text-[#556982] mt-0.5 block">Largest peak-to-trough decline</span>
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-[#142030] text-[11px] text-[#91a0b3] flex items-center gap-2">
                      <ShieldAlert size={14} className="text-amber-400 shrink-0" />
                      <span>
                        Calculations use synthetic historical daily NAV sequences for simulated educational analysis.
                      </span>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        )}

        {/* TAB 3: SIP & WEALTH CALCULATOR */}
        {activeTab === "sip" && (
          <div className="space-y-6">
            {/* Calculator Mode & Configuration Panel */}
            <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-bold text-[#edf3fa] flex items-center gap-2">
                    <Calculator size={18} className="text-[#71d5b3]" />
                    Mutual Fund Wealth Simulator
                  </h2>
                  <p className="text-xs text-[#556982]">
                    Backtest systematic monthly SIPs or lump-sum investments using exact historical trade-day NAVs and calculate true XIRR.
                  </p>
                </div>

                {/* Mode Switcher */}
                <div className="flex rounded-lg bg-[#080d16] p-1 border border-[#1e2d3e]">
                  <button
                    onClick={() => setCalcMode("sip")}
                    className={`px-3 py-1.5 text-xs rounded-md font-semibold transition-all ${
                      calcMode === "sip"
                        ? "bg-[#1e2d3e] text-[#71d5b3]"
                        : "text-[#91a0b3] hover:text-[#edf3fa]"
                    }`}
                  >
                    Monthly SIP
                  </button>
                  <button
                    onClick={() => setCalcMode("lumpsum")}
                    className={`px-3 py-1.5 text-xs rounded-md font-semibold transition-all ${
                      calcMode === "lumpsum"
                        ? "bg-[#1e2d3e] text-sky-400"
                        : "text-[#91a0b3] hover:text-[#edf3fa]"
                    }`}
                  >
                    Lump Sum
                  </button>
                </div>
              </div>

              {/* Input Form */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2 border-t border-[#1e2d3e]">
                {/* Scheme Picker */}
                <div className="md:col-span-1">
                  <label className="text-[11px] font-semibold text-[#91a0b3] block mb-1">
                    Select Mutual Fund
                  </label>
                  <select
                    value={sipFundId}
                    onChange={(e) => setSipFundId(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  >
                    {funds.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.scheme_name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Amount */}
                <div className="md:col-span-1">
                  <label className="text-[11px] font-semibold text-[#91a0b3] block mb-1">
                    {calcMode === "sip" ? "Monthly Installment (₹)" : "Initial Investment (₹)"}
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-[#556982]">₹</span>
                    <input
                      type="number"
                      value={calcMode === "sip" ? sipMonthlyAmount : lumpAmount}
                      onChange={(e) => {
                        const val = Math.max(100, Number(e.target.value));
                        if (calcMode === "sip") setSipMonthlyAmount(val);
                        else setLumpAmount(val);
                      }}
                      className="w-full pl-7 pr-3 py-2 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                    />
                  </div>
                  {/* Preset chips */}
                  <div className="flex gap-1.5 mt-1.5">
                    {(calcMode === "sip" ? [1000, 5000, 10000, 25000] : [25000, 50000, 100000, 500000]).map((amt) => (
                      <button
                        key={amt}
                        type="button"
                        onClick={() => {
                          if (calcMode === "sip") setSipMonthlyAmount(amt);
                          else setLumpAmount(amt);
                        }}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-[#142030] text-[#91a0b3] hover:text-[#71d5b3]"
                      >
                        {amt >= 100000 ? `${amt / 100000}L` : `${amt / 1000}k`}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Start Date */}
                <div className="md:col-span-1">
                  <label className="text-[11px] font-semibold text-[#91a0b3] block mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={calcMode === "sip" ? sipStartDate : lumpStartDate}
                    onChange={(e) => {
                      if (calcMode === "sip") setSipStartDate(e.target.value);
                      else setLumpStartDate(e.target.value);
                    }}
                    className="w-full px-3 py-2 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  />
                  <div className="flex gap-1.5 mt-1.5">
                    <button
                      type="button"
                      onClick={() => {
                        const d = "2024-01-05";
                        if (calcMode === "sip") setSipStartDate(d);
                        else setLumpStartDate(d);
                      }}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-[#142030] text-[#91a0b3] hover:text-[#71d5b3]"
                    >
                      Jan 2024
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const d = "2023-01-05";
                        if (calcMode === "sip") setSipStartDate(d);
                        else setLumpStartDate(d);
                      }}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-[#142030] text-[#91a0b3] hover:text-[#71d5b3]"
                    >
                      Jan 2023
                    </button>
                  </div>
                </div>

                {/* SIP Day or End Date */}
                <div className="md:col-span-1">
                  {calcMode === "sip" ? (
                    <>
                      <label className="text-[11px] font-semibold text-[#91a0b3] block mb-1">
                        SIP Day of Month
                      </label>
                      <select
                        value={sipDay}
                        onChange={(e) => setSipDay(Number(e.target.value))}
                        className="w-full px-3 py-2 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                      >
                        {[1, 5, 10, 15, 20, 25, 28].map((day) => (
                          <option key={day} value={day}>
                            {day}th of every month
                          </option>
                        ))}
                      </select>
                    </>
                  ) : (
                    <>
                      <label className="text-[11px] font-semibold text-[#91a0b3] block mb-1">
                        End Date
                      </label>
                      <input
                        type="date"
                        value={lumpEndDate}
                        onChange={(e) => setLumpEndDate(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                      />
                    </>
                  )}

                  <div className="mt-2.5">
                    <button
                      onClick={calcMode === "sip" ? handleCalculateSIP : handleCalculateLumpSum}
                      disabled={isCalculatingSIP || isCalculatingLump}
                      className="w-full py-2 text-xs font-bold rounded-lg bg-[#71d5b3] text-[#080d16] hover:bg-[#5bc29f] transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                    >
                      {isCalculatingSIP || isCalculatingLump ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Calculator size={13} />
                      )}
                      Simulate Investment
                    </button>
                  </div>
                </div>
              </div>

              {/* Error messages */}
              {(sipError || lumpError) && (
                <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-600/40 text-xs text-rose-300 flex items-center gap-2">
                  <AlertCircle size={14} />
                  <span>{sipError || lumpError}</span>
                </div>
              )}
            </div>

            {/* SIP Results View */}
            {calcMode === "sip" && sipResult && (
              <div className="space-y-6">
                {/* KPI Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Total Amount Invested</span>
                    <span className="text-xl font-black text-[#edf3fa] mt-1 block">
                      ₹{sipResult.total_invested.toLocaleString("en-IN")}
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      {sipResult.installments_count} monthly installments
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Current / Final Value</span>
                    <span className="text-xl font-black text-[#71d5b3] mt-1 block">
                      ₹{sipResult.final_value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      Units: {sipResult.units_accumulated.toFixed(3)}
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Total Gain / Profit</span>
                    <span className={`text-xl font-black mt-1 block ${
                      sipResult.total_profit >= 0 ? "text-[#71d5b3]" : "text-rose-400"
                    }`}>
                      {sipResult.total_profit >= 0 ? "+" : ""}₹{sipResult.total_profit.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      Abs: {sipResult.absolute_return_pct.toFixed(2)}%
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Annualized Return (XIRR)</span>
                    <span className="text-xl font-black text-sky-400 mt-1 block">
                      {sipResult.xirr_pct !== null ? `${sipResult.xirr_pct.toFixed(2)}%` : "N/A"}
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      True Money-Weighted Return
                    </span>
                  </div>
                </div>

                {/* Dual-Line Growth Chart (Invested vs Portfolio Value) */}
                {sipResult.timeline && sipResult.timeline.length >= 2 && (
                  <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div>
                        <h3 className="text-sm font-bold text-[#edf3fa]">SIP Wealth Accumulation Timeline</h3>
                        <p className="text-xs text-[#556982]">
                          {sipTimelineHover
                            ? `${sipTimelineHover.date} — Invested: ₹${sipTimelineHover.invested.toLocaleString("en-IN")} | Value: ₹${sipTimelineHover.value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
                            : "Interactive progression of cumulative invested capital vs portfolio market value."}
                        </p>
                      </div>

                      <div className="flex items-center gap-4 text-xs">
                        <span className="flex items-center gap-1.5 text-sky-400">
                          <span className="w-3 h-0.5 bg-sky-400 inline-block" />
                          Invested Capital
                        </span>
                        <span className="flex items-center gap-1.5 text-[#71d5b3]">
                          <span className="w-3 h-0.5 bg-[#71d5b3] inline-block" />
                          Portfolio Value
                        </span>
                      </div>
                    </div>

                    {/* Dual SVG Line Chart */}
                    <div className="h-64 w-full relative">
                      {(() => {
                        const width = 800;
                        const height = 240;
                        const padL = 60;
                        const padR = 20;
                        const padT = 20;
                        const padB = 30;

                        const timeline = sipResult?.timeline || [];
                        if (timeline.length < 2) {
                          return (
                            <div className="h-full flex items-center justify-center text-xs text-[#556982]">
                              Insufficient timeline history for charting.
                            </div>
                          );
                        }

                        const safeVals = timeline
                          .map((t) => [Number(t.invested) || 0, Number(t.value) || 0])
                          .flat()
                          .filter((v) => Number.isFinite(v) && v >= 0);

                        const maxVal = Math.max(1, ...(safeVals.length > 0 ? safeVals : [1])) * 1.05;
                        const rangeVal = maxVal <= 0 ? 1 : maxVal;
                        const count = timeline.length;
                        const divisor = count > 1 ? count - 1 : 1;

                        const ptsInvested = timeline.map((t, i) => {
                          const inv = Number.isFinite(Number(t.invested)) ? Math.max(0, Number(t.invested)) : 0;
                          const rawX = padL + (i / divisor) * (width - padL - padR);
                          const rawY = padT + (1 - inv / rangeVal) * (height - padT - padB);
                          return {
                            x: Number.isFinite(rawX) ? rawX : padL,
                            y: Number.isFinite(rawY) ? rawY : padT,
                            data: t,
                          };
                        });

                        const ptsValue = timeline.map((t, i) => {
                          const val = Number.isFinite(Number(t.value)) ? Math.max(0, Number(t.value)) : 0;
                          const rawX = padL + (i / divisor) * (width - padL - padR);
                          const rawY = padT + (1 - val / rangeVal) * (height - padT - padB);
                          return {
                            x: Number.isFinite(rawX) ? rawX : padL,
                            y: Number.isFinite(rawY) ? rawY : padT,
                            data: t,
                          };
                        });

                        const validPtsValue = ptsValue.filter((pt) => Number.isFinite(pt.x) && Number.isFinite(pt.y));
                        const validPtsInvested = ptsInvested.filter((pt) => Number.isFinite(pt.x) && Number.isFinite(pt.y));

                        if (validPtsValue.length === 0) {
                          return (
                            <div className="h-full flex items-center justify-center text-xs text-[#556982]">
                              No valid chart coordinates available.
                            </div>
                          );
                        }

                        const pathInvested = validPtsInvested.reduce(
                          (acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`),
                          ""
                        );
                        const pathValue = validPtsValue.reduce(
                          (acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`),
                          ""
                        );
                        const areaValue = validPtsValue.length > 1
                          ? `${pathValue} L ${validPtsValue[validPtsValue.length - 1].x} ${height - padB} L ${validPtsValue[0].x} ${height - padB} Z`
                          : "";

                        return (
                          <svg
                            viewBox={`0 0 ${width} ${height}`}
                            className="w-full h-full overflow-visible"
                            onMouseLeave={() => setSipTimelineHover(null)}
                          >
                            <defs>
                              <linearGradient id="valGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#71d5b3" stopOpacity="0.2" />
                                <stop offset="100%" stopColor="#71d5b3" stopOpacity="0.0" />
                              </linearGradient>
                            </defs>

                            {/* Horizontal gridlines */}
                            {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                              const y = padT + pct * (height - padT - padB);
                              const v = maxVal - pct * rangeVal;
                              return (
                                <g key={i}>
                                  <line
                                    x1={padL}
                                    y1={y}
                                    x2={width - padR}
                                    y2={y}
                                    stroke="#1e2d3e"
                                    strokeDasharray="4 4"
                                  />
                                  <text
                                    x={padL - 8}
                                    y={y + 3}
                                    textAnchor="end"
                                    fill="#556982"
                                    fontSize="10"
                                  >
                                    ₹{Math.round(v).toLocaleString("en-IN")}
                                  </text>
                                </g>
                              );
                            })}

                            {areaValue && <path d={areaValue} fill="url(#valGrad)" />}
                            {pathInvested && <path d={pathInvested} fill="none" stroke="#38bdf8" strokeWidth="2" strokeDasharray="3 3" />}
                            {pathValue && <path d={pathValue} fill="none" stroke="#71d5b3" strokeWidth="2.5" />}

                            {/* Tooltip trigger zones */}
                            {validPtsValue.map((pt, i) => (
                              <circle
                                key={i}
                                cx={pt.x}
                                cy={pt.y}
                                r={sipTimelineHover?.date === pt.data.date ? 5 : 3}
                                fill="#71d5b3"
                                className="opacity-0 hover:opacity-100 cursor-pointer"
                                onMouseEnter={() => setSipTimelineHover(pt.data)}
                              />
                            ))}

                            {/* Axis dates */}
                            <text x={padL} y={height - 8} textAnchor="start" fill="#556982" fontSize="10">
                              {timeline[0]?.date || ""}
                            </text>
                            <text x={width - padR} y={height - 8} textAnchor="end" fill="#556982" fontSize="10">
                              {timeline[timeline.length - 1]?.date || ""}
                            </text>
                          </svg>
                        );
                      })()}
                    </div>
                  </div>
                )}

                {/* Installment History Breakdown */}
                {sipResult.installments && sipResult.installments.length > 0 && (
                  <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                    <h3 className="text-sm font-bold text-[#edf3fa]">
                      SIP Installment Schedule ({sipResult.installments.length} Allotments)
                    </h3>
                    <div className="overflow-x-auto max-h-72 overflow-y-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-[#080d16] text-[#556982] uppercase text-[10px] sticky top-0">
                          <tr>
                            <th className="py-2.5 px-3">#</th>
                            <th className="py-2.5 px-3">Scheduled</th>
                            <th className="py-2.5 px-3">Executed</th>
                            <th className="py-2.5 px-3 text-right">NAV</th>
                            <th className="py-2.5 px-3 text-right">Installment</th>
                            <th className="py-2.5 px-3 text-right">Units Allotted</th>
                            <th className="py-2.5 px-3 text-right">Total Units</th>
                            <th className="py-2.5 px-3 text-right">Cumulative Invested</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#1e2d3e]">
                          {sipResult.installments.map((inst) => (
                            <tr key={inst.installment_number} className="hover:bg-[#121d2d] text-[#edf3fa]">
                              <td className="py-2 px-3 font-semibold text-[#556982]">{inst.installment_number}</td>
                              <td className="py-2 px-3 text-[#91a0b3]">{inst.scheduled_date}</td>
                              <td className="py-2 px-3">{inst.executed_date}</td>
                              <td className="py-2 px-3 text-right font-medium">₹{inst.nav.toFixed(4)}</td>
                              <td className="py-2 px-3 text-right font-semibold">₹{inst.amount.toLocaleString("en-IN")}</td>
                              <td className="py-2 px-3 text-right text-sky-400">{inst.units.toFixed(3)}</td>
                              <td className="py-2 px-3 text-right font-semibold">{inst.total_units.toFixed(3)}</td>
                              <td className="py-2 px-3 text-right text-[#91a0b3]">₹{inst.cumulative_invested.toLocaleString("en-IN")}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Lump Sum Results View */}
            {calcMode === "lumpsum" && lumpResult && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Initial Investment</span>
                    <span className="text-xl font-black text-[#edf3fa] mt-1 block">
                      ₹{lumpResult.initial_investment.toLocaleString("en-IN")}
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      On {lumpResult.start_date}
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Current / Final Value</span>
                    <span className="text-xl font-black text-[#71d5b3] mt-1 block">
                      ₹{lumpResult.final_value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      Units: {lumpResult.units_accumulated.toFixed(3)}
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Absolute Return</span>
                    <span className={`text-xl font-black mt-1 block ${
                      lumpResult.absolute_return_pct >= 0 ? "text-[#71d5b3]" : "text-rose-400"
                    }`}>
                      {lumpResult.absolute_return_pct.toFixed(2)}%
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      Gain: ₹{lumpResult.total_profit.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e]">
                    <span className="text-[10px] text-[#556982] uppercase tracking-wider block">Annualized Return (CAGR)</span>
                    <span className="text-xl font-black text-sky-400 mt-1 block">
                      {lumpResult.cagr_pct !== null ? `${lumpResult.cagr_pct.toFixed(2)}%` : "N/A"}
                    </span>
                    <span className="text-[10px] text-[#556982] block mt-0.5">
                      Over {lumpResult.duration_days} days
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: FUND COMPARISON */}
        {activeTab === "compare" && (
          <div className="space-y-6">
            {/* Header & Fund Selector */}
            <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h2 className="text-base font-bold text-[#edf3fa] flex items-center gap-2">
                    <Scale size={18} className="text-[#71d5b3]" />
                    Comparative Mutual Fund Analysis
                  </h2>
                  <p className="text-xs text-[#556982]">
                    Select up to 4 funds to benchmark risk-adjusted performance, normalized Base-100 NAV progression, volatility and drawdown.
                  </p>
                </div>

                {/* Period Selector */}
                <div className="flex rounded-lg bg-[#080d16] p-1 border border-[#1e2d3e]">
                  {["1M", "3M", "6M", "1Y", "ALL"].map((p) => (
                    <button
                      key={p}
                      onClick={() => setComparisonPeriod(p)}
                      className={`px-3 py-1 text-xs rounded-md font-semibold transition-all ${
                        comparisonPeriod === p
                          ? "bg-[#1e2d3e] text-[#71d5b3]"
                          : "text-[#91a0b3] hover:text-[#edf3fa]"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              {/* Fund Selection Tags */}
              <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#1e2d3e]">
                <span className="text-xs text-[#91a0b3] font-medium mr-1">Comparing:</span>
                {comparisonFundIds.map((id, idx) => {
                  const fund = funds.find((f) => f.id === id);
                  const color = COMPARISON_COLORS[idx % COMPARISON_COLORS.length];
                  return (
                    <span
                      key={id}
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold ${color.bg} ${color.text} border ${color.border}`}
                    >
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color.stroke }} />
                      {fund ? fund.scheme_name : id.slice(0, 8)}
                      <button
                        onClick={() => toggleComparisonFund(id)}
                        className="hover:text-white ml-1"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  );
                })}

                {comparisonFundIds.length < 4 && (
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        toggleComparisonFund(e.target.value);
                        e.target.value = "";
                      }
                    }}
                    defaultValue=""
                    className="px-2.5 py-1 text-xs rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[#71d5b3] focus:outline-none focus:border-[#71d5b3]"
                  >
                    <option value="" disabled>+ Add Scheme to Compare...</option>
                    {funds
                      .filter((f) => !comparisonFundIds.includes(f.id))
                      .map((f) => (
                        <option key={f.id} value={f.id}>
                          {f.scheme_name}
                        </option>
                      ))}
                  </select>
                )}
              </div>
            </div>

            {/* Comparison Content */}
            {isLoadingComparison ? (
              <div className="p-16 text-center rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
                <Loader2 size={24} className="animate-spin text-[#71d5b3] mx-auto mb-3" />
                <p className="text-xs text-[#91a0b3]">Rebasing historical NAVs to Base 100 and computing relative statistics...</p>
              </div>
            ) : comparisonError ? (
              <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-600/40 text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle size={16} />
                <span>{comparisonError}</span>
              </div>
            ) : comparisonData ? (
              <div className="space-y-6">
                {/* Normalized Base-100 Performance Chart */}
                <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-bold text-[#edf3fa]">
                        Normalized NAV Progression (Base 100)
                      </h3>
                      <p className="text-xs text-[#556982]">
                        {comparisonHoverPoint
                          ? `Date: ${comparisonHoverPoint.date}`
                          : `Rebased to 100 on ${comparisonData.start_date || "start"} for like-for-like comparison.`}
                      </p>
                    </div>

                    {/* Chart Legend */}
                    <div className="flex flex-wrap items-center gap-3 text-xs">
                      {comparisonData.funds.map((f, i) => {
                        const color = COMPARISON_COLORS[i % COMPARISON_COLORS.length];
                        const hoverVal = comparisonHoverPoint?.navs?.[f.fund_id];
                        return (
                          <div key={f.fund_id} className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color.stroke }} />
                            <span className="text-[#91a0b3] font-medium truncate max-w-[140px]">
                              {f.scheme_code}:
                            </span>
                            <span className="font-bold text-[#edf3fa]">
                              {hoverVal !== undefined && hoverVal !== null
                                ? hoverVal.toFixed(2)
                                : f.period_return_pct !== null && f.period_return_pct !== undefined
                                ? `${f.period_return_pct >= 0 ? "+" : ""}${f.period_return_pct.toFixed(2)}%`
                                : "—"}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Multi-line SVG Chart */}
                  <div className="h-64 w-full relative">
                    {comparisonData.normalized_chart && comparisonData.normalized_chart.length >= 2 ? (
                      (() => {
                        const width = 800;
                        const height = 240;
                        const padL = 45;
                        const padR = 20;
                        const padT = 20;
                        const padB = 30;

                        const allVals: number[] = [];
                        comparisonData.normalized_chart.forEach((pt) => {
                          Object.values(pt.navs).forEach((v) => {
                            if (v !== null && v !== undefined) allVals.push(Number(v));
                          });
                        });

                        const validVals = allVals.filter((v) => Number.isFinite(v));
                        const minVal = validVals.length > 0 ? Math.min(95, ...validVals) : 95;
                        const maxVal = validVals.length > 0 ? Math.max(105, ...validVals) : 105;
                        const rangeVal = maxVal - minVal <= 0 ? 1 : maxVal - minVal;
                        const chartLen = comparisonData.normalized_chart.length;
                        const divisor = chartLen > 1 ? chartLen - 1 : 1;

                        return (
                          <svg
                            viewBox={`0 0 ${width} ${height}`}
                            className="w-full h-full overflow-visible"
                            onMouseLeave={() => setComparisonHoverPoint(null)}
                          >
                            {/* Horizontal gridlines */}
                            {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                              const y = padT + pct * (height - padT - padB);
                              const v = maxVal - pct * rangeVal;
                              return (
                                <g key={i}>
                                  <line
                                    x1={padL}
                                    y1={y}
                                    x2={width - padR}
                                    y2={y}
                                    stroke="#1e2d3e"
                                    strokeDasharray="4 4"
                                  />
                                  <text
                                    x={padL - 8}
                                    y={y + 3}
                                    textAnchor="end"
                                    fill="#556982"
                                    fontSize="10"
                                  >
                                    {v.toFixed(0)}
                                  </text>
                                </g>
                              );
                            })}

                            {/* Base-100 reference dashed line */}
                            {minVal <= 100 && maxVal >= 100 && (() => {
                              const y100 = padT + (1 - (100 - minVal) / rangeVal) * (height - padT - padB);
                              if (!Number.isFinite(y100)) return null;
                              return (
                                <line
                                  x1={padL}
                                  y1={y100}
                                  x2={width - padR}
                                  y2={y100}
                                  stroke="#71d5b3"
                                  strokeWidth="1"
                                  strokeDasharray="2 2"
                                  opacity="0.5"
                                />
                              );
                            })()}

                            {/* Render lines for each fund */}
                            {comparisonData.funds.map((f, fundIdx) => {
                              const color = COMPARISON_COLORS[fundIdx % COMPARISON_COLORS.length];
                              const pts = comparisonData.normalized_chart
                                .map((pt, i) => {
                                  const val = pt.navs[f.fund_id];
                                  if (val === null || val === undefined) return null;
                                  const numVal = Number(val);
                                  if (!Number.isFinite(numVal)) return null;
                                  const rawX = padL + (i / divisor) * (width - padL - padR);
                                  const rawY = padT + (1 - (numVal - minVal) / rangeVal) * (height - padT - padB);
                                  if (!Number.isFinite(rawX) || !Number.isFinite(rawY)) return null;
                                  return { x: rawX, y: rawY, pt };
                                })
                                .filter(Boolean) as Array<{ x: number; y: number; pt: any }>;

                              if (pts.length < 2) return null;

                              const pathD = pts.reduce(
                                (acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`),
                                ""
                              );

                              return (
                                <g key={f.fund_id}>
                                  <path
                                    d={pathD}
                                    fill="none"
                                    stroke={color.stroke}
                                    strokeWidth="2.2"
                                    strokeLinecap="round"
                                  />
                                  {pts.filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y)).map((p, i) => (
                                    <circle
                                      key={i}
                                      cx={p.x}
                                      cy={p.y}
                                      r={3}
                                      fill={color.stroke}
                                      className="opacity-0 hover:opacity-100 cursor-pointer"
                                      onMouseEnter={() => setComparisonHoverPoint(p.pt)}
                                    />
                                  ))}
                                </g>
                              );
                            })}

                            {/* Dates */}
                            <text x={padL} y={height - 8} textAnchor="start" fill="#556982" fontSize="10">
                              {comparisonData.normalized_chart[0]?.date || ""}
                            </text>
                            <text x={width - padR} y={height - 8} textAnchor="end" fill="#556982" fontSize="10">
                              {comparisonData.normalized_chart[comparisonData.normalized_chart.length - 1]?.date || ""}
                            </text>
                          </svg>
                        );
                      })()
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-[#556982]">
                        Insufficient comparative data for the selected period.
                      </div>
                    )}
                  </div>
                </div>

                {/* Side-by-Side Comparison Metrics Table */}
                <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                  <h3 className="text-sm font-bold text-[#edf3fa]">
                    Side-by-Side Comparative Metrics ({comparisonPeriod})
                  </h3>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#080d16] text-[#556982] uppercase text-[10px]">
                        <tr>
                          <th className="py-3 px-4">Metric</th>
                          {comparisonData.funds.map((f, i) => {
                            const color = COMPARISON_COLORS[i % COMPARISON_COLORS.length];
                            return (
                              <th key={f.fund_id} className="py-3 px-4">
                                <span className={`inline-flex items-center gap-1.5 ${color.text} font-bold`}>
                                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color.stroke }} />
                                  {f.scheme_code}
                                </span>
                              </th>
                            );
                          })}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#1e2d3e]">
                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">Scheme Name</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className="py-2.5 px-4 font-bold text-[#edf3fa] max-w-[200px]">
                              {f.scheme_name}
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">Fund House (AMC)</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className="py-2.5 px-4 text-[#91a0b3]">
                              {f.amc_name}
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">Category / Plan</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className="py-2.5 px-4 text-[#91a0b3]">
                              {f.category} • {f.subcategory} ({f.plan_type})
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">Latest NAV</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className="py-2.5 px-4 font-bold text-[#edf3fa]">
                              {f.latest_nav ? `₹${f.latest_nav.toFixed(4)}` : "—"}
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">Period Return ({comparisonPeriod})</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className={`py-2.5 px-4 font-bold ${
                              f.period_return_pct !== null && f.period_return_pct >= 0 ? "text-[#71d5b3]" : "text-rose-400"
                            }`}>
                              {f.period_return_pct !== null ? `${f.period_return_pct.toFixed(2)}%` : "—"}
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">Annualized Return (CAGR)</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className={`py-2.5 px-4 font-bold ${
                              f.cagr_pct !== null && f.cagr_pct >= 0 ? "text-sky-400" : "text-rose-400"
                            }`}>
                              {f.cagr_pct !== null ? `${f.cagr_pct.toFixed(2)}%` : "N/A (< 1Y)"}
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">Annualized Volatility</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className="py-2.5 px-4 font-semibold text-[#edf3fa]">
                              {f.annualized_volatility_pct !== null ? `${f.annualized_volatility_pct.toFixed(2)}%` : "—"}
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">Maximum Drawdown</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className="py-2.5 px-4 font-semibold text-rose-400">
                              {f.max_drawdown_pct.toFixed(2)}%
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">AUM (Crores)</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className="py-2.5 px-4 font-medium text-[#edf3fa]">
                              {f.aum_crores ? `₹${f.aum_crores.toLocaleString("en-IN")} Cr` : "—"}
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">Expense Ratio</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className="py-2.5 px-4 text-[#edf3fa]">
                              {f.expense_ratio !== null ? `${f.expense_ratio}%` : "—"}
                            </td>
                          ))}
                        </tr>

                        <tr className="hover:bg-[#121d2d]">
                          <td className="py-2.5 px-4 font-semibold text-[#91a0b3]">CRISIL Rating</td>
                          {comparisonData.funds.map((f) => (
                            <td key={f.fund_id} className="py-2.5 px-4 text-amber-300 font-semibold">
                              {f.crisil_rating ? `${f.crisil_rating}★` : "Unrated"}
                            </td>
                          ))}
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
