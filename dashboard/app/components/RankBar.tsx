// RankBar — visualize a fraud's rank within its cohort with a bootstrap CI.
// Cleaner, lighter, more information-dense than the dark version.

interface RankBarProps {
  rank: number;
  total: number;
  ciLower?: number;
  ciUpper?: number;
  expected?: number;
  height?: "sm" | "md";
  toneByRank?: boolean; // color the marker by quartile
}

export function RankBar({
  rank,
  total,
  ciLower,
  ciUpper,
  expected,
  height = "md",
  toneByRank = false,
}: RankBarProps) {
  const pct = (n: number) => Math.max(0, Math.min(100, ((n - 0.5) / total) * 100));
  const widthPct =
    ciLower !== undefined && ciUpper !== undefined
      ? Math.max(0, ((ciUpper - ciLower + 1) / total) * 100)
      : 0;
  const ciOffset = ciLower !== undefined ? Math.max(0, ((ciLower - 1) / total) * 100) : 0;
  const h = height === "md" ? "h-6" : "h-4";

  let markerColor = "bg-navy-700";
  if (toneByRank) {
    const quartile = rank / total;
    if (quartile <= 0.25) markerColor = "bg-verdict-high-text";
    else if (quartile <= 0.5) markerColor = "bg-verdict-mixed-text";
    else markerColor = "bg-verdict-low-text";
  }

  return (
    <div className="w-full">
      <div className={`relative ${h} rounded bg-surface-2 border border-rule overflow-hidden`}>
        {widthPct > 0 && (
          <div
            className="absolute inset-y-0 bg-navy-100"
            style={{ left: `${ciOffset}%`, width: `${widthPct}%` }}
            aria-hidden="true"
          />
        )}
        {expected !== undefined && (
          <div
            className="absolute inset-y-0 w-px bg-rule-strong"
            style={{ left: `${pct(expected)}%` }}
            aria-hidden="true"
          />
        )}
        <div
          className={`absolute inset-y-0 w-1 ${markerColor}`}
          style={{ left: `${pct(rank)}%` }}
          aria-hidden="true"
        />
      </div>
      <div className="mt-1 flex justify-between text-[10px] num text-ink-3">
        <span>most anomalous (1)</span>
        <span>least ({total})</span>
      </div>
    </div>
  );
}
