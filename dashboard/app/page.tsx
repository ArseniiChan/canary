import Link from "next/link";
import perFraud from "../public/data/per_fraud_metrics.json";
import perFraudTfidf from "../public/data/per_fraud_metrics_tfidf.json";
import aggregate from "../public/data/aggregate_metrics.json";
import { RankStat } from "./components/Stat";
import { RankBar } from "./components/RankBar";

interface PerFraudRow {
  ticker: string;
  n_total: number;
  fraud_score: number;
  fraud_rank: number;
  fraud_percentile: number;
  hit_at_1: number; hit_at_3: number; hit_at_5: number;
  random_hit1: number; random_hit3: number; random_hit5: number;
  mw_p: number;
  mw_effect_rank_biserial: number;
  boot_lower_95: number; boot_upper_95: number;
  null_p_le_observed: number;
}

interface TfidfRow {
  ticker: string;
  fraud_rank: number;
  n_total: number;
  hit_at_1: number; hit_at_3: number; hit_at_5: number;
  mw_p: number;
  mw_effect_rank_biserial: number;
}

const FRAUD_NAMES: Record<string, string> = {
  ENE: "Enron Corp.", WCOM: "WorldCom Inc.", TYC: "Tyco International",
  HRC: "HealthSouth Corp.", VRX: "Valeant Pharmaceuticals", LEH: "Lehman Brothers",
};
const FRAUD_FY: Record<string, string> = {
  ENE: "FY2000", WCOM: "FY2001", TYC: "FY2001",
  HRC: "FY2001", VRX: "FY2014", LEH: "FY2007",
};

export default function Home() {
  const rows = (perFraud as { per_fraud: PerFraudRow[] }).per_fraud;
  const tfRows = (perFraudTfidf as { per_fraud: TfidfRow[] }).per_fraud;
  const tfByTicker: Record<string, TfidfRow> = Object.fromEntries(
    tfRows.map((r) => [r.ticker, r])
  );
  const tfAgg = {
    hit_at_1: tfRows.reduce((s, r) => s + r.hit_at_1, 0) / tfRows.length,
    hit_at_3: tfRows.reduce((s, r) => s + r.hit_at_3, 0) / tfRows.length,
    hit_at_5: tfRows.reduce((s, r) => s + r.hit_at_5, 0) / tfRows.length,
  };
  const agg = (aggregate as { aggregate: Record<string, number> }).aggregate;
  const lehman = rows.find((r) => r.ticker === "LEH")!;
  const lehmanTf = tfByTicker["LEH"];
  const others = rows.filter((r) => r.ticker !== "LEH").sort((a, b) => a.ticker.localeCompare(b.ticker));

  return (
    <div className="space-y-20">
      {/* HERO */}
      <section className="relative">
        <div className="eyebrow mb-5">
          A pre-registered study · CSC&nbsp;44800 · CCNY · Spring 2026
        </div>
        <h1 className="font-serif text-4xl md:text-[3.25rem] lg:text-[3.75rem] font-semibold text-navy-900 leading-[1.04] max-w-3xl">
          Can you flag accounting fraud a year early by reading the words in a 10-K?
        </h1>
        <span className="h1-rule" aria-hidden />
        <p className="mt-6 text-lg md:text-xl text-ink-2 leading-relaxed max-w-2xl">
          We pre-registered a study on six famous cases. Five failed.
          Lehman didn't — and that's the result.
        </p>

        <div className="mt-9 flex flex-wrap gap-3">
          <Link
            href="/scan/"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-md bg-navy-700 text-white text-sm font-semibold hover:bg-navy-800 transition-colors shadow-card"
          >
            <span>Scan a 10-K filing</span>
            <span aria-hidden>→</span>
          </Link>
          <Link
            href="/methodology/"
            className="inline-flex items-center px-5 py-3 rounded-md border border-rule text-ink-2 text-sm font-medium hover:text-navy-700 hover:border-rule-strong transition-colors"
          >
            How it works
          </Link>
        </div>
      </section>

      {/* LEHMAN — the lede surprise, not a footnote */}
      <section className="bg-surface accent-border-top rounded-md shadow-card">
        <div className="px-6 md:px-10 py-8 md:py-10 grid md:grid-cols-[1fr,1.4fr] gap-8 md:gap-12 items-start">
          <div>
            <div className="eyebrow mb-3">The exception</div>
            <h2 className="font-serif text-[1.75rem] md:text-[2rem] font-semibold text-navy-900 leading-[1.15]">
              Lehman Brothers, FY2007
            </h2>
            <p className="mt-4 text-base text-ink-2 leading-relaxed max-w-prose-narrow">
              Lehman's annual report — filed January 2008, eight months before
              Chapter 11 — ranks{" "}
              <strong className="num text-navy-700">{lehman.fraud_rank} of {lehman.n_total}</strong>{" "}
              under the autoencoder and{" "}
              <strong className="num text-navy-700">{lehmanTf.fraud_rank} of {lehmanTf.n_total}</strong>{" "}
              under a post-hoc TF-IDF&nbsp;+&nbsp;SVD32 baseline. Both methods
              place it above chance. The Mann-Whitney U test is highly
              significant in both cases (<span className="num">p ≈ 1.3 × 10⁻⁹</span>{" "}
              for the autoencoder; <span className="num">p ≈ 5 × 10⁻²²</span>{" "}
              for the baseline) with small effect sizes. The simpler method
              produces the cleaner result.{" "}
              <strong className="text-ink">We report the result. We do not claim a method.</strong>{" "}
              <Link href="/baseline/" className="underline hover:text-navy-700">
                See the head-to-head
              </Link>
              .
            </p>
            <Link
              href="/per-fraud/leh/"
              className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-navy-700 hover:text-navy-900"
            >
              <span>See Lehman's full breakdown</span>
              <span aria-hidden>→</span>
            </Link>
          </div>
          <div>
            <RankBar
              rank={lehman.fraud_rank}
              total={lehman.n_total}
              ciLower={lehman.boot_lower_95}
              ciUpper={lehman.boot_upper_95}
              expected={(lehman.n_total + 1) / 2}
            />
            <dl className="mt-7 grid grid-cols-3 gap-x-6">
              <div>
                <dt className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-2">Rank</dt>
                <dd className="num font-semibold text-3xl text-navy-700">
                  {lehman.fraud_rank}<span className="text-base font-normal text-ink-3"> / {lehman.n_total}</span>
                </dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-2">M-W p</dt>
                <dd className="num font-semibold text-3xl text-ink">
                  {lehman.mw_p < 0.001 ? lehman.mw_p.toExponential(1) : lehman.mw_p.toFixed(3)}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-2">95% CI</dt>
                <dd className="num font-semibold text-3xl text-ink">
                  [{Math.round(lehman.boot_lower_95)},&nbsp;{Math.round(lehman.boot_upper_95)}]
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      {/* THE OTHER FOUR + ENRON */}
      <section>
        <div className="flex items-baseline justify-between mb-5">
          <h2 className="h-section text-[1.5rem]">
            The other four cohorts
          </h2>
          <span className="text-xs text-ink-3 hidden md:inline">rank 1 = highest reconstruction error</span>
        </div>
        <div className="bg-surface rounded-md shadow-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 text-ink-3 text-[11px] uppercase tracking-[0.12em]">
              <tr>
                <th className="px-5 py-3 text-left font-semibold">Cohort</th>
                <th className="px-5 py-3 text-right font-semibold">AE rank</th>
                <th className="px-5 py-3 text-right font-semibold">TF-IDF rank</th>
                <th className="px-5 py-3 text-left font-semibold w-1/3">AE distribution</th>
                <th className="px-5 py-3 text-right font-semibold">AE M-W p</th>
                <th className="px-5 py-3 text-right font-semibold">AE effect</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {others.map((r, i) => (
                <tr
                  key={r.ticker}
                  className={`border-t border-rule ${i % 2 ? "bg-surface-2/40" : ""}`}
                >
                  <td className="px-5 py-4">
                    <div className="font-medium text-ink">{FRAUD_NAMES[r.ticker]}</div>
                    <div className="text-xs text-ink-3">{FRAUD_FY[r.ticker]}</div>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <RankStat rank={r.fraud_rank} total={r.n_total} size="sm" />
                  </td>
                  <td className={`px-5 py-4 text-right num ${tfByTicker[r.ticker] && tfByTicker[r.ticker].fraud_rank < r.fraud_rank ? "text-navy-700 font-semibold" : "text-ink-2"}`}>
                    {tfByTicker[r.ticker]
                      ? `${tfByTicker[r.ticker].fraud_rank} / ${tfByTicker[r.ticker].n_total}`
                      : "—"}
                  </td>
                  <td className="px-5 py-4">
                    <RankBar
                      rank={r.fraud_rank} total={r.n_total}
                      ciLower={r.boot_lower_95} ciUpper={r.boot_upper_95}
                      expected={(r.n_total + 1) / 2}
                      height="sm"
                    />
                  </td>
                  <td className="px-5 py-4 text-right num text-xs text-ink-2">
                    {r.mw_p < 0.001 ? r.mw_p.toExponential(1) : r.mw_p.toFixed(3)}
                  </td>
                  <td className={`px-5 py-4 text-right num ${r.mw_effect_rank_biserial > 0 ? "text-navy-700" : "text-ink-2"}`}>
                    {r.mw_effect_rank_biserial > 0 ? "+" : ""}{r.mw_effect_rank_biserial.toFixed(2)}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <Link
                      href={`/per-fraud/${r.ticker.toLowerCase()}/`}
                      className="text-ink-3 hover:text-navy-700 text-sm"
                      aria-label={`Drill into ${FRAUD_NAMES[r.ticker]}`}
                    >→</Link>
                  </td>
                </tr>
              ))}
              <tr className="border-t border-rule bg-surface-2/60">
                <td className="px-5 py-4">
                  <div className="font-medium text-ink-2">Enron Corp.</div>
                  <div className="text-xs text-ink-3">FY2000 — methodological exclusion</div>
                </td>
                <td colSpan={5} className="px-5 py-4 text-xs text-ink-3 italic">
                  Filed 2001‑04‑02 — earlier than every peer in every other cohort.
                  Strict leave-one-cohort-out + time-controlled training admits no
                  eligible data. Exclusion is the finding.
                </td>
                <td className="px-5 py-4 text-right">
                  <Link href="/per-fraud/ene/" className="text-ink-3 hover:text-navy-700 text-sm">→</Link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* AGGREGATE — one tidy strip, not three big cards */}
      <section>
        <h2 className="h-section text-[1.5rem] mb-5">
          Aggregate hit rates vs random baseline
        </h2>
        <div className="grid grid-cols-3 divide-x divide-rule bg-surface rounded-md shadow-card">
          {[
            { label: "Hit @ 1", ae: agg.hit_at_1, tf: tfAgg.hit_at_1, rnd: agg.random_hit_at_1 },
            { label: "Hit @ 3", ae: agg.hit_at_3, tf: tfAgg.hit_at_3, rnd: agg.random_hit_at_3 },
            { label: "Hit @ 5", ae: agg.hit_at_5, tf: tfAgg.hit_at_5, rnd: agg.random_hit_at_5 },
          ].map((m) => {
            const tfBeats = m.tf > m.rnd;
            return (
              <div key={m.label} className="p-5 md:p-6">
                <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-3">
                  {m.label}
                </div>
                <dl className="space-y-1.5">
                  <div className="flex items-baseline justify-between">
                    <dt className="text-[11px] uppercase tracking-[0.1em] text-ink-3">AE</dt>
                    <dd className="num font-semibold text-2xl text-ink">{m.ae.toFixed(2)}</dd>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <dt className="text-[11px] uppercase tracking-[0.1em] text-ink-3">TF-IDF</dt>
                    <dd className={`num font-semibold text-2xl ${tfBeats ? "text-navy-700" : "text-ink"}`}>
                      {m.tf.toFixed(2)}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <dt className="text-[11px] uppercase tracking-[0.1em] text-ink-3">random</dt>
                    <dd className="num text-2xl text-ink-3">{m.rnd.toFixed(3)}</dd>
                  </div>
                </dl>
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-xs text-ink-3 max-w-prose-narrow">
          The autoencoder rates fall at or <em>below</em> the random baseline
          at every threshold. The post-hoc TF-IDF + SVD32 baseline (added
          after results were observed; <Link href="/baseline/" className="underline hover:text-ink-2">see the baseline check</Link>)
          is the only configuration in this study that exceeds random at any k.
        </p>
      </section>

      {/* TAKEAWAY — clean dark card, modern */}
      <section className="bg-navy-900 text-white rounded-md px-6 md:px-10 py-10 md:py-14 relative overflow-hidden">
        <div
          aria-hidden
          className="absolute -top-24 -right-24 w-72 h-72 rounded-full bg-navy-700/40 blur-3xl pointer-events-none"
        />
        <div className="relative">
          <div className="text-[11px] uppercase tracking-[0.2em] text-navy-300 font-semibold mb-4">
            What this means
          </div>
          <p className="text-[1.35rem] md:text-[1.55rem] leading-[1.45] max-w-3xl text-white font-medium">
            One language signal — how unusual a filing's narrative reads
            against industry-and-year peers — does not catch five of six
            pre-discovery fraud filings.
          </p>
          <p className="mt-5 text-[15px] md:text-base text-navy-200 leading-relaxed max-w-3xl">
            The discipline that makes this finding informative is the discipline
            that costs nothing to replicate: pre-register, freeze the spec,
            leave one cohort out, control for filing time, and report the
            single-pass numbers.
          </p>
        </div>
      </section>
    </div>
  );
}
