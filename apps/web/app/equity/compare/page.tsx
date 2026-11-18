"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Check,
  Compass,
  FileText,
  Info,
  Layers,
  Loader2,
  Plus,
  Scale,
  Search,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react";
import { DashboardLayout } from "@/components/DashboardLayout";
import {
  api,
  EquityComparisonResponse,
  Instrument,
  InstrumentComparisonMetrics,
  NormalizedChartPoint,
} from "@/lib/api";

const SERIES_COLORS = [
  { stroke: "#71d5b3", bg: "bg-emerald-950/70", text: "text-[#71d5b3]", border: "border-emerald-600/50" },
  { stroke: "#38bdf8", bg: "bg-sky-950/70", text: "text-sky-300", border: "border-sky-600/50" },
  { stroke: "#f59e0b", bg: "bg-amber-950/70", text: "text-amber-300", border: "border-amber-600/50" },
  { stroke: "#c084fc", bg: "bg-purple-950/70", text: "text-purple-300", border: "border-purple-600/50" },
];

type PeriodOption = "1M" | "3M" | "6M" | "1Y" | "ALL";

function EquityCompareContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [period, setPeriod] = useState<PeriodOption>("1Y");
  const [comparisonData, setComparisonData] = useState<EquityComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Search picker state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Instrument[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [allInstruments, setAllInstruments] = useState<Instrument[]>([]);

  // Hover on chart
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // Initial load: fetch available instruments and preselect
  useEffect(() => {
    api.listInstruments({ size: 50 })
      .then((res) => {
        setAllInstruments(res.items);
        const urlIds = searchParams?.get("ids")?.split(",").filter(Boolean) || [];

        if (urlIds.length > 0) {
          setSelectedIds(urlIds.slice(0, 4));
        } else if (res.items.length >= 2) {
          // Preselect TCS and INFY or first two equities
          const tcs = res.items.find((i) => i.symbol === "TCS");
          const infy = res.items.find((i) => i.symbol === "INFY");
          if (tcs && infy) {
            setSelectedIds([tcs.id, infy.id]);
          } else {
            setSelectedIds([res.items[0].id, res.items[1].id]);
          }
        }
      })
      .catch((err) => {
        setError("Failed to load instrument directory");
      });
  }, [searchParams]);

  // Fetch comparison metrics whenever selectedIds or period changes
  useEffect(() => {
    if (selectedIds.length === 0) {
      setComparisonData(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    api.compareInstruments(selectedIds, period)
      .then((data) => {
        setComparisonData(data);
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Comparison failed";
        setError(msg);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [selectedIds, period]);

  // Search instruments for adding to comparison
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    const timeout = setTimeout(() => {
      api.searchInstruments(searchQuery, 8)
        .then((res) => {
          setSearchResults(res.filter((item) => !selectedIds.includes(item.id)));
        })
        .catch(() => {})
        .finally(() => setIsSearching(false));
    }, 200);

    return () => clearTimeout(timeout);
  }, [searchQuery, selectedIds]);

  const addInstrument = (id: string) => {
    if (selectedIds.length >= 4) return;
    const next = [...selectedIds, id];
    setSelectedIds(next);
    setSearchQuery("");
    setSearchResults([]);
  };

  const removeInstrument = (id: string) => {
    const next = selectedIds.filter((item) => item !== id);
    setSelectedIds(next);
  };

  // SVG Chart Geometry
  const svgWidth = 800;
  const svgHeight = 280;
  const padding = { top: 20, right: 25, bottom: 40, left: 55 };
  const chartWidth = svgWidth - padding.left - padding.right;
  const chartHeight = svgHeight - padding.top - padding.bottom;

  const chartCalculations = useMemo(() => {
    if (!comparisonData || comparisonData.normalized_chart.length === 0) return null;

    const chartPoints = comparisonData.normalized_chart;
    let minVal = 100.0;
    let maxVal = 100.0;

    chartPoints.forEach((pt) => {
      Object.values(pt.prices).forEach((val) => {
        if (val !== null && val !== undefined) {
          if (val < minVal) minVal = val;
          if (val > maxVal) maxVal = val;
        }
      });
    });

    const rangeVal = maxVal - minVal || 10;
    const yMin = Math.max(0, minVal - rangeVal * 0.08);
    const yMax = maxVal + rangeVal * 0.08;
    const effectiveRange = yMax - yMin;

    const baselineY = padding.top + chartHeight - ((100.0 - yMin) / effectiveRange) * chartHeight;

    // Coordinate mapping
    const pointsWithCoords = chartPoints.map((pt, idx) => {
      const x = padding.left + (idx / Math.max(1, chartPoints.length - 1)) * chartWidth;
      const coords: Record<string, number | null> = {};
      Object.entries(pt.prices).forEach(([sym, val]) => {
        if (val !== null && val !== undefined) {
          coords[sym] = padding.top + chartHeight - ((val - yMin) / effectiveRange) * chartHeight;
        } else {
          coords[sym] = null;
        }
      });
      return { x, raw: pt, coords };
    });

    // Generate paths for each instrument
    const paths: Record<string, string> = {};
    comparisonData.instruments.forEach((inst) => {
      let d = "";
      let started = false;
      pointsWithCoords.forEach((pt) => {
        const y = pt.coords[inst.symbol];
        if (y !== null && !isNaN(y)) {
          if (!started) {
            d += `M ${pt.x} ${y}`;
            started = true;
          } else {
            d += ` L ${pt.x} ${y}`;
          }
        }
      });
      paths[inst.symbol] = d;
    });

    return {
      points: pointsWithCoords,
      paths,
      yMin,
      yMax,
      baselineY,
    };
  }, [comparisonData, chartWidth, chartHeight, padding.left, padding.top]);

  const activePoint =
    hoverIndex !== null && chartCalculations && chartCalculations.points[hoverIndex]
      ? chartCalculations.points[hoverIndex]
      : chartCalculations && chartCalculations.points.length > 0
      ? chartCalculations.points[chartCalculations.points.length - 1]
      : null;

  return (
    <DashboardLayout title="Equity Comparison">
      <div className="space-y-6">
        {/* Navigation & Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/equity"
            className="inline-flex items-center gap-2 text-xs font-semibold text-[#8ca3ba] hover:text-[#71d5b3] transition-colors"
          >
            <ArrowLeft size={14} />
            Back to Equities Directory
          </Link>

          <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-emerald-950/70 text-[#71d5b3] border border-[#235848]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#71d5b3] animate-pulse" />
            SYNTHETIC DEMO COMPARISON
          </span>
        </div>

        {/* Multi-Instrument Selector Bar */}
        <div className="bg-[#0f1927] border border-[#202f42] rounded-2xl p-5 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-[#edf3fa] tracking-tight flex items-center gap-2.5">
                <Scale size={22} className="text-[#71d5b3]" />
                Multi-Company Comparison
              </h1>
              <p className="text-xs text-[#8ca3ba] mt-0.5">
                Select 2 to 4 companies to analyze relative returns, volatility, and financial ratios.
              </p>
            </div>

            {/* Time Horizon Selector */}
            <div className="flex items-center bg-[#09111c] border border-[#1d2b3e] p-1 rounded-xl text-xs self-start md:self-auto">
              {(["1M", "3M", "6M", "1Y", "ALL"] as PeriodOption[]).map((opt) => (
                <button
                  key={opt}
                  onClick={() => setPeriod(opt)}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    period === opt
                      ? "bg-[#182c42] text-[#71d5b3] shadow"
                      : "text-[#7f94aa] hover:text-[#edf3fa]"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          {/* Selected Instrument Chips & Search Dropdown */}
          <div className="flex flex-wrap items-center gap-2.5 pt-2 border-t border-[#182637]">
            {/* Active Chips */}
            {comparisonData?.instruments.map((inst, idx) => {
              const theme = SERIES_COLORS[idx % SERIES_COLORS.length];
              return (
                <div
                  key={inst.instrument_id}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border ${theme.bg} ${theme.border} text-xs font-semibold`}
                >
                  <span className={`w-2.5 h-2.5 rounded-full`} style={{ backgroundColor: theme.stroke }} />
                  <span className={theme.text}>{inst.symbol}</span>
                  <span className="text-[#64748b] text-[11px] truncate max-w-[120px]">
                    {inst.company_name}
                  </span>
                  <button
                    onClick={() => removeInstrument(inst.instrument_id)}
                    className="p-0.5 rounded hover:bg-black/30 text-[#8ca3ba] hover:text-[#edf3fa] ml-1"
                    title="Remove company"
                  >
                    <X size={13} />
                  </button>
                </div>
              );
            })}

            {/* Add Instrument Search Input */}
            {selectedIds.length < 4 && (
              <div className="relative">
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#09111c] border border-[#203144] text-xs">
                  <Search size={13} className="text-[#62778f]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Add stock (e.g. RELIANCE)..."
                    className="bg-transparent text-[#edf3fa] placeholder-[#576b80] focus:outline-none w-48 text-xs"
                  />
                  {searchQuery && (
                    <button onClick={() => setSearchQuery("")} className="text-[#62778f] hover:text-[#edf3fa]">
                      <X size={12} />
                    </button>
                  )}
                </div>

                {/* Search Dropdown */}
                {searchResults.length > 0 && (
                  <div className="absolute left-0 top-full mt-1.5 w-64 bg-[#0a1422] border border-[#23354b] rounded-xl shadow-2xl z-50 overflow-hidden divide-y divide-[#152335]">
                    {searchResults.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => addInstrument(item.id)}
                        className="w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-[#132235] transition-colors"
                      >
                        <div>
                          <strong className="text-[#edf3fa] block">{item.symbol}</strong>
                          <span className="text-[11px] text-[#6c8299] truncate block max-w-[180px]">
                            {item.company_name}
                          </span>
                        </div>
                        <Plus size={14} className="text-[#71d5b3]" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Loading and Error states */}
        {isLoading && (
          <div className="h-72 flex flex-col items-center justify-center gap-3 text-xs text-[#71d5b3] bg-[#0f1927] border border-[#202f42] rounded-2xl">
            <Loader2 size={24} className="animate-spin" />
            <span>Calculating normalized returns & risk indicators...</span>
          </div>
        )}

        {error && (
          <div className="p-5 rounded-2xl bg-[#141e2c] border border-rose-900/60 text-xs text-rose-300 space-y-2">
            <div className="flex items-center gap-2 font-bold">
              <ShieldAlert size={16} />
              <span>Comparison Error</span>
            </div>
            <p>{error}</p>
          </div>
        )}

        {/* Normalized Performance Chart */}
        {!isLoading && comparisonData && chartCalculations && (
          <div className="bg-[#0f1927] border border-[#202f42] rounded-2xl p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1b2b3d] pb-3">
              <div>
                <h2 className="text-sm font-bold text-[#edf3fa] tracking-wide uppercase flex items-center gap-2">
                  <TrendingUp size={16} className="text-[#71d5b3]" />
                  Normalized Price Performance (Rebased to 100.0)
                </h2>
                <span className="text-xs text-[#7f94aa]">
                  Period: {comparisonData.start_date} to {comparisonData.end_date}
                </span>
              </div>

              {/* Legend with active values */}
              <div className="flex flex-wrap items-center gap-3 text-xs">
                {comparisonData.instruments.map((inst, i) => {
                  const theme = SERIES_COLORS[i % SERIES_COLORS.length];
                  const activeVal = activePoint?.raw.prices[inst.symbol];
                  const retVal = activeVal ? activeVal - 100.0 : null;
                  return (
                    <div key={inst.symbol} className="flex items-center gap-1.5 font-mono">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: theme.stroke }} />
                      <strong className={theme.text}>{inst.symbol}:</strong>
                      <span className="text-[#edf3fa]">
                        {activeVal !== null && activeVal !== undefined ? activeVal.toFixed(1) : "-"}
                      </span>
                      {retVal !== null && (
                        <span className={`text-[10px] ${retVal >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          ({retVal >= 0 ? "+" : ""}{retVal.toFixed(1)}%)
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* SVG Normalized Multi-Line Chart */}
            <div className="relative w-full aspect-[25/10] min-h-[220px]">
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-full select-none overflow-visible"
                onMouseLeave={() => setHoverIndex(null)}
              >
                {/* Horizontal Baseline (100.0) */}
                <line
                  x1={padding.left}
                  y1={chartCalculations.baselineY}
                  x2={padding.left + chartWidth}
                  y2={chartCalculations.baselineY}
                  stroke="#2b435e"
                  strokeWidth="1.2"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 6}
                  y={chartCalculations.baselineY + 3}
                  textAnchor="end"
                  fill="#71d5b3"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  100 (Base)
                </text>

                {/* Y-Axis Grid Lines */}
                {[0, 0.33, 0.66, 1].map((pct, i) => {
                  const y = padding.top + chartHeight * pct;
                  const val = chartCalculations.yMax - pct * (chartCalculations.yMax - chartCalculations.yMin);
                  return (
                    <g key={i}>
                      <line
                        x1={padding.left}
                        y1={y}
                        x2={padding.left + chartWidth}
                        y2={y}
                        stroke="#162536"
                        strokeDasharray="2 2"
                      />
                      <text
                        x={padding.left - 6}
                        y={y + 3}
                        textAnchor="end"
                        fill="#4e6378"
                        fontSize="9"
                        fontFamily="monospace"
                      >
                        {val.toFixed(0)}
                      </text>
                    </g>
                  );
                })}

                {/* Render Each Instrument's Line Path */}
                {comparisonData.instruments.map((inst, i) => {
                  const theme = SERIES_COLORS[i % SERIES_COLORS.length];
                  const p = chartCalculations.paths[inst.symbol];
                  return p ? (
                    <path
                      key={inst.symbol}
                      d={p}
                      fill="none"
                      stroke={theme.stroke}
                      strokeWidth="2.2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      opacity="0.95"
                    />
                  ) : null;
                })}

                {/* Invisible Hover Rectangles */}
                {chartCalculations.points.map((pt, idx) => (
                  <rect
                    key={idx}
                    x={pt.x - (chartWidth / chartCalculations.points.length) / 2}
                    y={padding.top}
                    width={chartWidth / chartCalculations.points.length}
                    height={chartHeight}
                    fill="transparent"
                    onMouseEnter={() => setHoverIndex(idx)}
                  />
                ))}

                {/* Vertical Hover Crosshair */}
                {activePoint && (
                  <g>
                    <line
                      x1={activePoint.x}
                      y1={padding.top}
                      x2={activePoint.x}
                      y2={padding.top + chartHeight}
                      stroke="#8ca3ba"
                      strokeWidth="1"
                      strokeDasharray="2 2"
                      opacity="0.6"
                    />
                    {comparisonData.instruments.map((inst, i) => {
                      const theme = SERIES_COLORS[i % SERIES_COLORS.length];
                      const y = activePoint.coords[inst.symbol];
                      return y !== null && !isNaN(y) ? (
                        <circle
                          key={inst.symbol}
                          cx={activePoint.x}
                          cy={y}
                          r="4"
                          fill={theme.stroke}
                          stroke="#0f1927"
                          strokeWidth="2"
                        />
                      ) : null;
                    })}
                  </g>
                )}

                {/* X-Axis Dates */}
                {chartCalculations.points.length > 1 && (
                  <g transform={`translate(0, ${padding.top + chartHeight + 18})`}>
                    <text x={chartCalculations.points[0].x} y="0" fill="#5b6f84" fontSize="10">
                      {chartCalculations.points[0].raw.trade_date}
                    </text>
                    <text
                      x={chartCalculations.points[Math.floor(chartCalculations.points.length / 2)].x}
                      y="0"
                      fill="#5b6f84"
                      fontSize="10"
                      textAnchor="middle"
                    >
                      {chartCalculations.points[Math.floor(chartCalculations.points.length / 2)].raw.trade_date}
                    </text>
                    <text
                      x={chartCalculations.points[chartCalculations.points.length - 1].x}
                      y="0"
                      fill="#5b6f84"
                      fontSize="10"
                      textAnchor="end"
                    >
                      {chartCalculations.points[chartCalculations.points.length - 1].raw.trade_date}
                    </text>
                  </g>
                )}
              </svg>
            </div>
          </div>
        )}

        {/* Side-by-Side Comparison Matrix Table */}
        {!isLoading && comparisonData && (
          <div className="bg-[#0f1927] border border-[#202f42] rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#1b2b3d] pb-3">
              <h2 className="text-sm font-bold text-[#edf3fa] tracking-wide uppercase flex items-center gap-2">
                <FileText size={16} className="text-[#71d5b3]" />
                Side-by-Side Metric Matrix
              </h2>
              <span className="text-xs text-[#62778f]">
                {comparisonData.instruments.length} companies aligned
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#1f2e42] text-[#8ca3ba]">
                    <th className="py-3 px-4 font-semibold">Evaluation Metric</th>
                    {comparisonData.instruments.map((inst, i) => {
                      const theme = SERIES_COLORS[i % SERIES_COLORS.length];
                      return (
                        <th key={inst.instrument_id} className="py-3 px-4 font-bold text-right">
                          <span className={theme.text}>{inst.symbol}</span>
                          <span className="text-[10px] text-[#55697d] block font-normal">
                            {inst.exchange} • {inst.sector || "Equity"}
                          </span>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#152335] font-mono">
                  {/* Category: Performance & Risk */}
                  <tr className="bg-[#0b1420]/70 font-sans">
                    <td colSpan={comparisonData.instruments.length + 1} className="py-2 px-4 text-[#71d5b3] font-bold text-[11px] uppercase tracking-wider">
                      Performance & Risk ({period})
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#edf3fa]">Latest Close Price</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#edf3fa] font-bold">
                        ₹{inst.latest_price ? inst.latest_price.toFixed(2) : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">Period Total Return</td>
                    {comparisonData.instruments.map((inst) => {
                      const r = inst.period_return_pct;
                      const isUp = r !== null && r >= 0;
                      return (
                        <td key={inst.instrument_id} className={`py-2.5 px-4 text-right font-bold ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                          {r !== null ? `${isUp ? "+" : ""}${r.toFixed(2)}%` : "-"}
                        </td>
                      );
                    })}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">Annualized Volatility (σ)</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#cbd5e1]">
                        {inst.annualized_volatility_pct !== null ? `${inst.annualized_volatility_pct.toFixed(2)}%` : "-"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">Maximum Drawdown</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-rose-400/90">
                        {inst.max_drawdown_pct !== null ? `-${inst.max_drawdown_pct.toFixed(2)}%` : "-"}
                      </td>
                    ))}
                  </tr>

                  {/* Category: Valuation Ratios */}
                  <tr className="bg-[#0b1420]/70 font-sans">
                    <td colSpan={comparisonData.instruments.length + 1} className="py-2 px-4 text-[#71d5b3] font-bold text-[11px] uppercase tracking-wider">
                      Valuation Metrics
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#edf3fa]">P/E Ratio (Price / EPS)</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#edf3fa]">
                        {inst.pe_ratio !== null ? `${inst.pe_ratio.toFixed(2)}x` : "N/A"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">P/B Ratio (Price / Book Value)</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#cbd5e1]">
                        {inst.pb_ratio !== null ? `${inst.pb_ratio.toFixed(2)}x` : "N/A"}
                      </td>
                    ))}
                  </tr>

                  {/* Category: Profitability & Margins */}
                  <tr className="bg-[#0b1420]/70 font-sans">
                    <td colSpan={comparisonData.instruments.length + 1} className="py-2 px-4 text-[#71d5b3] font-bold text-[11px] uppercase tracking-wider">
                      Profitability & Returns
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#edf3fa]">Return on Equity (ROE)</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#71d5b3] font-bold">
                        {inst.roe_pct !== null ? `${inst.roe_pct.toFixed(2)}%` : "N/A"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">Operating Profit Margin (EBIT)</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#cbd5e1]">
                        {inst.operating_margin_pct !== null ? `${inst.operating_margin_pct.toFixed(2)}%` : "N/A"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">Net Profit Margin</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#cbd5e1]">
                        {inst.net_margin_pct !== null ? `${inst.net_margin_pct.toFixed(2)}%` : "N/A"}
                      </td>
                    ))}
                  </tr>

                  {/* Category: Financial Health & Leverage */}
                  <tr className="bg-[#0b1420]/70 font-sans">
                    <td colSpan={comparisonData.instruments.length + 1} className="py-2 px-4 text-[#71d5b3] font-bold text-[11px] uppercase tracking-wider">
                      Financial Health & Liquidity
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">Debt-to-Equity (D/E)</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#cbd5e1]">
                        {inst.debt_to_equity !== null ? inst.debt_to_equity.toFixed(2) : "0.00"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">Current Ratio</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#cbd5e1]">
                        {inst.current_ratio !== null ? inst.current_ratio.toFixed(2) : "N/A"}
                      </td>
                    ))}
                  </tr>

                  {/* Category: Technical Momentum */}
                  <tr className="bg-[#0b1420]/70 font-sans">
                    <td colSpan={comparisonData.instruments.length + 1} className="py-2 px-4 text-[#71d5b3] font-bold text-[11px] uppercase tracking-wider">
                      Technical Analysis Signals
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#edf3fa]">RSI (14) Indicator</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-[#edf3fa]">
                        {inst.rsi_14 !== null ? inst.rsi_14.toFixed(1) : "N/A"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">MA Cross Status (50 vs 200)</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-amber-300 font-sans text-[11px]">
                        {inst.ma_cross_state || "Neutral"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-sans text-[#91a0b3]">MACD Signal Bias</td>
                    {comparisonData.instruments.map((inst) => (
                      <td key={inst.instrument_id} className="py-2.5 px-4 text-right text-sky-400 font-sans text-[11px]">
                        {inst.macd_signal_state}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Disclaimer Footer */}
            <div className="pt-2 text-[11px] text-[#55697d] flex items-center gap-1.5 border-t border-[#182637]">
              <Info size={13} className="shrink-0" />
              <span>
                All performance metrics use daily close prices. Volatility is annualized using a factor of √252.
                Financial statements and valuation ratios are based on demo synthetic datasets for educational purposes.
              </span>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default function EquityComparePage() {
  return (
    <React.Suspense
      fallback={
        <DashboardLayout title="Equity Comparison">
          <div className="h-96 flex flex-col items-center justify-center gap-3 text-xs text-[#71d5b3]">
            <Loader2 size={24} className="animate-spin" />
            <span>Loading comparison workspace...</span>
          </div>
        </DashboardLayout>
      }
    >
      <EquityCompareContent />
    </React.Suspense>
  );
}
