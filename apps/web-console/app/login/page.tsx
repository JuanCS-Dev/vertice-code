"use client";

import { useCallback, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { getFirebaseAuth, getGoogleProvider } from "../../lib/firebaseClient";
import { signInWithPopup } from "firebase/auth";

function LoginContent() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const search = useSearchParams();
  const nextPath = search.get("next") || "/dashboard";

  const onLogin = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const auth = getFirebaseAuth();
      const cred = await signInWithPopup(auth, getGoogleProvider());
      const idToken = await cred.user.getIdToken(true);
      const res = await fetch("/api/auth/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idToken }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "failed to create session");
      }
      window.location.assign(nextPath);
    } catch (e) {
      setError(e instanceof Error ? e.message : "login failed");
    } finally {
      setLoading(false);
    }
  }, [nextPath]);

  return (
    <div className="w-full max-w-md bg-panel/70 border border-border-dim/50 rounded-2xl p-6">
      <h1 className="text-xl font-bold tracking-tight">Sign in</h1>
      <p className="text-sm text-gray-400 mt-1">Google-only authentication.</p>

      <button
        onClick={onLogin}
        disabled={loading}
        className="mt-6 w-full rounded-lg bg-primary text-panel py-2 text-sm font-semibold hover:bg-primary/90 disabled:opacity-60"
      >
        {loading ? "Signing in..." : "Continue with Google"}
      </button>

      {error ? <p className="mt-4 text-sm text-red-400">{error}</p> : null}
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-obsidian text-white flex items-center justify-center p-6">
      <Suspense fallback={<div className="text-gray-400">Loading login...</div>}>
        <LoginContent />
      </Suspense>
    </div>
  );
}
