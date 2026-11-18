"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  Search,
  Filter,
  ArrowRight,
  Database,
  Building2,
  RefreshCw,
  Loader2,
  Sparkles,
} from "lucide-react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { StockSearch } from "@/components/StockSearch";
import { api, Instrument } from "@/lib/api";

const SECTORS = [
  "All Sectors",
  "Information Technology",
  "Financial Services",
  "Energy",
  "Consumer Goods",
  "Construction",
  "Telecommunication",
];

export default function EquityDirectoryPage() {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [selectedSector, setSelectedSector] = useState("All Sectors");
  const [isLoading, setIsLoading] = useState(true);
  const [isSeeding, setIsSeeding] = useState(false);

  const fetchInstruments = (targetPage: number = 1, sectorFilter: string = selectedSector) => {
    setIsLoading(true);
    const sectorParam = sectorFilter === "All Sectors" ? undefined : sectorFilter;
    api
      .listInstruments({
        page: targetPage,
        size: 10,
        exchange: "NSE",
        sector: sectorParam,
      })
      .then((data) => {
        setInstruments(data.items);
        setTotal(data.total);
        setPage(data.page);
        setPages(data.pages);
      })
      .catch(() => {
        setInstruments([]);
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  useEffect(() => {
    fetchInstruments(1, selectedSector);
  }, [selectedSector]);

  const handleSeed = async () => {
    setIsSeeding(true);
    try {
      await api.seedMarketData();
      fetchInstruments(1, selectedSector);
    } catch {
      // Handle error
    } finally {
      setIsSeeding(false);
    }
  };

  return (
    <DashboardLayout title="Equity Intelligence — Indian Equities">
      <div className="space-y-6">
        {/* Banner with Stock Search */}
        <section className="p-6 sm:p-8 rounded-2xl bg-gradient-to-r from-[#0d1827] via-[#0f1d30] to-[#0a121d] border border-[#1f3044] space-y-5">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] font-bold text-[#71d5b3] tracking-widest uppercase bg-[#143226] border border-[#235845] px-2.5 py-0.5 rounded-full">
                Equity Intelligence
              </span>
              <span className="text-xs text-[#71859b]">NSE Reference Securities</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-[#edf3fa] tracking-tight">
              Indian Equity Directory, Technicals & Fundamentals
            </h2>
            <p className="mt-1 text-xs sm:text-sm text-[#8ca0b5] leading-relaxed">
              Explore NSE-listed reference equities, inspect technical indicator overlays (SMA, EMA, RSI, MACD, Bollinger Bands),
              review synthetic financial statements, and compare multi-company performance side-by-side.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 max-w-2xl">
            <div className="flex-1">
              <StockSearch placeholder="Quick search by ticker or company name..." />
            </div>
            <Link
              href="/equity/compare"
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-[#172b40] text-[#71d5b3] border border-[#28496b] hover:bg-[#1d3550] transition-colors text-xs font-bold whitespace-nowrap"
            >
              <TrendingUp size={14} />
              Compare Companies
            </Link>
            <Link
              href="/ai?explain=equity"
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-[#15273b] text-[#71d5b3] border border-[#1e3e4a] hover:bg-[#1c3550] transition-colors text-xs font-bold whitespace-nowrap"
            >
              <Sparkles size={14} />
              Explain with Copilot
            </Link>
          </div>
        </section>

        {/* Sector Filters & Stats */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            {SECTORS.map((sector) => (
              <button
                key={sector}
                onClick={() => {
                  setSelectedSector(sector);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                  selectedSector === sector
                    ? "bg-[#71d5b3] text-[#07130f]"
                    : "bg-[#0f1927] text-[#8699ad] hover:text-[#edf3fa] border border-[#1d2d3e]"
                }`}
              >
                {sector}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3 text-xs text-[#7a8fa5]">
            <span>Total: <strong className="text-[#edf3fa]">{total}</strong> instruments</span>
            {total === 0 && (
              <button
                onClick={handleSeed}
                disabled={isSeeding}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#193226] text-[#71d5b3] border border-[#2a614d] text-xs font-semibold hover:bg-[#204233] transition-colors disabled:opacity-50"
              >
                {isSeeding ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                <span>Seed Demo Data</span>
              </button>
            )}
          </div>
        </div>

        {/* Instruments Table */}
        <section className="bg-[#0f1927] border border-[#1f2f42] rounded-2xl overflow-hidden">
          {isLoading ? (
            <div className="p-12 flex flex-col items-center justify-center gap-2 text-xs text-[#71d5b3]">
              <Loader2 size={22} className="animate-spin" />
              <span>Loading instruments...</span>
            </div>
          ) : instruments.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#1f2f42] bg-[#0c1420] text-[#74889f] font-semibold text-[11px]">
                    <th className="py-3 px-4">Ticker</th>
                    <th className="py-3 px-4">Company Name</th>
                    <th className="py-3 px-4">Exchange</th>
                    <th className="py-3 px-4">Sector</th>
                    <th className="py-3 px-4">Currency</th>
                    <th className="py-3 px-4">Mode</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#172536]">
                  {instruments.map((inst) => (
                    <tr
                      key={inst.id}
                      className="hover:bg-[#132233] transition-colors group"
                    >
                      <td className="py-3.5 px-4 font-bold font-mono text-[#edf3fa]">
                        <Link
                          href={`/instruments/${inst.id}`}
                          className="hover:text-[#71d5b3] transition-colors flex items-center gap-1.5"
                        >
                          <TrendingUp size={14} className="text-[#71d5b3]" />
                          <span>{inst.symbol}</span>
                        </Link>
                      </td>
                      <td className="py-3.5 px-4 font-medium text-[#c0d1e4]">
                        {inst.company_name}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded bg-[#17283a] text-[#869cb2] font-mono text-[10px]">
                          {inst.exchange}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-[#869cb2]">
                        {inst.sector || "—"}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[#869cb2]">
                        {inst.currency}
                      </td>
                      <td className="py-3.5 px-4">
                        {inst.is_demo ? (
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-950/80 text-[#71d5b3] border border-[#255746]">
                            DEMO
                          </span>
                        ) : (
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-[#16273b] text-[#93a7bd]">
                            LIVE
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          href={`/instruments/${inst.id}`}
                          className="inline-flex items-center gap-1 text-[11px] font-bold text-[#71d5b3] hover:underline"
                        >
                          <span>Price Chart</span>
                          <ArrowRight size={12} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center space-y-3">
              <Database size={32} className="mx-auto text-[#5a6e84]" />
              <p className="text-xs text-[#8195aa]">No instruments found for the selected sector filter.</p>
              <button
                onClick={handleSeed}
                disabled={isSeeding}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#71d5b3] text-[#07130f] font-bold text-xs"
              >
                {isSeeding ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                <span>Populate Demo Indian Equities</span>
              </button>
            </div>
          )}

          {/* Pagination */}
          {pages > 1 && (
            <div className="p-4 border-t border-[#1b2b3d] flex items-center justify-between text-xs">
              <span className="text-[#6d8197]">
                Page {page} of {pages}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => fetchInstruments(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 rounded-lg bg-[#142335] hover:bg-[#1c3048] text-[#edf3fa] disabled:opacity-40"
                >
                  Previous
                </button>
                <button
                  onClick={() => fetchInstruments(Math.min(pages, page + 1))}
                  disabled={page === pages}
                  className="px-3 py-1.5 rounded-lg bg-[#142335] hover:bg-[#1c3048] text-[#edf3fa] disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </DashboardLayout>
  );
}
