// Stat — single source of truth for displaying numbers.
// Tabular monospace, fixed precision, baseline-aligned (not center).

import type { ReactNode } from "react";

type Tone = "default" | "navy" | "gold" | "low" | "mixed" | "high" | "muted";

const TONE: Record<Tone, string> = {
  default: "text-ink",
  navy: "text-navy-700",
  gold: "text-gold-600",
  low: "text-verdict-low-text",
  mixed: "text-verdict-mixed-text",
  high: "text-verdict-high-text",
  muted: "text-ink-3",
};

interface StatProps {
  value: number | string;
  label?: ReactNode;
  unit?: string;
  precision?: number;
  tone?: Tone;
  size?: "sm" | "md" | "lg" | "xl";
  hint?: ReactNode;
  className?: string;
}

const SIZE: Record<NonNullable<StatProps["size"]>, string> = {
  sm: "text-base",
  md: "text-2xl",
  lg: "text-[2.5rem] leading-none",
  xl: "text-[3.5rem] leading-none",
};

export function formatNumber(v: number | string, precision = 2): string {
  if (typeof v === "string") return v;
  if (!Number.isFinite(v)) return "—";
  if (v === 0) return "0";
  const abs = Math.abs(v);
  if (abs > 0 && abs < 0.001) return v.toExponential(2).replace("e", "×10^");
  return v.toFixed(precision);
}

export function Stat({
  value,
  label,
  unit,
  precision = 2,
  tone = "default",
  size = "md",
  hint,
  className = "",
}: StatProps) {
  const formatted = typeof value === "number" ? formatNumber(value, precision) : value;
  return (
    <div className={className}>
      {label !== undefined && (
        <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-2">
          {label}
        </div>
      )}
      <div className={`num font-semibold ${TONE[tone]} ${SIZE[size]}`}>
        {formatted}
        {unit && <span className="text-ink-3 text-base font-normal ml-1">{unit}</span>}
      </div>
      {hint && <div className="text-xs text-ink-3 mt-1.5 leading-relaxed">{hint}</div>}
    </div>
  );
}

export function RankStat({
  rank,
  total,
  tone = "default",
  size = "md",
}: {
  rank: number;
  total: number;
  tone?: Tone;
  size?: "sm" | "md" | "lg" | "xl";
}) {
  return (
    <div className={`num font-semibold ${TONE[tone]} ${SIZE[size]}`}>
      {rank}
      <span className="text-ink-3 font-normal">{` / ${total}`}</span>
    </div>
  );
}
