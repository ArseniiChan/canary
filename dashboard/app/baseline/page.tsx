import Link from "next/link";
import aePerFraud from "../../public/data/per_fraud_metrics.json";
import tfidfPerFraud from "../../public/data/per_fraud_metrics_tfidf.json";
import masking from "../../public/data/entity_masking_posthoc.json";

interface PerFraudRow {
  ticker: string;
  n_total: number;
  fraud_rank: number;
  mw_p: number;
  mw_effect_rank_biserial: number;
  hit_at_1: number;
  hit_at_3: number;
  hit_at_5: number;
}

interface MaskingRow {
  ticker: string;
  n_mentions_replaced_approx: number;
  original_rank: number;
  masked_rank: number;
  n_total_in_cohort: number;
  rank_delta: number;
}

const FRAUD_NAMES: Record<string, string> = {
  WCOM: "WorldCom Inc.",
  TYC: "Tyco International",
  HRC: "HealthSouth Corp.",
  VRX: "Valeant Pharmaceuticals",
  LEH: "Lehman Brothers",
};
const FRAUD_FY: Record<string, string> = {
  WCOM: "FY2001",
  TYC: "FY2001",
  HRC: "FY2001",
  VRX: "FY2014",
  LEH: "FY2007",
};

function fmtP(p: number): string {
  if (p < 0.001) return p.toExponential(1);
  return p.toFixed(3);
}

function fmtSigned(x: number): string {
  return (x >= 0 ? "+" : "") + x.toFixed(2);
}

export default function BaselineCheck() {
  const ae = (aePerFraud as { per_fraud: PerFraudRow[] }).per_fraud;
  const tf = (tfidfPerFraud as { per_fraud: PerFraudRow[] }).per_fraud;
  const tfByTicker: Record<string, PerFraudRow> = Object.fromEntries(
    tf.map((r) => [r.ticker, r])
  );
  const order = ["LEH", "HRC", "VRX", "TYC", "WCOM"];

  const aeAgg = {
    hit1: ae.reduce((s, r) => s + r.hit_at_1, 0) / ae.length,
    hit3: ae.reduce((s, r) => s + r.hit_at_3, 0) / ae.length,
    hit5: ae.reduce((s, r) => s + r.hit_at_5, 0) / ae.length,
  };
  const tfAgg = {
    hit1: tf.reduce((s, r) => s + r.hit_at_1, 0) / tf.length,
    hit3: tf.reduce((s, r) => s + r.hit_at_3, 0) / tf.length,
    hit5: tf.reduce((s, r) => s + r.hit_at_5, 0) / tf.length,
  };

  const maskingRows = (
    masking as { per_fraud: MaskingRow[] }
  ).per_fraud;

  return (
    <div className="space-y-16">
      {/* HERO */}
      <section>
        <div className="eyebrow mb-4">
          A post-hoc check that rewrote the headline
        </div>
        <h1 className="font-serif text-[2rem] md:text-[2.5rem] font-semibold text-navy-900 leading-[1.1] max-w-3xl">
          A 1990s baseline matches or beats the autoencoder on every cohort.
        </h1>
        <span className="h1-rule" aria-hidden />
        <p className="mt-5 text-base md:text-lg text-ink-2 leading-relaxed max-w-prose-narrow">
          The pre-registered analysis used a PyTorch autoencoder over MiniLM
          sentence embeddings. After the validation results came in, the
          council reviewing this work demanded a baseline — a TF-IDF +
          truncated-SVD pipeline with the same 32-dim bottleneck and the
          same training corpora. The baseline was added <em>after</em> the
          autoencoder ran, with a pre-committed decision rule: report it as
          headline only if it (i) matches or beats AE on aggregate hit@k and
          (ii) reproduces AE&rsquo;s top-cohort ordering. Both conditions
          held.
        </p>
      </section>

      {/* HEAD-TO-HEAD TABLE */}
      <section>
        <h2 className="h-section text-[1.5rem] mb-5">
          Head-to-head: autoencoder vs TF-IDF + SVD32
        </h2>
        <div className="bg-surface rounded-md shadow-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 text-ink-3 text-[11px] uppercase tracking-[0.12em]">
              <tr>
                <th className="px-5 py-3 text-left font-semibold">Cohort</th>
                <th className="px-5 py-3 text-right font-semibold">AE rank</th>
                <th className="px-5 py-3 text-right font-semibold">TF-IDF rank</th>
                <th className="px-5 py-3 text-right font-semibold">AE Mann-Whitney p</th>
                <th className="px-5 py-3 text-right font-semibold">TF-IDF Mann-Whitney p</th>
                <th className="px-5 py-3 text-right font-semibold">AE effect</th>
                <th className="px-5 py-3 text-right font-semibold">TF-IDF effect</th>
              </tr>
            </thead>
            <tbody>
              {order.map((ticker, i) => {
                const aeRow = ae.find((r) => r.ticker === ticker)!;
                const tfRow = tfByTicker[ticker]!;
                const tfBeats = tfRow.fraud_rank < aeRow.fraud_rank;
                return (
                  <tr
                    key={ticker}
                    className={`border-t border-rule ${i % 2 ? "bg-surface-2/40" : ""}`}
                  >
                    <td className="px-5 py-4">
                      <div className="font-medium text-ink">{FRAUD_NAMES[ticker]}</div>
                      <div className="text-xs text-ink-3">{FRAUD_FY[ticker]}</div>
                    </td>
                    <td className="px-5 py-4 text-right num text-ink-2">
                      {aeRow.fraud_rank} / {aeRow.n_total}
                    </td>
                    <td
                      className={`px-5 py-4 text-right num ${
                        tfBeats ? "text-navy-700 font-semibold" : "text-ink-2"
                      }`}
                    >
                      {tfRow.fraud_rank} / {tfRow.n_total}
                    </td>
                    <td className="px-5 py-4 text-right num text-xs text-ink-2">
                      {fmtP(aeRow.mw_p)}
                    </td>
                    <td
                      className={`px-5 py-4 text-right num text-xs ${
                        tfRow.mw_p < aeRow.mw_p ? "text-navy-700 font-semibold" : "text-ink-2"
                      }`}
                    >
                      {fmtP(tfRow.mw_p)}
                    </td>
                    <td
                      className={`px-5 py-4 text-right num ${
                        aeRow.mw_effect_rank_biserial > 0 ? "text-navy-700" : "text-ink-2"
                      }`}
                    >
                      {fmtSigned(aeRow.mw_effect_rank_biserial)}
                    </td>
                    <td
                      className={`px-5 py-4 text-right num ${
                        tfRow.mw_effect_rank_biserial > 0 ? "text-navy-700" : "text-ink-2"
                      }`}
                    >
                      {fmtSigned(tfRow.mw_effect_rank_biserial)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-ink-3 max-w-prose-narrow">
          Rank 1 = highest mean per-sentence reconstruction error within the
          cohort. Random-baseline expected rank is (N+1)/2 &asymp; 6&ndash;7.
          Mann-Whitney <span className="num">p</span> is one-sided
          &ldquo;fraud &gt; peers&rdquo;. Effect is rank-biserial correlation
          in [&minus;1, 1]; positive = fraud sentences score higher than peer
          sentences. <strong>Bold</strong> = TF-IDF beats AE on this metric.
        </p>
      </section>

      {/* AGGREGATE STRIP */}
      <section>
        <h2 className="h-section text-[1.5rem] mb-5">
          Aggregate hit@k vs random baseline
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          {[
            { label: "hit@1", ae: aeAgg.hit1, tf: tfAgg.hit1, rnd: 0.0782 },
            { label: "hit@3", ae: aeAgg.hit3, tf: tfAgg.hit3, rnd: 0.2346 },
            { label: "hit@5", ae: aeAgg.hit5, tf: tfAgg.hit5, rnd: 0.3910 },
          ].map((m) => {
            const tfBeats = m.tf > m.rnd;
            return (
              <div key={m.label} className="bg-surface rounded-md shadow-card px-6 py-5">
                <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-medium mb-3">
                  {m.label}
                </div>
                <dl className="grid grid-cols-3 gap-2">
                  <div>
                    <dt className="text-[10px] uppercase text-ink-3 mb-1">AE</dt>
                    <dd className="num text-2xl text-ink">{m.ae.toFixed(2)}</dd>
                  </div>
                  <div>
                    <dt className="text-[10px] uppercase text-ink-3 mb-1">TF-IDF</dt>
                    <dd
                      className={`num text-2xl ${
                        tfBeats ? "text-navy-700 font-semibold" : "text-ink"
                      }`}
                    >
                      {m.tf.toFixed(2)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[10px] uppercase text-ink-3 mb-1">random</dt>
                    <dd className="num text-2xl text-ink-3">
                      {m.rnd.toFixed(2)}
                    </dd>
                  </div>
                </dl>
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-xs text-ink-3 max-w-prose-narrow">
          The TF-IDF baseline produces aggregate hit@5 = 0.40 — the only
          configuration in this study that exceeds the random baseline at any
          k. The autoencoder remains at or below random on every threshold.
        </p>
      </section>

      {/* ENTITY MASKING */}
      <section>
        <h2 className="h-section text-[1.5rem] mb-5">
          Lehman&rsquo;s rank survives entity masking
        </h2>
        <p className="text-sm text-ink-2 leading-relaxed max-w-prose-narrow mb-5">
          A second post-hoc check addresses MiniLM pretraining contamination:
          if Lehman&rsquo;s rank is driven by literal name tokens
          (&ldquo;Lehman&rdquo;, &ldquo;Fuld&rdquo;, &ldquo;Repo 105&rdquo;, the
          auditor of record), masking those tokens with the literal string
          <span className="num"> [ENTITY] </span>
          should collapse the rank. It does not.
        </p>
        <div className="bg-surface rounded-md shadow-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 text-ink-3 text-[11px] uppercase tracking-[0.12em]">
              <tr>
                <th className="px-5 py-3 text-left font-semibold">Cohort</th>
                <th className="px-5 py-3 text-right font-semibold">Tokens replaced</th>
                <th className="px-5 py-3 text-right font-semibold">Original rank</th>
                <th className="px-5 py-3 text-right font-semibold">After masking</th>
                <th className="px-5 py-3 text-right font-semibold">&Delta;</th>
              </tr>
            </thead>
            <tbody>
              {maskingRows.map((m, i) => (
                <tr
                  key={m.ticker}
                  className={`border-t border-rule ${i % 2 ? "bg-surface-2/40" : ""}`}
                >
                  <td className="px-5 py-4">
                    <div className="font-medium text-ink">
                      {FRAUD_NAMES[m.ticker]}
                    </div>
                    <div className="text-xs text-ink-3">
                      {FRAUD_FY[m.ticker]}
                    </div>
                  </td>
                  <td className="px-5 py-4 text-right num text-ink-2">
                    {m.n_mentions_replaced_approx}
                  </td>
                  <td className="px-5 py-4 text-right num text-ink-2">
                    {m.original_rank} / {m.n_total_in_cohort}
                  </td>
                  <td className="px-5 py-4 text-right num text-ink-2">
                    {m.masked_rank} / {m.n_total_in_cohort}
                  </td>
                  <td
                    className={`px-5 py-4 text-right num ${
                      m.rank_delta === 0 ? "text-navy-700 font-semibold" : "text-ink-2"
                    }`}
                  >
                    {m.rank_delta > 0 ? "+" : ""}
                    {m.rank_delta}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-ink-3 max-w-prose-narrow">
          Lehman&rsquo;s rank is invariant under masking 93 mentions. The
          literal-name-leakage hypothesis fails to explain the result. Topical
          leakage (post-2008 commentary on repo accounting, off-balance-sheet
          vehicles) remains disclosed but unaddressed empirically.
        </p>
      </section>

      {/* INTERPRETATION */}
      <section className="bg-navy-900 text-white rounded-md px-6 md:px-10 py-10 md:py-14 relative overflow-hidden">
        <div
          aria-hidden
          className="absolute -top-24 -right-24 w-72 h-72 rounded-full bg-navy-700/40 blur-3xl pointer-events-none"
        />
        <div className="relative">
          <div className="text-[11px] uppercase tracking-[0.2em] text-navy-300 font-semibold mb-4">
            Reading the baseline check
          </div>
          <p className="text-[1.35rem] md:text-[1.55rem] leading-[1.45] max-w-3xl text-white font-medium">
            At N&nbsp;=&nbsp;6 frauds, on this single MD&amp;A signal, the
            2020s neural autoencoder did not earn its complexity. A 1990s
            latent-semantic-analysis baseline matched or exceeded it on every
            cohort.
          </p>
          <p className="mt-5 text-[15px] md:text-base text-navy-200 leading-relaxed max-w-3xl">
            That is the contribution: a pre-registered null result with a
            baseline check that the field claims to want and rarely produces.
            For the methodology in full, see the&nbsp;
            <Link href="/methodology/" className="underline hover:text-canary">
              methodology page
            </Link>
            ; for the limitations,&nbsp;
            <Link href="/limitations/" className="underline hover:text-canary">
              read here
            </Link>
            .
          </p>
        </div>
      </section>
    </div>
  );
}
