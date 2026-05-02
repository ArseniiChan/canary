import Link from "next/link";
import { notFound } from "next/navigation";
import perFraud from "../../../public/data/per_fraud_metrics.json";
import fraudManifest from "../../../public/data/fraud_manifest.json";
import { RankBar } from "../../components/RankBar";

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
  mw_n_fraud_sent: number;
  mw_n_peer_sent: number;
  boot_lower_95: number; boot_upper_95: number;
  null_p_le_observed: number;
}

const TICKERS = ["ene", "wcom", "tyc", "hrc", "vrx", "leh"];

export function generateStaticParams() {
  return TICKERS.map((ticker) => ({ ticker }));
}

export default function PerFraud({ params }: { params: { ticker: string } }) {
  const upper = params.ticker.toUpperCase();
  const rows = (perFraud as { per_fraud: PerFraudRow[] }).per_fraud;
  const row = rows.find((r) => r.ticker === upper);

  const manifest = (fraudManifest as { frauds: any[] }).frauds.find(
    (f) => f.ticker === upper
  );
  if (!manifest) notFound();

  if (upper === "ENE") {
    return (
      <div className="space-y-8 max-w-3xl">
        <Link href="/" className="text-sm text-ink-3 hover:text-navy-700">
          ← All cohorts
        </Link>
        <header>
          <div className="text-[11px] uppercase tracking-[0.2em] text-ink-3 font-semibold mb-3">
            Methodological exclusion
          </div>
          <h1 className="font-serif text-3xl md:text-4xl font-semibold text-navy-900 leading-tight tracking-tightish">
            Enron Corp. <span className="text-ink-3 font-normal">FY2000</span>
          </h1>
        </header>

        <section className="bg-verdict-mixed-bg accent-border-top--mixed rounded-md p-7 shadow-card">
          <h2 className="font-serif text-xl font-semibold text-verdict-mixed-text mb-3">
            Excluded from primary results — not by analyst choice
          </h2>
          <p className="text-base text-ink-2 leading-relaxed">
            Enron's FY2000 10-K was filed on{" "}
            <span className="num text-ink">{manifest.filing_date}</span> — earlier
            than every peer filing in every other cohort. Under the spec's strict
            leave-one-cohort-out + time-controlled rule ("training data = clean
            filings from <em>other</em> cohorts AND dated ≤ that fraud's filing
            date"), Enron's training set is empty. Rather than relax the spec
            post-hoc, Enron is excluded from primary results and the constraint
            is documented as a finding.
          </p>
        </section>

        <section className="bg-surface rounded-md shadow-card p-7">
          <h3 className="h-section text-[1.05rem] mb-4">Filing details</h3>
          <dl className="text-sm space-y-2.5">
            {[
              ["Accession", manifest.accession],
              ["CIK", manifest.cik],
              ["Filing date", manifest.filing_date],
              ["Period", manifest.report_date],
              ["Public revelation", manifest.revelation_date],
              ["Days pre-discovery", "197"],
              ["SIC", `${manifest.sic} — ${manifest.sic_description}`],
            ].map(([k, v]) => (
              <div key={k as string} className="flex">
                <dt className="w-44 text-ink-3 text-xs uppercase tracking-wide">{k}</dt>
                <dd className="num text-ink">{v as string}</dd>
              </div>
            ))}
            <div className="flex pt-2 mt-2 border-t border-rule">
              <dt className="w-44 text-ink-3 text-xs uppercase tracking-wide">SHA-256</dt>
              <dd className="num text-xs text-ink-2 break-all">{manifest.primary_doc_sha256}</dd>
            </div>
          </dl>
        </section>
      </div>
    );
  }

  if (!row) notFound();

  const beatsRandom = row.fraud_rank < (row.n_total + 1) / 2;
  const days = Math.round(
    (Date.parse(manifest.revelation_date) - Date.parse(manifest.filing_date)) / 86400000
  );

  return (
    <div className="space-y-10 max-w-4xl">
      <Link href="/" className="text-sm text-ink-3 hover:text-navy-700">
        ← All cohorts
      </Link>

      <header>
        <div className="text-[11px] uppercase tracking-[0.2em] text-ink-3 font-semibold mb-3">
          Per-fraud detail
        </div>
        <h1 className="font-serif text-3xl md:text-4xl font-semibold text-navy-900 leading-tight tracking-tightish">
          {manifest.name} <span className="text-ink-3 font-normal">FY{String(manifest.report_date).slice(0, 4)}</span>
        </h1>
      </header>

      <section className="bg-surface accent-border-top rounded-md shadow-card p-7 md:p-9">
        <RankBar
          rank={row.fraud_rank}
          total={row.n_total}
          ciLower={row.boot_lower_95}
          ciUpper={row.boot_upper_95}
          expected={(row.n_total + 1) / 2}
        />
        <div className="mt-7 grid grid-cols-3 gap-x-8">
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-semibold mb-2">Rank within cohort</div>
            <div className={`num font-semibold text-[2.5rem] leading-none ${beatsRandom ? "text-navy-700" : "text-ink"}`}>
              {row.fraud_rank}<span className="text-xl font-normal text-ink-3"> / {row.n_total}</span>
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-semibold mb-2">Percentile</div>
            <div className="num font-semibold text-[2.5rem] leading-none text-ink">
              {row.fraud_percentile.toFixed(0)}
              <span className="text-xl font-normal text-ink-3">%</span>
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-semibold mb-2">Bootstrap 95% CI</div>
            <div className="num font-semibold text-[2.5rem] leading-none text-ink">
              [{Math.round(row.boot_lower_95)},&nbsp;{Math.round(row.boot_upper_95)}]
            </div>
          </div>
        </div>
      </section>

      <section className="grid md:grid-cols-2 gap-6">
        <div className="bg-surface rounded-md shadow-card p-6">
          <h3 className="h-section text-[1.05rem] mb-4">Filing details</h3>
          <dl className="text-sm space-y-2.5">
            {[
              ["Accession", manifest.accession],
              ["CIK", manifest.cik],
              ["Filing date", manifest.filing_date],
              ["Period", manifest.report_date],
              ["Revelation", manifest.revelation_date],
              ["Pre-discovery", `${days} days`],
              ["SIC", manifest.sic],
            ].map(([k, v]) => (
              <div key={k as string} className="flex">
                <dt className="w-36 text-ink-3 text-xs uppercase tracking-wide">{k}</dt>
                <dd className="num text-ink">{v as string}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="bg-surface rounded-md shadow-card p-6">
          <h3 className="h-section text-[1.05rem] mb-4">Statistical detail</h3>
          <dl className="text-sm space-y-2.5">
            <div className="flex">
              <dt className="w-44 text-ink-3 text-xs uppercase tracking-wide">Mann-Whitney p</dt>
              <dd className="num text-ink">
                {row.mw_p < 0.001 ? row.mw_p.toExponential(2) : row.mw_p.toFixed(4)}
              </dd>
            </div>
            <div className="flex">
              <dt className="w-44 text-ink-3 text-xs uppercase tracking-wide">Effect (rank-biserial)</dt>
              <dd className={`num ${row.mw_effect_rank_biserial > 0 ? "text-navy-700" : "text-ink"}`}>
                {row.mw_effect_rank_biserial > 0 ? "+" : ""}{row.mw_effect_rank_biserial.toFixed(3)}
              </dd>
            </div>
            <div className="flex">
              <dt className="w-44 text-ink-3 text-xs uppercase tracking-wide">n fraud sentences</dt>
              <dd className="num text-ink">{row.mw_n_fraud_sent}</dd>
            </div>
            <div className="flex">
              <dt className="w-44 text-ink-3 text-xs uppercase tracking-wide">n peer sentences</dt>
              <dd className="num text-ink">{row.mw_n_peer_sent}</dd>
            </div>
            <div className="flex">
              <dt className="w-44 text-ink-3 text-xs uppercase tracking-wide">Null permutation p</dt>
              <dd className="num text-ink">{row.null_p_le_observed.toFixed(3)}</dd>
            </div>
            <div className="flex pt-2 mt-2 border-t border-rule">
              <dt className="w-44 text-ink-3 text-xs uppercase tracking-wide">Hit @ 1 / 3 / 5</dt>
              <dd className="num text-ink">{row.hit_at_1} / {row.hit_at_3} / {row.hit_at_5}</dd>
            </div>
            <div className="flex">
              <dt className="w-44 text-ink-3 text-xs uppercase tracking-wide">Random @ 1 / 3 / 5</dt>
              <dd className="num text-xs text-ink-3">
                {row.random_hit1.toFixed(2)} / {row.random_hit3.toFixed(2)} / {row.random_hit5.toFixed(2)}
              </dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  );
}
