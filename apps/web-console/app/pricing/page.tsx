"use client";

import Link from "next/link";
import { useState } from "react";

type PricingTier = {
  id: string;
  name: string;
  price_monthly: number | null;
  price_yearly: number | null;
  popular?: boolean;
  contact?: boolean;
  features: string[];
};

const tiers: PricingTier[] = [
  {
    id: "free",
    name: "Free",
    price_monthly: 0,
    price_yearly: 0,
    features: [
      "Start exploring the future of code",
      "50 requests/day",
      "100K tokens/month",
      "Gemini 3 Flash",
      "Community support",
    ],
  },
  {
    id: "developer",
    name: "Developer",
    price_monthly: 19,
    price_yearly: 190,
    popular: true,
    features: [
      "For individual builders shipping fast",
      "1,000 requests/day",
      "5M tokens/month",
      "Gemini 3 Pro + Flash",
      "Priority support",
      "Advanced analytics",
    ],
  },
  {
    id: "team",
    name: "Team",
    price_monthly: 49,
    price_yearly: 490,
    features: [
      "Collaborative AI for ambitious teams",
      "5,000 requests/day",
      "25M tokens/month",
      "All models including Pro",
      "Team collaboration",
      "Shared workspaces",
      "Admin controls",
    ],
  },
];

export default function PricingPage() {
  const [yearly, setYearly] = useState(false);

  const handleUpgrade = async (tierId: string) => {
    if (tierId === "enterprise") {
      window.location.href = "mailto:sales@vertice.ai?subject=Enterprise%20Inquiry";
      return;
    }

    try {
      const res = await fetch("/api/gateway/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yearly }),
      });

      if (!res.ok) throw new Error(await res.text());

      const data = await res.json();
      window.location.href = data.checkout_url;
    } catch (e) {
      console.error("Checkout failed:", e);
    }
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
          <span className="text-sm text-white">Pricing</span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/login"
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Login
          </Link>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-lg bg-primary text-obsidian text-sm font-bold hover:bg-primary/90 transition-all"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 py-16 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Hero */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold mb-4">
              Simple, transparent pricing
            </h1>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Start free and scale as you grow. No hidden fees.
            </p>
          </div>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center gap-4 mb-12">
            <span
              className={`text-sm ${!yearly ? "text-white" : "text-gray-500"}`}
            >
              Monthly
            </span>
            <button
              onClick={() => setYearly(!yearly)}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                yearly ? "bg-primary" : "bg-white/10"
              }`}
            >
              <div
                className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-transform ${
                  yearly ? "translate-x-8" : "translate-x-1"
                }`}
              />
            </button>
            <span
              className={`text-sm ${yearly ? "text-white" : "text-gray-500"}`}
            >
              Yearly
              <span className="ml-2 text-xs text-neon-emerald">Save 17%</span>
            </span>
          </div>

          {/* Pricing Cards */}
          <div className="grid md:grid-cols-3 gap-6">
            {tiers.map((tier) => (
              <div
                key={tier.id}
                className={`relative rounded-xl border bg-panel/50 backdrop-blur-md p-6 flex flex-col ${
                  tier.popular
                    ? "border-primary shadow-glow-cyan"
                    : "border-border-dim"
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-obsidian text-xs font-bold rounded-full">
                    Most Popular
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-2">{tier.name}</h3>
                  {tier.contact ? (
                    <div className="text-2xl font-bold">Custom</div>
                  ) : (
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold">
                        ${yearly ? tier.price_yearly : tier.price_monthly}
                      </span>
                      <span className="text-gray-500">
                        /{yearly ? "year" : "mo"}
                      </span>
                    </div>
                  )}
                </div>

                <ul className="flex-1 space-y-3 mb-6">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <span className="material-symbols-outlined text-primary text-lg">
                        check_circle
                      </span>
                      <span className="text-sm text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleUpgrade(tier.id)}
                  className={`w-full py-3 rounded-lg font-bold text-sm transition-all ${
                    tier.popular
                      ? "bg-primary text-obsidian hover:bg-primary/90"
                      : tier.contact
                      ? "border border-white/10 bg-white/5 hover:bg-white/10 text-white"
                      : "border border-primary/30 bg-primary/10 text-primary hover:bg-primary/20"
                  }`}
                >
                  {tier.contact
                    ? "Contact Sales"
                    : tier.price_monthly === 0
                    ? "Get Started Free"
                    : `Upgrade to ${tier.name}`}
                </button>
              </div>
            ))}
          </div>

          {/* FAQ Section */}
          <div className="mt-20 max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold text-center mb-8">
              Frequently Asked Questions
            </h2>
            <div className="space-y-4">
              {[
                {
                  q: "Can I cancel anytime?",
                  a: "Yes, you can cancel your subscription at any time. You'll continue to have access until the end of your billing period.",
                },
                {
                  q: "What payment methods do you accept?",
                  a: "We accept all major credit cards (Visa, Mastercard, American Express) through our secure payment partner, Stripe.",
                },
                {
                  q: "Is there a free trial?",
                  a: "The Free tier is always free with no time limit. For Pro features, we offer a 14-day money-back guarantee.",
                },
                {
                  q: "What happens if I exceed my limits?",
                  a: "You'll receive a notification when approaching your limits. Requests beyond the limit will be queued until the next period or you upgrade.",
                },
              ].map((faq) => (
                <div
                  key={faq.q}
                  className="rounded-xl border border-border-dim bg-panel/50 p-4"
                >
                  <h4 className="font-medium text-white mb-2">{faq.q}</h4>
                  <p className="text-sm text-gray-400">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border-dim py-8 px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-gray-500">
          <span>© 2026 Vertice Studio</span>
          <div className="flex gap-6">
            <Link href="/docs" className="hover:text-primary transition-colors">
              Documentation
            </Link>
            <Link href="#" className="hover:text-primary transition-colors">
              Terms
            </Link>
            <Link href="#" className="hover:text-primary transition-colors">
              Privacy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
