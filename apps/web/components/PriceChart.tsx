"use client";

import React, { useMemo, useState } from "react";
import { PriceBar, TechnicalAnalysisResponse, IndicatorPoint } from "@/lib/api";
import { TrendingUp, TrendingDown, Layers, Activity, SlidersHorizontal } from "lucide-react";

interface PriceChartProps {
  prices: PriceBar[];
  symbol: string;
  currency?: string;
  isDemo?: boolean;
  dataSource?: string | null;
  technicals?: TechnicalAnalysisResponse | null;
}

type RangeOption = "1M" | "3M" | "6M" | "1Y" | "ALL";
type SubChartOption = "none" | "rsi" | "macd";

export function PriceChart({
  prices,
  symbol,
  currency = "INR",
  isDemo = false,
  dataSource,
  technicals,
}: PriceChartProps) {
  const [range, setRange] = useState<RangeOption>("1Y");
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // Indicator overlay state
  const [showSMA20, setShowSMA20] = useState<boolean>(true);
  const [showSMA50, setShowSMA50] = useState<boolean>(true);
  const [showSMA200, setShowSMA200] = useState<boolean>(false);
  const [showBB, setShowBB] = useState<boolean>(false);
  const [subChart, setSubChart] = useState<SubChartOption>("none");

  // Map of trade_date to technical indicator point
  const techMap = useMemo(() => {
    const map = new Map<string, IndicatorPoint>();
    if (technicals?.points) {
      technicals.points.forEach((p) => {
        map.set(p.trade_date, p);
      });
    }
    return map;
  }, [technicals]);

  // Filter prices according to selected range
  const filteredPrices = useMemo(() => {
    if (!prices || prices.length === 0) return [];
    if (range === "ALL") return prices;

    const countMap: Record<RangeOption, number> = {
      "1M": 21,
      "3M": 63,
      "6M": 126,
      "1Y": 250,
      ALL: prices.length,
    };
    const targetCount = countMap[range] || prices.length;
    return prices.slice(Math.max(0, prices.length - targetCount));
  }, [prices, range]);

  // Compute key stats
  const stats = useMemo(() => {
    if (filteredPrices.length === 0) {
      return {
        latest: 0,
        start: 0,
        change: 0,
        changePct: 0,
        high: 0,
        low: 0,
        avgVolume: 0,
      };
    }
    const latest = Number(filteredPrices[filteredPrices.length - 1].close);
    const start = Number(filteredPrices[0].close);
    const change = latest - start;
    const changePct = start > 0 ? (change / start) * 100 : 0;

    let high = -Infinity;
    let low = Infinity;
    let totalVol = 0;

    filteredPrices.forEach((p) => {
      const c = Number(p.close);
      const h = p.high !== null ? Number(p.high) : c;
      const l = p.low !== null ? Number(p.low) : c;
      if (h > high) high = h;
      if (l < low) low = l;
      if (p.volume) totalVol += p.volume;
    });

    return {
      latest,
      start,
      change,
      changePct,
      high,
      low,
      avgVolume: Math.round(totalVol / filteredPrices.length),
    };
  }, [filteredPrices]);

  // SVG Chart Geometry
  const svgWidth = 800;
  const mainChartHeight = 240;
  const subChartHeight = subChart !== "none" ? 90 : 0;
  const padding = { top: 20, right: 20, bottom: 35, left: 65 };
  const chartWidth = svgWidth - padding.left - padding.right;
  const volumeHeight = 35;
  const totalSvgHeight = mainChartHeight + subChartHeight + padding.top + padding.bottom + (subChart !== "none" ? 20 : 0);

  const chartData = useMemo(() => {
    if (filteredPrices.length === 0) return null;

    let minPrice = Infinity;
    let maxPrice = -Infinity;
    let maxVolume = 0;

    filteredPrices.forEach((p) => {
      const c = Number(p.close);
      if (c < minPrice) minPrice = c;
      if (c > maxPrice) maxPrice = c;
      if (p.volume && p.volume > maxVolume) maxVolume = p.volume;

      // Include visible indicator overlays in price bounds
      const tech = techMap.get(p.trade_date);
      if (tech) {
        if (showSMA20 && tech.sma_20 !== null) {
          minPrice = Math.min(minPrice, tech.sma_20);
          maxPrice = Math.max(maxPrice, tech.sma_20);
        }
        if (showSMA50 && tech.sma_50 !== null) {
          minPrice = Math.min(minPrice, tech.sma_50);
          maxPrice = Math.max(maxPrice, tech.sma_50);
        }
        if (showSMA200 && tech.sma_200 !== null) {
          minPrice = Math.min(minPrice, tech.sma_200);
          maxPrice = Math.max(maxPrice, tech.sma_200);
        }
        if (showBB && tech.bb_upper !== null && tech.bb_lower !== null) {
          minPrice = Math.min(minPrice, tech.bb_lower);
          maxPrice = Math.max(maxPrice, tech.bb_upper);
        }
      }
    });

    // Add 4% buffer to top and bottom
    const priceRange = maxPrice - minPrice || 1;
    const yMin = Math.max(0, minPrice - priceRange * 0.04);
    const yMax = maxPrice + priceRange * 0.04;
    const effectivePriceRange = yMax - yMin;

    const points = filteredPrices.map((p, idx) => {
      const x = padding.left + (idx / Math.max(1, filteredPrices.length - 1)) * chartWidth;
      const y =
        padding.top +
        mainChartHeight -
        ((Number(p.close) - yMin) / effectivePriceRange) * (mainChartHeight - volumeHeight);
      const volHeight = maxVolume > 0 && p.volume ? (p.volume / maxVolume) * volumeHeight : 0;
      const volY = padding.top + mainChartHeight - volHeight;
      const tech = techMap.get(p.trade_date);

      // Indicator Y-coordinates
      const sma20Y = tech?.sma_20 !== null && tech?.sma_20 !== undefined
        ? padding.top + mainChartHeight - ((tech.sma_20 - yMin) / effectivePriceRange) * (mainChartHeight - volumeHeight)
        : null;

      const sma50Y = tech?.sma_50 !== null && tech?.sma_50 !== undefined
        ? padding.top + mainChartHeight - ((tech.sma_50 - yMin) / effectivePriceRange) * (mainChartHeight - volumeHeight)
        : null;

      const sma200Y = tech?.sma_200 !== null && tech?.sma_200 !== undefined
        ? padding.top + mainChartHeight - ((tech.sma_200 - yMin) / effectivePriceRange) * (mainChartHeight - volumeHeight)
        : null;

      const bbUpperY = tech?.bb_upper !== null && tech?.bb_upper !== undefined
        ? padding.top + mainChartHeight - ((tech.bb_upper - yMin) / effectivePriceRange) * (mainChartHeight - volumeHeight)
        : null;

      const bbLowerY = tech?.bb_lower !== null && tech?.bb_lower !== undefined
        ? padding.top + mainChartHeight - ((tech.bb_lower - yMin) / effectivePriceRange) * (mainChartHeight - volumeHeight)
        : null;

      return {
        x,
        y,
        volY,
        volHeight,
        sma20Y,
        sma50Y,
        sma200Y,
        bbUpperY,
        bbLowerY,
        data: p,
        tech,
      };
    });

    // Generate Main Price SVG Path
    const linePath = points.reduce(
      (acc, pt, idx) => (idx === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`),
      ""
    );
    const areaPath = `${linePath} L ${points[points.length - 1].x} ${
      padding.top + mainChartHeight
    } L ${points[0].x} ${padding.top + mainChartHeight} Z`;

    // Helper to generate path for an indicator
    const makePath = (getY: (p: typeof points[0]) => number | null) => {
      let d = "";
      let started = false;
      points.forEach((pt) => {
        const yVal = getY(pt);
        if (yVal !== null && !isNaN(yVal)) {
          if (!started) {
            d += `M ${pt.x} ${yVal}`;
            started = true;
          } else {
            d += ` L ${pt.x} ${yVal}`;
          }
        }
      });
      return d;
    };

    const sma20Path = makePath((p) => p.sma20Y);
    const sma50Path = makePath((p) => p.sma50Y);
    const sma200Path = makePath((p) => p.sma200Y);
    const bbUpperPath = makePath((p) => p.bbUpperY);
    const bbLowerPath = makePath((p) => p.bbLowerY);

    // Bollinger Band Area
    const validBBPoints = points.filter((p) => p.bbUpperY !== null && p.bbLowerY !== null);
    let bbAreaPath = "";
    if (validBBPoints.length > 1) {
      const topSegment = validBBPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.bbUpperY}`).join(" ");
      const bottomSegment = validBBPoints
        .slice()
        .reverse()
        .map((p) => `L ${p.x} ${p.bbLowerY}`)
        .join(" ");
      bbAreaPath = `${topSegment} ${bottomSegment} Z`;
    }

    return {
      points,
      linePath,
      areaPath,
      sma20Path,
      sma50Path,
      sma200Path,
      bbUpperPath,
      bbLowerPath,
      bbAreaPath,
      yMin,
      yMax,
      maxVolume,
    };
  }, [filteredPrices, chartWidth, mainChartHeight, padding.left, padding.top, techMap, showSMA20, showSMA50, showSMA200, showBB]);

  const activePoint =
    hoverIndex !== null && chartData && chartData.points[hoverIndex]
      ? chartData.points[hoverIndex]
      : chartData && chartData.points.length > 0
      ? chartData.points[chartData.points.length - 1]
      : null;

  const isPositive = stats.change >= 0;

  return (
    <div className="bg-[#0f1927] border border-[#202f42] rounded-2xl p-5 sm:p-6 space-y-4">
      {/* Top Header & Range Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-[#71d5b3]">
              {symbol} • Technical Price Chart
            </span>
            {isDemo && (
              <span className="inline-flex items-center gap-1 text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-950 text-[#71d5b3] border border-[#235848]">
                DEMO DATA
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-2xl sm:text-3xl font-extrabold text-[#edf3fa] tracking-tight">
              ₹
              {activePoint
                ? Number(activePoint.data.close).toLocaleString("en-IN", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })
                : stats.latest.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
            <span
              className={`flex items-center text-xs font-bold ${
                isPositive ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {isPositive ? <TrendingUp size={13} className="mr-1" /> : <TrendingDown size={13} className="mr-1" />}
              {isPositive ? "+" : ""}
              {stats.change.toFixed(2)} ({isPositive ? "+" : ""}
              {stats.changePct.toFixed(2)}%)
            </span>
          </div>
        </div>

        {/* Range Selector */}
        <div className="flex items-center bg-[#09111c] border border-[#1d2b3e] p-1 rounded-xl text-xs self-start sm:self-auto">
          {(["1M", "3M", "6M", "1Y", "ALL"] as RangeOption[]).map((opt) => (
            <button
              key={opt}
              onClick={() => setRange(opt)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                range === opt
                  ? "bg-[#182c42] text-[#71d5b3] shadow"
                  : "text-[#7f94aa] hover:text-[#edf3fa]"
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* Indicator Controls & Overlay Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 rounded-xl bg-[#0a1320] border border-[#1b2b3d] text-xs">
        {/* Overlay Checkboxes */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <span className="text-[11px] font-semibold text-[#6c8299] flex items-center gap-1.5">
            <Layers size={13} className="text-[#71d5b3]" />
            Overlays:
          </span>
          <button
            type="button"
            onClick={() => setShowSMA20(!showSMA20)}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors border ${
              showSMA20
                ? "bg-amber-950/60 text-amber-300 border-amber-600/50"
                : "bg-transparent text-[#62778f] border-[#202f42] hover:text-[#edf3fa]"
            }`}
          >
            SMA 20
          </button>
          <button
            type="button"
            onClick={() => setShowSMA50(!showSMA50)}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors border ${
              showSMA50
                ? "bg-sky-950/60 text-sky-300 border-sky-600/50"
                : "bg-transparent text-[#62778f] border-[#202f42] hover:text-[#edf3fa]"
            }`}
          >
            SMA 50
          </button>
          <button
            type="button"
            onClick={() => setShowSMA200(!showSMA200)}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors border ${
              showSMA200
                ? "bg-purple-950/60 text-purple-300 border-purple-600/50"
                : "bg-transparent text-[#62778f] border-[#202f42] hover:text-[#edf3fa]"
            }`}
          >
            SMA 200
          </button>
          <button
            type="button"
            onClick={() => setShowBB(!showBB)}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors border ${
              showBB
                ? "bg-cyan-950/60 text-cyan-300 border-cyan-600/50"
                : "bg-transparent text-[#62778f] border-[#202f42] hover:text-[#edf3fa]"
            }`}
          >
            Bollinger Bands (20,2)
          </button>
        </div>

        {/* Sub-chart Oscillator Selector */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold text-[#6c8299] flex items-center gap-1.5">
            <Activity size={13} className="text-[#38bdf8]" />
            Oscillator:
          </span>
          <div className="flex bg-[#070e17] p-0.5 rounded-lg border border-[#182738]">
            <button
              onClick={() => setSubChart("none")}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                subChart === "none" ? "bg-[#182b3d] text-[#edf3fa]" : "text-[#586c82] hover:text-[#edf3fa]"
              }`}
            >
              None
            </button>
            <button
              onClick={() => setSubChart("rsi")}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                subChart === "rsi" ? "bg-[#182b3d] text-[#71d5b3]" : "text-[#586c82] hover:text-[#edf3fa]"
              }`}
            >
              RSI (14)
            </button>
            <button
              onClick={() => setSubChart("macd")}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                subChart === "macd" ? "bg-[#182b3d] text-[#38bdf8]" : "text-[#586c82] hover:text-[#edf3fa]"
              }`}
            >
              MACD
            </button>
          </div>
        </div>
      </div>

      {/* Hover Inspection Meta Strip */}
      {activePoint && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-[#7f94aa] border-y border-[#182536] py-2">
          <span>
            Date: <strong className="text-[#edf3fa]">{activePoint.data.trade_date}</strong>
          </span>
          <span>
            Close: <strong className="text-[#edf3fa]">₹{Number(activePoint.data.close).toFixed(2)}</strong>
          </span>
          {showSMA20 && activePoint.tech?.sma_20 !== null && activePoint.tech?.sma_20 !== undefined && (
            <span className="text-amber-300">
              SMA 20: <strong>₹{activePoint.tech.sma_20.toFixed(2)}</strong>
            </span>
          )}
          {showSMA50 && activePoint.tech?.sma_50 !== null && activePoint.tech?.sma_50 !== undefined && (
            <span className="text-sky-300">
              SMA 50: <strong>₹{activePoint.tech.sma_50.toFixed(2)}</strong>
            </span>
          )}
          {showSMA200 && activePoint.tech?.sma_200 !== null && activePoint.tech?.sma_200 !== undefined && (
            <span className="text-purple-300">
              SMA 200: <strong>₹{activePoint.tech.sma_200.toFixed(2)}</strong>
            </span>
          )}
          {showBB && activePoint.tech && activePoint.tech.bb_upper !== null && activePoint.tech.bb_lower !== null && (
            <span className="text-cyan-300">
              BB: [<strong>₹{activePoint.tech.bb_lower.toFixed(2)}</strong> - <strong>₹{activePoint.tech.bb_upper.toFixed(2)}</strong>]
            </span>
          )}
          {subChart === "rsi" && activePoint.tech && activePoint.tech.rsi_14 !== null && (
            <span className={activePoint.tech.rsi_14 >= 70 ? "text-rose-400" : activePoint.tech.rsi_14 <= 30 ? "text-emerald-400" : "text-[#71d5b3]"}>
              RSI(14): <strong>{activePoint.tech.rsi_14.toFixed(1)}</strong>
            </span>
          )}
          {subChart === "macd" && activePoint.tech && activePoint.tech.macd_line !== null && activePoint.tech.macd_signal !== null && (
            <span className="text-sky-300">
              MACD: <strong>{activePoint.tech.macd_line.toFixed(2)}</strong> | Sig: <strong>{activePoint.tech.macd_signal.toFixed(2)}</strong>
            </span>
          )}
        </div>
      )}

      {/* SVG Chart Area */}
      <div className="relative w-full overflow-hidden">
        {chartData ? (
          <svg
            viewBox={`0 0 ${svgWidth} ${totalSvgHeight}`}
            className="w-full h-auto select-none overflow-visible"
            onMouseLeave={() => setHoverIndex(null)}
          >
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#71d5b3" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#71d5b3" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid Lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
              const y = padding.top + (mainChartHeight - volumeHeight) * pct;
              const priceVal = chartData.yMax - pct * (chartData.yMax - chartData.yMin);
              return (
                <g key={i}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={padding.left + chartWidth}
                    y2={y}
                    stroke="#1a2738"
                    strokeDasharray="3 3"
                    strokeWidth="1"
                  />
                  <text
                    x={padding.left - 8}
                    y={y + 3}
                    textAnchor="end"
                    fill="#5b6f84"
                    fontSize="10"
                    fontFamily="monospace"
                  >
                    ₹{priceVal.toFixed(0)}
                  </text>
                </g>
              );
            })}

            {/* Volume bars */}
            {chartData.points.map((pt, i) => (
              <rect
                key={i}
                x={pt.x - 1}
                y={pt.volY}
                width={Math.max(1.5, chartWidth / chartData.points.length - 1)}
                height={pt.volHeight}
                fill={hoverIndex === i ? "#71d5b3" : "#1c3249"}
                opacity={0.6}
              />
            ))}

            {/* Bollinger Band Shaded Area */}
            {showBB && chartData.bbAreaPath && (
              <path d={chartData.bbAreaPath} fill="#06b6d4" opacity="0.10" />
            )}

            {/* Bollinger Bands Lines */}
            {showBB && chartData.bbUpperPath && (
              <path d={chartData.bbUpperPath} fill="none" stroke="#06b6d4" strokeWidth="1.2" strokeDasharray="2 2" opacity="0.7" />
            )}
            {showBB && chartData.bbLowerPath && (
              <path d={chartData.bbLowerPath} fill="none" stroke="#06b6d4" strokeWidth="1.2" strokeDasharray="2 2" opacity="0.7" />
            )}

            {/* Main Price Area & Line */}
            <path d={chartData.areaPath} fill="url(#priceGradient)" />
            <path
              d={chartData.linePath}
              fill="none"
              stroke="#71d5b3"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Moving Average Overlays */}
            {showSMA20 && chartData.sma20Path && (
              <path d={chartData.sma20Path} fill="none" stroke="#f59e0b" strokeWidth="1.5" opacity="0.9" />
            )}
            {showSMA50 && chartData.sma50Path && (
              <path d={chartData.sma50Path} fill="none" stroke="#38bdf8" strokeWidth="1.5" opacity="0.9" />
            )}
            {showSMA200 && chartData.sma200Path && (
              <path d={chartData.sma200Path} fill="none" stroke="#c084fc" strokeWidth="1.5" opacity="0.9" />
            )}

            {/* Sub-Chart Oscillator Panel (RSI or MACD) */}
            {subChart === "rsi" && (
              <g transform={`translate(0, ${padding.top + mainChartHeight + 15})`}>
                <rect x={padding.left} y="0" width={chartWidth} height="70" fill="#080e18" rx="6" stroke="#172638" />
                {/* 70 overbought line */}
                <line x1={padding.left} y1="21" x2={padding.left + chartWidth} y2="21" stroke="#f43f5e" strokeDasharray="3 3" opacity="0.5" />
                <text x={padding.left - 6} y="24" fill="#f43f5e" fontSize="9" textAnchor="end">70</text>
                {/* 30 oversold line */}
                <line x1={padding.left} y1="49" x2={padding.left + chartWidth} y2="49" stroke="#10b981" strokeDasharray="3 3" opacity="0.5" />
                <text x={padding.left - 6} y="52" fill="#10b981" fontSize="9" textAnchor="end">30</text>
                {/* 50 midpoint */}
                <line x1={padding.left} y1="35" x2={padding.left + chartWidth} y2="35" stroke="#1e2f42" strokeDasharray="2 2" />

                {/* RSI Path */}
                {(() => {
                  let rsiPath = "";
                  let started = false;
                  chartData.points.forEach((pt) => {
                    const r = pt.tech?.rsi_14;
                    if (r !== null && r !== undefined && !isNaN(r)) {
                      // Map 0..100 to 70..0 px
                      const ry = 70 - (r / 100.0) * 70;
                      if (!started) {
                        rsiPath += `M ${pt.x} ${ry}`;
                        started = true;
                      } else {
                        rsiPath += ` L ${pt.x} ${ry}`;
                      }
                    }
                  });
                  return rsiPath ? <path d={rsiPath} fill="none" stroke="#71d5b3" strokeWidth="1.8" /> : null;
                })()}
                <text x={padding.left + 8} y="15" fill="#60768e" fontSize="10" fontWeight="bold">RSI (14) - Wilder Smoothing</text>
              </g>
            )}

            {subChart === "macd" && (
              <g transform={`translate(0, ${padding.top + mainChartHeight + 15})`}>
                <rect x={padding.left} y="0" width={chartWidth} height="70" fill="#080e18" rx="6" stroke="#172638" />
                {/* Zero line */}
                <line x1={padding.left} y1="35" x2={padding.left + chartWidth} y2="35" stroke="#233549" strokeWidth="1" />
                {/* MACD Histogram Bars and Lines */}
                {(() => {
                  // Find range of MACD values
                  let maxAbs = 5.0;
                  chartData.points.forEach((pt) => {
                    const l = pt.tech?.macd_line;
                    const s = pt.tech?.macd_signal;
                    if (l !== null && l !== undefined) maxAbs = Math.max(maxAbs, Math.abs(l));
                    if (s !== null && s !== undefined) maxAbs = Math.max(maxAbs, Math.abs(s));
                  });
                  maxAbs = maxAbs * 1.1;

                  let macdLinePath = "";
                  let signalLinePath = "";
                  let startedM = false;
                  let startedS = false;

                  const bars = chartData.points.map((pt, i) => {
                    const h = pt.tech?.macd_hist;
                    const m = pt.tech?.macd_line;
                    const s = pt.tech?.macd_signal;

                    if (m !== null && m !== undefined && !isNaN(m)) {
                      const my = 35 - (m / maxAbs) * 32;
                      if (!startedM) { macdLinePath += `M ${pt.x} ${my}`; startedM = true; }
                      else { macdLinePath += ` L ${pt.x} ${my}`; }
                    }

                    if (s !== null && s !== undefined && !isNaN(s)) {
                      const sy = 35 - (s / maxAbs) * 32;
                      if (!startedS) { signalLinePath += `M ${pt.x} ${sy}`; startedS = true; }
                      else { signalLinePath += ` L ${pt.x} ${sy}`; }
                    }

                    if (h !== null && h !== undefined && !isNaN(h)) {
                      const barH = (Math.abs(h) / maxAbs) * 32;
                      const barY = h >= 0 ? 35 - barH : 35;
                      const fill = h >= 0 ? "#10b981" : "#f43f5e";
                      return (
                        <rect
                          key={i}
                          x={pt.x - 1}
                          y={barY}
                          width={Math.max(1.5, chartWidth / chartData.points.length - 1)}
                          height={Math.max(1, barH)}
                          fill={fill}
                          opacity={0.7}
                        />
                      );
                    }
                    return null;
                  });

                  return (
                    <>
                      {bars}
                      {macdLinePath && <path d={macdLinePath} fill="none" stroke="#38bdf8" strokeWidth="1.5" />}
                      {signalLinePath && <path d={signalLinePath} fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="2 2" />}
                    </>
                  );
                })()}
                <text x={padding.left + 8} y="15" fill="#60768e" fontSize="10" fontWeight="bold">MACD (12, 26, 9)</text>
              </g>
            )}

            {/* Invisible Hit Zones for Hover Inspection */}
            {chartData.points.map((pt, idx) => (
              <rect
                key={idx}
                x={pt.x - (chartWidth / chartData.points.length) / 2}
                y={padding.top}
                width={chartWidth / chartData.points.length}
                height={mainChartHeight + subChartHeight + 20}
                fill="transparent"
                onMouseEnter={() => setHoverIndex(idx)}
              />
            ))}

            {/* Hover Vertical Guide Line */}
            {activePoint && (
              <g>
                <line
                  x1={activePoint.x}
                  y1={padding.top}
                  x2={activePoint.x}
                  y2={padding.top + mainChartHeight + (subChart !== "none" ? subChartHeight + 15 : 0)}
                  stroke="#71d5b3"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                  opacity="0.8"
                />
                <circle
                  cx={activePoint.x}
                  cy={activePoint.y}
                  r="4.5"
                  fill="#71d5b3"
                  stroke="#0f1927"
                  strokeWidth="2"
                />
              </g>
            )}

            {/* X-Axis Date markers */}
            {chartData.points.length > 1 && (
              <g transform={`translate(0, ${padding.top + mainChartHeight + (subChart !== "none" ? subChartHeight + 25 : 0)})`}>
                <text x={chartData.points[0].x} y="18" fill="#5b6f84" fontSize="10">
                  {chartData.points[0].data.trade_date}
                </text>
                <text
                  x={chartData.points[Math.floor(chartData.points.length / 2)].x}
                  y="18"
                  fill="#5b6f84"
                  fontSize="10"
                  textAnchor="middle"
                >
                  {chartData.points[Math.floor(chartData.points.length / 2)].data.trade_date}
                </text>
                <text
                  x={chartData.points[chartData.points.length - 1].x}
                  y="18"
                  fill="#5b6f84"
                  fontSize="10"
                  textAnchor="end"
                >
                  {chartData.points[chartData.points.length - 1].data.trade_date}
                </text>
              </g>
            )}
          </svg>
        ) : (
          <div className="h-64 flex items-center justify-center text-xs text-[#62778f]">
            No historical price records available for this instrument.
          </div>
        )}
      </div>

      {/* Summary Statistics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs border-t border-[#182536]">
        <div className="p-2.5 rounded-lg bg-[#09111c] border border-[#1b293a]">
          <span className="text-[10px] text-[#6b7e93] block">Period Range High</span>
          <strong className="text-[#edf3fa] font-mono">₹{stats.high.toFixed(2)}</strong>
        </div>
        <div className="p-2.5 rounded-lg bg-[#09111c] border border-[#1b293a]">
          <span className="text-[10px] text-[#6b7e93] block">Period Range Low</span>
          <strong className="text-[#edf3fa] font-mono">₹{stats.low.toFixed(2)}</strong>
        </div>
        <div className="p-2.5 rounded-lg bg-[#09111c] border border-[#1b293a]">
          <span className="text-[10px] text-[#6b7e93] block">Average Daily Volume</span>
          <strong className="text-[#edf3fa] font-mono">{stats.avgVolume.toLocaleString("en-IN")}</strong>
        </div>
        <div className="p-2.5 rounded-lg bg-[#09111c] border border-[#1b293a]">
          <span className="text-[10px] text-[#6b7e93] block">Data Source</span>
          <strong className="text-[#71d5b3] font-mono text-[11px] truncate block" title={dataSource || "Demo Synthetic Provider"}>
            {dataSource || "demo_synthetic"}
          </strong>
        </div>
      </div>
    </div>
  );
}
