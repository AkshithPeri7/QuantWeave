"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  Compass,
  Database,
  DollarSign,
  FileText,
  Gauge,
  Globe,
  Info,
  Layers,
  Loader2,
  PieChart,
  Scale,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
  Zap,
  Newspaper,
  ExternalLink,
} from "lucide-react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { PriceChart } from "@/components/PriceChart";
import {
  api,
  CompanyFundamentalsResponse,
  FinancialStatement,
  FundamentalRatios,
  InstrumentDetail,
  PriceBar,
  TechnicalAnalysisResponse,
  NewsArticle,
} from "@/lib/api";

type StatementTab = "income" | "balance" | "cashflow" | "ratios";

export default function InstrumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [instrument, setInstrument] = useState<InstrumentDetail | null>(null);
  const [prices, setPrices] = useState<PriceBar[]>([]);
  const [technicals, setTechnicals] = useState<TechnicalAnalysisResponse | null>(null);
  const [fundamentals, setFundamentals] = useState<CompanyFundamentalsResponse | null>(null);
  const [companyNews, setCompanyNews] = useState<NewsArticle[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<StatementTab>("income");
  const [tablePage, setTablePage] = useState(1);
  const tablePageSize = 10;

  useEffect(() => {
    if (!id) return;
    setIsLoading(true);
    setError(null);

    Promise.all([
      api.getInstrument(id),
      api.getInstrumentPrices(id, { limit: 1000 }),
      api.getInstrumentTechnicals(id).catch(() => null),
      api.getInstrumentFundamentals(id).catch(() => null),
      api.getCompanyNews(id, 6).catch(() => []),
    ])
      .then(([instData, pricesData, techData, fundData, newsData]) => {
        setInstrument(instData);
        setPrices(pricesData.prices || []);
        setTechnicals(techData);
        setFundamentals(fundData);
        setCompanyNews(newsData || []);
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Failed to load instrument details";
        setError(msg);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [id]);

  if (isLoading) {
    return (
      <DashboardLayout title="Loading Instrument...">
        <div className="h-96 flex flex-col items-center justify-center gap-3 text-xs text-[#71d5b3]">
          <Loader2 size={24} className="animate-spin" />
          <span>Retrieving market data, technical indicators & fundamentals...</span>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !instrument) {
    return (
      <DashboardLayout title="Instrument Not Found">
        <div className="max-w-xl mx-auto my-12 p-6 rounded-2xl bg-[#141e2c] border border-rose-900/60 text-center space-y-4">
          <ShieldAlert size={36} className="mx-auto text-rose-400" />
          <h2 className="text-lg font-bold text-[#edf3fa]">Failed to Load Instrument</h2>
          <p className="text-xs text-[#91a0b3]">{error || "The requested instrument could not be found."}</p>
          <Link
            href="/equity"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#71d5b3] text-[#07130f] font-bold text-xs"
          >
            <ArrowLeft size={14} />
            Back to Equity Directory
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  const latestPrice = instrument.latest_price;
  const isPositive = latestPrice && latestPrice.open
    ? Number(latestPrice.close) >= Number(latestPrice.open)
    : true;

  // Reverse price order for table (latest first)
  const reversedPrices = [...prices].reverse();
  const totalTablePages = Math.max(1, Math.ceil(reversedPrices.length / tablePageSize));
  const currentTableRows = reversedPrices.slice(
    (tablePage - 1) * tablePageSize,
    tablePage * tablePageSize
  );

  const annualStatements = fundamentals?.statements.filter((s) => s.period_type === "annual") || [];
  const latestRatios = fundamentals?.latest_ratios;

  return (
    <DashboardLayout title={`${instrument.symbol} (${instrument.exchange})`}>
      <div className="space-y-6">
        {/* Navigation & Header Actions */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/equity"
            className="inline-flex items-center gap-2 text-xs font-semibold text-[#8ca3ba] hover:text-[#71d5b3] transition-colors"
          >
            <ArrowLeft size={14} />
            Back to Equities
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href={`/equity/compare?ids=${instrument.id}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#142335] text-[#38bdf8] border border-[#23425e] hover:bg-[#1a2e46] transition-colors text-xs font-semibold"
            >
              <Scale size={13} />
              Compare With Peers
            </Link>

            <Link
              href={`/ai?explain=equity&symbol=${instrument.symbol}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#15273b] text-[#71d5b3] border border-[#1e3e4a] hover:bg-[#1c3550] transition-colors text-xs font-semibold"
            >
              <Zap size={13} />
              Explain with Copilot
            </Link>

            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-emerald-950/70 text-[#71d5b3] border border-[#235848]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#71d5b3] animate-pulse" />
              DEMO SYNTHETIC DATA
            </span>
          </div>
        </div>

        {/* Company Header Card */}
        <div className="bg-[#0f1927] border border-[#202f42] rounded-2xl p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl sm:text-3xl font-black text-[#edf3fa] tracking-tight">
                  {instrument.symbol}
                </h1>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-[#17273a] text-[#8ca3ba] border border-[#253d5a]">
                  {instrument.exchange}
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#132337] text-[#71d5b3]">
                  {instrument.sector || "Equity"}
                </span>
              </div>
              <p className="text-sm text-[#91a0b3] font-medium">{instrument.company_name}</p>
              <div className="flex flex-wrap items-center gap-4 text-xs text-[#62778f] pt-1">
                {instrument.industry && <span>Industry: {instrument.industry}</span>}
                {instrument.isin && <span>ISIN: {instrument.isin}</span>}
                <span>Currency: {instrument.currency}</span>
              </div>
            </div>

            {/* Quick Price Badge */}
            {latestPrice && (
              <div className="md:text-right">
                <span className="text-xs text-[#7f94aa] block mb-1">
                  Latest Daily Close ({instrument.as_of})
                </span>
                <div className="text-3xl font-extrabold text-[#edf3fa] tracking-tight font-mono">
                  ₹{Number(latestPrice.close).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </div>
                {latestPrice.open && (
                  <div
                    className={`inline-flex items-center text-xs font-bold mt-1 ${
                      isPositive ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {isPositive ? <TrendingUp size={13} className="mr-1" /> : <TrendingDown size={13} className="mr-1" />}
                    {isPositive ? "+" : ""}
                    {(Number(latestPrice.close) - Number(latestPrice.open)).toFixed(2)} (
                    {(((Number(latestPrice.close) - Number(latestPrice.open)) / Number(latestPrice.open)) * 100).toFixed(2)}%)
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Interactive Technical Price Chart */}
        <PriceChart
          prices={prices}
          symbol={instrument.symbol}
          currency={instrument.currency}
          isDemo={instrument.is_demo}
          dataSource={instrument.data_source}
          technicals={technicals}
        />

        {/* Technical Analysis Summary Card */}
        {technicals && technicals.summary && (
          <div className="bg-[#0f1927] border border-[#202f42] rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#1b2b3d] pb-3">
              <div className="flex items-center gap-2.5">
                <Compass size={18} className="text-[#71d5b3]" />
                <h2 className="text-sm font-bold text-[#edf3fa] tracking-wide uppercase">
                  Technical Indicator Analysis
                </h2>
              </div>
              <span
                className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                  technicals.summary.trend === "Bullish"
                    ? "bg-emerald-950 text-emerald-300 border-emerald-700/50"
                    : technicals.summary.trend === "Bearish"
                    ? "bg-rose-950 text-rose-300 border-rose-700/50"
                    : "bg-slate-900 text-slate-300 border-slate-700"
                }`}
              >
                Overall Trend: {technicals.summary.trend}
              </span>
            </div>

            <p className="text-xs text-[#91a0b3]">{technicals.summary.trend_description}</p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              {/* RSI (14) */}
              <div className="p-3 rounded-xl bg-[#0a1320] border border-[#1a2838]">
                <div className="flex items-center justify-between text-[11px] text-[#6b7e93] mb-1">
                  <span>RSI (14)</span>
                  <span
                    className={`font-bold text-[10px] px-1.5 py-0.2 rounded ${
                      technicals.summary.rsi_state === "Overbought"
                        ? "bg-rose-950 text-rose-400"
                        : technicals.summary.rsi_state === "Oversold"
                        ? "bg-emerald-950 text-emerald-400"
                        : "bg-slate-900 text-[#71d5b3]"
                    }`}
                  >
                    {technicals.summary.rsi_state}
                  </span>
                </div>
                <div className="text-lg font-mono font-bold text-[#edf3fa]">
                  {technicals.summary.rsi_value !== null ? technicals.summary.rsi_value.toFixed(1) : "N/A"}
                </div>
                <span className="text-[10px] text-[#55697d] block mt-0.5">
                  Wilder Smoothing (30/70)
                </span>
              </div>

              {/* MACD Signal */}
              <div className="p-3 rounded-xl bg-[#0a1320] border border-[#1a2838]">
                <div className="flex items-center justify-between text-[11px] text-[#6b7e93] mb-1">
                  <span>MACD (12,26,9)</span>
                  <span className="font-bold text-[10px] text-sky-400">
                    {technicals.summary.macd_state}
                  </span>
                </div>
                <div className="text-lg font-mono font-bold text-[#edf3fa]">
                  {technicals.summary.macd_histogram !== null
                    ? (technicals.summary.macd_histogram > 0 ? "+" : "") + technicals.summary.macd_histogram.toFixed(2)
                    : "N/A"}
                </div>
                <span className="text-[10px] text-[#55697d] block mt-0.5">Histogram Bias</span>
              </div>

              {/* Moving Average Alignment */}
              <div className="p-3 rounded-xl bg-[#0a1320] border border-[#1a2838]">
                <div className="flex items-center justify-between text-[11px] text-[#6b7e93] mb-1">
                  <span>MA Regime</span>
                  <span className="font-bold text-[10px] text-amber-300">
                    {technicals.summary.golden_cross === true
                      ? "Golden Cross"
                      : technicals.summary.golden_cross === false
                      ? "Death Cross"
                      : "Neutral"}
                  </span>
                </div>
                <div className="text-xs font-semibold text-[#edf3fa] truncate mt-1">
                  50 SMA {technicals.summary.golden_cross ? ">" : "<"} 200 SMA
                </div>
                <span className="text-[10px] text-[#55697d] block mt-1">Long-term Momentum</span>
              </div>

              {/* Bollinger Bands */}
              <div className="p-3 rounded-xl bg-[#0a1320] border border-[#1a2838]">
                <div className="flex items-center justify-between text-[11px] text-[#6b7e93] mb-1">
                  <span>Bollinger (20,2)</span>
                  <span className="font-bold text-[10px] text-cyan-300">
                    {technicals.summary.bb_state}
                  </span>
                </div>
                <div className="text-xs font-semibold text-[#edf3fa] truncate mt-1">
                  Vol Envelope
                </div>
                <span className="text-[10px] text-[#55697d] block mt-1">Std Dev 2.0 Bands</span>
              </div>
            </div>
          </div>
        )}

        {/* Fundamental Analysis & Valuation Section */}
        <div className="bg-[#0f1927] border border-[#202f42] rounded-2xl p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1b2b3d] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <FileText size={18} className="text-[#71d5b3]" />
                <h2 className="text-sm font-bold text-[#edf3fa] tracking-wide uppercase">
                  Fundamental Statements & Ratios
                </h2>
              </div>
              <p className="text-xs text-[#7f94aa] mt-0.5">
                Multi-period corporate accounting line items and financial metrics.
              </p>
            </div>

            {/* Statement Type Tabs */}
            <div className="flex bg-[#09111c] border border-[#1d2b3e] p-1 rounded-xl text-xs self-start sm:self-auto">
              <button
                onClick={() => setActiveTab("ratios")}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  activeTab === "ratios" ? "bg-[#182c42] text-[#71d5b3]" : "text-[#7f94aa] hover:text-[#edf3fa]"
                }`}
              >
                Ratios
              </button>
              <button
                onClick={() => setActiveTab("income")}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  activeTab === "income" ? "bg-[#182c42] text-[#71d5b3]" : "text-[#7f94aa] hover:text-[#edf3fa]"
                }`}
              >
                Income
              </button>
              <button
                onClick={() => setActiveTab("balance")}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  activeTab === "balance" ? "bg-[#182c42] text-[#71d5b3]" : "text-[#7f94aa] hover:text-[#edf3fa]"
                }`}
              >
                Balance Sheet
              </button>
              <button
                onClick={() => setActiveTab("cashflow")}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  activeTab === "cashflow" ? "bg-[#182c42] text-[#71d5b3]" : "text-[#7f94aa] hover:text-[#edf3fa]"
                }`}
              >
                Cash Flow
              </button>
            </div>
          </div>

          {/* Educational Demo Banner */}
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-950/30 border border-amber-800/40 text-amber-300 text-xs">
            <Info size={16} className="shrink-0 mt-0.5 text-amber-400" />
            <span>
              <strong>DEMO SYNTHETIC DISCLOSURES:</strong> Financial statement line items and valuation
              ratios presented here are synthetic deterministic fixtures generated for educational modeling.
              They are not real-world audited corporate filings.
            </span>
          </div>

          {/* Tab 1: Valuation & Ratios Cards */}
          {activeTab === "ratios" && latestRatios && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-[#09111c] border border-[#1b293a]">
                  <span className="text-xs text-[#6b7e93] block">P/E Ratio</span>
                  <div className="text-2xl font-bold font-mono text-[#edf3fa] mt-1">
                    {latestRatios.pe_ratio !== null ? `${latestRatios.pe_ratio}x` : "N/A"}
                  </div>
                  <span className="text-[11px] text-[#55697d] block mt-1">Price / EPS</span>
                </div>
                <div className="p-4 rounded-xl bg-[#09111c] border border-[#1b293a]">
                  <span className="text-xs text-[#6b7e93] block">P/B Ratio</span>
                  <div className="text-2xl font-bold font-mono text-[#edf3fa] mt-1">
                    {latestRatios.pb_ratio !== null ? `${latestRatios.pb_ratio}x` : "N/A"}
                  </div>
                  <span className="text-[11px] text-[#55697d] block mt-1">Price / Book Value</span>
                </div>
                <div className="p-4 rounded-xl bg-[#09111c] border border-[#1b293a]">
                  <span className="text-xs text-[#6b7e93] block">Return on Equity (ROE)</span>
                  <div className="text-2xl font-bold font-mono text-[#71d5b3] mt-1">
                    {latestRatios.roe_pct !== null ? `${latestRatios.roe_pct}%` : "N/A"}
                  </div>
                  <span className="text-[11px] text-[#55697d] block mt-1">Net Income / Equity</span>
                </div>
                <div className="p-4 rounded-xl bg-[#09111c] border border-[#1b293a]">
                  <span className="text-xs text-[#6b7e93] block">Debt-to-Equity</span>
                  <div className="text-2xl font-bold font-mono text-[#edf3fa] mt-1">
                    {latestRatios.debt_to_equity !== null ? latestRatios.debt_to_equity : "0.00"}
                  </div>
                  <span className="text-[11px] text-[#55697d] block mt-1">Total Debt / Equity</span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-[#09111c] border border-[#1b293a]">
                  <span className="text-xs text-[#6b7e93] block">Gross Margin</span>
                  <div className="text-xl font-bold font-mono text-[#edf3fa] mt-1">
                    {latestRatios.gross_margin_pct !== null ? `${latestRatios.gross_margin_pct}%` : "N/A"}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-[#09111c] border border-[#1b293a]">
                  <span className="text-xs text-[#6b7e93] block">Operating Margin (EBIT)</span>
                  <div className="text-xl font-bold font-mono text-[#edf3fa] mt-1">
                    {latestRatios.operating_margin_pct !== null ? `${latestRatios.operating_margin_pct}%` : "N/A"}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-[#09111c] border border-[#1b293a]">
                  <span className="text-xs text-[#6b7e93] block">Net Profit Margin</span>
                  <div className="text-xl font-bold font-mono text-[#edf3fa] mt-1">
                    {latestRatios.net_margin_pct !== null ? `${latestRatios.net_margin_pct}%` : "N/A"}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Income Statement Table */}
          {activeTab === "income" && annualStatements.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#1f2e42] text-[#71d5b3]">
                    <th className="py-2.5 px-3">Line Item (₹ in Cr)</th>
                    {annualStatements.map((s) => (
                      <th key={s.id} className="py-2.5 px-3 text-right font-mono">
                        FY{s.fiscal_year}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#172537] font-mono">
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#edf3fa] font-semibold">Total Revenue</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#edf3fa]">
                        {s.revenue ? Number(s.revenue).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#91a0b3]">Cost of Goods Sold (COGS)</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#91a0b3]">
                        {s.cost_of_goods_sold ? Number(s.cost_of_goods_sold).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#edf3fa] font-semibold">Gross Profit</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#71d5b3]">
                        {s.gross_profit ? Number(s.gross_profit).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#91a0b3]">Operating Expenses</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#91a0b3]">
                        {s.operating_expenses ? Number(s.operating_expenses).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#edf3fa] font-semibold">Operating Profit (EBIT)</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#edf3fa]">
                        {s.operating_income ? Number(s.operating_income).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#91a0b3]">Tax Expense</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#91a0b3]">
                        {s.tax_expense ? Number(s.tax_expense).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr className="bg-[#121e2e]">
                    <td className="py-2.5 px-3 font-sans text-[#71d5b3] font-bold">Net Income</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#71d5b3] font-bold">
                        {s.net_income ? Number(s.net_income).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#edf3fa]">Earnings Per Share (EPS)</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#edf3fa]">
                        ₹{s.eps ? Number(s.eps).toFixed(2) : "-"}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: Balance Sheet Table */}
          {activeTab === "balance" && annualStatements.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#1f2e42] text-[#71d5b3]">
                    <th className="py-2.5 px-3">Line Item (₹ in Cr)</th>
                    {annualStatements.map((s) => (
                      <th key={s.id} className="py-2.5 px-3 text-right font-mono">
                        FY{s.fiscal_year}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#172537] font-mono">
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#edf3fa]">Cash & Equivalents</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#edf3fa]">
                        {s.cash_and_equivalents ? Number(s.cash_and_equivalents).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#91a0b3]">Total Current Assets</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#91a0b3]">
                        {s.total_current_assets ? Number(s.total_current_assets).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr className="bg-[#121e2e]">
                    <td className="py-2.5 px-3 font-sans text-[#edf3fa] font-bold">Total Assets</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#edf3fa] font-bold">
                        {s.total_assets ? Number(s.total_assets).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#91a0b3]">Total Current Liabilities</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#91a0b3]">
                        {s.total_current_liabilities ? Number(s.total_current_liabilities).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#91a0b3]">Total Debt (Borrowings)</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#91a0b3]">
                        {s.total_debt ? Number(s.total_debt).toLocaleString("en-IN") : "0"}
                      </td>
                    ))}
                  </tr>
                  <tr className="bg-[#121e2e]">
                    <td className="py-2.5 px-3 font-sans text-[#71d5b3] font-bold">Shareholder Equity</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#71d5b3] font-bold">
                        {s.shareholder_equity ? Number(s.shareholder_equity).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#edf3fa]">Book Value Per Share</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#edf3fa]">
                        ₹{s.book_value_per_share ? Number(s.book_value_per_share).toFixed(2) : "-"}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 4: Cash Flow Table */}
          {activeTab === "cashflow" && annualStatements.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#1f2e42] text-[#71d5b3]">
                    <th className="py-2.5 px-3">Line Item (₹ in Cr)</th>
                    {annualStatements.map((s) => (
                      <th key={s.id} className="py-2.5 px-3 text-right font-mono">
                        FY{s.fiscal_year}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#172537] font-mono">
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#edf3fa]">Cash Flow from Operations (OCF)</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#edf3fa]">
                        {s.operating_cash_flow ? Number(s.operating_cash_flow).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-sans text-[#91a0b3]">Capital Expenditures (CapEx)</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#91a0b3]">
                        {s.capital_expenditures ? Number(s.capital_expenditures).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr className="bg-[#121e2e]">
                    <td className="py-2.5 px-3 font-sans text-[#71d5b3] font-bold">Free Cash Flow (FCF)</td>
                    {annualStatements.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 text-right text-[#71d5b3] font-bold">
                        {s.free_cash_flow ? Number(s.free_cash_flow).toLocaleString("en-IN") : "-"}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {annualStatements.length === 0 && (
            <div className="py-8 text-center text-xs text-[#62778f]">
              No financial statements available for this instrument.
            </div>
          )}
        </div>

        {/* Company News & MarketPulse Intelligence */}
        {companyNews && companyNews.length > 0 && (
          <div className="bg-[#0f1927] border border-[#202f42] rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#1f2e42] pb-3">
              <div className="flex items-center gap-2">
                <Newspaper size={16} className="text-[#71d5b3]" />
                <h2 className="text-sm font-bold text-[#edf3fa] tracking-wide uppercase">
                  MarketPulse News & Intelligence ({companyNews.length} Articles)
                </h2>
              </div>
              <Link
                href="/market"
                className="text-xs font-semibold text-[#71d5b3] hover:underline flex items-center gap-1"
              >
                Open News Wire <ExternalLink size={12} />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {companyNews.map((art) => {
                const sentiment = art.sentiment?.sentiment_label || "NEUTRAL";
                const sentimentColor =
                  sentiment === "POSITIVE"
                    ? "text-[#71d5b3] bg-emerald-950/60 border-emerald-600/40"
                    : sentiment === "NEGATIVE"
                    ? "text-rose-400 bg-rose-950/60 border-rose-600/40"
                    : "text-[#91a0b3] bg-[#142030] border-[#1e2d3e]";

                return (
                  <div
                    key={art.id}
                    className="p-4 rounded-xl bg-[#0c1624] border border-[#1b2b3d] hover:border-[#2d425c] transition-all flex flex-col justify-between space-y-2"
                  >
                    <div>
                      <div className="flex items-center justify-between text-[10px] text-[#556982] mb-1">
                        <span>{art.source_name || "QuantWeave Wire"}</span>
                        <span className={`px-1.5 py-0.2 rounded border font-bold ${sentimentColor}`}>
                          {sentiment}
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-[#edf3fa] line-clamp-2">
                        {art.title}
                      </h4>
                      {art.short_description && (
                        <p className="text-[11px] text-[#8ca3ba] line-clamp-2 mt-1">
                          {art.short_description}
                        </p>
                      )}
                    </div>
                    <div className="pt-2 border-t border-[#142232] flex items-center justify-between text-[10px] text-[#556982]">
                      <span>{new Date(art.published_at).toLocaleDateString("en-IN")}</span>
                      <a
                        href={art.canonical_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#71d5b3] hover:underline flex items-center gap-0.5 font-medium"
                      >
                        Read <ExternalLink size={10} />
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Historical Price Observations Table */}
        <div className="bg-[#0f1927] border border-[#202f42] rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#1f2e42] pb-3">
            <h2 className="text-sm font-bold text-[#edf3fa] tracking-wide uppercase">
              Historical Daily Observations ({prices.length} Sessions)
            </h2>
            <div className="flex items-center gap-2">
              <button
                disabled={tablePage === 1}
                onClick={() => setTablePage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 text-xs rounded-lg border border-[#22354a] bg-[#0c1624] text-[#8ca3ba] disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-xs text-[#62778f]">
                {tablePage} / {totalTablePages}
              </span>
              <button
                disabled={tablePage === totalTablePages}
                onClick={() => setTablePage((p) => Math.min(totalTablePages, p + 1))}
                className="px-2.5 py-1 text-xs rounded-lg border border-[#22354a] bg-[#0c1624] text-[#8ca3ba] disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#1b2b3d] text-[#71d5b3]">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3 text-right">Open</th>
                  <th className="py-2.5 px-3 text-right">High</th>
                  <th className="py-2.5 px-3 text-right">Low</th>
                  <th className="py-2.5 px-3 text-right">Close</th>
                  <th className="py-2.5 px-3 text-right">Volume</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#142232] font-mono text-[#cbd5e1]">
                {currentTableRows.map((bar) => {
                  const dayChange = bar.open ? Number(bar.close) - Number(bar.open) : 0;
                  return (
                    <tr key={bar.trade_date} className="hover:bg-[#121e2d] transition-colors">
                      <td className="py-2.5 px-3 font-sans font-medium text-[#edf3fa]">
                        {bar.trade_date}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        ₹{bar.open ? Number(bar.open).toFixed(2) : "-"}
                      </td>
                      <td className="py-2.5 px-3 text-right text-emerald-400/90">
                        ₹{bar.high ? Number(bar.high).toFixed(2) : "-"}
                      </td>
                      <td className="py-2.5 px-3 text-right text-rose-400/90">
                        ₹{bar.low ? Number(bar.low).toFixed(2) : "-"}
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-[#edf3fa]">
                        ₹{Number(bar.close).toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-[#8ca3ba]">
                        {bar.volume ? bar.volume.toLocaleString("en-IN") : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
