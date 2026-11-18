"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Menu, Activity, ShieldAlert } from "lucide-react";
import { api, HealthResponse } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { StockSearch } from "@/components/StockSearch";
import { UserProfileMenu } from "@/components/UserProfileMenu";

interface NavbarProps {
  onToggleSidebar: () => void;
  title?: string;
}

export function Navbar({ onToggleSidebar, title = "Platform Overview" }: NavbarProps) {
  const { user, isLoading } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    api
      .getHealth()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setIsHealthLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealth(null);
          setIsHealthLoading(false);
        }
      });

    const interval = setInterval(() => {
      api
        .getHealth()
        .then((data) => isMounted && setHealth(data))
        .catch(() => isMounted && setHealth(null));
    }, 20000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="h-16 border-b border-[var(--line)] bg-[var(--bg)]/90 backdrop-blur-xl sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 text-[var(--muted)] hover:text-[var(--text)] rounded-xl hover:bg-[var(--panel)] transition-colors"
          aria-label="Toggle navigation menu"
        >
          <Menu size={20} />
        </button>
        <div>
          <h1 className="text-sm sm:text-base font-bold text-[var(--text)] tracking-tight">{title}</h1>
          <p className="text-[10px] text-[var(--text-secondary)] hidden sm:block font-mono">
            Signal Loom • Connected Research Workspace
          </p>
        </div>
      </div>

      {/* Center Stock Search */}
      <div className="hidden lg:block w-80 max-w-sm">
        <StockSearch placeholder="Search securities (e.g. RELIANCE, TCS)..." />
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {/* Exchange Tag */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--panel)] border border-[var(--line)] text-[11px] text-[var(--text-secondary)] font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--gain)]" />
          <span>NSE Ref</span>
        </div>

        {/* Backend Telemetry Status */}
        <div className="flex items-center">
          {isHealthLoading ? (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--panel)] border border-[var(--line)] text-[10px] text-[var(--muted)] font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--warn)] animate-ping" />
              API: Syncing
            </span>
          ) : health?.status === "ok" ? (
            <span
              className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--gain)]/10 border border-[var(--gain)]/30 text-[10px] font-medium text-[var(--gain)] font-mono"
              title={`API online: ${health.service} (${health.database})`}
            >
              <Activity size={12} className="text-[var(--gain)]" />
              Online
            </span>
          ) : (
            <span
              className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--loss)]/10 border border-[var(--loss)]/30 text-[10px] font-medium text-[var(--loss)] font-mono"
              title="API unreachable"
            >
              <ShieldAlert size={12} className="text-[var(--loss)]" />
              Offline
            </span>
          )}
        </div>

        {/* Compact User Menu for Navbar */}
        {isLoading ? (
          <div className="w-8 h-8 rounded-xl bg-[var(--panel)] animate-pulse border border-[var(--line)]" />
        ) : user ? (
          <div className="hidden sm:block max-w-[200px]">
            <UserProfileMenu compact={true} placement="bottom" />
          </div>
        ) : null}
      </div>
    </header>
  );
}
