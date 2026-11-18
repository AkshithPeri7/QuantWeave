"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import {
  User as UserIcon,
  Settings,
  LayoutDashboard,
  LogOut,
  ChevronDown,
  ShieldCheck,
  Palette,
  Sun,
  Moon,
  Sparkles,
  Lock,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useTheme, THEMES, ThemeId } from "@/lib/theme-context";
import { UserAvatar } from "@/components/UserAvatar";

interface UserProfileMenuProps {
  placement?: "bottom" | "top";
  compact?: boolean;
}

export function UserProfileMenu({
  placement = "bottom",
  compact = false,
}: UserProfileMenuProps) {
  const { user, logout } = useAuth();
  const { theme, resolvedTheme, setTheme } = useTheme();

  const [isOpen, setIsOpen] = useState(false);
  const [menuCoords, setMenuCoords] = useState<{
    top: number;
    left: number;
    width: number;
  }>({
    top: 0,
    left: 0,
    width: 270,
  });

  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Calculate accurate viewport-collision-safe coordinates
  const updatePosition = useCallback(() => {
    if (!triggerRef.current) return;
    const triggerRect = triggerRef.current.getBoundingClientRect();

    const menuWidth = 270;
    const menuEstimatedHeight = 400;
    const padding = 12;

    const vWidth = window.innerWidth;
    const vHeight = window.innerHeight;

    // Horizontal position
    let left = triggerRect.left;
    if (left + menuWidth > vWidth - padding) {
      left = Math.max(padding, vWidth - menuWidth - padding);
    }
    if (left < padding) {
      left = padding;
    }

    // Vertical position with collision detection
    let top: number;
    const spaceBelow = vHeight - triggerRect.bottom;
    const spaceAbove = triggerRect.top;

    if (placement === "top") {
      if (spaceAbove >= menuEstimatedHeight || spaceAbove > spaceBelow) {
        // Place above trigger
        top = Math.max(padding, triggerRect.top - menuEstimatedHeight - 8);
      } else {
        // Fallback to below trigger if constrained
        top = Math.min(vHeight - menuEstimatedHeight - padding, triggerRect.bottom + 8);
      }
    } else {
      if (spaceBelow >= menuEstimatedHeight || spaceBelow > spaceAbove) {
        // Place below trigger
        top = Math.min(vHeight - menuEstimatedHeight - padding, triggerRect.bottom + 8);
      } else {
        // Flip to above trigger
        top = Math.max(padding, triggerRect.top - menuEstimatedHeight - 8);
      }
    }

    setMenuCoords({
      top: Math.round(top),
      left: Math.round(left),
      width: menuWidth,
    });
  }, [placement]);

  // Recalculate whenever opened, resized, or scrolled
  useEffect(() => {
    if (isOpen) {
      updatePosition();
      const handleReposition = () => updatePosition();
      window.addEventListener("resize", handleReposition);
      window.addEventListener("scroll", handleReposition, true);

      return () => {
        window.removeEventListener("resize", handleReposition);
        window.removeEventListener("scroll", handleReposition, true);
      };
    }
  }, [isOpen, updatePosition]);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      if (
        menuRef.current &&
        !menuRef.current.contains(target) &&
        triggerRef.current &&
        !triggerRef.current.contains(target)
      ) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  // Handle Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  if (!user) return null;

  return (
    <div className="relative inline-block w-full">
      {/* Trigger Button */}
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label="User account menu"
        className={`w-full group flex items-center justify-between p-2 rounded-xl transition-all duration-200 select-none ${
          isOpen
            ? "bg-[var(--elevated)] border border-[var(--accent)] text-[var(--text)] shadow-lg shadow-[var(--accent)]/10"
            : "hover:bg-[var(--panel)] border border-transparent hover:border-[var(--line)] text-[var(--muted)]"
        }`}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <UserAvatar name={user.name} size={compact ? "sm" : "md"} showStatus={true} />

          {!compact && (
            <div className="text-left min-w-0 flex-1">
              <p
                className="text-xs font-bold text-[var(--text)] truncate group-hover:text-[var(--accent)] transition-colors"
                title={user.name}
              >
                {user.name}
              </p>
              <p
                className="text-[10px] text-[var(--muted)] truncate font-mono"
                title={user.email}
              >
                {user.email}
              </p>
            </div>
          )}
        </div>

        {!compact && (
          <ChevronDown
            size={14}
            className={`text-[var(--muted)] transition-transform duration-200 flex-shrink-0 ${
              isOpen ? "rotate-180 text-[var(--accent)]" : "group-hover:text-[var(--text)]"
            }`}
          />
        )}
      </button>

      {/* Portal-Mounted Dropdown Menu */}
      {isOpen &&
        mounted &&
        createPortal(
          <div
            ref={menuRef}
            role="menu"
            aria-orientation="vertical"
            style={{
              position: "fixed",
              top: `${menuCoords.top}px`,
              left: `${menuCoords.left}px`,
              width: `${menuCoords.width}px`,
              zIndex: 99999,
            }}
            className="rounded-2xl bg-[var(--panel)] border border-[var(--line)] shadow-2xl shadow-black/80 backdrop-blur-2xl p-2.5 animate-in fade-in zoom-in-95 duration-150 flex flex-col text-[var(--text)]"
          >
            {/* User Header */}
            <div className="p-3 mb-2 border border-[var(--line)] bg-[var(--elevated)]/70 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold tracking-wider text-[var(--accent)] uppercase font-mono flex items-center gap-1">
                  <Sparkles size={11} /> Authenticated
                </span>
                <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-[var(--gain)] bg-[var(--gain)]/10 px-2 py-0.5 rounded-full border border-[var(--gain)]/30 font-mono">
                  <ShieldCheck size={10} />
                  {user.role?.toUpperCase() || "ANALYST"}
                </span>
              </div>
              <div className="flex items-center gap-2.5">
                <UserAvatar name={user.name} size="sm" />
                <div className="min-w-0 flex-1">
                  <p
                    className="text-xs font-bold text-[var(--text)] truncate"
                    title={user.name}
                  >
                    {user.name}
                  </p>
                  <p
                    className="text-[10px] text-[var(--muted)] truncate font-mono"
                    title={user.email}
                  >
                    {user.email}
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Theme Switcher Pill Row */}
            <div className="px-2 py-2 mb-2 rounded-xl bg-[var(--bg)] border border-[var(--line)]">
              <div className="flex items-center justify-between mb-1.5 px-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted)] font-mono flex items-center gap-1">
                  <Palette size={10} /> Theme Quick Switch
                </span>
                <span className="text-[9px] text-[var(--accent)] font-mono capitalize">
                  {resolvedTheme.replace("-", " ")}
                </span>
              </div>
              <div className="grid grid-cols-4 gap-1.5">
                {THEMES.map((t) => {
                  const isSelected = resolvedTheme === t.id;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setTheme(t.id)}
                      className={`flex flex-col items-center justify-center p-1.5 rounded-lg border text-[9px] font-mono transition-all ${
                        isSelected
                          ? "border-[var(--accent)] bg-[var(--elevated)] shadow-sm font-bold text-[var(--text)]"
                          : "border-transparent hover:border-[var(--line)] hover:bg-[var(--panel)] text-[var(--muted)]"
                      }`}
                      title={`${t.name} (${t.category})`}
                    >
                      <div
                        className="w-4 h-4 rounded-full border border-white/20 mb-1 flex items-center justify-center shadow-inner"
                        style={{ backgroundColor: t.background }}
                      >
                        <div
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: t.primaryAccent }}
                        />
                      </div>
                      <span className="truncate max-w-[50px]">{t.name.split(" ")[0]}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Navigation Actions */}
            <div className="space-y-0.5">
              <Link
                href="/profile"
                role="menuitem"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-[var(--text)] hover:text-[var(--accent)] hover:bg-[var(--elevated)] transition-colors"
              >
                <UserIcon size={14} className="text-[var(--accent)]" />
                <span>My Profile</span>
              </Link>

              <Link
                href="/profile#appearance"
                role="menuitem"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-[var(--text)] hover:text-[var(--accent)] hover:bg-[var(--elevated)] transition-colors"
              >
                <Palette size={14} className="text-[#54DCC5]" />
                <span>Appearance & Themes</span>
              </Link>

              <Link
                href="/profile#security"
                role="menuitem"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-[var(--text)] hover:text-[var(--accent)] hover:bg-[var(--elevated)] transition-colors"
              >
                <Lock size={14} className="text-[#F6BE76]" />
                <span>Account Security</span>
              </Link>

              <Link
                href="/dashboard"
                role="menuitem"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-[var(--text)] hover:text-[var(--accent)] hover:bg-[var(--elevated)] transition-colors"
              >
                <LayoutDashboard size={14} className="text-[#8E91FF]" />
                <span>Dashboard</span>
              </Link>
            </div>

            <div className="my-1.5 border-t border-[var(--line)]" />

            {/* Sign Out Action */}
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                setIsOpen(false);
                logout();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-[var(--loss)] hover:bg-[var(--loss)]/10 transition-colors"
            >
              <LogOut size={14} />
              <span>Sign Out</span>
            </button>
          </div>,
          document.body
        )}
    </div>
  );
}
