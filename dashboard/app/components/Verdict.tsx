// Verdict — descriptive summary card for a scan result.
// EXPLICITLY NOT a "fraud likelihood" or composite suspicion score.
// Describes the 5 cohort ranks in plain English and bins them into one of
// three buckets based on rank distribution.
//
// Bucket rules (deliberately simple, designed to be defensible):
//   - "Low novelty"      : 0-1 cohorts where rank <= top 33% of cohort
//   - "Mixed signal"     : 2 cohorts in top 33%
//   - "Elevated novelty" : 3+ cohorts in top 33%
//
// We pair every bucket with: median rank, percentile, # of cohorts in top tier,
// and a hard disclaimer that this is not a fraud verdict.

interface CohortResult {
  cohort_id: string;
  rank_if_added: number;
  n_after_add: number;
  percentile_within_cohort: number;
  fraud_score: number | null;
  score_mean: number;
}

const COHORT_LABEL: Record<string, string> = {
  ENE: "Enron", WCOM: "WorldCom", TYC: "Tyco",
  HRC: "HealthSouth", VRX: "Valeant", LEH: "Lehman",
};

interface VerdictProps {
  results: CohortResult[];
}

interface Bucket {
  label: string;
  bg: string;
  border: string;
  text: string;
  borderTopClass: string;
  oneliner: (cohortsInTop: number, n: number) => string;
}

const BUCKETS: Record<"low" | "mixed" | "high", Bucket> = {
  low: {
    label: "Low novelty across cohorts",
    bg: "bg-verdict-low-bg",
    border: "border-verdict-low-border",
    text: "text-verdict-low-text",
    borderTopClass: "accent-border-top--low",
    oneliner: (k, n) =>
      `This filing's MD&A is not particularly anomalous against any of the ${n} fraud-cohort baselines. ${k} cohorts placed it in the top tier.`,
  },
  mixed: {
    label: "Mixed signal",
    bg: "bg-verdict-mixed-bg",
    border: "border-verdict-mixed-border",
    text: "text-verdict-mixed-text",
    borderTopClass: "accent-border-top--mixed",
    oneliner: (k, n) =>
      `This filing's MD&A reads more anomalous than the historical fraud in ${k} of ${n} cohorts. The signal is not consistent across cohorts.`,
  },
  high: {
    label: "Elevated novelty across multiple cohorts",
    bg: "bg-verdict-high-bg",
    border: "border-verdict-high-border",
    text: "text-verdict-high-text",
    borderTopClass: "accent-border-top--high",
    oneliner: (k, n) =>
      `This filing's MD&A is more anomalous than the historical fraud in ${k} of ${n} cohorts. That is the same pattern Lehman Brothers' FY2007 10-K showed.`,
  },
};

function bucketFor(results: CohortResult[]): "low" | "mixed" | "high" {
  // "Top tier" = rank places it in top 1/3 of the cohort
  const inTop = results.filter(
    (r) => r.rank_if_added / r.n_after_add <= 0.33
  ).length;
  if (inTop >= 3) return "high";
  if (inTop === 2) return "mixed";
  return "low";
}

function median(nums: number[]): number {
  if (nums.length === 0) return NaN;
  const s = [...nums].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

export function Verdict({ results }: VerdictProps) {
  if (!results.length) return null;
  const bucket = bucketFor(results);
  const b = BUCKETS[bucket];
  const inTop = results.filter((r) => r.rank_if_added / r.n_after_add <= 0.33).length;
  const n = results.length;
  const medRank = median(results.map((r) => r.rank_if_added));
  const medPct = median(results.map((r) => r.percentile_within_cohort));
  const beat = results.filter(
    (r) => r.fraud_score !== null && r.score_mean > r.fraud_score!
  ).length;

  return (
    <section
      className={`relative ${b.bg} ${b.borderTopClass} rounded-md shadow-card overflow-hidden`}
    >
      <div className="px-6 md:px-8 py-7 md:py-8">
        <div className="flex items-baseline gap-3 mb-3">
          <span className="text-[10px] uppercase tracking-[0.18em] text-ink-3 font-semibold">
            Verdict — descriptive only
          </span>
          <span className="text-[10px] uppercase tracking-[0.16em] text-ink-3">
            {n} cohorts
          </span>
        </div>
        <h2 className={`font-serif text-2xl md:text-3xl font-semibold ${b.text} leading-tight`}>
          {b.label}
        </h2>
        <p className="mt-3 text-base text-ink-2 leading-relaxed max-w-prose-narrow">
          {b.oneliner(inTop, n)}
        </p>

        <div className="mt-7 grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-5">
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-1.5">
              Median rank
            </div>
            <div className={`num font-semibold text-3xl ${b.text}`}>
              {Number.isFinite(medRank) ? medRank.toFixed(1) : "—"}
            </div>
            <div className="text-xs text-ink-3 mt-1">across {n} cohorts</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-1.5">
              Median percentile
            </div>
            <div className="num font-semibold text-3xl text-ink">
              {Number.isFinite(medPct) ? medPct.toFixed(0) : "—"}
              <span className="text-base font-normal text-ink-3">%</span>
            </div>
            <div className="text-xs text-ink-3 mt-1">random baseline ≈ 50%</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-1.5">
              Top-tier cohorts
            </div>
            <div className="num font-semibold text-3xl text-ink">
              {inTop} <span className="text-base font-normal text-ink-3">/ {n}</span>
            </div>
            <div className="text-xs text-ink-3 mt-1">rank in top third</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-1.5">
              Beat the fraud
            </div>
            <div className="num font-semibold text-3xl text-ink">
              {beat} <span className="text-base font-normal text-ink-3">/ {n}</span>
            </div>
            <div className="text-xs text-ink-3 mt-1">more anomalous than the historical fraud</div>
          </div>
        </div>

        <div className="mt-6 pt-5 border-t border-rule">
          <p className="text-[12px] text-ink-3 leading-relaxed max-w-prose-narrow">
            <strong className="text-ink-2 font-semibold">This is not a fraud verdict.</strong>{" "}
            The label above describes how this filing's MD&amp;A reconstruction error
            ranks against five industry-and-year peer baselines — nothing more.
            Real evidence of fraud requires corroboration well beyond this signal.
            The academic study found only 1 of 5 historical frauds (Lehman) ranked
            highly under this method. Read the{" "}
            <a href="/limitations/" className="underline hover:text-navy-700">limitations</a>{" "}
            before reading too much into a single result.
          </p>
        </div>
      </div>
    </section>
  );
}
