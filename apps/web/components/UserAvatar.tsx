"use client";

import React from "react";
import { AvatarPresetId, useTheme } from "@/lib/theme-context";

export interface AvatarPresetConfig {
  id: AvatarPresetId;
  name: string;
  tagline: string;
  gradientClass: string;
  borderClass: string;
  textClass: string;
  glowClass: string;
  accentColor: string;
  bgPreview: string;
}

export const AVATAR_PRESETS: AvatarPresetConfig[] = [
  {
    id: "loom",
    name: "Signal Loom",
    tagline: "Luminous Periwinkle & Obsidian Alpha",
    gradientClass: "bg-gradient-to-br from-[#8E91FF] via-[#6366F1] to-[#3730A3]",
    borderClass: "border-[#8E91FF]/60",
    textClass: "text-[#FFFFFF]",
    glowClass: "shadow-[0_0_16px_rgba(142,145,255,0.35)]",
    accentColor: "#8E91FF",
    bgPreview: "linear-gradient(135deg, #8E91FF 0%, #6366F1 50%, #3730A3 100%)",
  },
  {
    id: "aqua",
    name: "Signal Aqua",
    tagline: "Algorithmic Mint & Marine Emerald",
    gradientClass: "bg-gradient-to-br from-[#54DCC5] via-[#10B981] to-[#065F46]",
    borderClass: "border-[#54DCC5]/60",
    textClass: "text-[#FFFFFF]",
    glowClass: "shadow-[0_0_16px_rgba(84,220,197,0.35)]",
    accentColor: "#54DCC5",
    bgPreview: "linear-gradient(135deg, #54DCC5 0%, #10B981 50%, #065F46 100%)",
  },
  {
    id: "amber",
    name: "Solar Amber",
    tagline: "Warm Gold & Volatility Topaz",
    gradientClass: "bg-gradient-to-br from-[#FCD34D] via-[#F59E0B] to-[#92400E]",
    borderClass: "border-[#F6BE76]/60",
    textClass: "text-[#FFFFFF]",
    glowClass: "shadow-[0_0_16px_rgba(246,190,118,0.35)]",
    accentColor: "#F6BE76",
    bgPreview: "linear-gradient(135deg, #FCD34D 0%, #F59E0B 50%, #92400E 100%)",
  },
  {
    id: "violet",
    name: "Nebula Violet",
    tagline: "Cosmic Ultraviolet & Galactic Orchid",
    gradientClass: "bg-gradient-to-br from-[#C084FC] via-[#A855F7] to-[#581C87]",
    borderClass: "border-[#C084FC]/60",
    textClass: "text-[#FFFFFF]",
    glowClass: "shadow-[0_0_16px_rgba(192,132,252,0.35)]",
    accentColor: "#C084FC",
    bgPreview: "linear-gradient(135deg, #C084FC 0%, #A855F7 50%, #581C87 100%)",
  },
  {
    id: "emerald",
    name: "Quantum Core",
    tagline: "Electric Azure & High-Frequency Cyan",
    gradientClass: "bg-gradient-to-br from-[#38BDF8] via-[#0284C7] to-[#075985]",
    borderClass: "border-[#38BDF8]/60",
    textClass: "text-[#FFFFFF]",
    glowClass: "shadow-[0_0_16px_rgba(56,189,248,0.35)]",
    accentColor: "#38BDF8",
    bgPreview: "linear-gradient(135deg, #38BDF8 0%, #0284C7 50%, #075985 100%)",
  },
  {
    id: "slate",
    name: "Obsidian Slate",
    tagline: "Polished Platinum & Carbon Monolith",
    gradientClass: "bg-gradient-to-br from-[#E2E8F0] via-[#94A3B8] to-[#334155]",
    borderClass: "border-[#E2E8F0]/60",
    textClass: "text-[#0F172A]",
    glowClass: "shadow-[0_0_16px_rgba(226,232,240,0.3)]",
    accentColor: "#E2E8F0",
    bgPreview: "linear-gradient(135deg, #E2E8F0 0%, #94A3B8 50%, #334155 100%)",
  },
];

interface UserAvatarProps {
  name?: string;
  preset?: AvatarPresetId;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  showStatus?: boolean;
  className?: string;
}

const SIZE_MAP = {
  xs: {
    box: "w-6 h-6 rounded-lg text-[10px]",
    status: "w-1.5 h-1.5 -bottom-0.5 -right-0.5 border",
  },
  sm: {
    box: "w-8 h-8 rounded-xl text-xs",
    status: "w-2 h-2 -bottom-0.5 -right-0.5 border",
  },
  md: {
    box: "w-9 h-9 rounded-xl text-xs",
    status: "w-2.5 h-2.5 -bottom-0.5 -right-0.5 border-2",
  },
  lg: {
    box: "w-12 h-12 rounded-2xl text-sm",
    status: "w-3 h-3 -bottom-0.5 -right-0.5 border-2",
  },
  xl: {
    box: "w-16 h-16 rounded-2xl text-lg",
    status: "w-3.5 h-3.5 -bottom-1 -right-1 border-2",
  },
};

export function UserAvatar({
  name = "Analyst",
  preset,
  size = "md",
  showStatus = false,
  className = "",
}: UserAvatarProps) {
  const { avatarPreset: contextPreset } = useTheme();
  const activePresetId = preset || contextPreset || "loom";

  const config =
    AVATAR_PRESETS.find((p) => p.id === activePresetId) || AVATAR_PRESETS[0];

  const initials = (name || "Analyst")
    .split(" ")
    .filter(Boolean)
    .map((n) => n[0])
    .join("")
    .substring(0, 2)
    .toUpperCase() || "QW";

  const sizeStyle = SIZE_MAP[size] || SIZE_MAP.md;

  return (
    <div className={`relative inline-flex flex-shrink-0 items-center justify-center ${className}`}>
      <div
        className={`${sizeStyle.box} ${config.gradientClass} ${config.glowClass} border ${config.borderClass} flex items-center justify-center font-black font-mono tracking-tight select-none transition-all duration-200`}
      >
        <span className={`${config.textClass} drop-shadow-sm`}>{initials}</span>
      </div>

      {showStatus && (
        <span
          className={`absolute ${sizeStyle.status} rounded-full bg-[#54DCC5] border-[var(--bg)]`}
          title="Active Session"
        />
      )}
    </div>
  );
}
