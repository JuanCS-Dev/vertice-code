// src/components/auth/SignIn.tsx
"use client";

import React, { useState } from "react";
import { GoogleAuthProvider, signInWithPopup, signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    setError("");
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
      router.push("/chat");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      await signInWithEmailAndPassword(auth, email, password);
      router.push("/chat");
    } catch (err: any) {
      setError("Invalid credentials. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#050505] relative overflow-hidden text-foreground">
      {/* Background Ambience */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-cyan-500/5 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.03] pointer-events-none" />

      <div className="w-full max-w-md relative z-10 p-8">
        {/* Header */}
        <div className="text-center mb-10 space-y-3">
          <div className="inline-block px-3 py-1 border border-white/5 rounded-full bg-white/[0.02] mb-6 backdrop-blur-sm">
            <span className="text-[10px] font-medium text-zinc-400 tracking-widest uppercase">Access Required</span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Identify Yourself
          </h2>
          <p className="text-sm text-zinc-400">
            Enter the sovereign domain.
          </p>
        </div>

        <div className="bg-[#0A0A0A]/50 backdrop-blur-xl border border-white/5 rounded-2xl p-8 shadow-2xl transition-all hover:border-white/10 hover:shadow-[0_0_50px_rgba(0,0,0,0.5)]">
          {error && (
            <div className="mb-6 p-3 bg-red-500/5 border border-red-500/10 rounded-lg text-red-400 text-xs flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
              {error}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleEmailSignIn}>
            <div className="space-y-4">
              <div className="group">
                <Label htmlFor="email" className="text-xs font-medium text-zinc-500 uppercase tracking-widest mb-2 block group-focus-within:text-cyan-400 transition-colors">
                  Email Protocol
                </Label>
                <Input
                  id="email"
                  type="email"
                  required
                  className="bg-transparent border-0 border-b border-white/10 rounded-none px-0 py-2 text-white placeholder:text-zinc-800 focus-visible:ring-0 focus-visible:border-cyan-500 transition-all h-auto font-mono text-sm"
                  placeholder="user@domain.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="group">
                <Label htmlFor="password" className="text-xs font-medium text-zinc-500 uppercase tracking-widest mb-2 block group-focus-within:text-cyan-400 transition-colors">
                  Security Token
                </Label>
                <Input
                  id="password"
                  type="password"
                  required
                  className="bg-transparent border-0 border-b border-white/10 rounded-none px-0 py-2 text-white placeholder:text-zinc-800 focus-visible:ring-0 focus-visible:border-cyan-500 transition-all h-auto font-mono text-sm"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className={cn(
                "w-full h-12 bg-white hover:bg-zinc-200 text-black font-semibold rounded-lg transition-all duration-300 relative overflow-hidden group",
                isLoading && "opacity-80"
              )}
            >
              <span className="relative z-10 flex items-center justify-center gap-2">
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Initialize Session <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </span>
            </Button>
          </form>

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/5" />
              </div>
              <div className="relative flex justify-center text-[10px] uppercase tracking-widest font-mono">
                <span className="bg-[#0A0A0A] px-2 text-zinc-600">
                  Or authenticate via
                </span>
              </div>
            </div>

            <div className="mt-6">
              <Button
                onClick={handleGoogleSignIn}
                disabled={isLoading}
                variant="outline"
                className="w-full h-12 border-white/5 hover:bg-white/5 hover:text-white hover:border-white/10 transition-all text-xs flex items-center justify-center gap-3 bg-transparent text-zinc-400"
              >
                <svg className="h-4 w-4" viewBox="0 0 24 24">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Google Identity
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
