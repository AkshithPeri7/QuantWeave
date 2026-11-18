"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  Briefcase,
  PieChart,
  Newspaper,
  FlaskConical,
  Bot,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  ChevronRight,
  Layers,
  Activity,
  Sparkles,
  BarChart3,
  Scale,
  LineChart,
  Search,
  Database,
  Cpu,
  Lock,
  Menu,
  X,
  ExternalLink,
  Code2,
  Sliders,
  AlertTriangle,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function HomePage() {
  const { user } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeHeroTab, setActiveHeroTab] = useState<"terminal" | "nodes" | "technicals">("terminal");

  // Helper for auth-gated links
  const getModuleHref = (path: string) => {
    return user ? path : `/login?next=${encodeURIComponent(path)}`;
  };

  return (
    <div className="min-h-screen bg-[#080D19] text-[#F2F4FF] selection:bg-[#8E91FF]/30 selection:text-[#F2F4FF]">
      {/* SECTION 1: Sticky Navigation Bar */}
      <header className="sticky top-0 z-50 bg-[#080D19]/90 backdrop-blur-xl border-b border-[#26344A]">
        <div className="shell flex items-center justify-between h-20">
          {/* Brand Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#8E91FF] via-[#54DCC5] to-[#F6BE76] p-[1.5px] shadow-lg shadow-[#8E91FF]/20">
              <div className="w-full h-full bg-[#080D19] rounded-[9px] flex items-center justify-center font-black text-sm text-[#8E91FF] font-mono group-hover:scale-105 transition-transform">
                QW
              </div>
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-lg tracking-tight text-[#F2F4FF]">
                QuantWeave
              </span>
              <span className="text-[10px] tracking-widest text-[#54DCC5] uppercase font-mono font-bold">
                Signal Loom
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-[#A6B6CC]">
            <a href="#platform" className="hover:text-[#8E91FF] transition-colors">
              Platform
            </a>
            <a href="#capabilities" className="hover:text-[#8E91FF] transition-colors">
              Capabilities
            </a>
            <a href="#how-it-works" className="hover:text-[#8E91FF] transition-colors">
              How It Works
            </a>
            <a href="#technology" className="hover:text-[#8E91FF] transition-colors">
              Technology
            </a>
            <a href="#responsible" className="hover:text-[#8E91FF] transition-colors">
              Research Standards
            </a>
          </nav>

          {/* Auth Action Buttons */}
          <div className="hidden sm:flex items-center gap-3">
            {user ? (
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#8E91FF] hover:bg-[#7b7eff] text-[#080D19] font-bold text-xs transition-colors shadow-lg shadow-[#8E91FF]/20"
              >
                <span>Open Terminal</span>
                <ArrowRight size={14} />
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-[#A6B6CC] hover:text-[#F2F4FF] hover:bg-[#101A2B] border border-transparent hover:border-[#26344A] transition-all"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#8E91FF] hover:bg-[#7b7eff] text-[#080D19] font-bold text-xs transition-colors shadow-lg shadow-[#8E91FF]/20"
                >
                  <span>Get Started</span>
                  <ArrowRight size={14} />
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-[#A6B6CC] hover:text-[#F2F4FF] hover:bg-[#101A2B]"
            aria-label="Toggle mobile menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#101A2B] border-b border-[#26344A] px-6 py-4 space-y-3 animate-in fade-in">
            <a
              href="#platform"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-xs font-semibold text-[#A6B6CC] hover:text-[#F2F4FF]"
            >
              Platform
            </a>
            <a
              href="#capabilities"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-xs font-semibold text-[#A6B6CC] hover:text-[#F2F4FF]"
            >
              Capabilities
            </a>
            <a
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-xs font-semibold text-[#A6B6CC] hover:text-[#F2F4FF]"
            >
              How It Works
            </a>
            <a
              href="#technology"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-xs font-semibold text-[#A6B6CC] hover:text-[#F2F4FF]"
            >
              Technology
            </a>
            <div className="pt-3 border-t border-[#26344A] flex flex-col gap-2">
              {user ? (
                <Link
                  href="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 rounded-xl bg-[#8E91FF] text-[#080D19] font-bold text-xs"
                >
                  Open Terminal
                </Link>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2 rounded-xl bg-[#142035] text-xs font-semibold text-[#F2F4FF]"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/register"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2.5 rounded-xl bg-[#8E91FF] text-[#080D19] font-bold text-xs"
                  >
                    Get Started Free
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* SECTION 2: Premium Hero with Signal Loom Visual Motif */}
      <section className="relative pt-16 sm:pt-24 pb-20 overflow-hidden border-b border-[#26344A]">
        {/* Subtle SVG Grid Background */}
        <div className="absolute inset-0 pointer-events-none opacity-20">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid-pattern" width="48" height="48" patternUnits="userSpaceOnUse">
                <path d="M 48 0 L 0 0 0 48" fill="none" stroke="#26344A" strokeWidth="0.8" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid-pattern)" />
          </svg>
        </div>

        <div className="shell relative z-10">
          <div className="max-w-3xl mx-auto text-center space-y-6">
            {/* Pill badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#8E91FF]/10 border border-[#8E91FF]/30 text-xs font-mono font-semibold text-[#8E91FF] shimmer-badge">
              <span className="w-2 h-2 rounded-full bg-[#54DCC5] animate-ping" />
              QUANTITATIVE RESEARCH WORKSPACE • SIGNAL LOOM
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight leading-[1.1] text-[#F2F4FF]">
              Financial intelligence, <br />
              <span className="bg-gradient-to-r from-[#8E91FF] via-[#54DCC5] to-[#F6BE76] bg-clip-text text-transparent">
                woven together.
              </span>
            </h1>

            {/* Supporting Description */}
            <p className="text-sm sm:text-base md:text-lg text-[#A6B6CC] leading-relaxed max-w-2xl mx-auto font-normal">
              QuantWeave brings equity research, portfolio intelligence, mutual fund analytics, market news, quantitative backtesting, and AI-assisted insights into one connected financial research platform.
            </p>

            {/* Hero CTAs */}
            <div className="flex flex-wrap items-center justify-center gap-3.5 pt-2">
              <Link
                href={user ? "/dashboard" : "/register"}
                className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-[#8E91FF] hover:bg-[#7b7eff] text-[#080D19] font-black text-xs sm:text-sm transition-all shadow-xl shadow-[#8E91FF]/25 hover:scale-102"
              >
                <span>{user ? "Enter Research Terminal" : "Start Free Research"}</span>
                <ArrowRight size={16} />
              </Link>
              <Link
                href={user ? "/profile" : "/login"}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#101A2B] hover:bg-[#142035] text-xs sm:text-sm font-bold text-[#F2F4FF] border border-[#26344A] hover:border-[#8E91FF]/50 transition-all"
              >
                <span>{user ? "View My Profile" : "Sign In to Workspace"}</span>
              </Link>
            </div>

            {/* Trust & Provenance Bar */}
            <div className="pt-4 flex flex-wrap items-center justify-center gap-6 text-[11px] text-[#A6B6CC]/70 font-mono">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 size={13} className="text-[#54DCC5]" />
                Deterministic Analytics
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 size={13} className="text-[#8E91FF]" />
                Zero Hallucinated Metrics
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 size={13} className="text-[#F6BE76]" />
                Synthetic & Reference NSE Data
              </span>
            </div>
          </div>

          {/* Interactive Connected Terminal Preview Card */}
          <div className="mt-14 max-w-5xl mx-auto animate-float">
            <div className="rounded-2xl bg-[#101A2B] border border-[#26344A] shadow-2xl shadow-black/80 overflow-hidden">
              {/* Window Header */}
              <div className="px-5 py-3 border-b border-[#26344A] bg-[#0c1422] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-rose-500/80" />
                  <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="ml-3 text-[11px] font-mono text-[#A6B6CC] hidden sm:inline">
                    terminal.quantweave.local — Active Session
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[10px] font-mono text-[#54DCC5] bg-[#54DCC5]/10 px-2.5 py-0.5 rounded-full border border-[#54DCC5]/30">
                  <Activity size={12} className="animate-pulse" />
                  <span>ALL ENGINES SYNCHRONIZED</span>
                </div>
              </div>

              {/* Terminal Body */}
              <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* Metric 1: Equity Matrix */}
                <div className="p-4 rounded-xl bg-[#080D19] border border-[#26344A] space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#8E91FF] font-bold flex items-center gap-1.5">
                      <TrendingUp size={14} /> NSE Reference Equities
                    </span>
                    <span className="text-[10px] text-[#A6B6CC]">1D Close</span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center py-1 border-b border-[#26344A]/60">
                      <span className="font-mono font-bold text-[#F2F4FF]">RELIANCE</span>
                      <span className="text-[#54DCC5] font-mono tabular-nums font-semibold">₹2,845.50 (+1.4%)</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-[#26344A]/60">
                      <span className="font-mono font-bold text-[#F2F4FF]">TCS</span>
                      <span className="text-[#54DCC5] font-mono tabular-nums font-semibold">₹3,920.00 (+0.8%)</span>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span className="font-mono font-bold text-[#F2F4FF]">HDFCBANK</span>
                      <span className="text-[#F6BE76] font-mono tabular-nums font-semibold">₹1,680.20 (+0.1%)</span>
                    </div>
                  </div>
                </div>

                {/* Metric 2: QuantLab Backtest Engine */}
                <div className="p-4 rounded-xl bg-[#080D19] border border-[#26344A] space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#54DCC5] font-bold flex items-center gap-1.5">
                      <FlaskConical size={14} /> QuantLab Simulation
                    </span>
                    <span className="text-[10px] text-[#54DCC5]">Verified</span>
                  </div>
                  <div className="space-y-2 text-xs font-mono">
                    <div className="flex justify-between items-center py-1 border-b border-[#26344A]/60">
                      <span className="text-[#A6B6CC]">Algorithm:</span>
                      <span className="text-[#F2F4FF] font-semibold">SMA (10/30) Cross</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-[#26344A]/60">
                      <span className="text-[#A6B6CC]">Sharpe Ratio:</span>
                      <span className="text-[#54DCC5] font-bold tabular-nums">1.68</span>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span className="text-[#A6B6CC]">Max Drawdown:</span>
                      <span className="text-[#F6BE76] font-bold tabular-nums">-8.4%</span>
                    </div>
                  </div>
                </div>

                {/* Metric 3: AI Copilot Grounding */}
                <div className="p-4 rounded-xl bg-[#080D19] border border-[#26344A] space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#F6BE76] font-bold flex items-center gap-1.5">
                      <Bot size={14} /> Grounded Copilot
                    </span>
                    <span className="text-[10px] text-[#8E91FF]">RAG Active</span>
                  </div>
                  <p className="text-xs text-[#A6B6CC] leading-relaxed">
                    &quot;TCS RSI Wilder indicator is at <strong className="text-[#54DCC5]">58.4</strong>. Operating margin is <strong className="text-[#F2F4FF]">24.8%</strong> with zero short-term debt.&quot;
                  </p>
                  <div className="text-[10px] text-[#A6B6CC]/70 font-mono flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#8E91FF]" />
                    Source: Verified Fixtures & Ledger
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 3: What is QuantWeave? (Split Layout with Connected Graphic) */}
      <section id="platform" className="py-20 border-b border-[#26344A] bg-[#080D19]">
        <div className="shell grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left: Narrative */}
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-0.5 rounded-full bg-[#54DCC5]/10 border border-[#54DCC5]/30 text-xs font-mono font-semibold text-[#54DCC5]">
              PRODUCT INTRODUCTION
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#F2F4FF] leading-tight">
              One connected workspace for modern quantitative intelligence.
            </h2>
            <p className="text-sm sm:text-base text-[#A6B6CC] leading-relaxed">
              Financial research often requires switching between market charts, company reports, portfolio spreadsheets, news feeds, and strategy-testing tools. QuantWeave brings these workflows together in a single platform where financial data, quantitative calculations, and AI-assisted explanations work side by side.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="p-3.5 rounded-xl bg-[#101A2B] border border-[#26344A] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#8E91FF]/10 text-[#8E91FF] flex items-center justify-center font-bold">
                  1
                </div>
                <span className="text-xs font-semibold text-[#F2F4FF]">Equity Research</span>
              </div>
              <div className="p-3.5 rounded-xl bg-[#101A2B] border border-[#26344A] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#54DCC5]/10 text-[#54DCC5] flex items-center justify-center font-bold">
                  2
                </div>
                <span className="text-xs font-semibold text-[#F2F4FF]">Portfolio Accounting</span>
              </div>
              <div className="p-3.5 rounded-xl bg-[#101A2B] border border-[#26344A] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#F6BE76]/10 text-[#F6BE76] flex items-center justify-center font-bold">
                  3
                </div>
                <span className="text-xs font-semibold text-[#F2F4FF]">Mutual Fund Analytics</span>
              </div>
              <div className="p-3.5 rounded-xl bg-[#101A2B] border border-[#26344A] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#8E91FF]/10 text-[#8E91FF] flex items-center justify-center font-bold">
                  4
                </div>
                <span className="text-xs font-semibold text-[#F2F4FF]">Strategy Backtesting</span>
              </div>
            </div>
          </div>

          {/* Right: Signal Loom System Illustration */}
          <div className="p-6 sm:p-8 rounded-2xl bg-[#101A2B] border border-[#26344A] relative overflow-hidden">
            <div className="text-xs font-mono text-[#8E91FF] font-bold mb-4 uppercase tracking-wider flex items-center gap-2">
              <Layers size={14} /> Connected Research Nodes
            </div>

            {/* Interwoven Node Graphic */}
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-[#080D19] border border-[#26344A] flex items-start gap-4">
                <div className="w-9 h-9 rounded-xl bg-[#8E91FF]/10 text-[#8E91FF] flex items-center justify-center flex-shrink-0 font-mono font-bold text-xs">
                  EQ
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#F2F4FF]">Equity Intelligence Engine</h4>
                  <p className="text-[11px] text-[#A6B6CC] mt-0.5">
                    Parses NSE reference daily OHLCV prices, calculates 5 deterministic indicators, and compiles balance sheets.
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#080D19] border border-[#26344A] flex items-start gap-4">
                <div className="w-9 h-9 rounded-xl bg-[#54DCC5]/10 text-[#54DCC5] flex items-center justify-center flex-shrink-0 font-mono font-bold text-xs">
                  PF
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#F2F4FF]">Double-Entry Portfolio Ledger</h4>
                  <p className="text-[11px] text-[#A6B6CC] mt-0.5">
                    Records idempotent trades, computes weighted average cost basis (WACB), and solves Newton-Raphson XIRR.
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#080D19] border border-[#26344A] flex items-start gap-4">
                <div className="w-9 h-9 rounded-xl bg-[#F6BE76]/10 text-[#F6BE76] flex items-center justify-center flex-shrink-0 font-mono font-bold text-xs">
                  QL
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#F2F4FF]">QuantLab Simulation Framework</h4>
                  <p className="text-[11px] text-[#A6B6CC] mt-0.5">
                    Simulates next-bar execution with fee and slippage models, eliminating lookahead bias.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: Six Connected Research Capabilities (Distinct Sections) */}
      <section id="capabilities" className="py-20 border-b border-[#26344A] space-y-16">
        <div className="shell text-center max-w-2xl mx-auto space-y-3">
          <span className="text-[10px] font-bold tracking-widest text-[#8E91FF] uppercase font-mono bg-[#8E91FF]/10 px-3 py-1 rounded-full border border-[#8E91FF]/30">
            SYSTEM ARCHITECTURE
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F2F4FF] tracking-tight">
            Six Specialized Research Modules
          </h2>
          <p className="text-xs sm:text-sm text-[#A6B6CC]">
            Each module is tailored to a distinct stage of quantitative analysis, connected through shared data structures.
          </p>
        </div>

        {/* Capability 1: Equity Intelligence */}
        <div className="shell grid grid-cols-1 lg:grid-cols-2 gap-8 items-center signal-card p-6 sm:p-10">
          <div className="space-y-4">
            <span className="text-[10px] font-bold font-mono text-[#8E91FF] uppercase tracking-wider">
              Module 01 • Fundamental & Technical Core
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-[#F2F4FF]">
              Equity Intelligence
            </h3>
            <p className="text-xs sm:text-sm text-[#A6B6CC] leading-relaxed">
              Explore company fundamentals, historical market prices, technical indicators, and peer comparisons through a unified equity research workspace.
            </p>
            <ul className="space-y-2 text-xs text-[#A6B6CC] pt-2">
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Stock search across NSE reference securities</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Deterministic SMA, EMA, Wilder RSI, MACD, and Bollinger Bands</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Synthetic financial statement ratios (P/E, P/B, ROE, Debt/Equity)</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Side-by-side multi-company technical and valuation comparison</span>
              </li>
            </ul>
            <div className="pt-2">
              <Link
                href={getModuleHref("/equity")}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#8E91FF] hover:bg-[#7b7eff] text-[#080D19] font-bold text-xs transition-colors"
              >
                <span>Explore Equity Intelligence</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
          <div className="p-5 rounded-xl bg-[#080D19] border border-[#26344A] space-y-3 font-mono text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-[#26344A]">
              <span className="font-bold text-[#F2F4FF]">RELIANCE • NSE</span>
              <span className="text-[#54DCC5]">₹2,845.50</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2.5 rounded bg-[#101A2B]">RSI (14): <strong className="text-[#54DCC5]">61.2</strong></div>
              <div className="p-2.5 rounded bg-[#101A2B]">SMA (20): <strong className="text-[#F2F4FF]">₹2,810.00</strong></div>
              <div className="p-2.5 rounded bg-[#101A2B]">MACD Hist: <strong className="text-[#54DCC5]">+14.20</strong></div>
              <div className="p-2.5 rounded bg-[#101A2B]">P/E Ratio: <strong className="text-[#F6BE76]">24.8x</strong></div>
            </div>
          </div>
        </div>

        {/* Capability 2: Portfolio Intelligence */}
        <div className="shell grid grid-cols-1 lg:grid-cols-2 gap-8 items-center signal-card p-6 sm:p-10">
          <div className="order-2 lg:order-1 p-5 rounded-xl bg-[#080D19] border border-[#26344A] space-y-3 font-mono text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-[#26344A]">
              <span className="font-bold text-[#F2F4FF]">Portfolio Valuation Ledger</span>
              <span className="text-[#54DCC5] font-bold">₹1,248,500.00</span>
            </div>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between py-1 border-b border-[#26344A]/60">
                <span className="text-[#A6B6CC]">Invested Capital:</span>
                <span className="text-[#F2F4FF]">₹1,000,000.00</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#26344A]/60">
                <span className="text-[#A6B6CC]">Unrealized Profit:</span>
                <span className="text-[#54DCC5] font-bold">+₹248,500.00 (+24.85%)</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[#A6B6CC]">Extended IRR (XIRR):</span>
                <span className="text-[#54DCC5] font-bold">18.42% p.a.</span>
              </div>
            </div>
          </div>
          <div className="order-1 lg:order-2 space-y-4">
            <span className="text-[10px] font-bold font-mono text-[#54DCC5] uppercase tracking-wider">
              Module 02 • Accounting & Risk Ledger
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-[#F2F4FF]">
              Portfolio Intelligence
            </h3>
            <p className="text-xs sm:text-sm text-[#A6B6CC] leading-relaxed">
              Understand your investments using transaction-based accounting, portfolio valuation, allocation analysis, and measurable risk statistics.
            </p>
            <ul className="space-y-2 text-xs text-[#A6B6CC] pt-2">
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Strict double-entry transaction ledger (BUY, SELL, CASH, DIVIDEND)</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Weighted Average Cost Basis (WACB) calculation without overselling</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Time-Weighted Return (TWR) and Exact Newton-Raphson XIRR</span>
              </li>
            </ul>
            <div className="pt-2">
              <Link
                href={getModuleHref("/portfolio")}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#54DCC5] hover:bg-[#46c2ad] text-[#080D19] font-bold text-xs transition-colors"
              >
                <span>Explore Portfolio Intelligence</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </div>

        {/* Capability 3: FundScope */}
        <div className="shell grid grid-cols-1 lg:grid-cols-2 gap-8 items-center signal-card p-6 sm:p-10">
          <div className="space-y-4">
            <span className="text-[10px] font-bold font-mono text-[#F6BE76] uppercase tracking-wider">
              Module 03 • Mutual Fund Intelligence
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-[#F2F4FF]">
              FundScope
            </h3>
            <p className="text-xs sm:text-sm text-[#A6B6CC] leading-relaxed">
              Research mutual funds with historical NAV analytics, SIP simulations, risk analysis, and multi-fund performance comparisons.
            </p>
            <ul className="space-y-2 text-xs text-[#A6B6CC] pt-2">
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#F6BE76]" />
                <span>Fund directory across Equity, Debt, and Hybrid categories</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#F6BE76]" />
                <span>Historical NAV charts with 1M, 3M, 6M, 1Y, and 2Y periods</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#F6BE76]" />
                <span>SIP and lump-sum compounding simulations</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#F6BE76]" />
                <span>Direct vs Regular plan transparent comparisons</span>
              </li>
            </ul>
            <div className="pt-2">
              <Link
                href={getModuleHref("/funds")}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#F6BE76] hover:bg-[#e4aa5f] text-[#080D19] font-bold text-xs transition-colors"
              >
                <span>Explore FundScope</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
          <div className="p-5 rounded-xl bg-[#080D19] border border-[#26344A] space-y-3 font-mono text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-[#26344A]">
              <span className="font-bold text-[#F2F4FF]">SIP Simulation (₹5,000 / mo)</span>
              <span className="text-[#54DCC5]">CAGR: 16.4%</span>
            </div>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between py-1 border-b border-[#26344A]/60">
                <span className="text-[#A6B6CC]">Duration:</span>
                <span className="text-[#F2F4FF]">12 Installments</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#26344A]/60">
                <span className="text-[#A6B6CC]">Total Invested:</span>
                <span className="text-[#F2F4FF]">₹60,000.00</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[#A6B6CC]">Final Market Value:</span>
                <span className="text-[#54DCC5] font-bold">₹65,240.00</span>
              </div>
            </div>
          </div>
        </div>

        {/* Capability 4: MarketPulse */}
        <div className="shell grid grid-cols-1 lg:grid-cols-2 gap-8 items-center signal-card p-6 sm:p-10">
          <div className="order-2 lg:order-1 p-5 rounded-xl bg-[#080D19] border border-[#26344A] space-y-3 text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-[#26344A] font-mono">
              <span className="font-bold text-[#F2F4FF]">Live Financial News Wire</span>
              <span className="text-[#8E91FF]">MarketPulse</span>
            </div>
            <div className="space-y-2">
              <div className="p-2.5 rounded bg-[#101A2B] border border-[#26344A]/60 space-y-1">
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-[#54DCC5] font-bold">RELIANCE</span>
                  <span className="text-[#54DCC5] bg-[#54DCC5]/10 px-1.5 py-0.5 rounded">POSITIVE (0.78)</span>
                </div>
                <p className="text-[11px] text-[#F2F4FF]">Jio Financial reports expansion into retail asset management.</p>
              </div>
              <div className="p-2.5 rounded bg-[#101A2B] border border-[#26344A]/60 space-y-1">
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-[#A6B6CC]">MACRO</span>
                  <span className="text-[#F6BE76] bg-[#F6BE76]/10 px-1.5 py-0.5 rounded">NEUTRAL (0.05)</span>
                </div>
                <p className="text-[11px] text-[#F2F4FF]">RBI keeps repo rate unchanged at 6.50% citing retail inflation alignment.</p>
              </div>
            </div>
          </div>
          <div className="order-1 lg:order-2 space-y-4">
            <span className="text-[10px] font-bold font-mono text-[#8E91FF] uppercase tracking-wider">
              Module 04 • News, Macro & Sentiment Wire
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-[#F2F4FF]">
              MarketPulse
            </h3>
            <p className="text-xs sm:text-sm text-[#A6B6CC] leading-relaxed">
              Connect financial news, company events, market sentiment, macroeconomic indicators, and personalized watchlists in one research feed.
            </p>
            <div className="p-2.5 rounded-lg bg-[#F6BE76]/10 border border-[#F6BE76]/30 text-[11px] text-[#F6BE76] flex items-center gap-2">
              <AlertTriangle size={14} className="flex-shrink-0" />
              <span>Sentiment scores are research estimates, not predictions of future returns.</span>
            </div>
            <ul className="space-y-2 text-xs text-[#A6B6CC] pt-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#8E91FF]" />
                <span>Company-linked news discovery</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#8E91FF]" />
                <span>Macroeconomic series: CPI inflation, RBI repo rate, GDP growth</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#8E91FF]" />
                <span>Personalized ticker watchlists and sentiment notifications</span>
              </li>
            </ul>
            <div className="pt-2">
              <Link
                href={getModuleHref("/market")}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#8E91FF] hover:bg-[#7b7eff] text-[#080D19] font-bold text-xs transition-colors"
              >
                <span>Explore MarketPulse</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </div>

        {/* Capability 5: QuantLab */}
        <div className="shell grid grid-cols-1 lg:grid-cols-2 gap-8 items-center signal-card p-6 sm:p-10">
          <div className="space-y-4">
            <span className="text-[10px] font-bold font-mono text-[#54DCC5] uppercase tracking-wider">
              Module 05 • Simulation & Backtest Lab
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-[#F2F4FF]">
              QuantLab
            </h3>
            <p className="text-xs sm:text-sm text-[#A6B6CC] leading-relaxed">
              Explore quantitative ideas through historical strategy simulations, transparent execution assumptions, risk analysis, and parameter experiments.
            </p>
            <div className="p-2.5 rounded-lg bg-[#54DCC5]/10 border border-[#54DCC5]/30 text-[11px] text-[#54DCC5] flex items-center gap-2">
              <ShieldCheck size={14} className="flex-shrink-0" />
              <span>QuantLab is a historical research environment, not a real-money trading engine.</span>
            </div>
            <ul className="space-y-2 text-xs text-[#A6B6CC] pt-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>SMA, EMA, RSI, and Buy-and-Hold strategies</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Next-bar execution prevents lookahead bias</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Realistic friction: brokerage commission and basis-point slippage</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#54DCC5]" />
                <span>Grid search parameter optimization with in-sample/out-of-sample split</span>
              </li>
            </ul>
            <div className="pt-2">
              <Link
                href={getModuleHref("/quantlab")}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#54DCC5] hover:bg-[#46c2ad] text-[#080D19] font-bold text-xs transition-colors"
              >
                <span>Launch QuantLab Simulator</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
          <div className="p-5 rounded-xl bg-[#080D19] border border-[#26344A] space-y-3 font-mono text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-[#26344A]">
              <span className="font-bold text-[#F2F4FF]">Strategy Performance Metrics</span>
              <span className="text-[#54DCC5]">Verified Run</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2.5 rounded bg-[#101A2B]">Total Return: <strong className="text-[#54DCC5]">+34.8%</strong></div>
              <div className="p-2.5 rounded bg-[#101A2B]">Sharpe Ratio: <strong className="text-[#54DCC5]">1.82</strong></div>
              <div className="p-2.5 rounded bg-[#101A2B]">Sortino Ratio: <strong className="text-[#54DCC5]">2.41</strong></div>
              <div className="p-2.5 rounded bg-[#101A2B]">Max Drawdown: <strong className="text-[#F6BE76]">-6.5%</strong></div>
            </div>
            <div className="p-2 rounded bg-[#142035] text-[10px] text-[#A6B6CC] text-center">
              Walk-forward 70/30 Train/Test Cross-Validation Active
            </div>
          </div>
        </div>

        {/* Capability 6: QuantWeave Copilot */}
        <div className="shell grid grid-cols-1 lg:grid-cols-2 gap-8 items-center signal-card p-6 sm:p-10">
          <div className="order-2 lg:order-1 p-5 rounded-xl bg-[#080D19] border border-[#26344A] space-y-3 text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-[#26344A] font-mono">
              <span className="font-bold text-[#F2F4FF] flex items-center gap-2">
                <Bot size={14} className="text-[#8E91FF]" />
                Copilot Grounded Turn
              </span>
              <span className="text-[#54DCC5] font-mono text-[10px]">Deterministic RAG</span>
            </div>
            <div className="p-3 rounded-lg bg-[#101A2B] border border-[#26344A] space-y-2">
              <div className="text-[10px] font-mono text-[#8E91FF] flex items-center gap-1">
                <Code2 size={12} /> Executing: tools.get_equity_technicals(symbol=&quot;TCS&quot;)
              </div>
              <p className="text-[11px] text-[#A6B6CC] leading-relaxed">
                &quot;TCS 14-day RSI Wilder smoothing stands at 58.4, within neutral territory. 20-day SMA is ₹3,880.00 versus current close of ₹3,920.00.&quot;
              </p>
              <div className="pt-1 border-t border-[#26344A]/60 flex items-center justify-between text-[10px] font-mono text-[#A6B6CC]/70">
                <span>Provenance: Calculated from NSE OHLCV</span>
                <span className="text-[#54DCC5]">Zero Hallucination</span>
              </div>
            </div>
          </div>
          <div className="order-1 lg:order-2 space-y-4">
            <span className="text-[10px] font-bold font-mono text-[#8E91FF] uppercase tracking-wider">
              Module 06 • Context-Aware Research Assistant
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-[#F2F4FF]">
              QuantWeave Copilot
            </h3>
            <p className="text-xs sm:text-sm text-[#A6B6CC] leading-relaxed">
              Ask financial research questions in natural language and receive explanations grounded in QuantWeave&apos;s existing analytics tools and research sources.
            </p>
            <div className="p-2.5 rounded-lg bg-[#8E91FF]/10 border border-[#8E91FF]/30 text-[11px] text-[#8E91FF] flex items-center gap-2">
              <Sparkles size={14} className="flex-shrink-0" />
              <span>Default local mock provider operates in development and demo mode.</span>
            </div>
            <ul className="space-y-2 text-xs text-[#A6B6CC] pt-1">
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#8E91FF]" />
                <span>Deterministic tool calling across Equities, Funds, and Portfolios</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#8E91FF]" />
                <span>RAG retrieval with source references and methodology citations</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={14} className="text-[#8E91FF]" />
                <span>Prompt injection prevention & strict cross-user data isolation</span>
              </li>
            </ul>
            <div className="pt-2">
              <Link
                href={getModuleHref("/ai")}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#8E91FF] hover:bg-[#7b7eff] text-[#080D19] font-bold text-xs transition-colors"
              >
                <span>Launch AI Copilot</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 5: How QuantWeave Works (4-Step Flow with Animated Weave) */}
      <section id="how-it-works" className="py-20 border-b border-[#26344A] bg-[#080D19]">
        <div className="shell space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <span className="text-[10px] font-bold tracking-widest text-[#54DCC5] uppercase font-mono bg-[#54DCC5]/10 px-3 py-1 rounded-full border border-[#54DCC5]/30">
              METHODOLOGY
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F2F4FF] tracking-tight">
              The Four-Stage Quantitative Workflow
            </h2>
            <p className="text-xs sm:text-sm text-[#A6B6CC]">
              From raw market data ingestion to transparent, AI-assisted explanations.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
            {/* Step 1 */}
            <div className="p-6 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-3 relative group hover:border-[#8E91FF]/50 transition-all">
              <div className="w-10 h-10 rounded-xl bg-[#8E91FF]/10 text-[#8E91FF] flex items-center justify-center font-black font-mono text-sm">
                01
              </div>
              <h3 className="text-base font-bold text-[#F2F4FF]">Discover Data</h3>
              <p className="text-xs text-[#A6B6CC] leading-relaxed">
                Ingest daily equity prices, AMFI mutual fund NAV histories, and macroeconomic observations with verified schemas.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-6 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-3 relative group hover:border-[#54DCC5]/50 transition-all">
              <div className="w-10 h-10 rounded-xl bg-[#54DCC5]/10 text-[#54DCC5] flex items-center justify-center font-black font-mono text-sm">
                02
              </div>
              <h3 className="text-base font-bold text-[#F2F4FF]">Analyze Risk</h3>
              <p className="text-xs text-[#A6B6CC] leading-relaxed">
                Compute deterministic indicators, weighted cost-basis allocations, underwater drawdowns, and portfolio Sharpe ratios.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-6 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-3 relative group hover:border-[#F6BE76]/50 transition-all">
              <div className="w-10 h-10 rounded-xl bg-[#F6BE76]/10 text-[#F6BE76] flex items-center justify-center font-black font-mono text-sm">
                03
              </div>
              <h3 className="text-base font-bold text-[#F2F4FF]">Experiment Models</h3>
              <p className="text-xs text-[#A6B6CC] leading-relaxed">
                Simulate quantitative strategies with next-bar execution, fees, slippage, and walk-forward cross-validation.
              </p>
            </div>

            {/* Step 4 */}
            <div className="p-6 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-3 relative group hover:border-[#8E91FF]/50 transition-all">
              <div className="w-10 h-10 rounded-xl bg-[#8E91FF]/10 text-[#8E91FF] flex items-center justify-center font-black font-mono text-sm">
                04
              </div>
              <h3 className="text-base font-bold text-[#F2F4FF]">Explain Insights</h3>
              <p className="text-xs text-[#A6B6CC] leading-relaxed">
                Interact with the AI Copilot to interpret complex calculations, compare peers, and inspect execution ledgers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 6: Technology and Architecture */}
      <section id="technology" className="py-20 border-b border-[#26344A] bg-[#0c1422]/60">
        <div className="shell space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <span className="text-[10px] font-bold tracking-widest text-[#8E91FF] uppercase font-mono bg-[#8E91FF]/10 px-3 py-1 rounded-full border border-[#8E91FF]/30">
              STACK VERIFICATION
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F2F4FF] tracking-tight">
              Production Architecture & Rigorous Engineering
            </h2>
            <p className="text-xs sm:text-sm text-[#A6B6CC]">
              Built with modern, production-grade frameworks with zero fictitious claims.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-5 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-[#8E91FF]">
                <Cpu size={16} /> Frontend Layer
              </div>
              <ul className="text-xs text-[#A6B6CC] space-y-1.5 font-mono">
                <li>• Next.js 15 (App Router)</li>
                <li>• React 19 & TypeScript</li>
                <li>• Tailwind CSS & Signal Loom</li>
                <li>• Edge Route Middleware</li>
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-[#54DCC5]">
                <Database size={16} /> Backend Layer
              </div>
              <ul className="text-xs text-[#A6B6CC] space-y-1.5 font-mono">
                <li>• FastAPI & Python 3.13</li>
                <li>• SQLAlchemy ORM</li>
                <li>• PostgreSQL & SQLite</li>
                <li>• Alembic DB Migrations</li>
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-[#F6BE76]">
                <Sparkles size={16} /> Analytics & Intelligence
              </div>
              <ul className="text-xs text-[#A6B6CC] space-y-1.5 font-mono">
                <li>• Deterministic Indicators</li>
                <li>• Next-Bar Sim Engine</li>
                <li>• Grounded Tool Execution</li>
                <li>• TF-IDF Lexical RAG</li>
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-[#8E91FF]">
                <Lock size={16} /> Security & Hardening
              </div>
              <ul className="text-xs text-[#A6B6CC] space-y-1.5 font-mono">
                <li>• JWT + HttpOnly Cookies</li>
                <li>• Sliding Window Rate Limiter</li>
                <li>• 138/138 Pytest Suite</li>
                <li>• Playwright E2E Specs</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 7: Responsible Research & Disclaimers */}
      <section id="responsible" className="py-16 border-b border-[#26344A] bg-[#080D19]">
        <div className="shell max-w-4xl mx-auto p-6 sm:p-8 rounded-2xl bg-[#101A2B] border border-[#26344A] space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-[#F6BE76] uppercase tracking-wider font-mono">
            <AlertTriangle size={16} />
            Responsible Financial Research Standards
          </div>
          <h3 className="text-lg font-bold text-[#F2F4FF]">
            Educational Scope & Transparent Limitations
          </h3>
          <p className="text-xs text-[#A6B6CC] leading-relaxed">
            QuantWeave is an educational research and quantitative simulation platform. Market data fixtures, mutual fund NAV series, and company financial statements are synthetic or historical reference samples labeled explicitly for academic and demonstration purposes.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-[11px] text-[#A6B6CC] font-mono">
            <div className="p-3 rounded-xl bg-[#080D19] border border-[#26344A]">
              ✓ No live capital or real-money execution
            </div>
            <div className="p-3 rounded-xl bg-[#080D19] border border-[#26344A]">
              ✓ No financial advice or return guarantees
            </div>
            <div className="p-3 rounded-xl bg-[#080D19] border border-[#26344A]">
              ✓ Strict user ledger isolation
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 8: Final Brand Quote Section */}
      <section className="py-24 border-b border-[#26344A] bg-gradient-to-b from-[#080D19] via-[#101A2B] to-[#080D19] relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-gradient-to-r from-[#8E91FF]/15 via-[#54DCC5]/10 to-transparent blur-3xl pointer-events-none rounded-full" />

        <div className="shell relative z-10 max-w-3xl mx-auto text-center space-y-6">
          <span className="text-xs font-mono font-bold text-[#8E91FF] tracking-widest uppercase">
            THE QUANTWEAVE CREED
          </span>

          <blockquote className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#F2F4FF] leading-snug tracking-tight">
            &ldquo;Every meaningful insight begins with a question. Every better decision begins with understanding.&rdquo;
          </blockquote>

          <p className="text-xs sm:text-sm font-mono text-[#54DCC5] font-semibold tracking-wider uppercase">
            QuantWeave — Connect the data. Understand the risk. Make informed decisions.
          </p>

          <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
            <Link
              href={user ? "/dashboard" : "/register"}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#8E91FF] hover:bg-[#7b7eff] text-[#080D19] font-black text-xs sm:text-sm transition-all shadow-xl shadow-[#8E91FF]/25 hover:scale-102"
            >
              <span>{user ? "Open Terminal" : "Start Exploring Now"}</span>
              <ArrowRight size={16} />
            </Link>
            <Link
              href={user ? "/dashboard" : "/login"}
              className="px-6 py-3 rounded-xl bg-[#101A2B] hover:bg-[#142035] text-xs sm:text-sm font-bold text-[#F2F4FF] border border-[#26344A] hover:border-[#8E91FF]/50 transition-all"
            >
              Sign In to Workspace
            </Link>
          </div>
        </div>
      </section>

      {/* SECTION 9: Footer */}
      <footer className="py-12 bg-[#080D19] border-t border-[#26344A]">
        <div className="shell grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-[#8E91FF] to-[#54DCC5] p-[1.5px]">
                <div className="w-full h-full bg-[#080D19] rounded-[6px] flex items-center justify-center font-black text-xs text-[#8E91FF] font-mono">
                  QW
                </div>
              </div>
              <span className="font-extrabold text-base text-[#F2F4FF]">QuantWeave</span>
            </div>
            <p className="text-xs text-[#A6B6CC] leading-relaxed">
              AI-Powered Financial Intelligence & Quantitative Research Platform.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-mono font-bold text-[#8E91FF] uppercase tracking-wider">Platform</h4>
            <ul className="text-xs text-[#A6B6CC] space-y-1.5">
              <li><Link href={getModuleHref("/dashboard")} className="hover:text-[#F2F4FF]">Dashboard</Link></li>
              <li><Link href={getModuleHref("/equity")} className="hover:text-[#F2F4FF]">Equity Intelligence</Link></li>
              <li><Link href={getModuleHref("/portfolio")} className="hover:text-[#F2F4FF]">Portfolio Intelligence</Link></li>
              <li><Link href={getModuleHref("/funds")} className="hover:text-[#F2F4FF]">FundScope</Link></li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-mono font-bold text-[#54DCC5] uppercase tracking-wider">Research</h4>
            <ul className="text-xs text-[#A6B6CC] space-y-1.5">
              <li><Link href={getModuleHref("/quantlab")} className="hover:text-[#F2F4FF]">QuantLab Simulator</Link></li>
              <li><Link href={getModuleHref("/market")} className="hover:text-[#F2F4FF]">MarketPulse News</Link></li>
              <li><Link href={getModuleHref("/ai")} className="hover:text-[#F2F4FF]">QuantWeave AI Copilot</Link></li>
              <li><Link href={getModuleHref("/profile")} className="hover:text-[#F2F4FF]">User Profile</Link></li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-mono font-bold text-[#F6BE76] uppercase tracking-wider">Integrity</h4>
            <p className="text-[11px] text-[#A6B6CC] leading-relaxed">
              Educational simulation only. Not SEBI registered. No trading or investment execution.
            </p>
            <p className="text-[11px] text-[#A6B6CC]/70 font-mono">
              Next.js 15 • FastAPI • SQLAlchemy
            </p>
          </div>
        </div>

        <div className="shell pt-6 border-t border-[#26344A] flex flex-col sm:flex-row items-center justify-between text-xs text-[#A6B6CC] font-mono gap-3">
          <p>© 2026 QuantWeave Platform. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <span className="text-[#54DCC5]">● Systems Normal</span>
            <span className="text-[#8E91FF]">Signal Loom v1.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
