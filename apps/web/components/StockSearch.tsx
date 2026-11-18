"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2, TrendingUp, X } from "lucide-react";
import { api, Instrument } from "@/lib/api";

interface StockSearchProps {
  className?: string;
  placeholder?: string;
  onSelect?: (instrument: Instrument) => void;
}

export function StockSearch({
  className = "",
  placeholder = "Search NSE/BSE stocks (e.g. RELIANCE, TCS, INFY)...",
  onSelect,
}: StockSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Instrument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(() => {
      setIsLoading(true);
      api
        .searchInstruments(query.trim(), 8)
        .then((data) => {
          setResults(data);
          setIsOpen(true);
        })
        .catch(() => {
          setResults([]);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (instrument: Instrument) => {
    setIsOpen(false);
    setQuery("");
    if (onSelect) {
      onSelect(instrument);
    } else {
      router.push(`/instruments/${instrument.id}`);
    }
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#62788e]">
          <Search size={15} />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim() && setResults.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          className="w-full pl-10 pr-9 py-2 bg-[#0c1522] border border-[#203144] rounded-xl text-xs text-[#edf3fa] placeholder-[#576c85] focus:outline-none focus:border-[#71d5b3] focus:ring-1 focus:ring-[#71d5b3] transition-colors"
        />
        {query && (
          <button
            onClick={() => {
              setQuery("");
              setResults([]);
              setIsOpen(false);
            }}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#62788e] hover:text-[#edf3fa]"
          >
            <X size={14} />
          </button>
        )}
        {isLoading && (
          <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-[#71d5b3]">
            <Loader2 size={14} className="animate-spin" />
          </div>
        )}
      </div>

      {/* Results Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1.5 bg-[#0f1b2b] border border-[#22364c] rounded-xl shadow-2xl overflow-hidden z-50 max-h-80 overflow-y-auto">
          {results.length > 0 ? (
            <div className="py-1 divide-y divide-[#182637]">
              {results.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  className="w-full px-4 py-2.5 text-left flex items-center justify-between hover:bg-[#16273c] transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#142335] text-[#71d5b3] flex items-center justify-center font-bold text-xs">
                      <TrendingUp size={14} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-[#edf3fa] group-hover:text-[#71d5b3] transition-colors">
                          {item.symbol}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#172739] text-[#7d93aa]">
                          {item.exchange}
                        </span>
                        {item.is_demo && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#1c2e27] text-[#71d5b3] font-medium border border-[#285747]">
                            DEMO
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-[#7f91a6] truncate max-w-xs sm:max-w-sm">
                        {item.company_name}
                      </p>
                    </div>
                  </div>
                  {item.sector && (
                    <span className="text-[10px] text-[#637990] hidden sm:inline">
                      {item.sector}
                    </span>
                  )}
                </button>
              ))}
            </div>
          ) : (
            <div className="px-4 py-6 text-center text-xs text-[#6e8297]">
              No instruments found matching &quot;{query}&quot;
            </div>
          )}
        </div>
      )}
    </div>
  );
}
