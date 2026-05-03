"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileDropZone } from "../components/FileDropZone";
import { Verdict } from "../components/Verdict";
import { RankBar } from "../components/RankBar";
import { RankStat, formatNumber } from "../components/Stat";

const API_URL = process.env.NEXT_PUBLIC_CANARY_API || "";

// Pre-baked entity-stripped Lehman MD&A for the live demo path. See
// reports/demo_snippet.txt and reports/demo_script.md. Loaded when the
// page is opened with ?demo=1.
const DEMO_SNIPPET = `We expect global fixed income origination to decline in 2008 as a result of lower volumes of securitizations and M&A financings. Fixed income capital markets are expected to continue to face uncertainties in the 2008 calendar year. In the U.S., economic growth showed signs of strength at the beginning of our fiscal year, driven by higher net exports and consumption levels, among other indicators, but the pace of growth slowed in the latter half. Over the twelve-month period, the U.S. housing market weakened, business confidence declined, and, in the last six months of the year, consumer confidence dropped. The labor market followed the same trajectory, showing signs of deterioration in the second half of the period as unemployment levels increased modestly and payroll data showed some signs of weakness. Responding to concerns over liquidity in the financial markets and inflationary pressures, the U.S. Federal Reserve reduced rates three times during the calendar year and made an additional inter-meeting rate cut in January 2008, and most observers anticipate additional reductions will occur in the early part of our 2008 fiscal year. Long-term bond yields declined, with the 10-year Treasury note yield ending our fiscal year down 52 basis points at 3.94%. The S&P 500 Index, Dow Jones Industrial Average and NASDAQ composites were up 5.7%, 9.4%, and 9.4%, respectively, from November 2006 levels. The current high levels of U.S. home inventories suggest that an extended period of construction declines and housing price cuts will combine with tighter credit conditions and increasing oil prices to slow down consumer spending.`;

const FRAUD_NAMES: Record<string, string> = {
  ENE: "Enron Corp.", WCOM: "WorldCom Inc.", TYC: "Tyco International",
  HRC: "HealthSouth Corp.", VRX: "Valeant Pharmaceuticals", LEH: "Lehman Brothers",
};
const FRAUD_FY: Record<string, string> = {
  WCOM: "FY2001", TYC: "FY2001", HRC: "FY2001", VRX: "FY2014", LEH: "FY2007",
};

interface CohortResult {
  cohort_id: string;
  rank_if_added: number;
  n_after_add: number;
  percentile_within_cohort: number;
  score_mean: number;
  score_trimmed_mean: number;
  score_max: number;
  fraud_score: number | null;
}

interface ScanResult {
  ok: boolean;
  error?: string;
  extraction?: { method: string; chars: number; note: string };
  n_sentences?: number;
  per_cohort?: CohortResult[];
}

async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => {
      const s = r.result as string;
      const idx = s.indexOf(",");
      resolve(idx >= 0 ? s.slice(idx + 1) : s);
    };
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
}

export default function Scan() {
  const [mode, setMode] = useState<"file" | "text">("file");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);

  // Demo-mode pre-fill: ?demo=1 in the URL loads the prepared snippet and
  // switches to "Paste text" mode. Used at the May 7 presentation when the
  // podium machine doesn't have clipboard access. See reports/demo_script.md.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("demo") === "1") {
      setMode("text");
      setText(DEMO_SNIPPET);
    }
  }, []);

  const ready =
    (mode === "file" && file !== null) ||
    (mode === "text" && text.trim().length > 200);

  async function submit() {
    if (!API_URL) {
      setResult({ ok: false, error: "Backend not configured. Set NEXT_PUBLIC_CANARY_API and rebuild." });
      return;
    }
    setSubmitting(true);
    setResult(null);
    const t0 = performance.now();
    try {
      const body =
        mode === "file" && file
          ? { filename: file.name, content_b64: await fileToBase64(file) }
          : { text };
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      setResult(await res.json());
    } catch (e: unknown) {
      setResult({ ok: false, error: e instanceof Error ? e.message : "request failed" });
    } finally {
      setElapsedMs(Math.round(performance.now() - t0));
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-12">
      {/* HEADER */}
      <section>
        <div className="eyebrow mb-4">Scan a filing</div>
        <h1 className="font-serif text-[2.25rem] md:text-[2.75rem] font-semibold text-navy-900 leading-[1.1] max-w-3xl">
          Compare any 10-K against five historical fraud cohorts
        </h1>
        <span className="h1-rule" aria-hidden />
        <p className="mt-5 text-base md:text-lg text-ink-2 leading-relaxed max-w-prose-narrow">
          Upload a 10-K filing or paste its MD&amp;A section &mdash; the
          "Management&rsquo;s Discussion &amp; Analysis," the long narrative
          part where executives explain the year &mdash; and we&rsquo;ll run the
          exact pipeline the academic study used to see where it would rank in
          each cohort.
        </p>
      </section>

      {/* INPUT */}
      <section className="bg-surface rounded-md shadow-card overflow-hidden">
        <div className="border-b border-rule px-6 md:px-8 py-4 flex gap-1 text-sm">
          <button
            onClick={() => setMode("file")}
            className={`px-4 py-1.5 rounded-md font-medium transition-colors ${
              mode === "file"
                ? "bg-navy-700 text-white"
                : "text-ink-2 hover:text-navy-700"
            }`}
          >
            Upload file
          </button>
          <button
            onClick={() => setMode("text")}
            className={`px-4 py-1.5 rounded-md font-medium transition-colors ${
              mode === "text"
                ? "bg-navy-700 text-white"
                : "text-ink-2 hover:text-navy-700"
            }`}
          >
            Paste text
          </button>
        </div>

        <div className="px-6 md:px-8 py-7">
          {mode === "file" ? (
            <FileDropZone file={file} onFileSelected={setFile} />
          ) : (
            <div>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={12}
                placeholder="Paste the Management's Discussion & Analysis (Item 7) section of a 10-K here. 200+ characters minimum; the full section (10-100k chars) gives the most useful signal."
                className="w-full bg-surface-2 border border-rule rounded-md p-4 text-[13px] font-mono leading-relaxed text-ink focus:outline-none focus:ring-2 focus:ring-navy-500 focus:border-navy-500 placeholder:text-ink-3"
              />
              <p className="mt-2 text-xs text-ink-3">
                <span className="num">{text.length}</span> characters
                {text.length > 200 ? " · ready" : ` · need ${200 - text.length} more`}
              </p>
            </div>
          )}

          <div className="mt-6 flex items-center justify-between gap-4">
            <button
              disabled={!ready || submitting}
              onClick={submit}
              className="px-5 py-2.5 rounded bg-navy-700 text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors shadow-card"
            >
              {submitting ? "Scoring…" : "Score this filing"}
            </button>
            <div className="text-xs text-ink-3">
              {submitting && "First scan after a quiet spell can take 10-20 seconds."}
              {!submitting && elapsedMs !== null && (
                <>
                  Last scan: <span className="num">{(elapsedMs / 1000).toFixed(1)}s</span>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ERROR */}
      {result && !result.ok && (
        <section className="rounded-md bg-verdict-high-bg border border-verdict-high-border accent-border-top--high px-6 py-5 shadow-card">
          <div className="text-[10px] uppercase tracking-[0.18em] font-semibold text-verdict-high-text mb-1">
            Couldn't score this filing
          </div>
          <p className="text-sm text-ink">{result.error || "unknown error"}</p>
        </section>
      )}

      {/* RESULTS */}
      {result && result.ok && result.per_cohort && (
        <>
          <Verdict results={result.per_cohort} />

          <section className="bg-surface rounded-md shadow-card px-6 md:px-8 py-6 grid md:grid-cols-3 gap-x-8 gap-y-4 text-sm">
            <div>
              <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-semibold mb-1">
                Extraction method
              </div>
              <div className="num text-ink">{result.extraction?.method}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-semibold mb-1">
                Body extracted
              </div>
              <div>
                <span className="num text-ink">
                  {result.extraction?.chars?.toLocaleString()}
                </span>{" "}
                <span className="text-ink-3">chars ·</span>{" "}
                <span className="num text-ink">{result.n_sentences}</span>{" "}
                <span className="text-ink-3">sentences</span>
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-semibold mb-1">
                Pipeline
              </div>
              <div className="text-ink-2 text-xs">
                MiniLM embeddings → 5 cohort autoencoders → mean per-sentence
                reconstruction error
              </div>
            </div>
          </section>

          <section>
            <h2 className="h-section text-[1.5rem] mb-5">
              Per-cohort breakdown
            </h2>
            <div className="space-y-3">
              {result.per_cohort.map((c) => {
                const inTopThird = c.rank_if_added / c.n_after_add <= 0.33;
                const fraudCmp =
                  c.fraud_score !== null
                    ? c.score_mean > c.fraud_score
                      ? `more anomalous than ${FRAUD_NAMES[c.cohort_id]}'s 10-K`
                      : `less anomalous than ${FRAUD_NAMES[c.cohort_id]}'s 10-K`
                    : "no historical fraud baseline";
                return (
                  <div
                    key={c.cohort_id}
                    className="bg-surface rounded-md shadow-card px-5 md:px-6 py-5 grid md:grid-cols-[1fr,2fr,auto] gap-5 md:gap-7 items-center"
                  >
                    <div>
                      <div className="text-[10px] uppercase tracking-[0.14em] text-ink-3 font-semibold mb-1">
                        vs cohort
                      </div>
                      <div className="font-medium text-ink leading-tight">
                        {FRAUD_NAMES[c.cohort_id]}
                      </div>
                      <div className="text-xs text-ink-3 mt-0.5">
                        {FRAUD_FY[c.cohort_id]}
                      </div>
                    </div>
                    <div>
                      <RankBar
                        rank={c.rank_if_added}
                        total={c.n_after_add}
                        expected={(c.n_after_add + 1) / 2}
                        toneByRank
                      />
                      <div className="mt-2 text-[12px] text-ink-3">
                        Score{" "}
                        <span className="num text-ink">{formatNumber(c.score_mean, 5)}</span>{" "}
                        · {fraudCmp}
                      </div>
                    </div>
                    <RankStat
                      rank={c.rank_if_added}
                      total={c.n_after_add}
                      size="md"
                      tone={inTopThird ? "high" : "default"}
                    />
                  </div>
                );
              })}
            </div>
          </section>

          <p className="text-xs text-ink-3 leading-relaxed max-w-prose-narrow">
            A high rank in a single cohort just means this filing&rsquo;s
            language is unusual relative to that cohort&rsquo;s peers. It does{" "}
            <em>not</em> mean the filing is fraudulent. Real evidence of fraud
            requires high ranks across multiple cohorts <em>and</em>{" "}
            corroboration outside this signal. See{" "}
            <Link href="/limitations/" className="underline hover:text-navy-700">
              limitations
            </Link>{" "}
            before reading too much into a single result.
          </p>
        </>
      )}
    </div>
  );
}
