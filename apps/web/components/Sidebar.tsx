"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  Scale,
  Briefcase,
  PieChart,
  Newspaper,
  FlaskConical,
  Bot,
  User as UserIcon,
  X,
  Radio,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { UserProfileMenu } from "@/components/UserProfileMenu";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navItems = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    badge: "Terminal",
  },
  {
    name: "Equity Intelligence",
    href: "/equity",
    icon: TrendingUp,
    badge: "NSE",
  },
  {
    name: "Compare Equities",
    href: "/equity/compare",
    icon: Scale,
  },
  {
    name: "Portfolio Intelligence",
    href: "/portfolio",
    icon: Briefcase,
    badge: "WACB",
  },
  {
    name: "FundScope",
    href: "/funds",
    icon: PieChart,
    badge: "AMFI",
  },
  {
    name: "MarketPulse",
    href: "/market",
    icon: Newspaper,
    badge: "News",
  },
  {
    name: "QuantLab",
    href: "/quantlab",
    icon: FlaskConical,
    badge: "Sim",
  },
  {
    name: "QuantWeave AI",
    href: "/ai",
    icon: Bot,
    badge: "Copilot",
  },
  {
    name: "My Profile",
    href: "/profile",
    icon: UserIcon,
  },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user, isLoading } = useAuth();

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/75 z-40 lg:hidden backdrop-blur-md transition-opacity"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[var(--bg)] border-r border-[var(--line)] flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Signal Loom Brand Header */}
        <div className="h-20 px-5 flex items-center justify-between border-b border-[var(--line)]">
          <Link
            href="/dashboard"
            className="flex items-center gap-3 font-extrabold text-xl tracking-tight text-[var(--text)] group"
            onClick={onClose}
          >
            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#8E91FF] via-[#54DCC5] to-[#F6BE76] p-[1.5px] shadow-lg shadow-[#8E91FF]/25">
                <div className="w-full h-full bg-[var(--bg)] rounded-[10px] flex items-center justify-center font-black text-sm text-[var(--accent)] font-mono group-hover:scale-105 transition-transform">
                  QW
                </div>
              </div>
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold tracking-tight text-base text-[var(--text)] flex items-center gap-1.5">
                QuantWeave
              </span>
              <span className="text-[10px] tracking-wider text-[var(--text-secondary)] uppercase font-mono">
                Signal Loom
              </span>
            </div>
          </Link>

          <button
            onClick={onClose}
            className="lg:hidden p-1.5 text-[var(--muted)] hover:text-[var(--text)] rounded-lg hover:bg-[var(--panel)]"
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        {/* Live Signal Wire Status */}
        <div className="px-5 py-2.5 border-b border-[var(--line)] bg-[var(--panel)]/60">
          <div className="flex items-center justify-between text-[10px] font-semibold tracking-wider text-[var(--accent)] font-mono">
            <span className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--gain)] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--gain)]"></span>
              </span>
              <span>NETWORK CONNECTED</span>
            </span>
            <span className="text-[var(--muted)]">v1.0</span>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className={`group flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
                  isActive
                    ? "bg-[var(--elevated)] text-[var(--accent)] border border-[var(--accent)]/40 shadow-md shadow-black/10"
                    : "text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--panel)]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    size={16}
                    className={`transition-colors duration-150 ${
                      isActive
                        ? "text-[var(--accent)]"
                        : "text-[var(--muted)] group-hover:text-[var(--text)]"
                    }`}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[9px] px-2 py-0.5 rounded-full font-mono transition-colors ${
                      isActive
                        ? "bg-[var(--accent)]/20 text-[var(--accent)] border border-[var(--accent)]/40"
                        : "bg-[var(--panel)] text-[var(--muted)] border border-[var(--line)]"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Interactive User Profile Control (Portal-based, viewport collision-safe) */}
        <div className="p-3 border-t border-[var(--line)] bg-[var(--bg)]/90 relative z-10">
          {isLoading ? (
            <div className="py-2.5 flex items-center justify-center text-xs text-[var(--muted)]">
              <span className="animate-pulse font-mono text-[11px]">Loading user state...</span>
            </div>
          ) : user ? (
            <UserProfileMenu placement="top" />
          ) : null}
        </div>
      </aside>
    </>
  );
}
