"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Briefcase,
  Plus,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  Wallet,
  PieChart,
  History,
  ShieldAlert,
  Calendar,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Loader2,
  DollarSign,
  ArrowLeft,
  X,
  Layers,
  Lock,
  LogIn,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { DashboardLayout } from "@/components/DashboardLayout";
import {
  api,
  Portfolio,
  PortfolioValuation,
  PortfolioPerformance,
  PortfolioTransaction,
  EquityPoint,
  Instrument,
} from "@/lib/api";

export default function PortfolioPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string>("");
  const [valuation, setValuation] = useState<PortfolioValuation | null>(null);
  const [performance, setPerformance] = useState<PortfolioPerformance | null>(null);
  const [history, setHistory] = useState<EquityPoint[]>([]);
  const [transactions, setTransactions] = useState<PortfolioTransaction[]>([]);
  const [availableInstruments, setAvailableInstruments] = useState<Instrument[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<"holdings" | "allocation" | "transactions">("holdings");

  const { user } = useAuth();

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState("");
  const [newPortfolioDesc, setNewPortfolioDesc] = useState("");
  const [isCreatingPortfolio, setIsCreatingPortfolio] = useState(false);

  const [showTxModal, setShowTxModal] = useState(false);
  const [txType, setTxType] = useState<string>("CASH_DEPOSIT");
  const [txInstrumentId, setTxInstrumentId] = useState<string>("");
  const [txTradeDate, setTxTradeDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [txQuantity, setTxQuantity] = useState<string>("10");
  const [txPrice, setTxPrice] = useState<string>("10000");
  const [txFees, setTxFees] = useState<string>("0");
  const [txNotes, setTxNotes] = useState<string>("");
  const [isSubmittingTx, setIsSubmittingTx] = useState(false);
  const [txErrorMessage, setTxErrorMessage] = useState<string | null>(null);
  const [txSuccessMessage, setTxSuccessMessage] = useState<string | null>(null);

  // Load initial portfolio list & available instruments
  useEffect(() => {
    if (user) {
      loadPortfolios();
      api.listInstruments({ size: 50 }).then((res) => {
        setAvailableInstruments(res.items);
        if (res.items.length > 0 && !txInstrumentId) {
          setTxInstrumentId(res.items[0].id);
        }
      }).catch(() => {});
    }
  }, [user]);

  const loadPortfolios = async () => {
    setIsLoading(true);
    try {
      const list = await api.listPortfolios();
      setPortfolios(list);
      if (list.length > 0) {
        const targetId = selectedPortfolioId && list.some((p) => p.id === selectedPortfolioId)
          ? selectedPortfolioId
          : list[0].id;
        setSelectedPortfolioId(targetId);
        await loadPortfolioData(targetId);
      } else {
        setSelectedPortfolioId("");
        setValuation(null);
        setPerformance(null);
        setHistory([]);
        setTransactions([]);
      }
    } catch (err) {
      console.error("Failed to load portfolios", err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadPortfolioData = async (portfolioId: string) => {
    setIsRefreshing(true);
    try {
      const [valRes, perfRes, histRes, txRes] = await Promise.all([
        api.getPortfolioValuation(portfolioId),
        api.getPortfolioPerformance(portfolioId),
        api.getPortfolioHistory(portfolioId),
        api.listPortfolioTransactions(portfolioId, 100),
      ]);
      setValuation(valRes);
      setPerformance(perfRes);
      setHistory(histRes);
      setTransactions(txRes);
    } catch (err) {
      console.error("Failed to fetch portfolio data", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleSelectPortfolio = (id: string) => {
    setSelectedPortfolioId(id);
    loadPortfolioData(id);
  };

  const handleCreatePortfolio = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPortfolioName.trim()) return;
    setIsCreatingPortfolio(true);
    try {
      const created = await api.createPortfolio({
        name: newPortfolioName.trim(),
        description: newPortfolioDesc.trim() || undefined,
        base_currency: "INR",
      });
      setShowCreateModal(false);
      setNewPortfolioName("");
      setNewPortfolioDesc("");
      await loadPortfolios();
      setSelectedPortfolioId(created.id);
      await loadPortfolioData(created.id);
    } catch (err: any) {
      alert(err.message || "Failed to create portfolio");
    } finally {
      setIsCreatingPortfolio(false);
    }
  };

  const handleRecordTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolioId) return;
    setIsSubmittingTx(true);
    setTxErrorMessage(null);
    setTxSuccessMessage(null);

    const idempotencyKey = `tx-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

    try {
      const payload: any = {
        transaction_type: txType,
        trade_date: txTradeDate,
        fees: parseFloat(txFees) || 0,
        notes: txNotes.trim() || undefined,
        idempotency_key: idempotencyKey,
      };

      if (txType === "BUY" || txType === "SELL") {
        payload.instrument_id = txInstrumentId;
        payload.quantity = parseFloat(txQuantity) || 0;
        payload.price_per_unit = parseFloat(txPrice) || 0;
      } else if (txType === "CASH_DEPOSIT" || txType === "CASH_WITHDRAWAL") {
        payload.price_per_unit = parseFloat(txPrice) || 0;
        payload.quantity = 0;
      } else if (txType === "DIVIDEND") {
        payload.instrument_id = txInstrumentId;
        payload.price_per_unit = parseFloat(txPrice) || 0;
        payload.quantity = 0;
      }

      await api.recordPortfolioTransaction(selectedPortfolioId, payload);
      setTxSuccessMessage("Transaction recorded successfully into ledger.");
      setTimeout(() => {
        setShowTxModal(false);
        setTxSuccessMessage(null);
      }, 1200);

      await loadPortfolioData(selectedPortfolioId);
    } catch (err: any) {
      setTxErrorMessage(err.message || "Failed to record transaction.");
    } finally {
      setIsSubmittingTx(false);
    }
  };

  // Helper formatting functions
  const formatINR = (val: number | null | undefined) => {
    if (val === null || val === undefined) return "₹0.00";
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(val);
  };

  const formatPct = (val: number | null | undefined) => {
    if (val === null || val === undefined) return "—";
    return `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;
  };

  // SVG Chart points calculation
  const chartCoordinates = useMemo(() => {
    if (!history || history.length < 2) return null;
    const values = history.map((h) => h.total_value);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal === 0 ? 1 : maxVal - minVal;

    const width = 800;
    const height = 240;
    const padding = 30;

    const points = history.map((pt, idx) => {
      const x = padding + (idx / (history.length - 1)) * (width - 2 * padding);
      const normalizedY = (pt.total_value - minVal) / range;
      const y = height - padding - normalizedY * (height - 2 * padding);
      return { x, y, ...pt };
    });

    const pathD = points.reduce((acc, pt, idx) => {
      return idx === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`;
    }, "");

    const areaD = `${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`;

    return { points, pathD, areaD, width, height, minVal, maxVal };
  }, [history]);

  return (
    <DashboardLayout title="Portfolio Intelligence">
      <div className="space-y-6">
        {/* Top Header Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-[#1e2d3e]">
          <div>
            <div className="flex items-center gap-2">
              <Link href="/dashboard" className="text-xs text-[#91a0b3] hover:text-[#edf3fa] flex items-center gap-1">
                <ArrowLeft size={13} /> Dashboard
              </Link>
              <span className="text-xs text-[#41536b]">/</span>
              <span className="text-xs text-[#71d5b3] font-medium">Portfolio Intelligence</span>
            </div>
            <h1 className="text-2xl font-bold text-[#edf3fa] mt-1 flex items-center gap-2.5">
              <Briefcase size={22} className="text-[#71d5b3]" />
              Portfolio Intelligence
            </h1>
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            {portfolios.length > 0 && (
              <select
                value={selectedPortfolioId}
                onChange={(e) => handleSelectPortfolio(e.target.value)}
                className="bg-[#0e1724] border border-[#1e2d3e] text-[#edf3fa] text-xs rounded-xl px-3 py-2 font-medium focus:outline-none focus:border-[#71d5b3]"
              >
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.base_currency})
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-[#15273b] hover:bg-[#1a334e] text-[#edf3fa] border border-[#1e2d3e] transition-colors"
            >
              <Plus size={14} className="text-[#71d5b3]" />
              New Portfolio
            </button>

            <Link
              href="/ai?explain=portfolio"
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-[#15273b] hover:bg-[#1a334e] text-[#71d5b3] border border-[#1e3e4a] transition-colors"
            >
              Explain with Copilot
            </Link>

            {selectedPortfolioId && (
              <>
                <button
                  onClick={() => loadPortfolioData(selectedPortfolioId)}
                  disabled={isRefreshing}
                  className="p-2 rounded-xl bg-[#0e1724] border border-[#1e2d3e] text-[#91a0b3] hover:text-[#edf3fa] transition-colors disabled:opacity-50"
                  title="Refresh Data"
                >
                  <RefreshCw size={15} className={isRefreshing ? "animate-spin text-[#71d5b3]" : ""} />
                </button>

                <button
                  onClick={() => {
                    setTxErrorMessage(null);
                    setTxSuccessMessage(null);
                    setShowTxModal(true);
                  }}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-[#71d5b3] hover:bg-[#5ec4a0] text-[#080e18] transition-colors"
                >
                  <Plus size={14} />
                  Record Transaction
                </button>
              </>
            )}
          </div>
        </div>

        {/* Guest Demo Mode Notice */}
        {!user && (
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-[#15273b]/50 border border-[#71d5b3]/30 text-xs text-[#91a0b3]">
            <div className="flex items-center gap-2.5">
              <span className="w-2 h-2 rounded-full bg-[#71d5b3] shrink-0" />
              <div>
                <span className="font-semibold text-[#edf3fa] mr-1.5">Guest Demo Mode:</span>
                <span>Portfolios are private to registered user accounts. Sign in or register to create custom INR portfolios, record buy/sell transactions, and track weighted P&L.</span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link
                href="/login?redirect=/portfolio"
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#71d5b3] text-[#080e18] hover:bg-[#5ec4a0] transition-colors inline-flex items-center gap-1"
              >
                <LogIn size={12} /> Sign In
              </Link>
            </div>
          </div>
        )}

        {/* Demo Data Disclaimer Banner */}
        <div className="flex items-center gap-3 p-3.5 rounded-xl bg-[#0e1724] border border-[#f59e0b]/30 text-xs text-[#91a0b3]">
          <ShieldAlert size={16} className="text-[#f59e0b] shrink-0" />
          <div className="flex-1">
            <span className="font-bold text-[#f59e0b] uppercase mr-2 tracking-wider">Demo / Educational Data:</span>
            Portfolio balances and financial indicators are simulated using deterministic synthetic fixtures for paper trading research. No real broker execution.
          </div>
        </div>

        {/* Loading State */}
        {isLoading ? (
          <div className="p-16 flex flex-col items-center justify-center space-y-3 bg-[#0e1724] border border-[#1e2d3e] rounded-2xl">
            <Loader2 size={32} className="animate-spin text-[#71d5b3]" />
            <p className="text-xs text-[#91a0b3]">Loading Portfolio Ledger & Analytics...</p>
          </div>
        ) : portfolios.length === 0 ? (
          /* Empty Portfolios State */
          <div className="p-16 text-center space-y-4 bg-[#0e1724] border border-[#1e2d3e] rounded-2xl">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-[#15273b] text-[#71d5b3] flex items-center justify-center">
              {user ? <Briefcase size={28} /> : <Lock size={28} />}
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#edf3fa]">
                {user ? "No Portfolios Yet" : "Private Portfolio Ledger"}
              </h2>
              <p className="text-xs text-[#91a0b3] max-w-md mx-auto mt-1">
                {user
                  ? "Create your first INR paper-trading portfolio to start recording deposits, trades, and analyzing weighted-average cost basis and risk."
                  : "Personal portfolios and transaction histories are isolated to authenticated user accounts for data privacy. Sign in or register to track your custom holdings and calculate returns."}
              </p>
            </div>
            {user ? (
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#71d5b3] hover:bg-[#5ec4a0] text-[#080e18] transition-colors"
              >
                <Plus size={15} /> Create My First Portfolio
              </button>
            ) : (
              <div className="flex items-center justify-center gap-3 pt-2">
                <Link
                  href="/login?redirect=/portfolio"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#71d5b3] hover:bg-[#5ec4a0] text-[#080e18] transition-colors"
                >
                  <LogIn size={15} /> Sign In
                </Link>
                <Link
                  href="/register?redirect=/portfolio"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#15273b] hover:bg-[#1a334e] text-[#edf3fa] border border-[#1e2d3e] transition-colors"
                >
                  Register Free
                </Link>
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Summary Metrics Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Total Portfolio Value */}
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-2">
                <div className="flex items-center justify-between text-xs text-[#91a0b3]">
                  <span>Total Portfolio Value</span>
                  <Briefcase size={16} className="text-[#71d5b3]" />
                </div>
                <div className="text-2xl font-bold text-[#edf3fa]">
                  {formatINR(valuation?.total_value)}
                </div>
                <div className="flex items-center gap-1.5 text-xs">
                  <span className="text-[#91a0b3]">Total P&L:</span>
                  <span
                    className={`font-semibold flex items-center ${
                      (valuation?.total_pnl || 0) >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                    }`}
                  >
                    {(valuation?.total_pnl || 0) >= 0 ? (
                      <ArrowUpRight size={13} />
                    ) : (
                      <ArrowDownRight size={13} />
                    )}
                    {formatINR(valuation?.total_pnl)}
                  </span>
                </div>
              </div>

              {/* Available Cash Balance */}
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-2">
                <div className="flex items-center justify-between text-xs text-[#91a0b3]">
                  <span>Available Cash</span>
                  <Wallet size={16} className="text-[#38bdf8]" />
                </div>
                <div className="text-2xl font-bold text-[#edf3fa]">
                  {formatINR(valuation?.cash_balance)}
                </div>
                <div className="text-xs text-[#91a0b3]">
                  {valuation?.total_value && valuation.total_value > 0
                    ? `${(((valuation.cash_balance || 0) / valuation.total_value) * 100).toFixed(1)}% of total capital`
                    : "Ready for allocation"}
                </div>
              </div>

              {/* Invested Cost Basis */}
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-2">
                <div className="flex items-center justify-between text-xs text-[#91a0b3]">
                  <span>Invested Holdings</span>
                  <TrendingUp size={16} className="text-[#a78bfa]" />
                </div>
                <div className="text-2xl font-bold text-[#edf3fa]">
                  {formatINR(valuation?.holdings_market_value)}
                </div>
                <div className="text-xs text-[#91a0b3]">
                  Cost Basis: {formatINR(valuation?.cost_basis)}
                </div>
              </div>

              {/* Unrealized vs Realized P&L */}
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-2">
                <div className="flex items-center justify-between text-xs text-[#91a0b3]">
                  <span>Unrealized / Realized P&L</span>
                  <Layers size={16} className="text-[#fb923c]" />
                </div>
                <div
                  className={`text-2xl font-bold ${
                    (valuation?.unrealized_pnl || 0) >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                  }`}
                >
                  {formatPct(valuation?.unrealized_pnl_percent)}
                </div>
                <div className="text-xs text-[#91a0b3] flex justify-between">
                  <span>Unrealized: {formatINR(valuation?.unrealized_pnl)}</span>
                  <span>Realized: {formatINR(valuation?.realized_pnl)}</span>
                </div>
              </div>
            </div>

            {/* Historical Valuation / Equity Curve SVG Chart */}
            <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-bold text-[#edf3fa] flex items-center gap-2">
                    <TrendingUp size={16} className="text-[#71d5b3]" />
                    Historical Portfolio Valuation Timeline
                  </h3>
                  <p className="text-[11px] text-[#91a0b3]">
                    Daily asset equity curve reconstructed strictly chronologically (no look-ahead pricing)
                  </p>
                </div>
                {history.length > 0 && (
                  <div className="text-xs text-[#91a0b3] font-mono">
                    {history[0].date} → {history[history.length - 1].date} ({history.length} days)
                  </div>
                )}
              </div>

              {chartCoordinates ? (
                <div className="relative w-full overflow-hidden">
                  <svg
                    viewBox={`0 0 ${chartCoordinates.width} ${chartCoordinates.height}`}
                    className="w-full h-56 select-none"
                  >
                    <defs>
                      <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#71d5b3" stopOpacity="0.25" />
                        <stop offset="100%" stopColor="#71d5b3" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Horizontal reference grid lines */}
                    <line
                      x1="30"
                      y1={chartCoordinates.height - 30}
                      x2={chartCoordinates.width - 30}
                      y2={chartCoordinates.height - 30}
                      stroke="#1e2d3e"
                      strokeWidth="1"
                    />
                    <line
                      x1="30"
                      y1="30"
                      x2={chartCoordinates.width - 30}
                      y2="30"
                      stroke="#1e2d3e"
                      strokeWidth="1"
                      strokeDasharray="4 4"
                    />

                    {/* Area under curve */}
                    <path d={chartCoordinates.areaD} fill="url(#equityGrad)" />

                    {/* Line curve */}
                    <path
                      d={chartCoordinates.pathD}
                      fill="none"
                      stroke="#71d5b3"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                    />

                    {/* Data dots */}
                    {chartCoordinates.points.map((pt, i) => (
                      <circle
                        key={i}
                        cx={pt.x}
                        cy={pt.y}
                        r="3"
                        className="fill-[#71d5b3] hover:r-5 transition-all cursor-pointer"
                      >
                        <title>{`${pt.date}: ${formatINR(pt.total_value)} (Cash: ${formatINR(
                          pt.cash
                        )}, Holdings: ${formatINR(pt.holdings_value)})`}</title>
                      </circle>
                    ))}
                  </svg>
                  <div className="flex justify-between text-[10px] text-[#91a0b3] font-mono px-2">
                    <span>Low: {formatINR(chartCoordinates.minVal)}</span>
                    <span>Peak: {formatINR(chartCoordinates.maxVal)}</span>
                    <span>Current: {formatINR(history[history.length - 1].total_value)}</span>
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-[#91a0b3] space-y-1">
                  <p>Insufficient timeline data to render equity curve.</p>
                  <p className="text-[11px] text-[#41536b]">Record multiple deposits and trades to track daily value evolution.</p>
                </div>
              )}
            </div>

            {/* Performance & Risk Analytics Card */}
            <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
              <div>
                <h3 className="text-sm font-bold text-[#edf3fa] flex items-center gap-2">
                  <PieChart size={16} className="text-[#38bdf8]" />
                  Performance & Risk Analytics
                </h3>
                <p className="text-[11px] text-[#91a0b3]">
                  Time-Weighted Return (TWR), Money-Weighted Return (XIRR), and annualized risk statistics
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="p-3.5 rounded-xl bg-[#15273b]/60 border border-[#1e2d3e]">
                  <div className="text-[11px] text-[#91a0b3]">TWR (Time-Weighted)</div>
                  <div
                    className={`text-lg font-bold mt-1 ${
                      (performance?.twr_percent || 0) >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                    }`}
                  >
                    {formatPct(performance?.twr_percent)}
                  </div>
                  <div className="text-[9px] text-[#91a0b3] mt-0.5">Adjusts for cash timings</div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#15273b]/60 border border-[#1e2d3e]">
                  <div className="text-[11px] text-[#91a0b3]">XIRR (Money-Weighted)</div>
                  <div
                    className={`text-lg font-bold mt-1 ${
                      (performance?.xirr_percent || 0) >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                    }`}
                  >
                    {formatPct(performance?.xirr_percent)}
                  </div>
                  <div className="text-[9px] text-[#91a0b3] mt-0.5">Annualized investor return</div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#15273b]/60 border border-[#1e2d3e]">
                  <div className="text-[11px] text-[#91a0b3]">Annual Volatility (σ)</div>
                  <div className="text-lg font-bold text-[#edf3fa] mt-1">
                    {performance?.annualized_volatility_percent !== null && performance?.annualized_volatility_percent !== undefined
                      ? `${performance.annualized_volatility_percent.toFixed(2)}%`
                      : "—"}
                  </div>
                  <div className="text-[9px] text-[#91a0b3] mt-0.5">Scaled by √252 days</div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#15273b]/60 border border-[#1e2d3e]">
                  <div className="text-[11px] text-[#91a0b3]">Sharpe Ratio</div>
                  <div className="text-lg font-bold text-[#edf3fa] mt-1">
                    {performance?.sharpe_ratio !== null && performance?.sharpe_ratio !== undefined
                      ? performance.sharpe_ratio.toFixed(2)
                      : "—"}
                  </div>
                  <div className="text-[9px] text-[#91a0b3] mt-0.5">Assumes Rf = 6.0%</div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#15273b]/60 border border-[#1e2d3e]">
                  <div className="text-[11px] text-[#91a0b3]">Max Drawdown</div>
                  <div className="text-lg font-bold text-[#f87171] mt-1">
                    {performance?.max_drawdown_percent !== undefined
                      ? `-${performance.max_drawdown_percent.toFixed(2)}%`
                      : "0.00%"}
                  </div>
                  <div className="text-[9px] text-[#91a0b3] mt-0.5">Peak-to-trough drop</div>
                </div>
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex items-center gap-2 border-b border-[#1e2d3e] pb-1">
              <button
                onClick={() => setActiveTab("holdings")}
                className={`px-4 py-2 text-xs font-semibold rounded-xl transition-colors ${
                  activeTab === "holdings"
                    ? "bg-[#15273b] text-[#71d5b3] border border-[#1e2d3e]"
                    : "text-[#91a0b3] hover:text-[#edf3fa]"
                }`}
              >
                Holdings & Positions ({valuation?.holdings?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab("allocation")}
                className={`px-4 py-2 text-xs font-semibold rounded-xl transition-colors ${
                  activeTab === "allocation"
                    ? "bg-[#15273b] text-[#71d5b3] border border-[#1e2d3e]"
                    : "text-[#91a0b3] hover:text-[#edf3fa]"
                }`}
              >
                Diversification & Allocation
              </button>
              <button
                onClick={() => setActiveTab("transactions")}
                className={`px-4 py-2 text-xs font-semibold rounded-xl transition-colors ${
                  activeTab === "transactions"
                    ? "bg-[#15273b] text-[#71d5b3] border border-[#1e2d3e]"
                    : "text-[#91a0b3] hover:text-[#edf3fa]"
                }`}
              >
                Transaction History ({transactions.length})
              </button>
            </div>

            {/* Tab Content: Holdings Table */}
            {activeTab === "holdings" && (
              <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-[#edf3fa]">Active Equity Holdings</h3>
                    <p className="text-[11px] text-[#91a0b3]">
                      Reconstructed with Weighted-Average Cost Basis (WACB) and marked-to-market valuations
                    </p>
                  </div>
                </div>

                {!valuation?.holdings || valuation.holdings.length === 0 ? (
                  <div className="py-12 text-center text-xs text-[#91a0b3] space-y-3">
                    <p>No active stock holdings in this portfolio.</p>
                    <button
                      onClick={() => {
                        setTxType("BUY");
                        setShowTxModal(true);
                      }}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-[#71d5b3] text-[#080e18] font-semibold"
                    >
                      <Plus size={13} /> Buy an Instrument
                    </button>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#1e2d3e] text-[#91a0b3]">
                          <th className="pb-3 font-semibold">Instrument</th>
                          <th className="pb-3 font-semibold">Sector</th>
                          <th className="pb-3 font-semibold text-right">Shares</th>
                          <th className="pb-3 font-semibold text-right">Avg Cost</th>
                          <th className="pb-3 font-semibold text-right">Market Price</th>
                          <th className="pb-3 font-semibold text-right">Market Value</th>
                          <th className="pb-3 font-semibold text-right">Unrealized P&L</th>
                          <th className="pb-3 font-semibold text-right">Alloc %</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#1e2d3e]">
                        {valuation.holdings.map((h) => {
                          const isProfitable = h.unrealized_pnl >= 0;
                          return (
                            <tr key={h.instrument_id} className="hover:bg-[#15273b]/40 transition-colors">
                              <td className="py-3">
                                <Link
                                  href={`/equity`}
                                  className="font-bold text-[#edf3fa] hover:text-[#71d5b3] transition-colors"
                                >
                                  {h.symbol}
                                </Link>
                                <div className="text-[10px] text-[#91a0b3] truncate max-w-[180px]">
                                  {h.company_name}
                                </div>
                              </td>
                              <td className="py-3 text-[#91a0b3]">{h.sector}</td>
                              <td className="py-3 text-right font-mono text-[#edf3fa]">{h.quantity}</td>
                              <td className="py-3 text-right font-mono text-[#91a0b3]">
                                {formatINR(h.average_buy_price)}
                              </td>
                              <td className="py-3 text-right font-mono">
                                <div className="text-[#edf3fa]">{formatINR(h.current_price)}</div>
                                {h.is_stale && (
                                  <span className="text-[9px] text-[#f59e0b] bg-[#f59e0b]/10 px-1 rounded">
                                    Stale
                                  </span>
                                )}
                              </td>
                              <td className="py-3 text-right font-mono font-bold text-[#edf3fa]">
                                {formatINR(h.market_value)}
                              </td>
                              <td
                                className={`py-3 text-right font-mono font-semibold ${
                                  isProfitable ? "text-[#71d5b3]" : "text-[#f87171]"
                                }`}
                              >
                                <div>{formatINR(h.unrealized_pnl)}</div>
                                <div className="text-[10px]">{formatPct(h.unrealized_pnl_percent)}</div>
                              </td>
                              <td className="py-3 text-right font-mono text-[#91a0b3]">
                                {h.allocation_percent ? `${h.allocation_percent.toFixed(1)}%` : "0.0%"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Tab Content: Allocation Breakdown */}
            {activeTab === "allocation" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Asset Allocations */}
                <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                  <h3 className="text-sm font-bold text-[#edf3fa] flex items-center gap-2">
                    <PieChart size={16} className="text-[#71d5b3]" />
                    Asset Distribution
                  </h3>
                  <div className="space-y-3">
                    {valuation?.asset_allocations?.map((item, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-[#edf3fa] font-medium">{item.name}</span>
                          <span className="text-[#91a0b3] font-mono">
                            {formatINR(item.value)} ({item.percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-[#15273b] overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              item.type === "cash" ? "bg-[#38bdf8]" : "bg-[#71d5b3]"
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, item.percentage))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Sector Allocations */}
                <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                  <h3 className="text-sm font-bold text-[#edf3fa] flex items-center gap-2">
                    <Layers size={16} className="text-[#a78bfa]" />
                    Sector Diversification
                  </h3>
                  <div className="space-y-3">
                    {valuation?.sector_allocations?.map((sec, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-[#edf3fa] font-medium">{sec.sector}</span>
                          <span className="text-[#91a0b3] font-mono">
                            {formatINR(sec.value)} ({sec.percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-[#15273b] overflow-hidden">
                          <div
                            className="h-full rounded-full bg-[#a78bfa]"
                            style={{ width: `${Math.min(100, Math.max(0, sec.percentage))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Tab Content: Transaction Ledger History */}
            {activeTab === "transactions" && (
              <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-[#edf3fa] flex items-center gap-2">
                      <History size={16} className="text-[#71d5b3]" />
                      Append-Only Transaction Ledger
                    </h3>
                    <p className="text-[11px] text-[#91a0b3]">
                      Immutable audit history of all deposits, withdrawals, equity trades and dividends
                    </p>
                  </div>
                </div>

                {transactions.length === 0 ? (
                  <div className="py-12 text-center text-xs text-[#91a0b3]">
                    No transactions recorded in this portfolio yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#1e2d3e] text-[#91a0b3]">
                          <th className="pb-3 font-semibold">Date</th>
                          <th className="pb-3 font-semibold">Type</th>
                          <th className="pb-3 font-semibold">Instrument</th>
                          <th className="pb-3 font-semibold text-right">Quantity</th>
                          <th className="pb-3 font-semibold text-right">Unit Price</th>
                          <th className="pb-3 font-semibold text-right">Fees</th>
                          <th className="pb-3 font-semibold text-right">Net Cash Flow</th>
                          <th className="pb-3 font-semibold">Notes</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#1e2d3e]">
                        {transactions.map((tx) => {
                          const isCashInflow = tx.cash_amount >= 0;
                          return (
                            <tr key={tx.id} className="hover:bg-[#15273b]/40 transition-colors">
                              <td className="py-3 font-mono text-[#91a0b3]">{tx.trade_date}</td>
                              <td className="py-3">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                    tx.transaction_type === "BUY"
                                      ? "bg-[#71d5b3]/15 text-[#71d5b3]"
                                      : tx.transaction_type === "SELL"
                                      ? "bg-[#fb923c]/15 text-[#fb923c]"
                                      : tx.transaction_type === "CASH_DEPOSIT"
                                      ? "bg-[#38bdf8]/15 text-[#38bdf8]"
                                      : tx.transaction_type === "CASH_WITHDRAWAL"
                                      ? "bg-[#f87171]/15 text-[#f87171]"
                                      : "bg-[#a78bfa]/15 text-[#a78bfa]"
                                  }`}
                                >
                                  {tx.transaction_type}
                                </span>
                              </td>
                              <td className="py-3 font-medium text-[#edf3fa]">
                                {tx.instrument_symbol || "—"}
                              </td>
                              <td className="py-3 text-right font-mono text-[#91a0b3]">
                                {tx.quantity > 0 ? tx.quantity : "—"}
                              </td>
                              <td className="py-3 text-right font-mono text-[#91a0b3]">
                                {formatINR(tx.price_per_unit)}
                              </td>
                              <td className="py-3 text-right font-mono text-[#91a0b3]">
                                {formatINR(tx.fees)}
                              </td>
                              <td
                                className={`py-3 text-right font-mono font-semibold ${
                                  isCashInflow ? "text-[#71d5b3]" : "text-[#f87171]"
                                }`}
                              >
                                {formatINR(tx.cash_amount)}
                              </td>
                              <td className="py-3 text-[#91a0b3] max-w-[150px] truncate">
                                {tx.notes || "—"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Modal: Create Portfolio */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0e1724] border border-[#1e2d3e] rounded-2xl p-6 w-full max-w-md space-y-4 shadow-xl">
              <div className="flex items-center justify-between pb-2 border-b border-[#1e2d3e]">
                <h3 className="text-base font-bold text-[#edf3fa]">Create New Portfolio</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-[#91a0b3] hover:text-[#edf3fa]"
                >
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleCreatePortfolio} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                    Portfolio Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Core Wealth Alpha"
                    value={newPortfolioName}
                    onChange={(e) => setNewPortfolioName(e.target.value)}
                    className="w-full bg-[#15273b] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                    Description (Optional)
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Brief investment thesis or benchmark goal"
                    value={newPortfolioDesc}
                    onChange={(e) => setNewPortfolioDesc(e.target.value)}
                    className="w-full bg-[#15273b] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                    Base Currency
                  </label>
                  <input
                    type="text"
                    disabled
                    value="INR (Indian Rupee)"
                    className="w-full bg-[#080e18] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#91a0b3]"
                  />
                  <p className="text-[10px] text-[#91a0b3] mt-1">
                    Current release supports INR portfolios exclusively.
                  </p>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#15273b] hover:bg-[#1a334e] text-[#edf3fa]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isCreatingPortfolio || !newPortfolioName.trim()}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#71d5b3] hover:bg-[#5ec4a0] text-[#080e18] transition-colors disabled:opacity-50"
                  >
                    {isCreatingPortfolio ? "Creating..." : "Create Portfolio"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Record Transaction */}
        {showTxModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0e1724] border border-[#1e2d3e] rounded-2xl p-6 w-full max-w-lg space-y-4 shadow-xl">
              <div className="flex items-center justify-between pb-2 border-b border-[#1e2d3e]">
                <h3 className="text-base font-bold text-[#edf3fa] flex items-center gap-2">
                  <Briefcase size={18} className="text-[#71d5b3]" /> Record Portfolio Transaction
                </h3>
                <button
                  onClick={() => setShowTxModal(false)}
                  className="text-[#91a0b3] hover:text-[#edf3fa]"
                >
                  <X size={18} />
                </button>
              </div>

              {txErrorMessage && (
                <div className="p-3 rounded-xl bg-red-950/40 border border-red-800/60 text-red-200 text-xs flex items-center gap-2">
                  <AlertCircle size={15} className="shrink-0" />
                  <span>{txErrorMessage}</span>
                </div>
              )}

              {txSuccessMessage && (
                <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-200 text-xs flex items-center gap-2">
                  <CheckCircle2 size={15} className="shrink-0" />
                  <span>{txSuccessMessage}</span>
                </div>
              )}

              <form onSubmit={handleRecordTransaction} className="space-y-4">
                {/* Transaction Type */}
                <div>
                  <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                    Transaction Type *
                  </label>
                  <select
                    value={txType}
                    onChange={(e) => setTxType(e.target.value)}
                    className="w-full bg-[#15273b] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  >
                    <option value="CASH_DEPOSIT">CASH_DEPOSIT (Add funds to available cash)</option>
                    <option value="CASH_WITHDRAWAL">CASH_WITHDRAWAL (Withdraw available cash)</option>
                    <option value="BUY">BUY (Acquire equity shares)</option>
                    <option value="SELL">SELL (Liquidate equity shares)</option>
                    <option value="DIVIDEND">DIVIDEND (Cash dividend received)</option>
                  </select>
                </div>

                {/* Instrument Selector for BUY, SELL, DIVIDEND */}
                {(txType === "BUY" || txType === "SELL" || txType === "DIVIDEND") && (
                  <div>
                    <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                      Target Equity Instrument *
                    </label>
                    <select
                      value={txInstrumentId}
                      onChange={(e) => setTxInstrumentId(e.target.value)}
                      className="w-full bg-[#15273b] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                      required
                    >
                      {availableInstruments.map((inst) => (
                        <option key={inst.id} value={inst.id}>
                          {inst.exchange}:{inst.symbol} - {inst.company_name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Trade Date */}
                <div>
                  <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                    Trade Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={txTradeDate}
                    onChange={(e) => setTxTradeDate(e.target.value)}
                    className="w-full bg-[#15273b] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  />
                </div>

                {/* Quantity and Price Grid */}
                <div className="grid grid-cols-2 gap-3">
                  {(txType === "BUY" || txType === "SELL") && (
                    <div>
                      <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                        Quantity (Shares) *
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        min="0.0001"
                        required
                        value={txQuantity}
                        onChange={(e) => setTxQuantity(e.target.value)}
                        className="w-full bg-[#15273b] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                      />
                    </div>
                  )}

                  <div className={txType === "BUY" || txType === "SELL" ? "" : "col-span-2"}>
                    <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                      {txType === "BUY" || txType === "SELL"
                        ? "Price Per Unit (₹) *"
                        : "Total Cash Amount (₹) *"}
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      value={txPrice}
                      onChange={(e) => setTxPrice(e.target.value)}
                      className="w-full bg-[#15273b] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                    />
                  </div>
                </div>

                {/* Fees */}
                <div>
                  <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                    Brokerage / Regulatory Fees (₹)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={txFees}
                    onChange={(e) => setTxFees(e.target.value)}
                    className="w-full bg-[#15273b] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  />
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-xs font-semibold text-[#91a0b3] mb-1">
                    Notes (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Initial capital deposit, rebalancing trade"
                    value={txNotes}
                    onChange={(e) => setTxNotes(e.target.value)}
                    className="w-full bg-[#15273b] border border-[#1e2d3e] rounded-xl px-3 py-2 text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowTxModal(false)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#15273b] hover:bg-[#1a334e] text-[#edf3fa]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingTx}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#71d5b3] hover:bg-[#5ec4a0] text-[#080e18] transition-colors disabled:opacity-50"
                  >
                    {isSubmittingTx ? "Submitting..." : "Submit Transaction"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
