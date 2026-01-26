import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        obsidian: "#0B1416",
        "obsidian-deep": "#050a0a",
        "background-light": "#0B1416",
        "background-dark": "#050a0a",
        "surface-dark": "#0B1416",
        "surface-card": "#111C1E",
        "border-color": "#1F2E33",
        "text-main": "#E5E7EB",
        "text-muted": "#94A3B8",
        "text-subtle": "#64748B",
        primary: "#00E5FF", // Alias for porting ease
        "neon-cyan": "#00E5FF",
        "neon-cyan-dim": "#00C4D9",
        "neon-emerald": "#10B981",
        "neon-amber": "#F59E0B",
        "panel": "#111C1E",
        "panel-light": "#162629",
        "border-dim": "#1F2E33",
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "matrix-pattern":
          "linear-gradient(rgba(0,229,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,0.06) 1px, transparent 1px)",
      },
      boxShadow: {
        glow: "0 0 30px -10px rgba(0,229,255,0.35)",
        "glow-cyan": "0 0 20px rgba(0,229,255,0.35)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
        "fade-in": "fade-in 240ms ease-out both",
        "fade-in-up": "fade-in-up 420ms ease-out both",
        "flow": "flow 1.2s linear infinite",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px #00E5FF" },
          "100%": { boxShadow: "0 0 20px #00E5FF" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        flow: {
          "0%": { strokeDashoffset: "0" },
          "100%": { strokeDashoffset: "-20" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
