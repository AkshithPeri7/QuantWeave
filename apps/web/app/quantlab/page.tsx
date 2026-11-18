"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  FlaskConical,
  TrendingUp,
  TrendingDown,
  Layers,
  Settings,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Sliders,
  Calendar,
  DollarSign,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Scale,
  Plus,
  Trash2,
  ShieldAlert,
  BarChart3,
  Percent,
  Check,
  ChevronRight,
  Info,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/lib/auth-context";
import {
  api,
  BacktestComparisonItem,
  BacktestEquityPoint,
  BacktestMetrics,
  BacktestRun,
  BacktestTrade,
  GridSearchResultItem,
  Instrument,
  ResearchStrategy,
} from "@/lib/api";

type TabMode = "simulator" | "optimizer" | "strategies" | "history";

const STRATEGY_PRESETS = [
  {
    type: "SMA_CROSSOVER",
    name: "SMA Crossover",
    description: "Classic trend-following strategy using fast and slow simple moving averages.",
    defaultParams: { fast_period: 20, slow_period: 50 },
  },
  {
    type: "EMA_CROSSOVER",
    name: "EMA Crossover",
    description: "Exponential moving average crossover reacting faster to recent price moves.",
    defaultParams: { fast_period: 12, slow_period: 26 },
  },
  {
    type: "RSI_THRESHOLD",
    name: "RSI Mean-Reversion",
    description: "Counter-trend strategy buying when RSI indicates oversold and selling at overbought.",
    defaultParams: { rsi_period: 14, oversold_threshold: 30, overbought_threshold: 70 },
  },
  {
    type: "BUY_AND_HOLD",
    name: "Buy & Hold (Benchmark)",
    description: "Passive baseline investment purchasing on day one and holding across the period.",
    defaultParams: {},
  },
];

export default function QuantLabPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabMode>("simulator");
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loadingInstruments, setLoadingInstruments] = useState(false);

  // Backtest Simulator State
  const [selectedInstrumentId, setSelectedInstrumentId] = useState<string>("");
  const [strategyType, setStrategyType] = useState<string>("SMA_CROSSOVER");
  const [fastPeriod, setFastPeriod] = useState<number>(20);
  const [slowPeriod, setSlowPeriod] = useState<number>(50);
  const [rsiPeriod, setRsiPeriod] = useState<number>(14);
  const [rsiOversold, setRsiOversold] = useState<number>(30);
  const [rsiOverbought, setRsiOverbought] = useState<number>(70);
  const [startDate, setStartDate] = useState<string>("2025-12-02");
  const [endDate, setEndDate] = useState<string>("2026-11-16");
  const [startingCapital, setStartingCapital] = useState<number>(100000);
  const [feeRatePct, setFeeRatePct] = useState<number>(0.1);
  const [slippageBps, setSlippageBps] = useState<number>(5);

  // Available Historical Range
  const [availableDateRange, setAvailableDateRange] = useState<{ start: string; end: string; count: number } | null>(null);
  const [loadingPriceRange, setLoadingPriceRange] = useState(false);

  const [runningBacktest, setRunningBacktest] = useState(false);
  const [currentRun, setCurrentRun] = useState<BacktestRun | null>(null);
  const [runTrades, setRunTrades] = useState<BacktestTrade[]>([]);
  const [runEquity, setRunEquity] = useState<BacktestEquityPoint[]>([]);
  const [backtestError, setBacktestError] = useState<string | null>(null);

  // Optimizer (Grid Search) State
  const [optStrategyType, setOptStrategyType] = useState<string>("SMA_CROSSOVER");
  const [fastCandidates, setFastCandidates] = useState<string>("10, 20, 30");
  const [slowCandidates, setSlowCandidates] = useState<string>("50, 100");
  const [rsiPeriodCandidates, setRsiPeriodCandidates] = useState<string>("10, 14");
  const [rsiOversoldCandidates, setRsiOversoldCandidates] = useState<string>("25, 30");
  const [rsiOverboughtCandidates, setRsiOverboughtCandidates] = useState<string>("70, 75");
  const [trainRatio, setTrainRatio] = useState<number>(0.7);
  const [runningOptimizer, setRunningOptimizer] = useState(false);
  const [optimizerError, setOptimizerError] = useState<string | null>(null);
  const [gridResults, setGridResults] = useState<GridSearchResultItem[]>([]);
  const [gridSummary, setGridSummary] = useState<string | null>(null);
  const [bestParams, setBestParams] = useState<Record<string, any> | null>(null);

  // Strategies Tab State
  const [savedStrategies, setSavedStrategies] = useState<ResearchStrategy[]>([]);
  const [loadingStrategies, setLoadingStrategies] = useState(false);
  const [newStrategyName, setNewStrategyName] = useState("");
  const [newStrategyDesc, setNewStrategyDesc] = useState("");
  const [creatingStrategy, setCreatingStrategy] = useState(false);

  // History & Comparison State
  const [historicalRuns, setHistoricalRuns] = useState<BacktestRun[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [comparingRuns, setComparingRuns] = useState(false);
  const [comparisonItems, setComparisonItems] = useState<BacktestComparisonItem[]>([]);

  // Load instruments & strategies on mount
  useEffect(() => {
    async function initData() {
      setLoadingInstruments(true);
      try {
        const res = await api.listInstruments({ size: 100 });
        setInstruments(res.items);
        if (res.items.length > 0) {
          setSelectedInstrumentId(res.items[0].id);
        }
      } catch (err) {
        console.error("Failed to load instruments", err);
      } finally {
        setLoadingInstruments(false);
      }
    }
    initData();
  }, []);

  // Fetch instrument's available historical date range
  useEffect(() => {
    if (!selectedInstrumentId) return;
    let isCancelled = false;
    setLoadingPriceRange(true);
    api.getInstrumentPrices(selectedInstrumentId, { limit: 1000 })
      .then((res) => {
        if (!isCancelled && res.prices && res.prices.length > 0) {
          const firstDate = res.start_date || res.prices[0].trade_date;
          const lastDate = res.end_date || res.prices[res.prices.length - 1].trade_date;
          setAvailableDateRange({
            start: firstDate,
            end: lastDate,
            count: res.count || res.prices.length,
          });
          // Auto-sync start and end dates with instrument availability
          setStartDate(firstDate);
          setEndDate(lastDate);
        }
      })
      .catch((err) => {
        console.warn("Could not load price range for instrument", err);
      })
      .finally(() => {
        if (!isCancelled) setLoadingPriceRange(false);
      });
    return () => {
      isCancelled = true;
    };
  }, [selectedInstrumentId]);

  const handleUseFullRange = () => {
    if (availableDateRange) {
      setStartDate(availableDateRange.start);
      setEndDate(availableDateRange.end);
      setBacktestError(null);
      setOptimizerError(null);
    }
  };

  // Fetch strategies when entering strategies tab
  useEffect(() => {
    if (activeTab === "strategies") {
      fetchStrategies();
    } else if (activeTab === "history") {
      fetchRuns();
    }
  }, [activeTab]);

  const fetchStrategies = async () => {
    if (!user) return;
    setLoadingStrategies(true);
    try {
      const data = await api.listStrategies();
      setSavedStrategies(data);
    } catch (err) {
      console.error("Failed to list strategies", err);
    } finally {
      setLoadingStrategies(false);
    }
  };

  const fetchRuns = async () => {
    if (!user) return;
    setLoadingRuns(true);
    try {
      const data = await api.listBacktestRuns(50);
      setHistoricalRuns(data);
    } catch (err) {
      console.error("Failed to list backtest runs", err);
    } finally {
      setLoadingRuns(false);
    }
  };

  // Build current parameters for simulation
  const currentParams = useMemo(() => {
    if (strategyType === "SMA_CROSSOVER") {
      return { fast_period: fastPeriod, slow_period: slowPeriod };
    }
    if (strategyType === "EMA_CROSSOVER") {
      return { fast_period: fastPeriod, slow_period: slowPeriod };
    }
    if (strategyType === "RSI_THRESHOLD") {
      return {
        rsi_period: rsiPeriod,
        oversold_threshold: rsiOversold,
        overbought_threshold: rsiOverbought,
      };
    }
    return {};
  }, [strategyType, fastPeriod, slowPeriod, rsiPeriod, rsiOversold, rsiOverbought]);

  // Execute Backtest
  const handleRunBacktest = async () => {
    if (!selectedInstrumentId) {
      setBacktestError("Please select a target equity instrument.");
      return;
    }
    if (!startDate || !endDate) {
      setBacktestError("Please choose both a Start Date and an End Date.");
      return;
    }
    if (startDate >= endDate) {
      setBacktestError(`Start date (${startDate}) must be strictly before End date (${endDate}).`);
      return;
    }
    if (availableDateRange) {
      if (startDate > availableDateRange.end || endDate < availableDateRange.start) {
        setBacktestError(
          `Selected dates (${startDate} to ${endDate}) fall outside the available history for this instrument (${availableDateRange.start} to ${availableDateRange.end}). Click 'Use Available Range' to populate valid historical dates.`
        );
        return;
      }
    }
    setBacktestError(null);
    setRunningBacktest(true);
    try {
      const run = await api.runInstantBacktest({
        strategy_type: strategyType,
        parameters: currentParams,
        instrument_id: selectedInstrumentId,
        start_date: startDate,
        end_date: endDate,
        starting_capital: startingCapital,
        fee_rate: feeRatePct / 100,
        slippage_bps: slippageBps,
      });

      setCurrentRun(run);
      // Fetch trades and equity
      const [trades, equity] = await Promise.all([
        api.getBacktestTrades(run.id),
        api.getBacktestEquity(run.id),
      ]);
      setRunTrades(trades);
      setRunEquity(equity);
    } catch (err: any) {
      setBacktestError(err.message || "Failed to execute backtest simulation.");
    } finally {
      setRunningBacktest(false);
    }
  };

  // Run Grid Search Optimizer
  const handleRunOptimizer = async () => {
    if (!selectedInstrumentId) {
      setOptimizerError("Please select an instrument.");
      return;
    }
    if (!startDate || !endDate) {
      setOptimizerError("Please choose both a Start Date and an End Date.");
      return;
    }
    if (startDate >= endDate) {
      setOptimizerError(`Start date (${startDate}) must be strictly before End date (${endDate}).`);
      return;
    }
    if (availableDateRange) {
      if (startDate > availableDateRange.end || endDate < availableDateRange.start) {
        setOptimizerError(
          `Selected dates (${startDate} to ${endDate}) fall outside available history (${availableDateRange.start} to ${availableDateRange.end}). Click 'Use Available Range' to populate valid dates.`
        );
        return;
      }
    }
    setOptimizerError(null);

    let paramGrid: Record<string, any[]> = {};
    if (optStrategyType === "SMA_CROSSOVER" || optStrategyType === "EMA_CROSSOVER") {
      const fasts = fastCandidates.split(",").map((x) => parseInt(x.trim())).filter((x) => !isNaN(x) && x > 0);
      const slows = slowCandidates.split(",").map((x) => parseInt(x.trim())).filter((x) => !isNaN(x) && x > 0);
      if (fasts.length === 0 || slows.length === 0) {
        setOptimizerError("Provide at least one candidate value for fast and slow periods.");
        return;
      }
      if (fasts.length * slows.length > 25) {
        setOptimizerError(`Parameter combinations (${fasts.length * slows.length}) exceed maximum permitted bound of 25.`);
        return;
      }
      paramGrid = { fast_period: fasts, slow_period: slows };
    } else if (optStrategyType === "RSI_THRESHOLD") {
      const periods = rsiPeriodCandidates.split(",").map((x) => parseInt(x.trim())).filter((x) => !isNaN(x) && x > 0);
      const oversolds = rsiOversoldCandidates.split(",").map((x) => parseInt(x.trim())).filter((x) => !isNaN(x) && x > 0);
      const overboughts = rsiOverboughtCandidates.split(",").map((x) => parseInt(x.trim())).filter((x) => !isNaN(x) && x > 0);
      const totalCombos = periods.length * oversolds.length * overboughts.length;
      if (totalCombos === 0) {
        setOptimizerError("Provide valid candidates for RSI parameters.");
        return;
      }
      if (totalCombos > 25) {
        setOptimizerError(`Parameter combinations (${totalCombos}) exceed maximum permitted bound of 25.`);
        return;
      }
      paramGrid = {
        rsi_period: periods,
        oversold_threshold: oversolds,
        overbought_threshold: overboughts,
      };
    }

    setRunningOptimizer(true);
    try {
      const res = await api.runGridSearch({
        strategy_type: optStrategyType,
        param_grid: paramGrid,
        instrument_id: selectedInstrumentId,
        start_date: startDate,
        end_date: endDate,
        starting_capital: startingCapital,
        fee_rate: feeRatePct / 100,
        slippage_bps: slippageBps,
        train_ratio: trainRatio,
      });

      setGridResults(res.results);
      setGridSummary(res.summary);
      setBestParams(res.best_params);
    } catch (err: any) {
      setOptimizerError(err.message || "Failed to execute parameter grid search.");
    } finally {
      setRunningOptimizer(false);
    }
  };

  // Create Strategy
  const handleCreateStrategy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStrategyName.trim()) return;
    setCreatingStrategy(true);
    try {
      await api.createStrategy({
        name: newStrategyName.trim(),
        description: newStrategyDesc.trim() || undefined,
        strategy_type: strategyType,
        parameters: currentParams,
      });
      setNewStrategyName("");
      setNewStrategyDesc("");
      await fetchStrategies();
    } catch (err: any) {
      alert(err.message || "Failed to create strategy");
    } finally {
      setCreatingStrategy(false);
    }
  };

  // Delete Strategy
  const handleDeleteStrategy = async (id: string) => {
    if (!confirm("Are you sure you want to delete this research strategy?")) return;
    try {
      await api.deleteStrategy(id);
      await fetchStrategies();
    } catch (err: any) {
      alert(err.message || "Failed to delete strategy");
    }
  };

  // Compare Runs
  const handleCompareRuns = async () => {
    if (selectedRunIds.length < 2) {
      alert("Please select at least 2 runs to compare.");
      return;
    }
    setComparingRuns(true);
    try {
      const res = await api.compareBacktestRuns(selectedRunIds);
      setComparisonItems(res.runs);
    } catch (err: any) {
      alert(err.message || "Comparison failed");
    } finally {
      setComparingRuns(false);
    }
  };

  // Toggle run selection
  const toggleRunSelection = (id: string) => {
    setSelectedRunIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((x) => x !== id);
      }
      if (prev.length >= 5) {
        alert("You can compare a maximum of 5 runs at once.");
        return prev;
      }
      return [...prev, id];
    });
  };

  // SVG Chart Helper for Equity Curve
  const equitySvgData = useMemo(() => {
    if (!runEquity || runEquity.length < 2) return null;
    const width = 800;
    const height = 260;
    const padding = { top: 20, right: 30, bottom: 30, left: 60 };

    const equities = runEquity.map((d) => d.equity);
    const benchmarks = runEquity.map((d) => d.benchmark_equity ?? startingCapital);
    const allVals = [...equities, ...benchmarks];

    const minVal = Math.min(...allVals) * 0.98;
    const maxVal = Math.max(...allVals) * 1.02;
    const range = maxVal - minVal || 1;

    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const getX = (idx: number) => padding.left + (idx / (runEquity.length - 1)) * chartW;
    const getY = (val: number) => padding.top + chartH - ((val - minVal) / range) * chartH;

    // Strategy Path
    const stratPath = runEquity.reduce((acc, pt, i) => {
      const x = getX(i);
      const y = getY(pt.equity);
      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, "");

    // Benchmark Path
    const benchPath = runEquity.reduce((acc, pt, i) => {
      const x = getX(i);
      const y = getY(pt.benchmark_equity ?? startingCapital);
      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, "");

    return {
      width,
      height,
      stratPath,
      benchPath,
      minVal,
      maxVal,
      padding,
      firstDate: runEquity[0].point_date,
      lastDate: runEquity[runEquity.length - 1].point_date,
    };
  }, [runEquity, startingCapital]);

  // SVG Drawdown Curve Helper
  const drawdownSvgData = useMemo(() => {
    if (!runEquity || runEquity.length < 2) return null;
    const width = 800;
    const height = 120;
    const padding = { top: 10, right: 30, bottom: 25, left: 60 };

    const drawdowns = runEquity.map((d) => d.drawdown_pct);
    const maxDD = Math.max(...drawdowns, 0.05); // min 5% scale

    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const getX = (idx: number) => padding.left + (idx / (runEquity.length - 1)) * chartW;
    const getY = (val: number) => padding.top + (val / maxDD) * chartH;

    // Area path down from y=0
    let areaPath = `M ${padding.left} ${padding.top}`;
    runEquity.forEach((pt, i) => {
      const x = getX(i);
      const y = getY(pt.drawdown_pct);
      areaPath += ` L ${x} ${y}`;
    });
    areaPath += ` L ${padding.left + chartW} ${padding.top} Z`;

    return {
      width,
      height,
      areaPath,
      maxDD,
      padding,
    };
  }, [runEquity]);

  return (
    <DashboardLayout title="QuantLab">
      <div className="space-y-6">
        {/* Header Title & Educational Disclaimer */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e]">
          <div className="space-y-1.5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#15273b] text-[#71d5b3] flex items-center justify-center">
                <FlaskConical size={22} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-[#edf3fa]">QuantLab Research & Backtesting</h1>
                  <span className="text-[10px] font-bold tracking-wide uppercase px-2 py-0.5 rounded bg-[#102a24] text-[#71d5b3] border border-[#1b4338]">
                    QuantLab Backtest Engine
                  </span>
                </div>
                <p className="text-xs text-[#91a0b3]">
                  Event-driven historical simulation engine with zero look-ahead bias, next-bar Open execution, and modeled friction.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 p-3 rounded-xl bg-[#131f2f] border border-[#1e2d3e] text-xs text-[#cbd5e1] max-w-md">
            <ShieldAlert size={18} className="text-[#f59e0b] shrink-0" />
            <p className="text-[11px] leading-tight">
              <strong>Educational Simulation Only:</strong> Backtesting results represent simulated paper performance. Past returns do not guarantee future live execution profits.
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 border-b border-[#1e2d3e] pb-1 overflow-x-auto">
          <button
            onClick={() => setActiveTab("simulator")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "simulator"
                ? "bg-[#15273b] text-[#71d5b3] border border-[#233f5d]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#0e1724]"
            }`}
          >
            <Play size={14} />
            Backtest Simulator
          </button>

          <button
            onClick={() => setActiveTab("optimizer")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "optimizer"
                ? "bg-[#15273b] text-[#71d5b3] border border-[#233f5d]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#0e1724]"
            }`}
          >
            <Sliders size={14} />
            Parameter Optimizer (Grid Search)
          </button>

          <button
            onClick={() => setActiveTab("strategies")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "strategies"
                ? "bg-[#15273b] text-[#71d5b3] border border-[#233f5d]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#0e1724]"
            }`}
          >
            <Layers size={14} />
            Strategy Studio
          </button>

          <button
            onClick={() => setActiveTab("history")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "history"
                ? "bg-[#15273b] text-[#71d5b3] border border-[#233f5d]"
                : "text-[#91a0b3] hover:text-[#edf3fa] hover:bg-[#0e1724]"
            }`}
          >
            <Scale size={14} />
            Simulation History & Compare
          </button>

          <Link
            href="/ai?explain=quantlab"
            className="ml-auto px-3 py-1.5 text-xs font-semibold rounded-lg text-[#71d5b3] bg-[#15273b] hover:bg-[#1c3550] border border-[#1e3e4a] flex items-center gap-1.5 transition-all self-center"
          >
            Explain with Copilot
          </Link>
        </div>

        {/* ========================================================= */}
        {/* TAB 1: BACKTEST SIMULATOR */}
        {/* ========================================================= */}
        {activeTab === "simulator" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Configuration Form */}
            <div className="lg:col-span-4 space-y-5">
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                <div className="flex items-center justify-between border-b border-[#1e2d3e] pb-3">
                  <h3 className="text-sm font-bold text-[#edf3fa] flex items-center gap-2">
                    <Settings size={16} className="text-[#71d5b3]" />
                    Strategy Configuration
                  </h3>
                </div>

                {/* Target Equity Instrument */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#91a0b3]">Target Equity (NSE / BSE)</label>
                  <select
                    value={selectedInstrumentId}
                    onChange={(e) => setSelectedInstrumentId(e.target.value)}
                    disabled={loadingInstruments}
                    className="w-full px-3 py-2 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  >
                    {instruments.map((inst) => (
                      <option key={inst.id} value={inst.id}>
                        {inst.symbol} — {inst.company_name} ({inst.exchange})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Strategy Type Preset */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#91a0b3]">Strategy Type</label>
                  <select
                    value={strategyType}
                    onChange={(e) => setStrategyType(e.target.value)}
                    className="w-full px-3 py-2 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa] focus:outline-none focus:border-[#71d5b3]"
                  >
                    {STRATEGY_PRESETS.map((p) => (
                      <option key={p.type} value={p.type}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Strategy Dynamic Parameters */}
                {(strategyType === "SMA_CROSSOVER" || strategyType === "EMA_CROSSOVER") && (
                  <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-[#080d16] border border-[#1e2d3e]">
                    <div className="space-y-1">
                      <label className="text-[11px] text-[#91a0b3]">Fast Period</label>
                      <input
                        type="number"
                        min="2"
                        max="200"
                        value={fastPeriod}
                        onChange={(e) => setFastPeriod(parseInt(e.target.value) || 2)}
                        className="w-full px-2.5 py-1.5 bg-[#0e1724] border border-[#1e2d3e] rounded-lg text-xs text-[#edf3fa]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[11px] text-[#91a0b3]">Slow Period</label>
                      <input
                        type="number"
                        min="5"
                        max="500"
                        value={slowPeriod}
                        onChange={(e) => setSlowPeriod(parseInt(e.target.value) || 5)}
                        className="w-full px-2.5 py-1.5 bg-[#0e1724] border border-[#1e2d3e] rounded-lg text-xs text-[#edf3fa]"
                      />
                    </div>
                  </div>
                )}

                {strategyType === "RSI_THRESHOLD" && (
                  <div className="grid grid-cols-3 gap-2 p-3 rounded-xl bg-[#080d16] border border-[#1e2d3e]">
                    <div className="space-y-1">
                      <label className="text-[10px] text-[#91a0b3]">RSI Period</label>
                      <input
                        type="number"
                        min="2"
                        max="50"
                        value={rsiPeriod}
                        onChange={(e) => setRsiPeriod(parseInt(e.target.value) || 14)}
                        className="w-full px-2 py-1.5 bg-[#0e1724] border border-[#1e2d3e] rounded-lg text-xs text-[#edf3fa]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] text-[#91a0b3]">Oversold</label>
                      <input
                        type="number"
                        min="5"
                        max="50"
                        value={rsiOversold}
                        onChange={(e) => setRsiOversold(parseInt(e.target.value) || 30)}
                        className="w-full px-2 py-1.5 bg-[#0e1724] border border-[#1e2d3e] rounded-lg text-xs text-[#edf3fa]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] text-[#91a0b3]">Overbought</label>
                      <input
                        type="number"
                        min="50"
                        max="95"
                        value={rsiOverbought}
                        onChange={(e) => setRsiOverbought(parseInt(e.target.value) || 70)}
                        className="w-full px-2 py-1.5 bg-[#0e1724] border border-[#1e2d3e] rounded-lg text-xs text-[#edf3fa]"
                      />
                    </div>
                  </div>
                )}

                {strategyType === "BUY_AND_HOLD" && (
                  <p className="text-[11px] text-[#91a0b3] italic p-3 rounded-xl bg-[#080d16] border border-[#1e2d3e]">
                    Zero tunable parameters. Buys full long position on bar 1 and holds until test completion.
                  </p>
                )}

                {/* Backtest Parameters */}
                <div className="space-y-3 pt-2 border-t border-[#1e2d3e]">
                  <h4 className="text-xs font-bold text-[#edf3fa]">Simulation Environment</h4>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[11px] text-[#91a0b3]">Start Date</label>
                      <input
                        type="date"
                        value={startDate}
                        min={availableDateRange?.start}
                        max={availableDateRange?.end}
                        onChange={(e) => {
                          setStartDate(e.target.value);
                          setBacktestError(null);
                        }}
                        className="w-full px-2.5 py-1.5 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[11px] text-[#91a0b3]">End Date</label>
                      <input
                        type="date"
                        value={endDate}
                        min={availableDateRange?.start}
                        max={availableDateRange?.end}
                        onChange={(e) => {
                          setEndDate(e.target.value);
                          setBacktestError(null);
                        }}
                        className="w-full px-2.5 py-1.5 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                      />
                    </div>
                  </div>

                  {availableDateRange && (
                    <div className="flex items-center justify-between p-2 rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[11px]">
                      <div className="flex items-center gap-1.5 text-[#8293a7]">
                        <Calendar size={13} className="text-[#71d5b3]" />
                        <span>
                          Available: <strong className="text-[#edf3fa] font-mono">{availableDateRange.start}</strong> to{" "}
                          <strong className="text-[#edf3fa] font-mono">{availableDateRange.end}</strong> ({availableDateRange.count} bars)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={handleUseFullRange}
                        className="px-2 py-0.5 rounded bg-[#152a3b] hover:bg-[#1c3850] text-[#71d5b3] font-semibold text-[10px] transition-colors"
                      >
                        Use Available Range
                      </button>
                    </div>
                  )}

                  <div className="space-y-1">
                    <label className="text-[11px] text-[#91a0b3]">Starting Capital (INR)</label>
                    <input
                      type="number"
                      min="1000"
                      step="10000"
                      value={startingCapital}
                      onChange={(e) => setStartingCapital(parseFloat(e.target.value) || 100000)}
                      className="w-full px-2.5 py-1.5 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[11px] text-[#91a0b3]">Fee Rate (%)</label>
                      <input
                        type="number"
                        min="0"
                        max="2"
                        step="0.05"
                        value={feeRatePct}
                        onChange={(e) => setFeeRatePct(parseFloat(e.target.value) || 0)}
                        className="w-full px-2.5 py-1.5 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[11px] text-[#91a0b3]">Slippage (bps)</label>
                      <input
                        type="number"
                        min="0"
                        max="50"
                        step="1"
                        value={slippageBps}
                        onChange={(e) => setSlippageBps(parseFloat(e.target.value) || 0)}
                        className="w-full px-2.5 py-1.5 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                      />
                    </div>
                  </div>
                </div>

                {backtestError && (
                  <div className="p-3.5 rounded-xl bg-[#2a1215] border border-[#4a1c22] text-[#f87171] text-xs space-y-2">
                    <div className="flex items-start gap-2">
                      <AlertCircle size={16} className="shrink-0 mt-0.5" />
                      <span className="leading-relaxed">{backtestError}</span>
                    </div>
                    {availableDateRange && (
                      <div className="pt-1">
                        <button
                          type="button"
                          onClick={handleUseFullRange}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#3a1a20] hover:bg-[#4d222b] text-rose-200 text-xs font-semibold border border-rose-500/30 transition-colors"
                        >
                          <RotateCcw size={12} />
                          Use Available Range ({availableDateRange.start} to {availableDateRange.end})
                        </button>
                      </div>
                    )}
                  </div>
                )}

                <button
                  onClick={handleRunBacktest}
                  disabled={runningBacktest}
                  className="w-full py-2.5 rounded-xl bg-[#71d5b3] text-[#080d16] font-bold text-xs hover:bg-[#5bc4a0] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {runningBacktest ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Simulating Strategy Execution...
                    </>
                  ) : (
                    <>
                      <Play size={16} />
                      Run Backtest Simulation
                    </>
                  )}
                </button>
              </div>

              {/* Quick Strategy Saving */}
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                <h4 className="text-xs font-bold text-[#edf3fa] flex items-center gap-1.5">
                  <Plus size={14} className="text-[#71d5b3]" />
                  Save as Research Strategy
                </h4>
                <form onSubmit={handleCreateStrategy} className="space-y-2">
                  <input
                    type="text"
                    placeholder="Strategy Name (e.g. Reliance SMA 20/50)"
                    value={newStrategyName}
                    onChange={(e) => setNewStrategyName(e.target.value)}
                    className="w-full px-2.5 py-1.5 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                  />
                  <input
                    type="text"
                    placeholder="Brief hypothesis / notes (optional)"
                    value={newStrategyDesc}
                    onChange={(e) => setNewStrategyDesc(e.target.value)}
                    className="w-full px-2.5 py-1.5 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                  />
                  <button
                    type="submit"
                    disabled={creatingStrategy || !newStrategyName.trim()}
                    className="w-full py-1.5 rounded-xl bg-[#15273b] text-[#71d5b3] font-semibold text-xs border border-[#233f5d] hover:bg-[#1b324c] disabled:opacity-50"
                  >
                    {creatingStrategy ? "Saving..." : "Save Strategy"}
                  </button>
                </form>
              </div>
            </div>

            {/* Right: Simulation Results & Analytics */}
            <div className="lg:col-span-8 space-y-6">
              {!currentRun ? (
                <div className="space-y-5">
                  {/* Research Methodology & Workspace Overview */}
                  <div className="p-6 rounded-2xl bg-[#111B2B] border border-[#1E2D42] space-y-4">
                    <div className="flex items-center justify-between border-b border-[#1E2D42] pb-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-xl bg-[#172338] text-[#67D7B4] flex items-center justify-center border border-[#1E2D42]">
                          <FlaskConical size={18} />
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-[#F1F5FA]">
                            Strategy Research Workspace
                          </h3>
                          <p className="text-[11px] text-[#94A8C2] font-mono">
                            Institutional Quantitative Engine • Zero Look-Ahead Bias
                          </p>
                        </div>
                      </div>
                      <span className="px-2.5 py-0.5 rounded-full bg-[#15342a] text-[#67D7B4] border border-[#235845] text-[10px] font-mono uppercase">
                        Simulation Ready
                      </span>
                    </div>

                    <p className="text-xs text-[#94A8C2] leading-relaxed">
                      Configure strategy parameters on the left and execute the backtest.
                      The Python simulation engine calculates bar-by-bar signals, enforces realistic
                      next-bar open execution, deducts slippage and exchange fees, and outputs risk-adjusted metrics.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
                      <div className="p-3.5 rounded-xl bg-[#080D18] border border-[#1E2D42] space-y-1">
                        <span className="text-[10px] text-[#94A8C2] font-mono uppercase">Active Strategy</span>
                        <div className="text-xs font-bold text-[#67D7B4]">
                          {strategyType === "SMA_CROSSOVER" && "SMA Crossover"}
                          {strategyType === "EMA_CROSSOVER" && "EMA Crossover"}
                          {strategyType === "RSI_THRESHOLD" && "RSI Mean-Reversion"}
                          {strategyType === "BUY_AND_HOLD" && "Buy & Hold Benchmark"}
                        </div>
                        <p className="text-[10px] text-[#556D8C]">
                          {strategyType === "SMA_CROSSOVER" && `Fast: ${fastPeriod}d • Slow: ${slowPeriod}d`}
                          {strategyType === "EMA_CROSSOVER" && `Fast: ${fastPeriod}d • Slow: ${slowPeriod}d`}
                          {strategyType === "RSI_THRESHOLD" && `RSI: ${rsiPeriod} • Bounds: ${rsiOversold}/${rsiOverbought}`}
                          {strategyType === "BUY_AND_HOLD" && "100% Invested from Day 1"}
                        </p>
                      </div>

                      <div className="p-3.5 rounded-xl bg-[#080D18] border border-[#1E2D42] space-y-1">
                        <span className="text-[10px] text-[#94A8C2] font-mono uppercase">Data Coverage</span>
                        <div className="text-xs font-bold text-[#79A9E8] font-mono">
                          {availableDateRange ? `${availableDateRange.count} Daily Bars` : "NSE Historical"}
                        </div>
                        <p className="text-[10px] text-[#556D8C] font-mono truncate">
                          {availableDateRange ? `${availableDateRange.start} → ${availableDateRange.end}` : "Available Range"}
                        </p>
                      </div>

                      <div className="p-3.5 rounded-xl bg-[#080D18] border border-[#1E2D42] space-y-1">
                        <span className="text-[10px] text-[#94A8C2] font-mono uppercase">Friction Modeling</span>
                        <div className="text-xs font-bold text-[#A49AF6] font-mono">
                          {feeRatePct}% Fee • {slippageBps} bps
                        </div>
                        <p className="text-[10px] text-[#556D8C]">
                          Next-Bar Open Execution
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Research Methodology Breakdown */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-5 rounded-2xl bg-[#111B2B] border border-[#1E2D42] space-y-2.5">
                      <h4 className="text-xs font-bold text-[#F1F5FA] flex items-center gap-2">
                        <ShieldCheck size={16} className="text-[#67D7B4]" />
                        Mathematical Rigor & Bias Elimination
                      </h4>
                      <ul className="text-xs text-[#94A8C2] space-y-1.5 leading-relaxed">
                        <li className="flex items-start gap-2">
                          <span className="text-[#67D7B4] font-bold">•</span>
                          <span><strong>No Look-Ahead Bias:</strong> Signals computed on bar Close at time <em>t</em> execute only at bar Open at <em>t+1</em>.</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-[#67D7B4] font-bold">•</span>
                          <span><strong>Cash Constraints:</strong> Long-only cash positions prevent overselling or synthetic leverage.</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-[#67D7B4] font-bold">•</span>
                          <span><strong>Friction Modeling:</strong> Deducts commissions and bid-ask slippage on every trade entry and exit.</span>
                        </li>
                      </ul>
                    </div>

                    <div className="p-5 rounded-2xl bg-[#111B2B] border border-[#1E2D42] space-y-2.5">
                      <h4 className="text-xs font-bold text-[#F1F5FA] flex items-center gap-2">
                        <Activity size={16} className="text-[#79A9E8]" />
                        Institutional Metrics Computed
                      </h4>
                      <ul className="text-xs text-[#94A8C2] space-y-1.5 leading-relaxed">
                        <li className="flex items-start gap-2">
                          <span className="text-[#79A9E8] font-bold">•</span>
                          <span><strong>Sharpe & Sortino:</strong> Annualized excess return over 6% risk-free Indian benchmark (91-day T-bill).</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-[#79A9E8] font-bold">•</span>
                          <span><strong>Underwater Drawdown:</strong> High-water mark tracking with peak-to-trough drop quantification.</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-[#79A9E8] font-bold">•</span>
                          <span><strong>Execution Ledger:</strong> Detailed chronological table recording every transaction, fee, and realized P&L.</span>
                        </li>
                      </ul>
                    </div>
                  </div>

                  {/* One-Click Quick Run Action */}
                  <div className="p-5 rounded-2xl bg-gradient-to-r from-[#111B2B] via-[#172338] to-[#111B2B] border border-[#1E2D42] flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="space-y-0.5 text-center sm:text-left">
                      <div className="text-xs font-bold text-[#F1F5FA]">
                        Ready to compute strategy metrics?
                      </div>
                      <div className="text-[11px] text-[#94A8C2]">
                        Click to simulate {strategyType} on {instruments.find(i => i.id === selectedInstrumentId)?.symbol || "selected equity"}.
                      </div>
                    </div>
                    <button
                      onClick={handleRunBacktest}
                      disabled={runningBacktest}
                      className="px-5 py-2.5 rounded-xl bg-[#67D7B4] hover:bg-[#52c9a4] text-[#080D18] font-bold text-xs transition-all shadow-md shadow-[#67D7B4]/15 flex items-center gap-2 shrink-0 disabled:opacity-50"
                    >
                      {runningBacktest ? (
                        <>
                          <Loader2 size={14} className="animate-spin" />
                          <span>Simulating...</span>
                        </>
                      ) : (
                        <>
                          <Play size={14} />
                          <span>Run Quick Backtest</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Performance Summary Cards */}
                  {currentRun.metrics && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {/* Total Return */}
                      <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e] space-y-1">
                        <span className="text-[11px] text-[#91a0b3] font-medium">Total Return</span>
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`text-lg font-bold ${
                              currentRun.metrics.total_return_pct >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                            }`}
                          >
                            {currentRun.metrics.total_return_pct > 0 ? "+" : ""}
                            {currentRun.metrics.total_return_pct.toFixed(2)}%
                          </span>
                        </div>
                        <span className="text-[10px] text-[#64748b]">
                          Benchmark: {currentRun.metrics.benchmark_return_pct.toFixed(2)}%
                        </span>
                      </div>

                      {/* Net Profit */}
                      <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e] space-y-1">
                        <span className="text-[11px] text-[#91a0b3] font-medium">Net Profit</span>
                        <div className="text-lg font-bold text-[#edf3fa]">
                          ₹{currentRun.metrics.net_profit.toLocaleString("en-IN")}
                        </div>
                        <span className="text-[10px] text-[#64748b]">
                          Start: ₹{currentRun.metrics.starting_capital.toLocaleString("en-IN")}
                        </span>
                      </div>

                      {/* Sharpe Ratio */}
                      <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e] space-y-1">
                        <span className="text-[11px] text-[#91a0b3] font-medium">Sharpe Ratio (Rf=6%)</span>
                        <div className="text-lg font-bold text-[#38bdf8]">
                          {currentRun.metrics.sharpe_ratio !== null
                            ? currentRun.metrics.sharpe_ratio.toFixed(2)
                            : "N/A"}
                        </div>
                        <span className="text-[10px] text-[#64748b]">
                          Sortino: {currentRun.metrics.sortino_ratio !== null ? currentRun.metrics.sortino_ratio.toFixed(2) : "N/A"}
                        </span>
                      </div>

                      {/* Max Drawdown */}
                      <div className="p-4 rounded-xl bg-[#0e1724] border border-[#1e2d3e] space-y-1">
                        <span className="text-[11px] text-[#91a0b3] font-medium">Max Drawdown</span>
                        <div className="text-lg font-bold text-[#f87171]">
                          -{currentRun.metrics.max_drawdown_pct.toFixed(2)}%
                        </div>
                        <span className="text-[10px] text-[#64748b]">
                          Calmar: {currentRun.metrics.calmar_ratio !== null ? currentRun.metrics.calmar_ratio.toFixed(2) : "N/A"}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Secondary Metrics Bar */}
                  {currentRun.metrics && (
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 p-3 rounded-xl bg-[#080d16] border border-[#1e2d3e] text-[11px]">
                      <div>
                        <span className="text-[#64748b]">CAGR:</span>{" "}
                        <strong className="text-[#edf3fa]">
                          {currentRun.metrics.cagr_pct !== null
                            ? `${currentRun.metrics.cagr_pct > 0 ? "+" : ""}${currentRun.metrics.cagr_pct.toFixed(2)}%`
                            : "N/A (<1Y)"}
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#64748b]">Trades:</span>{" "}
                        <strong className="text-[#edf3fa]">
                          {currentRun.metrics.total_trades} ({currentRun.metrics.winning_trades}W / {currentRun.metrics.losing_trades}L)
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#64748b]">Win Rate:</span>{" "}
                        <strong className="text-[#71d5b3]">{currentRun.metrics.win_rate_pct.toFixed(1)}%</strong>
                      </div>
                      <div>
                        <span className="text-[#64748b]">Profit Factor:</span>{" "}
                        <strong className="text-[#edf3fa]">
                          {currentRun.metrics.profit_factor !== null
                            ? currentRun.metrics.profit_factor.toFixed(2)
                            : "N/A"}
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#64748b]">Exposure:</span>{" "}
                        <strong className="text-[#cbd5e1]">{currentRun.metrics.exposure_pct.toFixed(1)}%</strong>
                      </div>
                    </div>
                  )}

                  {/* Dual-Line Equity Curve SVG Chart */}
                  <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <h4 className="text-xs font-bold text-[#edf3fa] flex items-center gap-2">
                          <Activity size={16} className="text-[#71d5b3]" />
                          Portfolio Equity Curve vs Benchmark
                        </h4>
                        <span className="text-[11px] text-[#91a0b3]">
                          Chronological equity path (next-bar Open execution, fees deducted)
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-[11px]">
                        <div className="flex items-center gap-1.5">
                          <div className="w-3 h-1 bg-[#71d5b3] rounded" />
                          <span className="text-[#edf3fa]">Strategy Equity</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <div className="w-3 h-1 bg-[#38bdf8] rounded" />
                          <span className="text-[#91a0b3]">Buy & Hold Benchmark</span>
                        </div>
                      </div>
                    </div>

                    {equitySvgData && (
                      <div className="w-full overflow-x-auto">
                        <svg
                          viewBox={`0 0 ${equitySvgData.width} ${equitySvgData.height}`}
                          className="w-full h-auto min-w-[500px]"
                        >
                          {/* Gridlines */}
                          <line
                            x1={equitySvgData.padding.left}
                            y1={equitySvgData.padding.top}
                            x2={equitySvgData.width - equitySvgData.padding.right}
                            y2={equitySvgData.padding.top}
                            stroke="#1e2d3e"
                            strokeDasharray="3 3"
                          />
                          <line
                            x1={equitySvgData.padding.left}
                            y1={equitySvgData.height / 2}
                            x2={equitySvgData.width - equitySvgData.padding.right}
                            y2={equitySvgData.height / 2}
                            stroke="#1e2d3e"
                            strokeDasharray="3 3"
                          />
                          <line
                            x1={equitySvgData.padding.left}
                            y1={equitySvgData.height - equitySvgData.padding.bottom}
                            x2={equitySvgData.width - equitySvgData.padding.right}
                            y2={equitySvgData.height - equitySvgData.padding.bottom}
                            stroke="#1e2d3e"
                          />

                          {/* Y-axis Labels */}
                          <text
                            x={equitySvgData.padding.left - 10}
                            y={equitySvgData.padding.top + 4}
                            fill="#64748b"
                            fontSize="10"
                            textAnchor="end"
                          >
                            ₹{Math.round(equitySvgData.maxVal).toLocaleString("en-IN")}
                          </text>
                          <text
                            x={equitySvgData.padding.left - 10}
                            y={equitySvgData.height - equitySvgData.padding.bottom}
                            fill="#64748b"
                            fontSize="10"
                            textAnchor="end"
                          >
                            ₹{Math.round(equitySvgData.minVal).toLocaleString("en-IN")}
                          </text>

                          {/* Benchmark line */}
                          <path
                            d={equitySvgData.benchPath}
                            fill="none"
                            stroke="#38bdf8"
                            strokeWidth="1.8"
                            strokeDasharray="4 4"
                            opacity="0.8"
                          />

                          {/* Strategy line */}
                          <path
                            d={equitySvgData.stratPath}
                            fill="none"
                            stroke="#71d5b3"
                            strokeWidth="2.5"
                          />

                          {/* Date markers */}
                          <text
                            x={equitySvgData.padding.left}
                            y={equitySvgData.height - 8}
                            fill="#64748b"
                            fontSize="10"
                          >
                            {equitySvgData.firstDate}
                          </text>
                          <text
                            x={equitySvgData.width - equitySvgData.padding.right}
                            y={equitySvgData.height - 8}
                            fill="#64748b"
                            fontSize="10"
                            textAnchor="end"
                          >
                            {equitySvgData.lastDate}
                          </text>
                        </svg>
                      </div>
                    )}
                  </div>

                  {/* Drawdown Curve */}
                  {drawdownSvgData && (
                    <div className="p-4 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-[#edf3fa]">Underwater Drawdown Profile</span>
                        <span className="text-[#f87171] font-semibold">
                          Max: -{(drawdownSvgData.maxDD * 100).toFixed(1)}%
                        </span>
                      </div>
                      <svg
                        viewBox={`0 0 ${drawdownSvgData.width} ${drawdownSvgData.height}`}
                        className="w-full h-auto min-w-[500px]"
                      >
                        <path
                          d={drawdownSvgData.areaPath}
                          fill="#ef4444"
                          fillOpacity="0.25"
                          stroke="#ef4444"
                          strokeWidth="1.5"
                        />
                      </svg>
                    </div>
                  )}

                  {/* Trade Execution Ledger Table */}
                  <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                    <div className="flex items-center justify-between border-b border-[#1e2d3e] pb-3">
                      <div>
                        <h4 className="text-xs font-bold text-[#edf3fa]">Executed Trades Ledger</h4>
                        <span className="text-[11px] text-[#91a0b3]">
                          Orders placed on signal bar close and filled at next bar Open price
                        </span>
                      </div>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#15273b] text-[#71d5b3]">
                        {runTrades.length} Total Executions
                      </span>
                    </div>

                    {runTrades.length === 0 ? (
                      <p className="text-xs text-[#91a0b3] py-4 text-center">
                        No trade signals generated during this simulation period.
                      </p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="border-b border-[#1e2d3e] text-[#64748b]">
                              <th className="py-2 px-2 font-medium">Side</th>
                              <th className="py-2 px-2 font-medium">Signal Date</th>
                              <th className="py-2 px-2 font-medium">Fill Date</th>
                              <th className="py-2 px-2 font-medium text-right">Shares</th>
                              <th className="py-2 px-2 font-medium text-right">Fill Price</th>
                              <th className="py-2 px-2 font-medium text-right">Fees & Slip</th>
                              <th className="py-2 px-2 font-medium text-right">Cash Balance</th>
                              <th className="py-2 px-2 font-medium text-right">Realized P&L</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#1e2d3e]/50 text-[#cbd5e1]">
                            {runTrades.map((t) => (
                              <tr key={t.id} className="hover:bg-[#131f2f]/50">
                                <td className="py-2 px-2 font-bold">
                                  <span
                                    className={`px-2 py-0.5 rounded text-[10px] ${
                                      t.side === "BUY"
                                        ? "bg-[#102a24] text-[#71d5b3] border border-[#1b4338]"
                                        : "bg-[#2a1215] text-[#f87171] border border-[#4a1c22]"
                                    }`}
                                  >
                                    {t.side}
                                  </span>
                                </td>
                                <td className="py-2 px-2 text-[#91a0b3]">{t.signal_date}</td>
                                <td className="py-2 px-2 text-[#edf3fa] font-medium">{t.execution_date}</td>
                                <td className="py-2 px-2 text-right">{t.quantity}</td>
                                <td className="py-2 px-2 text-right font-medium">
                                  ₹{t.execution_price.toFixed(2)}
                                </td>
                                <td className="py-2 px-2 text-right text-[#91a0b3]">
                                  ₹{(t.fees + t.slippage_cost).toFixed(2)}
                                </td>
                                <td className="py-2 px-2 text-right">₹{t.cash_after.toLocaleString("en-IN")}</td>
                                <td className="py-2 px-2 text-right font-bold">
                                  {t.realized_pnl !== null ? (
                                    <span
                                      className={
                                        t.realized_pnl >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                                      }
                                    >
                                      {t.realized_pnl >= 0 ? "+" : ""}₹{t.realized_pnl.toFixed(2)} (
                                      {t.pnl_pct !== null ? `${t.pnl_pct.toFixed(1)}%` : ""})
                                    </span>
                                  ) : (
                                    <span className="text-[#64748b]">—</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 2: PARAMETER OPTIMIZER (GRID SEARCH) */}
        {/* ========================================================= */}
        {activeTab === "optimizer" && (
          <div className="space-y-6">
            {/* Split Information Banner */}
            <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-2">
              <div className="flex items-center gap-2 text-sm font-bold text-[#edf3fa]">
                <Sliders size={18} className="text-[#71d5b3]" />
                Train / Test Validation Split to Prevent Overfitting
              </div>
              <p className="text-xs text-[#91a0b3] leading-relaxed">
                Backtest parameter search splits your dataset chronologically into <strong>In-Sample (Training)</strong> and <strong>Out-of-Sample (Forward Testing)</strong> periods. Strategies that fit well on training data but deteriorate dramatically out-of-sample are automatically flagged with an <strong>Overfitting Warning</strong>.
              </p>
            </div>

            {/* Optimizer Configuration Form */}
            <div className="p-6 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
              <h3 className="text-xs font-bold text-[#edf3fa] uppercase tracking-wider">
                Grid Search Parameters (Capped at 25 Combinations)
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#91a0b3]">Strategy Type</label>
                  <select
                    value={optStrategyType}
                    onChange={(e) => setOptStrategyType(e.target.value)}
                    className="w-full px-3 py-2 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                  >
                    <option value="SMA_CROSSOVER">SMA Crossover</option>
                    <option value="EMA_CROSSOVER">EMA Crossover</option>
                    <option value="RSI_THRESHOLD">RSI Mean-Reversion</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#91a0b3]">Target Equity</label>
                  <select
                    value={selectedInstrumentId}
                    onChange={(e) => setSelectedInstrumentId(e.target.value)}
                    className="w-full px-3 py-2 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                  >
                    {instruments.map((inst) => (
                      <option key={inst.id} value={inst.id}>
                        {inst.symbol} — {inst.company_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#91a0b3]">
                    In-Sample Train Ratio ({(trainRatio * 100).toFixed(0)}%)
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="0.85"
                    step="0.05"
                    value={trainRatio}
                    onChange={(e) => setTrainRatio(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Date selection for Optimizer */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-[#1e2d3e]">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#91a0b3]">Evaluation Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    min={availableDateRange?.start}
                    max={availableDateRange?.end}
                    onChange={(e) => {
                      setStartDate(e.target.value);
                      setOptimizerError(null);
                    }}
                    className="w-full px-3 py-2 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#91a0b3]">Evaluation End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    min={availableDateRange?.start}
                    max={availableDateRange?.end}
                    onChange={(e) => {
                      setEndDate(e.target.value);
                      setOptimizerError(null);
                    }}
                    className="w-full px-3 py-2 bg-[#080d16] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                  />
                </div>
              </div>

              {availableDateRange && (
                <div className="flex items-center justify-between p-2 rounded-lg bg-[#080d16] border border-[#1e2d3e] text-[11px]">
                  <div className="flex items-center gap-1.5 text-[#8293a7]">
                    <Calendar size={13} className="text-[#71d5b3]" />
                    <span>
                      Available History: <strong className="text-[#edf3fa] font-mono">{availableDateRange.start}</strong> to{" "}
                      <strong className="text-[#edf3fa] font-mono">{availableDateRange.end}</strong> ({availableDateRange.count} bars)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={handleUseFullRange}
                    className="px-2 py-0.5 rounded bg-[#152a3b] hover:bg-[#1c3850] text-[#71d5b3] font-semibold text-[10px] transition-colors"
                  >
                    Use Available Range
                  </button>
                </div>
              )}

              {/* Dynamic Candidate Inputs */}
              {(optStrategyType === "SMA_CROSSOVER" || optStrategyType === "EMA_CROSSOVER") && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl bg-[#080d16] border border-[#1e2d3e]">
                  <div className="space-y-1">
                    <label className="text-xs text-[#91a0b3]">Fast Period Candidates (comma-separated)</label>
                    <input
                      type="text"
                      value={fastCandidates}
                      onChange={(e) => setFastCandidates(e.target.value)}
                      placeholder="10, 20, 30"
                      className="w-full px-3 py-2 bg-[#0e1724] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-[#91a0b3]">Slow Period Candidates (comma-separated)</label>
                    <input
                      type="text"
                      value={slowCandidates}
                      onChange={(e) => setSlowCandidates(e.target.value)}
                      placeholder="50, 100, 200"
                      className="w-full px-3 py-2 bg-[#0e1724] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                    />
                  </div>
                </div>
              )}

              {optStrategyType === "RSI_THRESHOLD" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-4 rounded-xl bg-[#080d16] border border-[#1e2d3e]">
                  <div className="space-y-1">
                    <label className="text-xs text-[#91a0b3]">RSI Periods</label>
                    <input
                      type="text"
                      value={rsiPeriodCandidates}
                      onChange={(e) => setRsiPeriodCandidates(e.target.value)}
                      placeholder="10, 14"
                      className="w-full px-3 py-2 bg-[#0e1724] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-[#91a0b3]">Oversold Thresholds</label>
                    <input
                      type="text"
                      value={rsiOversoldCandidates}
                      onChange={(e) => setRsiOversoldCandidates(e.target.value)}
                      placeholder="25, 30"
                      className="w-full px-3 py-2 bg-[#0e1724] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-[#91a0b3]">Overbought Thresholds</label>
                    <input
                      type="text"
                      value={rsiOverboughtCandidates}
                      onChange={(e) => setRsiOverboughtCandidates(e.target.value)}
                      placeholder="70, 75"
                      className="w-full px-3 py-2 bg-[#0e1724] border border-[#1e2d3e] rounded-xl text-xs text-[#edf3fa]"
                    />
                  </div>
                </div>
              )}

              {optimizerError && (
                <div className="p-3.5 rounded-xl bg-[#2a1215] border border-[#4a1c22] text-[#f87171] text-xs space-y-2">
                  <div className="flex items-start gap-2">
                    <AlertCircle size={16} className="shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{optimizerError}</span>
                  </div>
                  {availableDateRange && (
                    <div className="pt-1">
                      <button
                        type="button"
                        onClick={handleUseFullRange}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#3a1a20] hover:bg-[#4d222b] text-rose-200 text-xs font-semibold border border-rose-500/30 transition-colors"
                      >
                        <RotateCcw size={12} />
                        Use Available Range ({availableDateRange.start} to {availableDateRange.end})
                      </button>
                    </div>
                  )}
                </div>
              )}

              <button
                onClick={handleRunOptimizer}
                disabled={runningOptimizer}
                className="px-6 py-2.5 rounded-xl bg-[#71d5b3] text-[#080d16] font-bold text-xs hover:bg-[#5bc4a0] transition-all flex items-center gap-2 disabled:opacity-50"
              >
                {runningOptimizer ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Running Bounded Parameter Search...
                  </>
                ) : (
                  <>
                    <Sliders size={16} />
                    Execute Grid Search Experiment
                  </>
                )}
              </button>
            </div>

            {/* Results Display */}
            {gridResults.length === 0 ? (
              <div className="p-8 rounded-2xl bg-[#111B2B] border border-[#1E2D42] text-center space-y-4">
                <div className="w-12 h-12 rounded-xl bg-[#172338] text-[#79A9E8] flex items-center justify-center mx-auto border border-[#1E2D42]">
                  <Sliders size={22} />
                </div>
                <div className="max-w-md mx-auto space-y-1.5">
                  <h3 className="text-sm font-bold text-[#F1F5FA]">Parameter Optimizer Ready</h3>
                  <p className="text-xs text-[#94A8C2] leading-relaxed">
                    Specify candidate values above (up to 25 combinations) and click <strong>Execute Grid Search Experiment</strong>.
                    The platform evaluates all combinations across chronological in-sample training and out-of-sample forward-test periods.
                  </p>
                </div>
                <div className="pt-2 flex items-center justify-center gap-6 text-[11px] text-[#556D8C] font-mono">
                  <span>• Max 25 Combinations</span>
                  <span>• Train/Test Walk-Forward Split</span>
                  <span>• Overfitting Detection</span>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {bestParams && (
                  <div className="p-4 rounded-xl bg-[#102a24] border border-[#1b4338] text-xs flex items-center justify-between">
                    <div>
                      <strong className="text-[#71d5b3]">Optimal Parameter Configuration Found:</strong>{" "}
                      <span className="text-[#edf3fa] font-mono">{JSON.stringify(bestParams)}</span>
                    </div>
                    {gridSummary && <span className="text-[#91a0b3]">{gridSummary}</span>}
                  </div>
                )}

                <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                  <h4 className="text-xs font-bold text-[#edf3fa]">Tested Parameter Combinations</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#1e2d3e] text-[#64748b]">
                          <th className="py-2 px-3 font-medium">Parameters</th>
                          <th className="py-2 px-3 font-medium text-right">In-Sample Return</th>
                          <th className="py-2 px-3 font-medium text-right">In-Sample Sharpe</th>
                          <th className="py-2 px-3 font-medium text-right">In-Sample Max DD</th>
                          <th className="py-2 px-3 font-medium text-right">Out-of-Sample Return</th>
                          <th className="py-2 px-3 font-medium text-right">Out-of-Sample Sharpe</th>
                          <th className="py-2 px-3 font-medium text-right">Out-of-Sample Max DD</th>
                          <th className="py-2 px-3 font-medium text-center">Overfitting Check</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#1e2d3e]/50 text-[#cbd5e1]">
                        {gridResults.map((r, i) => (
                          <tr key={i} className="hover:bg-[#131f2f]/50">
                            <td className="py-2.5 px-3 font-mono font-medium text-[#edf3fa]">
                              {JSON.stringify(r.params)}
                            </td>
                            <td
                              className={`py-2.5 px-3 text-right font-medium ${
                                r.in_sample_return_pct >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                              }`}
                            >
                              {r.in_sample_return_pct > 0 ? "+" : ""}
                              {r.in_sample_return_pct.toFixed(2)}%
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              {r.in_sample_sharpe !== null ? r.in_sample_sharpe.toFixed(2) : "—"}
                            </td>
                            <td className="py-2.5 px-3 text-right text-[#f87171]">
                              -{r.in_sample_max_dd_pct.toFixed(2)}%
                            </td>
                            <td
                              className={`py-2.5 px-3 text-right font-bold ${
                                r.out_of_sample_return_pct >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                              }`}
                            >
                              {r.out_of_sample_return_pct > 0 ? "+" : ""}
                              {r.out_of_sample_return_pct.toFixed(2)}%
                            </td>
                            <td className="py-2.5 px-3 text-right font-bold text-[#38bdf8]">
                              {r.out_of_sample_sharpe !== null ? r.out_of_sample_sharpe.toFixed(2) : "—"}
                            </td>
                            <td className="py-2.5 px-3 text-right text-[#f87171]">
                              -{r.out_of_sample_max_dd_pct.toFixed(2)}%
                            </td>
                            <td className="py-2.5 px-3 text-center">
                              {r.overfitting_warning ? (
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#2a1215] text-[#f87171] border border-[#4a1c22]">
                                  Severe Degradation
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#102a24] text-[#71d5b3] border border-[#1b4338]">
                                  Robust OOS
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 3: STRATEGY STUDIO */}
        {/* ========================================================= */}
        {activeTab === "strategies" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-[#edf3fa]">Saved Research Strategies</h3>
                <p className="text-xs text-[#91a0b3]">
                  Reusable strategy configurations with version tracking and validated parameter constraints.
                </p>
              </div>
              <button
                onClick={fetchStrategies}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0e1724] border border-[#1e2d3e] text-xs text-[#cbd5e1] hover:bg-[#15273b]"
              >
                <RefreshCw size={12} className={loadingStrategies ? "animate-spin" : ""} />
                Refresh
              </button>
            </div>

            {loadingStrategies ? (
              <div className="p-8 text-center text-[#91a0b3] text-xs">
                <Loader2 size={20} className="animate-spin mx-auto mb-2 text-[#71d5b3]" />
                Loading saved strategies...
              </div>
            ) : savedStrategies.length === 0 ? (
              <div className="p-8 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] text-center space-y-2">
                <p className="text-xs text-[#91a0b3]">
                  You have not saved any research strategies yet. Save one from the Backtest Simulator tab.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedStrategies.map((s) => (
                  <div
                    key={s.id}
                    className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3 flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="flex items-start justify-between">
                        <h4 className="text-sm font-bold text-[#edf3fa]">{s.name}</h4>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#15273b] text-[#71d5b3]">
                          v{s.version}
                        </span>
                      </div>
                      {s.description && (
                        <p className="text-xs text-[#91a0b3] line-clamp-2">{s.description}</p>
                      )}
                      <div className="p-2.5 rounded-xl bg-[#080d16] border border-[#1e2d3e] text-[11px] font-mono text-[#cbd5e1]">
                        <span className="text-[#64748b]">Type:</span> {s.strategy_type}
                        <br />
                        <span className="text-[#64748b]">Params:</span> {JSON.stringify(s.parameters)}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-[#1e2d3e]">
                      <button
                        onClick={() => {
                          setStrategyType(s.strategy_type);
                          if (s.parameters.fast_period) setFastPeriod(s.parameters.fast_period);
                          if (s.parameters.slow_period) setSlowPeriod(s.parameters.slow_period);
                          if (s.parameters.rsi_period) setRsiPeriod(s.parameters.rsi_period);
                          if (s.parameters.oversold_threshold) setRsiOversold(s.parameters.oversold_threshold);
                          if (s.parameters.overbought_threshold) setRsiOverbought(s.parameters.overbought_threshold);
                          setActiveTab("simulator");
                        }}
                        className="text-xs text-[#71d5b3] hover:underline flex items-center gap-1 font-semibold"
                      >
                        Load in Simulator <ChevronRight size={14} />
                      </button>

                      <button
                        onClick={() => handleDeleteStrategy(s.id)}
                        className="text-xs text-[#f87171] hover:text-[#ef4444] p-1"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 4: SIMULATION HISTORY & COMPARISON */}
        {/* ========================================================= */}
        {activeTab === "history" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-[#edf3fa]">Simulation History & Multi-Run Comparison</h3>
                <p className="text-xs text-[#91a0b3]">
                  Select 2 to 5 historical runs to compare key risk and return metrics side-by-side.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleCompareRuns}
                  disabled={comparingRuns || selectedRunIds.length < 2}
                  className="px-4 py-2 rounded-xl bg-[#71d5b3] text-[#080d16] font-bold text-xs hover:bg-[#5bc4a0] disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Scale size={14} />
                  Compare Selected ({selectedRunIds.length})
                </button>
                <button
                  onClick={fetchRuns}
                  className="px-3 py-2 rounded-xl bg-[#0e1724] border border-[#1e2d3e] text-xs text-[#cbd5e1] hover:bg-[#15273b]"
                >
                  <RefreshCw size={14} className={loadingRuns ? "animate-spin" : ""} />
                </button>
              </div>
            </div>

            {/* Comparison Side-by-Side View */}
            {comparisonItems.length > 0 && (
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-4">
                <div className="flex items-center justify-between border-b border-[#1e2d3e] pb-3">
                  <h4 className="text-sm font-bold text-[#edf3fa]">Side-by-Side Strategy Comparison</h4>
                  <button
                    onClick={() => setComparisonItems([])}
                    className="text-xs text-[#91a0b3] hover:text-[#edf3fa]"
                  >
                    Clear Comparison
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#1e2d3e] text-[#64748b]">
                        <th className="py-2 px-3 font-medium">Metric</th>
                        {comparisonItems.map((item) => (
                          <th key={item.run_id} className="py-2 px-3 font-bold text-[#edf3fa]">
                            {item.strategy_name} ({item.instrument_ticker})
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1e2d3e]/50 text-[#cbd5e1]">
                      <tr>
                        <td className="py-2 px-3 text-[#91a0b3]">Total Return</td>
                        {comparisonItems.map((item) => (
                          <td
                            key={item.run_id}
                            className={`py-2 px-3 font-bold ${
                              (item.metrics?.total_return_pct ?? 0) >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                            }`}
                          >
                            {item.metrics?.total_return_pct?.toFixed(2)}%
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-[#91a0b3]">Benchmark Return</td>
                        {comparisonItems.map((item) => (
                          <td key={item.run_id} className="py-2 px-3">
                            {item.metrics?.benchmark_return_pct?.toFixed(2)}%
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-[#91a0b3]">Sharpe Ratio (Rf=6%)</td>
                        {comparisonItems.map((item) => (
                          <td key={item.run_id} className="py-2 px-3 font-bold text-[#38bdf8]">
                            {item.metrics?.sharpe_ratio !== null ? item.metrics?.sharpe_ratio?.toFixed(2) : "N/A"}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-[#91a0b3]">Sortino Ratio</td>
                        {comparisonItems.map((item) => (
                          <td key={item.run_id} className="py-2 px-3">
                            {item.metrics?.sortino_ratio !== null ? item.metrics?.sortino_ratio?.toFixed(2) : "N/A"}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-[#91a0b3]">Max Drawdown</td>
                        {comparisonItems.map((item) => (
                          <td key={item.run_id} className="py-2 px-3 text-[#f87171] font-bold">
                            -{item.metrics?.max_drawdown_pct?.toFixed(2)}%
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-[#91a0b3]">Total Trades</td>
                        {comparisonItems.map((item) => (
                          <td key={item.run_id} className="py-2 px-3">
                            {item.metrics?.total_trades}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-[#91a0b3]">Win Rate</td>
                        {comparisonItems.map((item) => (
                          <td key={item.run_id} className="py-2 px-3 text-[#71d5b3]">
                            {item.metrics?.win_rate_pct?.toFixed(1)}%
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-[#91a0b3]">Profit Factor</td>
                        {comparisonItems.map((item) => (
                          <td key={item.run_id} className="py-2 px-3">
                            {item.metrics?.profit_factor !== null ? item.metrics?.profit_factor?.toFixed(2) : "N/A"}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-[#91a0b3]">Exposure %</td>
                        {comparisonItems.map((item) => (
                          <td key={item.run_id} className="py-2 px-3">
                            {item.metrics?.exposure_pct?.toFixed(1)}%
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Historical Runs Table */}
            {loadingRuns ? (
              <div className="p-8 text-center text-[#91a0b3] text-xs">
                <Loader2 size={20} className="animate-spin mx-auto mb-2 text-[#71d5b3]" />
                Loading backtest history...
              </div>
            ) : historicalRuns.length === 0 ? (
              <div className="p-8 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] text-center space-y-2">
                <p className="text-xs text-[#91a0b3]">
                  No simulation history found. Run a backtest in the Simulator tab to record history.
                </p>
              </div>
            ) : (
              <div className="p-5 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] space-y-3">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#1e2d3e] text-[#64748b]">
                        <th className="py-2 px-2 w-8">Select</th>
                        <th className="py-2 px-3 font-medium">Strategy & Ticker</th>
                        <th className="py-2 px-3 font-medium">Period</th>
                        <th className="py-2 px-3 font-medium text-right">Total Return</th>
                        <th className="py-2 px-3 font-medium text-right">Sharpe</th>
                        <th className="py-2 px-3 font-medium text-right">Max DD</th>
                        <th className="py-2 px-3 font-medium text-right">Trades</th>
                        <th className="py-2 px-3 font-medium text-right">Executed On</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1e2d3e]/50 text-[#cbd5e1]">
                      {historicalRuns.map((r) => {
                        const isSelected = selectedRunIds.includes(r.id);
                        return (
                          <tr key={r.id} className="hover:bg-[#131f2f]/50">
                            <td className="py-2.5 px-2">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleRunSelection(r.id)}
                                className="rounded bg-[#080d16] border-[#1e2d3e]"
                              />
                            </td>
                            <td className="py-2.5 px-3">
                              <div className="font-bold text-[#edf3fa]">{r.strategy_name}</div>
                              <div className="text-[11px] text-[#91a0b3]">{r.instrument_ticker}</div>
                            </td>
                            <td className="py-2.5 px-3 text-[#91a0b3]">
                              {r.start_date} to {r.end_date}
                            </td>
                            <td
                              className={`py-2.5 px-3 text-right font-bold ${
                                (r.metrics?.total_return_pct ?? 0) >= 0 ? "text-[#71d5b3]" : "text-[#f87171]"
                              }`}
                            >
                              {(r.metrics?.total_return_pct ?? 0) > 0 ? "+" : ""}
                              {r.metrics?.total_return_pct?.toFixed(2)}%
                            </td>
                            <td className="py-2.5 px-3 text-right font-semibold text-[#38bdf8]">
                              {r.metrics?.sharpe_ratio !== null ? r.metrics?.sharpe_ratio?.toFixed(2) : "—"}
                            </td>
                            <td className="py-2.5 px-3 text-right text-[#f87171]">
                              -{r.metrics?.max_drawdown_pct?.toFixed(2)}%
                            </td>
                            <td className="py-2.5 px-3 text-right">{r.metrics?.total_trades ?? 0}</td>
                            <td className="py-2.5 px-3 text-right text-[#64748b]">
                              {new Date(r.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
