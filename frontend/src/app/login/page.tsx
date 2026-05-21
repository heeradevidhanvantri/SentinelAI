"use client";

import { useState } from "react";
import { Zap, AlertCircle } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const { login, error, clearError, loading: authLoading } = useAuth();
  const [email, setEmail] = useState("admin@sentinelai.io");
  const [password, setPassword] = useState("sentinel123");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setLocalError(null);
    clearError();

    try {
      await login(email, password);
    } catch (err) {
      if (err instanceof ApiError) {
        setLocalError(err.detail || "Invalid email or password");
      } else {
        setLocalError("Unable to sign in. Check your connection and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  const displayError = localError || error;

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-md rounded-xl border border-border/50 bg-card/60 p-8 shadow-xl backdrop-blur-xl">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sentinel-cyan/20">
            <Zap className="h-6 w-6 text-sentinel-cyan" />
          </div>
          <div>
            <h1 className="text-xl font-bold">SentinelAI</h1>
            <p className="text-sm text-muted-foreground">Sign in to your SRE platform</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-1.5 block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full rounded-lg border border-border bg-secondary/50 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sentinel-cyan"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1.5 block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full rounded-lg border border-border bg-secondary/50 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sentinel-cyan"
            />
          </div>

          {displayError && (
            <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{displayError}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-sentinel-cyan py-2.5 text-sm font-medium text-background transition-colors hover:bg-sentinel-cyan/90 disabled:opacity-50"
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          API: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
        </p>
      </div>
    </div>
  );
}
