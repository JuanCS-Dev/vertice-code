"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

type Subscription = {
  org_id: string;
  tier: string;
  status: string;
  is_active: boolean;
  is_pro: boolean;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
};

type UsageSummary = {
  metric: string;
  total: number;
  limit: number;
  tier: string;
};

export default function BillingSettingsPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [subRes, tokensRes, requestsRes] = await Promise.all([
        fetch("/api/gateway/billing/subscription"),
        fetch("/api/gateway/billing/usage/tokens"),
        fetch("/api/gateway/billing/usage/requests?days=1"),
      ]);

      if (subRes.ok) {
        setSubscription(await subRes.json());
      }

      const usageData: UsageSummary[] = [];
      if (tokensRes.ok) usageData.push(await tokensRes.json());
      if (requestsRes.ok) usageData.push(await requestsRes.json());
      setUsage(usageData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load billing data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleManageSubscription = async () => {
    setBusy(true);
    try {
      const res = await fetch("/api/gateway/billing/portal", { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      window.location.href = data.portal_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to open portal");
    } finally {
      setBusy(false);
    }
  };

  const handleUpgrade = async () => {
    setBusy(true);
    try {
      const res = await fetch("/api/gateway/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yearly: false }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      window.location.href = data.checkout_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start checkout");
    } finally {
      setBusy(false);
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return "N/A";
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const getUsagePercent = (total: number, limit: number) => {
    if (limit <= 0) return 0;
    return Math.min(100, Math.round((total / limit) * 100));
  };

  return (
    <div className="bg-obsidian min-h-screen flex flex-col font-display text-white selection:bg-primary/30">
      {/* Header */}
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-border-dim bg-panel/90 backdrop-blur-md px-6 py-3">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-primary text-sm font-bold">
            Vertice
          </Link>
          <div className="h-6 w-px bg-border-dim"></div>
          <Link href="/dashboard" className="text-sm text-gray-400 hover:text-white">
            Dashboard
          </Link>
          <span className="text-gray-600">/</span>
          <Link href="/settings" className="text-sm text-gray-400 hover:text-white">
            Settings
          </Link>
          <span className="text-gray-600">/</span>
          <span className="text-sm text-white">Billing</span>
        </div>
        <button
          onClick={() => void refresh()}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-white text-xs font-medium transition-all disabled:opacity-50"
        >
          Refresh
        </button>
      </header>

      {/* Main */}
      <main className="flex-1 p-6 max-w-4xl w-full mx-auto">
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-sm text-gray-400">Loading billing data…</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Current Plan */}
            <section className="rounded-xl border border-border-dim bg-panel/50 backdrop-blur-md">
              <div className="px-4 py-3 border-b border-border-dim">
                <h2 className="text-sm font-semibold">Current Plan</h2>
              </div>
              <div className="p-4">
                {subscription ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-2xl font-bold capitalize">
                          {subscription.tier}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Status:{" "}
                          <span
                            className={
                              subscription.is_active
                                ? "text-neon-emerald"
                                : "text-neon-amber"
                            }
                          >
                            {subscription.status}
                          </span>
                        </div>
                      </div>
                      {subscription.is_pro && (
                        <div className="px-3 py-1 bg-primary/10 text-primary text-xs font-bold rounded-full">
                          PRO
                        </div>
                      )}
                    </div>

                    {subscription.current_period_end && (
                      <div className="text-xs text-gray-400">
                        {subscription.cancel_at_period_end
                          ? "Cancels on "
                          : "Renews on "}
                        {formatDate(subscription.current_period_end)}
                      </div>
                    )}

                    <div className="flex gap-2 pt-2">
                      {subscription.is_pro ? (
                        <button
                          onClick={handleManageSubscription}
                          disabled={busy}
                          className="px-4 py-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-white text-sm font-medium transition-all disabled:opacity-50"
                        >
                          Manage Subscription
                        </button>
                      ) : (
                        <button
                          onClick={handleUpgrade}
                          disabled={busy}
                          className="px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-obsidian text-sm font-bold transition-all disabled:opacity-50"
                        >
                          Upgrade to Pro
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-gray-400">No subscription data</div>
                )}
              </div>
            </section>

            {/* Usage */}
            <section className="rounded-xl border border-border-dim bg-panel/50 backdrop-blur-md">
              <div className="px-4 py-3 border-b border-border-dim">
                <h2 className="text-sm font-semibold">Usage</h2>
              </div>
              <div className="p-4 space-y-4">
                {usage.length > 0 ? (
                  usage.map((u) => {
                    const percent = getUsagePercent(u.total, u.limit);
                    return (
                      <div key={u.metric}>
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className="capitalize text-white">{u.metric}</span>
                          <span className="text-gray-400">
                            {u.total.toLocaleString()} /{" "}
                            {u.limit < 0 ? "∞" : u.limit.toLocaleString()}
                          </span>
                        </div>
                        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              percent > 90
                                ? "bg-red-500"
                                : percent > 70
                                ? "bg-neon-amber"
                                : "bg-primary"
                            }`}
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-gray-400 text-sm">No usage data</div>
                )}
              </div>
            </section>

            {/* Upgrade CTA (for free users) */}
            {subscription && !subscription.is_pro && (
              <section className="md:col-span-2 rounded-xl border border-primary/30 bg-gradient-to-r from-primary/5 to-neon-emerald/5 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold mb-1">Unlock Pro Features</h3>
                    <p className="text-sm text-gray-400">
                      Get 20x more requests, access to Gemini 3 Pro, and priority support.
                    </p>
                  </div>
                  <Link
                    href="/pricing"
                    className="px-6 py-3 rounded-lg bg-primary text-obsidian font-bold hover:bg-primary/90 transition-all"
                  >
                    View Plans
                  </Link>
                </div>
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
