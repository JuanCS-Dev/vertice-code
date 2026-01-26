"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

type Org = {
  org_id: string;
  name: string;
  created_at: string;
  owner_uid: string;
  role: string;
};

type MeResponse = {
  uid: string;
  default_org_id: string;
  orgs: Org[];
};

export default function SettingsPage() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newOrgName, setNewOrgName] = useState("");
  const [busy, setBusy] = useState(false);

  const effectiveOrgId = useMemo(() => {
    return activeOrgId || me?.default_org_id || null;
  }, [activeOrgId, me?.default_org_id]);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [meRes, activeRes] = await Promise.all([
        fetch("/api/gateway/me", { cache: "no-store" as RequestCache }),
        fetch("/api/org/active", { cache: "no-store" as RequestCache }),
      ]);
      if (!meRes.ok) throw new Error(await meRes.text());
      if (!activeRes.ok) throw new Error(await activeRes.text());
      const meData = (await meRes.json()) as MeResponse;
      const activeData = (await activeRes.json()) as { active_org_id: string | null };
      setMe(meData);
      setActiveOrgId(activeData.active_org_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed to load settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const selectOrg = useCallback(
    async (orgId: string | null) => {
      setBusy(true);
      try {
        if (orgId) {
          const res = await fetch("/api/org/select", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ orgId }),
          });
          if (!res.ok) throw new Error(await res.text());
        } else {
          const res = await fetch("/api/org/clear", { method: "POST" });
          if (!res.ok) throw new Error(await res.text());
        }
        await refresh();
      } finally {
        setBusy(false);
      }
    },
    [refresh],
  );

  const createOrg = useCallback(async () => {
    const name = newOrgName.trim();
    if (!name) return;
    setBusy(true);
    try {
      const res = await fetch("/api/gateway/orgs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!res.ok) throw new Error(await res.text());
      const created = (await res.json()) as Org;
      setNewOrgName("");
      await selectOrg(created.org_id);
    } finally {
      setBusy(false);
    }
  }, [newOrgName, selectOrg]);

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" }).catch(() => undefined);
    window.location.href = "/login";
  }, []);

  return (
    <div className="bg-background-light dark:bg-obsidian min-h-screen flex flex-col font-display text-white selection:bg-primary/30">
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
          <span className="text-sm text-white">Settings</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-white text-xs font-medium transition-all"
            onClick={() => void refresh()}
            type="button"
            disabled={loading || busy}
          >
            Refresh
          </button>
          <button
            className="px-3 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-obsidian text-xs font-bold transition-all"
            onClick={() => void logout()}
            type="button"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="flex-1 p-6 max-w-4xl w-full mx-auto">
        {error ? <div className="text-sm text-red-300 mb-4">{error}</div> : null}
        {loading || !me ? (
          <div className="text-sm text-gray-400">Loading…</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <section className="rounded-xl border border-border-dim bg-panel/50 backdrop-blur-md">
              <div className="px-4 py-3 border-b border-border-dim">
                <h2 className="text-sm font-semibold">Workspace</h2>
                <p className="text-xs text-gray-400 mt-1">Active org controls isolation for runs and artifacts.</p>
              </div>
              <div className="p-4">
                <div className="text-[11px] text-gray-500 font-mono mb-3">uid: {me.uid}</div>
                <ul className="divide-y divide-white/5">
                  {me.orgs.map((org) => {
                    const selected = effectiveOrgId === org.org_id;
                    return (
                      <li key={org.org_id} className="py-2 flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <div className="text-sm text-white truncate">{org.name}</div>
                          <div className="mt-1 text-[10px] text-gray-500 font-mono">
                            {org.org_id} · role:{org.role}
                          </div>
                        </div>
                        <button
                          className={
                            selected
                              ? "px-3 py-1.5 rounded-lg bg-primary text-obsidian text-xs font-bold"
                              : "px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-white text-xs font-medium"
                          }
                          onClick={() => void selectOrg(org.org_id)}
                          disabled={busy}
                          type="button"
                        >
                          {selected ? "Active" : "Use"}
                        </button>
                      </li>
                    );
                  })}
                </ul>
                <div className="mt-4 flex items-center justify-between gap-3">
                  <button
                    className="text-xs text-gray-300 hover:text-white"
                    onClick={() => void selectOrg(null)}
                    disabled={busy}
                    type="button"
                  >
                    Reset to default org
                  </button>
                  <div className="text-[10px] text-gray-500 font-mono">
                    default: {me.default_org_id}
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-xl border border-border-dim bg-panel/50 backdrop-blur-md">
              <div className="px-4 py-3 border-b border-border-dim">
                <h2 className="text-sm font-semibold">Create Org</h2>
                <p className="text-xs text-gray-400 mt-1">Creates a new org and switches to it.</p>
              </div>
              <div className="p-4">
                <div className="flex gap-2">
                  <input
                    className="flex-1 bg-panel border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                    placeholder="Org name (e.g. Acme)"
                    value={newOrgName}
                    onChange={(e) => setNewOrgName(e.target.value)}
                    disabled={busy}
                  />
                  <button
                    className="px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-obsidian text-sm font-bold transition-all disabled:opacity-50"
                    onClick={() => void createOrg()}
                    disabled={busy || !newOrgName.trim()}
                    type="button"
                  >
                    Create
                  </button>
                </div>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
