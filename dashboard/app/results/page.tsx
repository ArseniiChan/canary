import Link from "next/link";
import perFraud from "../../public/data/per_fraud_metrics.json";

interface PerFraudRow {
  ticker: string;
  n_total: number;
  fraud_score: number;
  fraud_rank: number;
  fraud_percentile: number;
  mw_p: number;
  mw_effect_rank_biserial: number;
  mw_n_fraud_sent: number;
  mw_n_peer_sent: number;
  boot_lower_95: number;
  boot_upper_95: number;
  null_p_le_observed: number;
}

export default function Results() {
  const rows = (perFraud as { per_fraud: PerFraudRow[] }).per_fraud;

  return (
    <div className="space-y-10">
      <section>
        <h1 className="text-2xl font-semibold tracking-tight text-accent">
          Detailed results
        </h1>
        <p className="mt-2 text-sm text-secondary">
          Per-cohort detail for the pre-registered autoencoder. The frozen
          analysis spec is at git tag{" "}
          <span className="num">validation-spec-frozen</span>; this page is
          generated once from the validation script's output and not iterated.
        </p>
        <div className="mt-4 rounded-md border border-rule bg-surface px-5 py-4 text-sm">
          <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-semibold mb-1">
            Read this alongside the baseline check
          </div>
          <p className="text-ink-2 leading-relaxed">
            The numbers on this page are the autoencoder's, single-pass
            against the frozen spec. After validation, I ran a post-hoc
            TF-IDF + SVD32 baseline that tied or beat the autoencoder on
            every cohort.{" "}
            <Link href="/baseline/" className="underline hover:text-navy-700">
              See the head-to-head comparison
            </Link>{" "}
            before drawing conclusions from the autoencoder column alone.
          </p>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-accent mb-3">
          Bootstrap confidence intervals on rank
        </h2>
        <div className="space-y-3">
          {rows.map((r) => {
            const lo = r.boot_lower_95;
            const hi = r.boot_upper_95;
            const total = r.n_total;
            const widthPct = ((hi - lo + 1) / total) * 100;
            const offsetPct = ((lo - 1) / total) * 100;
            const obsPct = ((r.fraud_rank - 0.5) / total) * 100;
            return (
              <div key={r.ticker}>
                <div className="flex items-baseline justify-between text-sm mb-1">
                  <div className="font-semibold">{r.ticker}</div>
                  <div className="num text-xs text-secondary">
                    rank {r.fraud_rank}/{total} · CI [{Math.round(lo)}, {Math.round(hi)}]
                  </div>
                </div>
                <div className="relative h-6 rounded bg-bg-2 overflow-hidden">
                  <div
                    className="absolute top-0 bottom-0 bg-accent/30 opacity-60"
                    style={{ left: `${offsetPct}%`, width: `${widthPct}%` }}
                    title={`bootstrap 95% CI: [${Math.round(lo)}, ${Math.round(hi)}]`}
                  />
                  <div
                    className="absolute top-0 bottom-0 w-1 bg-accent"
                    style={{ left: `${obsPct}%` }}
                    title={`observed rank: ${r.fraud_rank}`}
                  />
                </div>
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-xs text-tertiary">
          Bar = bootstrap 95% CI on rank (1,000 filing-level resamples).
          Vertical line = observed rank. Lower = higher reconstruction error,
          which is the predicted direction.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-accent mb-3">
          Mann-Whitney U on per-sentence reconstruction error
        </h2>
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="min-w-full text-sm">
            <thead className="bg-bg-1 text-secondary">
              <tr>
                <th className="px-4 py-3 text-left">Cohort</th>
                <th className="px-4 py-3 text-right">n fraud sent</th>
                <th className="px-4 py-3 text-right">n peer sent</th>
                <th className="px-4 py-3 text-right">U stat</th>
                <th className="px-4 py-3 text-right">p (one-sided)</th>
                <th className="px-4 py-3 text-right">effect (rank-biserial)</th>
                <th className="px-4 py-3 text-right">null perm p</th>
              </tr>
            </thead>
            <tbody className="bg-bg">
              {rows.map((r) => (
                <tr key={r.ticker} className="border-t border-border">
                  <td className="px-4 py-3 font-semibold">{r.ticker}</td>
                  <td className="px-4 py-3 text-right num">{r.mw_n_fraud_sent}</td>
                  <td className="px-4 py-3 text-right num">{r.mw_n_peer_sent}</td>
                  <td className="px-4 py-3 text-right num">{r["fraud_score"] ? "" : ""}{(r as any).mw_u?.toLocaleString?.() ?? ""}</td>
                  <td className="px-4 py-3 text-right num text-xs">
                    {r.mw_p < 0.001 ? r.mw_p.toExponential(2) : r.mw_p.toFixed(4)}
                  </td>
                  <td className={`px-4 py-3 text-right num ${r.mw_effect_rank_biserial > 0 ? "text-accent" : ""}`}>
                    {r.mw_effect_rank_biserial > 0 ? "+" : ""}{r.mw_effect_rank_biserial.toFixed(3)}
                  </td>
                  <td className="px-4 py-3 text-right num text-xs">
                    {r.null_p_le_observed.toFixed(3)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
