"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Lock, Mail, ArrowRight, AlertCircle, Loader2, CheckCircle2, Shield } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, login, isLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validate relative return path safely
  const rawNext = searchParams.get("next");
  const targetNext =
    rawNext && rawNext.startsWith("/") && !rawNext.startsWith("//")
      ? rawNext
      : "/dashboard";

  // If already authenticated, redirect
  useEffect(() => {
    if (user && !isLoading) {
      router.replace(targetNext);
    }
  }, [user, isLoading, targetNext, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#080D19] flex flex-col items-center justify-center p-4">
        <Loader2 size={32} className="animate-spin text-[#8E91FF] mb-3" />
        <p className="text-xs text-[#A6B6CC] font-mono">Verifying QuantWeave session...</p>
      </div>
    );
  }

  if (user) {
    return (
      <div className="min-h-screen bg-[#080D19] flex flex-col items-center justify-center p-4 text-center">
        <div className="p-8 rounded-2xl bg-[#101A2B] border border-[#26344A] max-w-sm w-full space-y-4 shadow-2xl">
          <div className="w-12 h-12 rounded-2xl bg-[#54DCC5]/10 text-[#54DCC5] flex items-center justify-center mx-auto border border-[#54DCC5]/30">
            <CheckCircle2 size={24} />
          </div>
          <h2 className="text-base font-bold text-[#F2F4FF]">Already Authenticated</h2>
          <p className="text-xs text-[#A6B6CC] leading-relaxed">
            Signed in as <strong className="text-[#F2F4FF]">{user.name}</strong> ({user.email}).
          </p>
          <Link
            href={targetNext}
            className="inline-flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-[#8E91FF] text-[#080D19] font-bold text-xs hover:bg-[#7b7eff] transition-all shadow-lg shadow-[#8E91FF]/20"
          >
            Open Workspace <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError("Please provide both email address and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email.trim(), password);
      router.replace(targetNext);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to sign in";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080D19] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background radial glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-r from-[#8E91FF]/15 via-[#54DCC5]/10 to-transparent blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        <Link href="/" className="inline-flex items-center gap-3 mb-6 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#8E91FF] via-[#54DCC5] to-[#F6BE76] p-[1.5px] shadow-lg shadow-[#8E91FF]/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#080D19] rounded-[9px] flex items-center justify-center font-black text-sm text-[#8E91FF] font-mono">
              QW
            </div>
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-[#F2F4FF]">
            QuantWeave
          </span>
        </Link>
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-[#F2F4FF]">
          Sign in to Terminal
        </h2>
        <p className="mt-1.5 text-xs text-[#A6B6CC]">
          Authentication required for quantitative research workspace
        </p>

        {rawNext && rawNext !== "/dashboard" && (
          <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#142035] border border-[#26344A] text-[11px] text-[#8E91FF]">
            <Shield size={12} />
            <span>Sign in to access protected module: <strong>{rawNext}</strong></span>
          </div>
        )}
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4 sm:px-0">
        <div className="bg-[#101A2B] py-8 px-6 sm:px-10 shadow-2xl rounded-2xl border border-[#26344A]">
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 text-xs flex items-start gap-2.5">
              <AlertCircle size={16} className="text-rose-400 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-semibold uppercase tracking-wider text-[#A6B6CC] mb-1.5"
              >
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A6B6CC]/60">
                  <Mail size={15} />
                </div>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@quantweave.test"
                  disabled={isSubmitting}
                  className="w-full pl-10 pr-3.5 py-2.5 bg-[#080D19] border border-[#26344A] rounded-xl text-xs text-[#F2F4FF] placeholder-[#A6B6CC]/50 focus:outline-none focus:border-[#8E91FF] focus:ring-1 focus:ring-[#8E91FF] transition-colors disabled:opacity-50"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="password"
                  className="block text-xs font-semibold uppercase tracking-wider text-[#A6B6CC]"
                >
                  Password
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A6B6CC]/60">
                  <Lock size={15} />
                </div>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  disabled={isSubmitting}
                  className="w-full pl-10 pr-3.5 py-2.5 bg-[#080D19] border border-[#26344A] rounded-xl text-xs text-[#F2F4FF] placeholder-[#A6B6CC]/50 focus:outline-none focus:border-[#8E91FF] focus:ring-1 focus:ring-[#8E91FF] transition-colors disabled:opacity-50"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-[#8E91FF] hover:bg-[#7b7eff] text-[#080D19] font-bold text-xs tracking-wide transition-all shadow-md hover:shadow-lg shadow-[#8E91FF]/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In to QuantWeave</span>
                    <ArrowRight size={15} />
                  </>
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 pt-5 border-t border-[#26344A] text-center">
            <p className="text-xs text-[#A6B6CC]">
              Need a research workspace?{" "}
              <Link
                href={rawNext ? `/register?next=${encodeURIComponent(rawNext)}` : "/register"}
                className="font-semibold text-[#8E91FF] hover:underline"
              >
                Create an account
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link
            href="/"
            className="text-xs text-[#A6B6CC]/70 hover:text-[#F2F4FF] transition-colors"
          >
            ← Back to platform homepage
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#080D19] flex items-center justify-center">
          <Loader2 size={32} className="animate-spin text-[#8E91FF]" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
