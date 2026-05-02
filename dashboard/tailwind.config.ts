import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Page + surface
        page: "var(--page)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        // Border / divider
        rule: "var(--rule)",
        "rule-strong": "var(--rule-strong)",
        // Text hierarchy
        ink: "var(--ink)",
        "ink-2": "var(--ink-2)",
        "ink-3": "var(--ink-3)",
        // Primary navy — slightly brighter at 500 for a contemporary feel
        navy: {
          50:  "hsl(217, 80%, 96%)",
          100: "hsl(217, 75%, 92%)",
          200: "hsl(217, 70%, 84%)",
          300: "hsl(217, 65%, 70%)",
          400: "hsl(217, 70%, 56%)",
          500: "hsl(218, 80%, 46%)",
          600: "hsl(218, 75%, 36%)",
          700: "hsl(218, 65%, 26%)",
          800: "hsl(218, 60%, 18%)",
          900: "hsl(218, 60%, 12%)",
        },
        // Restrained gold (used VERY sparingly — logo, key emphasis only)
        gold: {
          100: "hsl(40, 80%, 92%)",
          400: "hsl(38, 75%, 56%)",
          500: "hsl(38, 75%, 46%)",
          600: "hsl(36, 70%, 38%)",
          700: "hsl(34, 70%, 30%)",
        },
        // Verdict semantic colors
        verdict: {
          low: {
            bg: "hsl(160, 50%, 96%)",
            border: "hsl(160, 40%, 70%)",
            text: "hsl(160, 50%, 26%)",
          },
          mixed: {
            bg: "hsl(40, 80%, 96%)",
            border: "hsl(38, 70%, 70%)",
            text: "hsl(34, 70%, 28%)",
          },
          high: {
            bg: "hsl(0, 70%, 97%)",
            border: "hsl(0, 60%, 75%)",
            text: "hsl(0, 60%, 35%)",
          },
        },
      },
      fontFamily: {
        serif: ['"Source Serif 4"', '"Source Serif Pro"', "Georgia", "serif"],
        sans: ['"Inter"', "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "monospace"],
      },
      boxShadow: {
        // Refactoring UI: shadows replace borders for subtler separation
        card: "0 1px 2px hsla(213, 30%, 12%, 0.06), 0 2px 6px hsla(213, 30%, 12%, 0.04)",
        "card-hover": "0 2px 4px hsla(213, 30%, 12%, 0.08), 0 8px 16px hsla(213, 30%, 12%, 0.06)",
        // Inset for input wells
        inset: "inset 0 1px 2px hsla(213, 30%, 12%, 0.06)",
      },
      letterSpacing: {
        tightish: "-0.011em",
      },
      maxWidth: {
        "prose-narrow": "34em",
      },
    },
  },
  plugins: [],
};

export default config;
