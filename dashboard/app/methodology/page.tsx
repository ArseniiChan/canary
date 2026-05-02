export default function Methodology() {
  return (
    <div className="space-y-10 max-w-3xl">
      <section>
        <div className="eyebrow mb-4">Methodology</div>
        <h1 className="font-serif text-[2.25rem] md:text-[2.75rem] font-semibold text-navy-900 leading-[1.1]">
          One question, one signal, one test.
        </h1>
        <span className="h1-rule" aria-hidden />
        <p className="mt-5 text-lg text-ink-2 leading-relaxed">
          The discipline of this study is what makes the result informative. Every
          choice was committed to <span className="num">analysis_spec.md</span>{" "}
          and git-tagged before the validation script ran.
        </p>
      </section>

      <section className="bg-surface accent-border-top rounded-md shadow-card p-7 md:p-9 space-y-4">
        <h2 className="h-section text-[1.4rem]">The question</h2>
        <p className="text-ink-2 leading-relaxed">
          Does an unsupervised novelty signal computed over Management's Discussion
          and Analysis (Item 7) language assign elevated reconstruction error to
          historical fraud filings, relative to industry-and-year-matched clean
          peer filings, under strict out-of-sample evaluation?
        </p>
        <p className="text-sm text-ink-3">
          Single signal. Single test. No composite "fraud score." No fraud labels
          enter training.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="h-section text-[1.4rem]">Data</h2>
        <ul className="checklist text-ink-2 leading-relaxed">
          <li>
            Six historical fraud 10-Ks (Enron, WorldCom, Tyco, HealthSouth, Valeant,
            Lehman) — pre-discovery accessions verified against documented public-revelation
            dates.
          </li>
          <li>
            Industry-and-year-matched clean peer cohorts via SIC 2-digit + same
            calendar year of period-of-report. Achieved 12 clean peers per cohort
            with no SIC-1 fallback.
          </li>
          <li>
            Source: SEC EDGAR (public, free). 10 req/sec throttle, contact-email
            User-Agent per fair-access policy.
          </li>
        </ul>
        <p className="text-sm text-ink-3">
          A peer is "clean" if it is not on the AAER deny-list, has no 10-K/A
          within five years post-filing (programmatic via EDGAR), and is not on
          the class-action deny-list. Deny-lists are editable text files,
          intentionally incomplete, and disclosed in limitations.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="h-section text-[1.4rem]">MD&amp;A extraction</h2>
        <p className="text-ink-2 leading-relaxed">
          Multi-strategy parser handles both pre-2002 SGML/text and modern HTML
          filings. Locates an end boundary (last Item 7A or Item 8 anchor), then
          a start (first Item 7 past the table-of-contents threshold, falling
          back to a "Management's Discussion and Analysis" header for
          incorporation-by-reference filings like Tyco 2001). Rejects pairs that
          appear within 1,000 chars of each other (TOC noise) and bodies outside
          a sane size range.
        </p>
        <p className="text-sm text-ink-3">
          Extraction success rate across 78 filings: <span className="num">93.6%</span>{" "}
          (gate: <span className="num">≥ 80%</span>).
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="h-section text-[1.4rem]">The single signal</h2>
        <p className="text-ink-2 leading-relaxed">
          Each filing's MD&amp;A is sentence-tokenized, then embedded with{" "}
          <span className="num bg-surface-2 px-1.5 py-0.5 rounded text-sm">all-MiniLM-L6-v2</span>{" "}
          (384-dim). A PyTorch autoencoder
          (<span className="num">384 → 128 → 32 → 128 → 384</span>, ReLU, MSE,
          Adam <span className="num">lr=1e-3</span>, batch <span className="num">16</span>,
          200 epochs with early stopping on a 20% validation split, all seeded)
          is trained per-cohort under{" "}
          <strong>leave-one-cohort-out + time-controlled</strong> rules: the
          training set comprises clean peer filings from <em>other</em> cohorts
          dated on or before this fraud's filing date. Per-filing sentence cap of
          100 during training prevents long-MD&amp;A pseudoreplication.
          Filing-level score is the mean per-sentence reconstruction error.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="h-section text-[1.4rem]">Statistical defense</h2>
        <ul className="checklist text-ink-2 leading-relaxed">
          <li>Per-fraud rank within cohort, paired with random-baseline expectation.</li>
          <li>Mann-Whitney U on per-sentence reconstruction-error distributions; rank-biserial effect size.</li>
          <li>Bootstrap 95% CI on rank with 1,000 filing-level resamples.</li>
          <li>Within-cohort null-permutation p-value of P(rank ≤ observed) with 1,000 permutations.</li>
          <li>Leave-one-fraud-out aggregate sensitivity.</li>
        </ul>
      </section>

      <section className="bg-navy-50 rounded-md p-7 border border-navy-100 space-y-3">
        <h2 className="h-section text-[1.25rem]">Frozen-spec contract</h2>
        <p className="text-ink-2 leading-relaxed">
          The full analysis spec is committed to git and tagged{" "}
          <span className="num bg-surface px-1.5 py-0.5 rounded text-sm">validation-spec-frozen</span>{" "}
          before the validation script runs. Whatever the numbers say, that's
          the result — no tuning to the evaluation set, no iteration on the
          autoencoder or scoring after seeing per-fraud ranks.
        </p>
      </section>
    </div>
  );
}
