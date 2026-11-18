"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  Briefcase,
  PieChart,
  Newspaper,
  FlaskConical,
  Bot,
  Shield,
  Database,
  Server,
  ArrowRight,
  RefreshCw,
  Cpu,
  UserCheck,
  Sparkles,
  Calendar,
  Layers,
  ChevronRight,
  Plus,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  ShieldCheck,
} from "lucide-react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/lib/auth-context";
import {
  api,
  HealthResponse,
  Instrument,
  Portfolio,
  NewsArticle,
  BacktestRun,
} from "@/lib/api";

export default function DashboardPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [recentBacktests, setRecentBacktests] = useState<BacktestRun[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);

  const loadDashboardData = async () => {
    setIsLoadingData(true);
    try {
      const [healthRes, instRes, portRes, newsRes, runsRes] = await Promise.allSettled([
        api.getHealth(),
        api.listInstruments({ size: 5 }),
        api.listPortfolios(),
        api.listNews({ size: 4 }),
        api.listBacktestRuns(5),
      ]);

      if (healthRes.status === "fulfilled") setHealth(healthRes.value);
      if (instRes.status === "fulfilled") setInstruments(instRes.value.items || []);
      if (portRes.status === "fulfilled") setPortfolios(portRes.value || []);
      if (newsRes.status === "fulfilled") setNews(newsRes.value.items || []);
      if (runsRes.status === "fulfilled") setRecentBacktests(runsRes.value || []);
    } catch (err) {
      console.error("Dashboard overview data loading error:", err);
    } finally {
      setIsLoadingData(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadDashboardData();
    }
  }, [user]);

  return (
    <DashboardLayout title="Central Intelligence Terminal">
      <div className="space-y-6">
        {/* Workspace Header Banner */}
        <section className="relative overflow-hidden rounded-2xl bg-[#101A2B] border border-[#26344A] p-6 sm:p-8">
          <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-[#8E91FF]/10 via-[#54DCC5]/5 to-transparent rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-4xl space-y-3">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="px-2.5 py-0.5 rounded-full bg-[#54DCC5]/10 text-[#54DCC5] text-[10px] font-bold tracking-wider uppercase border border-[#54DCC5]/30 flex items-center gap-1.5 font-mono">
                <ShieldCheck size={12} />
                Authenticated Session
              </span>
              <span className="text-xs text-[#A6B6CC] font-mono">
                {user?.email} • Role: {user?.role || "analyst"}
              </span>
              <span className="text-[#A6B6CC]/40 hidden sm:inline">•</span>
              <span className="text-[11px] text-[#8E91FF] font-mono flex items-center gap-1">
                <Activity size={12} /> Live Deterministic Fixtures
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F2F4FF] tracking-tight">
              Welcome back, <span className="text-[#8E91FF]">{user?.name}</span>
            </h1>

            <p className="text-xs sm:text-sm text-[#A6B6CC] leading-relaxed max-w-2xl">
              QuantWeave Central Intelligence Terminal provides unified access to Indian equity indicators,
              double-entry portfolio tracking, mutual fund simulations, and zero look-ahead strategy backtesting.
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-2.5">
              <Link
                href="/quantlab"
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#8E91FF] hover:bg-[#7b7eff] text-[#080D19] font-bold text-xs transition-all shadow-md shadow-[#8E91FF]/20"
              >
                <FlaskConical size={14} />
                <span>Launch QuantLab Simulator</span>
              </Link>
              <Link
                href="/ai"
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#142035] hover:bg-[#101A2B] text-[#54DCC5] font-semibold text-xs border border-[#26344A] transition-colors"
              >
                <Bot size={14} />
                <span>Ask AI Copilot</span>
              </Link>
              <Link
                href="/portfolio"
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#101A2B] hover:bg-[#142035] text-[#F2F4FF] font-medium text-xs border border-[#26344A] transition-colors"
              >
                <Briefcase size={14} />
                <span>Manage Portfolios</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Foundation Status Metric Tiles */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-1">
            <div className="flex items-center justify-between text-[#A6B6CC] text-xs">
              <span className="font-semibold uppercase tracking-wider text-[10px] font-mono">FastAPI Backend</span>
              <Server size={16} className="text-[#54DCC5]" />
            </div>
            <div className="text-xl font-bold text-[#F2F4FF] font-mono">
              {health?.service || "quantweave-api"}
            </div>
            <p className="text-[11px] text-[#54DCC5] font-medium flex items-center gap-1 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-[#54DCC5]" />
              {health?.status === "ok" ? "Operational (200 OK)" : "Connecting"}
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-1">
            <div className="flex items-center justify-between text-[#A6B6CC] text-xs">
              <span className="font-semibold uppercase tracking-wider text-[10px] font-mono">Reference Equities</span>
              <TrendingUp size={16} className="text-[#8E91FF]" />
            </div>
            <div className="text-xl font-bold text-[#F2F4FF] font-mono">
              10 NSE Securities
            </div>
            <p className="text-[11px] text-[#A6B6CC] font-mono">
              Wilder RSI • MACD • Bands
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-1">
            <div className="flex items-center justify-between text-[#A6B6CC] text-xs">
              <span className="font-semibold uppercase tracking-wider text-[10px] font-mono">Mutual Funds Tracked</span>
              <PieChart size={16} className="text-[#F6BE76]" />
            </div>
            <div className="text-xl font-bold text-[#F2F4FF] font-mono">
              10 Schemes
            </div>
            <p className="text-[11px] text-[#A6B6CC] font-mono">
              Direct & Regular • SIP Model
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-1">
            <div className="flex items-center justify-between text-[#A6B6CC] text-xs">
              <span className="font-semibold uppercase tracking-wider text-[10px] font-mono">Macro Wire</span>
              <Newspaper size={16} className="text-[#8E91FF]" />
            </div>
            <div className="text-xl font-bold text-[#F2F4FF] font-mono">
              RBI & MOSPI
            </div>
            <p className="text-[11px] text-[#A6B6CC] font-mono">
              Repo Rate • CPI • Oil
            </p>
          </div>
        </section>

        {/* Central Workspace Grid (2 Columns) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (7 cols): Portfolio & QuantLab Overview */}
          <div className="lg:col-span-7 space-y-6">
            {/* Portfolio Intelligence Quick Card */}
            <div className="p-6 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-4">
              <div className="flex items-center justify-between border-b border-[#26344A] pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-[#142035] text-[#54DCC5] flex items-center justify-center border border-[#26344A]">
                    <Briefcase size={16} />
                  </div>
                  <h2 className="text-sm font-bold text-[#F2F4FF]">Portfolio Ledger & Valuation</h2>
                </div>
                <Link
                  href="/portfolio"
                  className="text-xs font-semibold text-[#8E91FF] hover:text-[#7b7eff] inline-flex items-center gap-1 font-mono"
                >
                  <span>Open Ledger</span>
                  <ChevronRight size={13} />
                </Link>
              </div>

              {portfolios.length === 0 ? (
                <div className="p-8 text-center rounded-xl bg-[#080D19] border border-[#26344A] space-y-2">
                  <Briefcase size={28} className="mx-auto text-[#A6B6CC]/50" />
                  <h3 className="text-sm font-bold text-[#F2F4FF]">No Portfolios Created Yet</h3>
                  <p className="text-xs text-[#A6B6CC] max-w-sm mx-auto">
                    Create an INR paper-trading portfolio to record transactions, track cost basis (WACB),
                    and compute XIRR performance.
                  </p>
                  <div className="pt-2">
                    <Link
                      href="/portfolio"
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#8E91FF] text-[#080D19] font-bold text-xs"
                    >
                      <Plus size={14} /> Create Portfolio
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="p-3.5 rounded-xl bg-[#080D19] border border-[#26344A]">
                      <span className="text-[10px] text-[#A6B6CC] font-mono uppercase">Active Portfolios</span>
                      <div className="text-lg font-bold text-[#F2F4FF] font-mono mt-0.5">
                        {portfolios.length}
                      </div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-[#080D19] border border-[#26344A]">
                      <span className="text-[10px] text-[#A6B6CC] font-mono uppercase">Base Currency</span>
                      <div className="text-lg font-bold text-[#54DCC5] font-mono mt-0.5">
                        INR (₹)
                      </div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-[#080D19] border border-[#26344A] col-span-2 sm:col-span-1">
                      <span className="text-[10px] text-[#A6B6CC] font-mono uppercase">Accounting Basis</span>
                      <div className="text-xs font-bold text-[#8E91FF] font-mono mt-1">
                        Weighted Average (WACB)
                      </div>
                    </div>
                  </div>

                  <div className="divide-y divide-[#26344A] border border-[#26344A] rounded-xl overflow-hidden bg-[#080D19]">
                    {portfolios.slice(0, 3).map((p) => (
                      <div key={p.id} className="p-3 flex items-center justify-between text-xs">
                        <div>
                          <strong className="text-[#F2F4FF] font-semibold">{p.name}</strong>
                          <span className="text-[#A6B6CC] ml-2 font-mono text-[11px]">{p.base_currency}</span>
                        </div>
                        <Link
                          href="/portfolio"
                          className="text-[#54DCC5] hover:underline font-mono text-[11px] flex items-center gap-1"
                        >
                          View Holdings <ArrowRight size={11} />
                        </Link>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* QuantLab Recent Research Runs */}
            <div className="p-6 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-4">
              <div className="flex items-center justify-between border-b border-[#26344A] pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-[#142035] text-[#8E91FF] flex items-center justify-center border border-[#26344A]">
                    <FlaskConical size={16} />
                  </div>
                  <h2 className="text-sm font-bold text-[#F2F4FF]">QuantLab Strategy Simulations</h2>
                </div>
                <Link
                  href="/quantlab"
                  className="text-xs font-semibold text-[#8E91FF] hover:text-[#7b7eff] inline-flex items-center gap-1 font-mono"
                >
                  <span>Open Studio</span>
                  <ChevronRight size={13} />
                </Link>
              </div>

              {recentBacktests.length === 0 ? (
                <div className="p-8 text-center rounded-xl bg-[#080D19] border border-[#26344A] space-y-2">
                  <FlaskConical size={28} className="mx-auto text-[#A6B6CC]/50" />
                  <h3 className="text-sm font-bold text-[#F2F4FF]">No Strategy Backtests Run Yet</h3>
                  <p className="text-xs text-[#A6B6CC] max-w-sm mx-auto">
                    Test SMA/EMA crossovers, RSI mean-reversion, or Buy & Hold strategies against NSE historical data.
                  </p>
                  <div className="pt-2">
                    <Link
                      href="/quantlab"
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#8E91FF] text-[#080D19] font-bold text-xs"
                    >
                      <Plus size={14} /> New Backtest Simulation
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="divide-y divide-[#26344A] border border-[#26344A] rounded-xl overflow-hidden bg-[#080D19]">
                  {recentBacktests.map((run) => (
                    <div key={run.id} className="p-3.5 flex items-center justify-between text-xs">
                      <div className="space-y-0.5">
                        <div className="font-semibold text-[#F2F4FF] flex items-center gap-2">
                          <span>{run.strategy_name || run.strategy_type || "Strategy"}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#142035] text-[#8E91FF] font-mono border border-[#26344A]">
                            {run.instrument_ticker || "NSE"}
                          </span>
                        </div>
                        <div className="text-[11px] text-[#A6B6CC] font-mono">
                          {run.start_date} to {run.end_date}
                        </div>
                      </div>

                      <div className="text-right">
                        {run.metrics?.total_return_pct !== undefined ? (
                          <div
                            className={`font-mono font-bold tabular-nums ${
                              run.metrics.total_return_pct >= 0 ? "text-[#54DCC5]" : "text-[#F26C6C]"
                            }`}
                          >
                            {run.metrics.total_return_pct >= 0 ? "+" : ""}
                            {run.metrics.total_return_pct.toFixed(2)}%
                          </div>
                        ) : (
                          <span className="text-xs text-[#A6B6CC] font-mono">Completed</span>
                        )}
                        <span className="text-[10px] text-[#A6B6CC]/70 font-mono">
                          Sharpe: {run.metrics?.sharpe_ratio?.toFixed(2) ?? "N/A"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column (5 cols): Equity Radar & MarketPulse Wire */}
          <div className="lg:col-span-5 space-y-6">
            {/* Equity Reference Radar */}
            <div className="p-6 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-4">
              <div className="flex items-center justify-between border-b border-[#26344A] pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-[#142035] text-[#54DCC5] flex items-center justify-center border border-[#26344A]">
                    <TrendingUp size={16} />
                  </div>
                  <h2 className="text-sm font-bold text-[#F2F4FF]">Indian Equity Radar</h2>
                </div>
                <Link
                  href="/equity"
                  className="text-xs font-semibold text-[#54DCC5] hover:text-[#46c2ad] inline-flex items-center gap-1 font-mono"
                >
                  <span>Directory</span>
                  <ChevronRight size={13} />
                </Link>
              </div>

              <div className="space-y-2">
                {instruments.map((inst) => (
                  <Link
                    key={inst.id}
                    href={`/instruments/${inst.id}`}
                    className="p-3 rounded-xl bg-[#080D19] hover:bg-[#142035] border border-[#26344A] flex items-center justify-between transition-colors group block"
                  >
                    <div>
                      <div className="font-bold text-xs text-[#F2F4FF] group-hover:text-[#8E91FF] transition-colors font-mono">
                        {inst.symbol}
                      </div>
                      <div className="text-[11px] text-[#A6B6CC] truncate max-w-[180px]">
                        {inst.company_name}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="px-2 py-0.5 rounded-full bg-[#142035] text-[10px] font-mono text-[#8E91FF] border border-[#26344A]">
                        {inst.sector || "Large Cap"}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            {/* MarketPulse News Wire */}
            <div className="p-6 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-4">
              <div className="flex items-center justify-between border-b border-[#26344A] pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-[#142035] text-[#F6BE76] flex items-center justify-center border border-[#26344A]">
                    <Newspaper size={16} />
                  </div>
                  <h2 className="text-sm font-bold text-[#F2F4FF]">MarketPulse Wire</h2>
                </div>
                <Link
                  href="/market"
                  className="text-xs font-semibold text-[#F6BE76] hover:text-[#e4aa5f] inline-flex items-center gap-1 font-mono"
                >
                  <span>All News</span>
                  <ChevronRight size={13} />
                </Link>
              </div>

              <div className="space-y-2.5">
                {news.map((n) => (
                  <div key={n.id} className="p-3 rounded-xl bg-[#080D19] border border-[#26344A] space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-[#A6B6CC]/70 font-mono">
                      <span className="text-[#8E91FF]">{n.source_name || "Market Wire"}</span>
                      <span>{n.published_at ? n.published_at.split("T")[0] : ""}</span>
                    </div>
                    <h3 className="text-xs font-semibold text-[#F2F4FF] line-clamp-2 leading-relaxed">
                      {n.title}
                    </h3>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Research Prompts */}
            <div className="p-5 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-[#8E91FF]">
                <Bot size={16} />
                <span>Quick Copilot Prompts</span>
              </div>
              <p className="text-xs text-[#A6B6CC] leading-relaxed">
                Click any prompt to launch grounded AI analysis based on verified backend analytics.
              </p>
              <div className="space-y-1.5">
                <Link
                  href="/ai?prompt=Explain%20how%20Wilder%20RSI%2014%20differs%20from%20simple%20momentum"
                  className="block p-2 rounded-xl bg-[#080D19] hover:bg-[#142035] border border-[#26344A] text-[11px] text-[#F2F4FF] hover:text-[#8E91FF] transition-colors"
                >
                  &quot;Explain Wilder RSI 14 formula smoothing&quot; →
                </Link>
                <Link
                  href="/ai?prompt=What%20is%20the%20WACB%20method%20used%20for%20portfolio%20tax%20and%20P%26L?"
                  className="block p-2 rounded-xl bg-[#080D19] hover:bg-[#142035] border border-[#26344A] text-[11px] text-[#F2F4FF] hover:text-[#54DCC5] transition-colors"
                >
                  &quot;How does WACB calculate cost basis on sell?&quot; →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
