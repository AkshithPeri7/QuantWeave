"use client";

import React, { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { Loader2 } from "lucide-react";

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export function DashboardLayout({ children, title }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !user) {
      const safePath =
        pathname && pathname.startsWith("/") && !pathname.startsWith("//")
          ? pathname
          : "/dashboard";
      router.replace(`/login?next=${encodeURIComponent(safePath)}`);
    }
  }, [user, isLoading, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--bg)] flex flex-col items-center justify-center p-6 text-center">
        <div className="w-12 h-12 rounded-2xl bg-[var(--panel)] border border-[var(--line)] flex items-center justify-center text-[var(--accent)] mb-4 shadow-xl shadow-black/20">
          <Loader2 size={24} className="animate-spin text-[var(--accent)]" />
        </div>
        <h2 className="text-sm font-semibold text-[var(--text)] tracking-wide">
          Verifying QuantWeave Session
        </h2>
        <p className="text-xs text-[var(--text-secondary)] mt-1 font-mono">
          Connecting to Signal Loom research workspace...
        </p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] flex">
      {/* Sidebar navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main content wrapper */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        <Navbar onToggleSidebar={() => setSidebarOpen((prev) => !prev)} title={title} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
