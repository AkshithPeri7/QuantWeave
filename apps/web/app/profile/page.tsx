"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  User as UserIcon,
  Mail,
  Shield,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  Save,
  Lock,
  Calendar,
  Sparkles,
  ArrowLeft,
  LogOut,
  Palette,
  Check,
  ShieldCheck,
  Loader2,
  Sun,
  Moon,
  Monitor,
  Eye,
  Sliders,
  Laptop,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { DashboardLayout } from "@/components/DashboardLayout";
import { api } from "@/lib/api";
import {
  useTheme,
  THEMES,
  ThemeId,
  AvatarPresetId,
  ColorMode,
} from "@/lib/theme-context";
import { UserAvatar, AVATAR_PRESETS } from "@/components/UserAvatar";

export default function ProfilePage() {
  const { user, updateUser, logout } = useAuth();
  const {
    theme,
    resolvedTheme,
    avatarPreset,
    colorMode,
    reducedMotion,
    setTheme,
    setAvatarPreset,
    setColorMode,
    setReducedMotion,
  } = useTheme();

  // Active sub-section / tab state
  const [activeTab, setActiveTab] = useState<"overview" | "appearance" | "security">("overview");

  // Profile Edit State
  const [displayName, setDisplayName] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileSuccessMsg, setProfileSuccessMsg] = useState<string | null>(null);
  const [profileErrorMsg, setProfileErrorMsg] = useState<string | null>(null);

  // Appearance feedback
  const [themeSuccessMsg, setThemeSuccessMsg] = useState<string | null>(null);

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordSuccessMsg, setPasswordSuccessMsg] = useState<string | null>(null);
  const [passwordErrorMsg, setPasswordErrorMsg] = useState<string | null>(null);

  // Synchronize hash from URL (#appearance, #security)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const hash = window.location.hash.replace("#", "");
      if (hash === "appearance") setActiveTab("appearance");
      else if (hash === "security" || hash === "settings") setActiveTab("security");
    }
  }, []);

  useEffect(() => {
    if (user) {
      setDisplayName(user.name);
    }
  }, [user]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName.trim() || displayName.trim().length < 2) {
      setProfileErrorMsg("Display name must be at least 2 characters long.");
      return;
    }
    setIsSavingProfile(true);
    setProfileErrorMsg(null);
    setProfileSuccessMsg(null);

    try {
      await updateUser({ name: displayName.trim() });
      setProfileSuccessMsg("Profile display name successfully updated across QuantWeave.");
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      setProfileErrorMsg(error.detail || error.message || "Failed to update profile name.");
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleThemeSelect = async (newThemeId: ThemeId) => {
    await setTheme(newThemeId);
    setThemeSuccessMsg(`Applied ${newThemeId.replace("-", " ")} theme globally.`);
    setTimeout(() => setThemeSuccessMsg(null), 3000);
  };

  const handleAvatarSelect = async (presetId: AvatarPresetId) => {
    await setAvatarPreset(presetId);
    setThemeSuccessMsg("Avatar appearance preset updated.");
    setTimeout(() => setThemeSuccessMsg(null), 3000);
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordErrorMsg(null);
    setPasswordSuccessMsg(null);

    if (!currentPassword) {
      setPasswordErrorMsg("Please enter your current password.");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordErrorMsg("New password must contain at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordErrorMsg("New password and confirmation do not match.");
      return;
    }

    setIsChangingPassword(true);
    try {
      const res = await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccessMsg(res.message || "Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      setPasswordErrorMsg(error.detail || error.message || "Password verification failed.");
    } finally {
      setIsChangingPassword(false);
    }
  };

  if (!user) return null;

  return (
    <DashboardLayout title="User Profile & Appearance">
      <div className="max-w-5xl mx-auto space-y-6 pb-12">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors"
          >
            <ArrowLeft size={14} /> Back to Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-[var(--muted)]">Active Theme:</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/30 capitalize">
              {resolvedTheme.replace("-", " ")}
            </span>
          </div>
        </div>

        {/* Profile Hero Header Card */}
        <div className="p-6 sm:p-8 rounded-3xl bg-[var(--panel)] border border-[var(--line)] shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--accent)]/10 rounded-full blur-3xl pointer-events-none" />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative z-10">
            <div className="flex items-center gap-5">
              <UserAvatar name={user.name} size="xl" showStatus={true} />
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-xl sm:text-2xl font-black text-[var(--text)] tracking-tight">
                    {user.name}
                  </h1>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold font-mono bg-[var(--gain)]/10 text-[var(--gain)] border border-[var(--gain)]/30">
                    <ShieldCheck size={11} />
                    {user.role?.toUpperCase() || "ANALYST"}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] mt-1 font-mono flex items-center gap-1.5">
                  <Mail size={13} className="text-[var(--muted)]" />
                  {user.email}
                </p>
                <p className="text-[10px] text-[var(--muted)] mt-1 font-mono flex items-center gap-1.5">
                  <Calendar size={12} />
                  Member since {new Date(user.created_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={logout}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-[var(--loss)] bg-[var(--loss)]/10 hover:bg-[var(--loss)]/20 border border-[var(--loss)]/30 transition-colors"
              >
                <LogOut size={14} /> Sign Out
              </button>
            </div>
          </div>

          {/* Section Navigation Tabs */}
          <div className="flex items-center gap-2 mt-8 pt-4 border-t border-[var(--line)] overflow-x-auto">
            <button
              onClick={() => {
                setActiveTab("overview");
                if (typeof window !== "undefined") window.location.hash = "overview";
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "overview"
                  ? "bg-[var(--elevated)] text-[var(--accent)] border border-[var(--accent)]/40 shadow-sm"
                  : "text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--elevated)]/50"
              }`}
            >
              <UserIcon size={14} /> Profile Overview
            </button>
            <button
              onClick={() => {
                setActiveTab("appearance");
                if (typeof window !== "undefined") window.location.hash = "appearance";
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "appearance"
                  ? "bg-[var(--elevated)] text-[var(--accent)] border border-[var(--accent)]/40 shadow-sm"
                  : "text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--elevated)]/50"
              }`}
            >
              <Palette size={14} /> Appearance & Themes
            </button>
            <button
              onClick={() => {
                setActiveTab("security");
                if (typeof window !== "undefined") window.location.hash = "security";
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "security"
                  ? "bg-[var(--elevated)] text-[var(--accent)] border border-[var(--accent)]/40 shadow-sm"
                  : "text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--elevated)]/50"
              }`}
            >
              <Lock size={14} /> Account Security
            </button>
          </div>
        </div>

        {/* Global Feedback Banner */}
        {themeSuccessMsg && (
          <div className="p-3.5 rounded-2xl bg-[var(--gain)]/10 border border-[var(--gain)]/30 text-[var(--gain)] text-xs flex items-center gap-2 font-mono animate-in fade-in">
            <CheckCircle2 size={16} />
            <span>{themeSuccessMsg}</span>
          </div>
        )}

        {/* TAB 1: OVERVIEW & PERSONAL INFO */}
        {(activeTab === "overview" || activeTab === "appearance") && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Personal Details Form */}
            <div className="md:col-span-2 p-6 sm:p-7 rounded-3xl bg-[var(--panel)] border border-[var(--line)] space-y-5">
              <div>
                <h2 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
                  <UserIcon size={17} className="text-[var(--accent)]" /> Personal Information
                </h2>
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  Manage your public display name and verified identity across all quantitative research records.
                </p>
              </div>

              {profileSuccessMsg && (
                <div className="p-3.5 rounded-xl bg-[var(--gain)]/10 border border-[var(--gain)]/30 text-[var(--gain)] text-xs flex items-center gap-2">
                  <CheckCircle2 size={16} /> {profileSuccessMsg}
                </div>
              )}

              {profileErrorMsg && (
                <div className="p-3.5 rounded-xl bg-[var(--loss)]/10 border border-[var(--loss)]/30 text-[var(--loss)] text-xs flex items-center gap-2">
                  <AlertCircle size={16} /> {profileErrorMsg}
                </div>
              )}

              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[var(--text)] mb-1.5">
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    required
                    minLength={2}
                    maxLength={100}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--elevated)] border border-[var(--line)] text-xs text-[var(--text)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] transition-all font-sans"
                    placeholder="e.g. Vikramaditya Rathore"
                  />
                  <p className="text-[11px] text-[var(--muted)] mt-1 font-mono">
                    This name appears on saved strategies, AI Copilot sessions, and portfolio ledgers.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[var(--text)] mb-1.5">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={user.email}
                    disabled
                    className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--elevated)]/50 border border-[var(--line)] text-xs text-[var(--muted)] font-mono cursor-not-allowed select-none"
                  />
                  <p className="text-[11px] text-[var(--muted)] mt-1 font-mono">
                    Primary login credential cannot be modified directly. Contact platform administrator.
                  </p>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isSavingProfile}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-[var(--accent)] hover:opacity-90 disabled:opacity-50 transition-all shadow-md shadow-[var(--accent)]/20"
                  >
                    {isSavingProfile ? (
                      <>
                        <Loader2 size={14} className="animate-spin" /> Saving Changes...
                      </>
                    ) : (
                      <>
                        <Save size={14} /> Save Name Changes
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Account Quick Stats */}
            <div className="p-6 rounded-3xl bg-[var(--panel)] border border-[var(--line)] space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] font-mono flex items-center gap-1.5">
                <Shield size={14} className="text-[var(--accent)]" /> Account Metadata
              </h3>

              <div className="space-y-3 pt-1">
                <div className="p-3 rounded-2xl bg-[var(--elevated)] border border-[var(--line)] space-y-1">
                  <span className="text-[10px] text-[var(--muted)] font-mono uppercase">User Role</span>
                  <p className="text-xs font-bold text-[var(--text)] font-mono">
                    {user.role === "admin" ? "Platform Administrator" : "Quantitative Analyst"}
                  </p>
                </div>

                <div className="p-3 rounded-2xl bg-[var(--elevated)] border border-[var(--line)] space-y-1">
                  <span className="text-[10px] text-[var(--muted)] font-mono uppercase">Account ID</span>
                  <p className="text-[11px] font-mono text-[var(--text-secondary)] truncate" title={user.id}>
                    {user.id}
                  </p>
                </div>

                <div className="p-3 rounded-2xl bg-[var(--elevated)] border border-[var(--line)] space-y-1">
                  <span className="text-[10px] text-[var(--muted)] font-mono uppercase">Session Status</span>
                  <p className="text-xs font-bold text-[var(--gain)] font-mono flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[var(--gain)] animate-pulse" />
                    Authenticated & Active
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: COMPLETE WEBSITE APPEARANCE & THEMES */}
        {(activeTab === "overview" || activeTab === "appearance") && (
          <div id="appearance" className="space-y-6 pt-2">
            {/* Website Themes Grid */}
            <div className="p-6 sm:p-8 rounded-3xl bg-[var(--panel)] border border-[var(--line)] space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
                    <Palette size={18} className="text-[var(--accent)]" /> Website Theme System
                  </h2>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">
                    Select a full website theme. The entire platform immediately updates with consistent tokens and contrast-verified charts.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-[var(--muted)]">4 Complete Themes</span>
                </div>
              </div>

              {/* Theme Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {THEMES.map((t) => {
                  const isSelected = resolvedTheme === t.id;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => handleThemeSelect(t.id)}
                      className={`group relative text-left p-4 rounded-2xl border transition-all duration-200 overflow-hidden flex flex-col justify-between ${
                        isSelected
                          ? "border-[var(--accent)] ring-2 ring-[var(--accent)]/30 bg-[var(--elevated)] shadow-lg"
                          : "border-[var(--line)] hover:border-[var(--accent)]/50 bg-[var(--panel)] hover:bg-[var(--elevated)]/50"
                      }`}
                    >
                      {/* Top Checkmark Badge */}
                      <div className="flex items-center justify-between mb-3 w-full">
                        <span
                          className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded-full border ${
                            t.category === "dark"
                              ? "bg-slate-900/60 text-slate-300 border-slate-700/60"
                              : "bg-amber-100 text-amber-900 border-amber-300/80"
                          }`}
                        >
                          {t.category.toUpperCase()}
                        </span>

                        <div
                          className={`w-5 h-5 rounded-full flex items-center justify-center transition-all ${
                            isSelected
                              ? "bg-[var(--accent)] text-white shadow-sm"
                              : "border border-[var(--line)] group-hover:border-[var(--muted)]"
                          }`}
                        >
                          {isSelected && <Check size={12} strokeWidth={3} />}
                        </div>
                      </div>

                      {/* Mini UI Mockup Preview */}
                      <div
                        className="w-full h-24 rounded-xl border border-black/10 overflow-hidden p-2 flex flex-col justify-between mb-3 shadow-inner select-none"
                        style={{ backgroundColor: t.background }}
                      >
                        {/* Mock Navbar */}
                        <div
                          className="h-3.5 rounded-md px-2 flex items-center justify-between"
                          style={{ backgroundColor: t.surface, border: `1px solid ${t.border}` }}
                        >
                          <div className="flex items-center gap-1">
                            <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: t.primaryAccent }} />
                            <div className="w-6 h-1 rounded-sm bg-white/20" />
                          </div>
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: t.secondaryAccent }} />
                        </div>

                        {/* Mock Chart & Panel */}
                        <div className="flex gap-1.5 flex-1 mt-1.5">
                          <div
                            className="w-1/3 rounded p-1 flex flex-col justify-around"
                            style={{ backgroundColor: t.surface }}
                          >
                            <div className="w-full h-1 bg-white/20 rounded" />
                            <div className="w-3/4 h-1 bg-white/10 rounded" />
                          </div>

                          {/* SVG Micro Chart */}
                          <div
                            className="flex-1 rounded p-1 flex items-center justify-center"
                            style={{ backgroundColor: t.elevated }}
                          >
                            <svg className="w-full h-full" viewBox="0 0 60 20" preserveAspectRatio="none">
                              <path
                                d="M 0 16 Q 15 4, 30 12 T 60 2"
                                fill="none"
                                stroke={t.primaryAccent}
                                strokeWidth="2.5"
                              />
                              <path
                                d="M 0 18 Q 15 12, 30 15 T 60 8"
                                fill="none"
                                stroke={t.secondaryAccent}
                                strokeWidth="1.5"
                                strokeDasharray="2 1"
                              />
                            </svg>
                          </div>
                        </div>
                      </div>

                      {/* Theme Name & Description */}
                      <div>
                        <h4 className="text-xs font-bold text-[var(--text)] group-hover:text-[var(--accent)] transition-colors">
                          {t.name}
                        </h4>
                        <p className="text-[10px] text-[var(--text-secondary)] mt-0.5 line-clamp-2 leading-relaxed">
                          {t.tagline}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Display Preferences Row (Light / Dark / System & Reduced Motion) */}
              <div className="pt-4 border-t border-[var(--line)] grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-[var(--elevated)] border border-[var(--line)] space-y-2">
                  <span className="text-xs font-bold text-[var(--text)] flex items-center gap-2">
                    <Monitor size={14} className="text-[var(--accent)]" /> Theme Mode Preference
                  </span>
                  <p className="text-[11px] text-[var(--text-secondary)]">
                    Sync automatic day/night mode or lock specific color tone.
                  </p>
                  <div className="grid grid-cols-3 gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => setColorMode("system")}
                      className={`flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl text-xs font-mono font-semibold transition-all ${
                        colorMode === "system"
                          ? "bg-[var(--accent)] text-white shadow-sm"
                          : "bg-[var(--panel)] text-[var(--text-secondary)] border border-[var(--line)] hover:text-[var(--text)]"
                      }`}
                    >
                      <Monitor size={12} /> System
                    </button>
                    <button
                      type="button"
                      onClick={() => setColorMode("dark")}
                      className={`flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl text-xs font-mono font-semibold transition-all ${
                        colorMode === "dark"
                          ? "bg-[var(--accent)] text-white shadow-sm"
                          : "bg-[var(--panel)] text-[var(--text-secondary)] border border-[var(--line)] hover:text-[var(--text)]"
                      }`}
                    >
                      <Moon size={12} /> Dark
                    </button>
                    <button
                      type="button"
                      onClick={() => setColorMode("light")}
                      className={`flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl text-xs font-mono font-semibold transition-all ${
                        colorMode === "light"
                          ? "bg-[var(--accent)] text-white shadow-sm"
                          : "bg-[var(--panel)] text-[var(--text-secondary)] border border-[var(--line)] hover:text-[var(--text)]"
                      }`}
                    >
                      <Sun size={12} /> Light
                    </button>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-[var(--elevated)] border border-[var(--line)] space-y-2 flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-bold text-[var(--text)] flex items-center gap-2">
                      <Sliders size={14} className="text-[var(--accent-secondary)]" /> Accessibility & Motion
                    </span>
                    <p className="text-[11px] text-[var(--text-secondary)] mt-1">
                      Reduce animations, pulse effects, and mesh transitions across all charts and UI cards.
                    </p>
                  </div>
                  <div className="pt-2 flex items-center justify-between">
                    <span className="text-xs font-mono text-[var(--text)]">Prefers Reduced Motion:</span>
                    <button
                      type="button"
                      onClick={() => setReducedMotion(!reducedMotion)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        reducedMotion ? "bg-[var(--accent)]" : "bg-[var(--panel)] border border-[var(--line)]"
                      }`}
                      aria-pressed={reducedMotion}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          reducedMotion ? "translate-x-6" : "translate-x-1"
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Avatar Appearance Customizer */}
            <div className="p-6 sm:p-8 rounded-3xl bg-[var(--panel)] border border-[var(--line)] space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
                    <Sparkles size={18} className="text-[var(--accent-secondary)]" /> Avatar Appearance Presets
                  </h2>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">
                    Distinctive institutional avatar treatments. Updated instantly across your sidebar, navbar, and terminal sessions.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-[var(--muted)]">6 Distinct Presets</span>
                </div>
              </div>

              {/* 6 Avatar Presets Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
                {AVATAR_PRESETS.map((preset) => {
                  const isSelected = avatarPreset === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => handleAvatarSelect(preset.id)}
                      className={`group relative p-4 rounded-2xl border transition-all duration-200 flex flex-col items-center text-center ${
                        isSelected
                          ? "border-[var(--accent)] bg-[var(--elevated)] ring-2 ring-[var(--accent)]/30 shadow-md"
                          : "border-[var(--line)] hover:border-[var(--accent)]/50 bg-[var(--panel)] hover:bg-[var(--elevated)]/50"
                      }`}
                    >
                      {/* Checkmark Indicator */}
                      <div
                        className={`absolute top-2.5 right-2.5 w-4 h-4 rounded-full flex items-center justify-center transition-all ${
                          isSelected
                            ? "bg-[var(--accent)] text-white shadow-sm scale-100"
                            : "opacity-0 group-hover:opacity-40 border border-[var(--line)]"
                        }`}
                      >
                        {isSelected && <Check size={10} strokeWidth={3} />}
                      </div>

                      {/* Visibly Larger Preview */}
                      <div className="my-2 group-hover:scale-105 transition-transform">
                        <UserAvatar name={user.name} preset={preset.id} size="lg" />
                      </div>

                      {/* Preset Name & Tagline */}
                      <h4 className="text-xs font-bold text-[var(--text)] mt-1 group-hover:text-[var(--accent)] transition-colors">
                        {preset.name}
                      </h4>
                      <p className="text-[9px] text-[var(--text-secondary)] mt-0.5 line-clamp-1 font-mono">
                        {preset.tagline.split("&")[0]}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: ACCOUNT SECURITY */}
        {(activeTab === "overview" || activeTab === "security") && (
          <div id="security" className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
            {/* Password Change Form */}
            <div className="md:col-span-2 p-6 sm:p-7 rounded-3xl bg-[var(--panel)] border border-[var(--line)] space-y-5">
              <div>
                <h2 className="text-base font-bold text-[var(--text)] flex items-center gap-2">
                  <KeyRound size={17} className="text-[#F6BE76]" /> Account Password & Security
                </h2>
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  Rotate your master password. Passwords are salted with bcrypt rounds and verified server-side.
                </p>
              </div>

              {passwordSuccessMsg && (
                <div className="p-3.5 rounded-xl bg-[var(--gain)]/10 border border-[var(--gain)]/30 text-[var(--gain)] text-xs flex items-center gap-2">
                  <CheckCircle2 size={16} /> {passwordSuccessMsg}
                </div>
              )}

              {passwordErrorMsg && (
                <div className="p-3.5 rounded-xl bg-[var(--loss)]/10 border border-[var(--loss)]/30 text-[var(--loss)] text-xs flex items-center gap-2">
                  <AlertCircle size={16} /> {passwordErrorMsg}
                </div>
              )}

              <form onSubmit={handleChangePassword} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[var(--text)] mb-1.5">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--elevated)] border border-[var(--line)] text-xs text-[var(--text)] focus:outline-none focus:border-[#F6BE76] focus:ring-1 focus:ring-[#F6BE76] transition-all font-mono"
                    placeholder="••••••••••••"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[var(--text)] mb-1.5">
                      New Password
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                      minLength={8}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--elevated)] border border-[var(--line)] text-xs text-[var(--text)] focus:outline-none focus:border-[#F6BE76] focus:ring-1 focus:ring-[#F6BE76] transition-all font-mono"
                      placeholder="Minimum 8 characters"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[var(--text)] mb-1.5">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      minLength={8}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--elevated)] border border-[var(--line)] text-xs text-[var(--text)] focus:outline-none focus:border-[#F6BE76] focus:ring-1 focus:ring-[#F6BE76] transition-all font-mono"
                      placeholder="Repeat new password"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isChangingPassword}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-[#080D19] bg-[#F6BE76] hover:bg-[#F6BE76]/90 disabled:opacity-50 transition-all shadow-md shadow-[#F6BE76]/20"
                  >
                    {isChangingPassword ? (
                      <>
                        <Loader2 size={14} className="animate-spin" /> Verifying Credentials...
                      </>
                    ) : (
                      <>
                        <Lock size={14} /> Update Account Password
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Cryptographic Session Telemetry */}
            <div className="p-6 rounded-3xl bg-[var(--panel)] border border-[var(--line)] space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] font-mono flex items-center gap-1.5">
                <ShieldCheck size={14} className="text-[var(--gain)]" /> Session Telemetry
              </h3>

              <div className="space-y-3 pt-1 text-xs">
                <div className="p-3 rounded-2xl bg-[var(--elevated)] border border-[var(--line)] space-y-1">
                  <span className="text-[10px] text-[var(--muted)] font-mono uppercase">Signing Algorithm</span>
                  <p className="font-mono text-xs text-[var(--text)] font-bold">HMAC-SHA256 (JWT)</p>
                </div>

                <div className="p-3 rounded-2xl bg-[var(--elevated)] border border-[var(--line)] space-y-1">
                  <span className="text-[10px] text-[var(--muted)] font-mono uppercase">Cookie Transport</span>
                  <p className="font-mono text-[11px] text-[var(--text-secondary)]">HttpOnly, Secure, SameSite=Lax</p>
                </div>

                <div className="p-3 rounded-2xl bg-[var(--elevated)] border border-[var(--line)] space-y-1">
                  <span className="text-[10px] text-[var(--muted)] font-mono uppercase">CSRF Mitigation</span>
                  <p className="font-mono text-xs text-[var(--gain)] font-bold">Enforced on Mutations</p>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={logout}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-[var(--loss)] bg-[var(--loss)]/10 hover:bg-[var(--loss)]/20 border border-[var(--loss)]/30 transition-colors"
                >
                  <LogOut size={14} /> Terminate All Active Sessions
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
