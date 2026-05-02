const LIMITS = [
  {
    title: "N = 6 frauds (5 in primary results)",
    body: (
      <>
        Confidence intervals on aggregate hit rates are wide. We report
        bootstrap CIs and leave-one-fraud-out sensitivity to make this explicit.
        Enron is excluded from primary results by the methodological constraint
        below — not by analyst choice.
      </>
    ),
  },
  {
    title: "Enron methodological exclusion",
    body: (
      <>
        Enron's FY2000 10-K was filed 2001-04-02 — earlier than every peer
        filing in every other cohort. Under the spec's strict
        leave-one-cohort-out + time-controlled rule, Enron's training set is
        empty. We document this as a finding rather than relax the spec
        post-hoc.
      </>
    ),
  },
  {
    title: "MiniLM pretraining contamination",
    body: (
      <>
        The embedding model was trained on the public web and may have seen
        post-2008 commentary about these specific frauds. An entity-masking
        ablation on Enron is part of the appendix; masking does not address
        possible contamination via paraphrase or topical leakage.
      </>
    ),
  },
  {
    title: "Peer-matching residuals",
    body: (
      <>
        SIC 2-digit + same fiscal year does not perfectly control for size,
        geography, or business model. EDGAR's currently-reported SIC may differ
        from a firm's 2001-era SIC (Enron is currently SIC 6200, Security &amp;
        Commodity Brokers — not the energy classification one might expect).
      </>
    ),
  },
  {
    title: "Parser-quality risk",
    body: (
      <>
        MD&amp;A extraction reached 93.6% across 78 filings. Per-cohort
        extraction quality varies; manual extraction fixes (none in this run)
        would be logged and applied symmetrically to fraud and peer filings.
      </>
    ),
  },
  {
    title: 'Operational "clean" rule with partial coverage',
    body: (
      <>
        AAER and class-action screening were applied via editable deny-lists
        rather than systematic database lookups. A peer that committed
        undisclosed fraud could appear in the cohort. Empirically, this would
        push our null toward zero (peers behave more like frauds), making our
        test conservative.
      </>
    ),
  },
  {
    title: "Single signal, single test",
    body: (
      <>
        We test exactly one signal — mean per-sentence reconstruction error
        from a 384→32 autoencoder over MiniLM embeddings. We do not compose
        multiple signals into a "fraud score" and we deliberately reject any
        framing that adds composite metrics to defend the primary result.
      </>
    ),
  },
  {
    title: "Negative-result honesty",
    body: (
      <>
        The aggregate hit@k is at or below the random baseline. Only Lehman
        shows a clear elevated rank within cohort. This study is most informative
        as evidence about <em>this specific signal at this sample size</em> — not
        as a general claim about MD&amp;A fraud-detection.
      </>
    ),
  },
];

export default function Limitations() {
  return (
    <div className="space-y-10 max-w-3xl">
      <section>
        <div className="eyebrow mb-4">Limitations — read first</div>
        <h1 className="font-serif text-[2.25rem] md:text-[2.75rem] font-semibold text-navy-900 leading-[1.1]">
          What this study cannot tell you.
        </h1>
        <span className="h1-rule" aria-hidden />
        <p className="mt-5 text-lg text-ink-2 leading-relaxed">
          This is the most important page on the site. Read it before reading
          any of the results.
        </p>
      </section>

      <ol className="space-y-5">
        {LIMITS.map((l, i) => (
          <li key={l.title} className="bg-surface rounded-md shadow-card p-6 md:p-7 flex gap-5">
            <div className="num text-2xl font-semibold text-navy-500 leading-none w-8 shrink-0">
              {String(i + 1).padStart(2, "0")}
            </div>
            <div>
              <h2 className="h-section text-[1.15rem]">
                {l.title}
              </h2>
              <p className="mt-2 text-[15px] text-ink-2 leading-relaxed">{l.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
