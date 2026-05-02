"""Phase 6 — entity-masking ablation on Enron only (appendix experiment).

Replaces company-name + named-entity tokens in Enron's MD&A with the literal
``[ENTITY]`` token, recomputes embeddings + reconstruction error using Enron's
existing cohort autoencoder, then reports whether Enron's rank within its
cohort changes.

This is a defensive experiment for MiniLM contamination: if Enron's anomaly
score is being driven by literal mentions of "Enron" / "Skilling" / "Lay" /
"Andersen" etc. that MiniLM has seen in post-2008 web text, masking those
tokens should reduce the rank substantially. If the rank holds up, the signal
is unlikely to be pure literal-name leakage.

Hardcoded entity list keeps this reproducible — we deliberately don't run a
full NER model here (avoids spaCy as a dependency and the analysis-time
ambiguity of "what counts as an entity").
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.autoencoder import MODEL_DIR, load_cohort_autoencoder
from engine.edgar import _strip_dashes
from engine.embeddings import EmbeddingEngine, _cache_path
from engine.parsing import split_sentences
from engine.scoring import score_filing
from engine.stats import bootstrap_rank_ci, mann_whitney_fraud_vs_peers, rank_fraud_in_cohort

ENRON_TICKER = "ENE"
ENRON_ACCESSION = "0001024401-01-500010"

# Hardcoded entity list (case-insensitive). Includes Enron, key executives,
# auditor, and Enron's special-purpose entities widely known post-2002.
ENTITY_TOKENS = [
    "Enron",
    "Skilling",
    "Lay",
    "Fastow",
    "Causey",
    "Whalley",
    "Andersen",
    "Arthur Andersen",
    "Vinson & Elkins",
    "Vinson and Elkins",
    "JEDI",
    "Chewco",
    "LJM",
    "LJM1",
    "LJM2",
    "Raptor",
    "Whitewing",
    "Marlin",
    "Osprey",
]


def mask_entities(text: str, tokens: list[str] = ENTITY_TOKENS, replacement: str = "[ENTITY]") -> str:
    """Case-insensitive whole-word replacement of every token in ``tokens``."""
    if not tokens:
        return text
    pat = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in tokens) + r")\b", re.IGNORECASE)
    return pat.sub(replacement, text)


def main() -> int:
    parsed_path = REPO_ROOT / f"data/processed/parsed/{_strip_dashes(ENRON_ACCESSION)}.txt"
    if not parsed_path.exists():
        print(f"FAIL: {parsed_path} missing — run Phase 2 first.")
        return 1
    body = parsed_path.read_text(encoding="utf-8")

    masked = mask_entities(body)
    n_replacements = body.count("Enron") + body.count("ENRON") + body.count("Andersen")  # rough
    print(f"Original chars: {len(body):,}  Masked chars: {len(masked):,}")
    print(f"Approx Enron+Andersen mentions in original: {n_replacements}")

    sentences = split_sentences(masked)
    print(f"Sentences after masking: {len(sentences)}")

    engine = EmbeddingEngine()
    masked_acc = ENRON_ACCESSION + "__masked"
    fe = engine.encode_filing(masked_acc, sentences)
    print(f"Encoded {fe.n_sentences} masked sentences with MiniLM.")

    model_path = MODEL_DIR / f"{ENRON_TICKER}.pt"
    if not model_path.exists():
        print(f"FAIL: {model_path} missing — run Phase 3 first.")
        return 1
    model = load_cohort_autoencoder(model_path)

    score = score_filing(masked_acc, fe.embeddings, model)
    print(f"Masked Enron score (mean recon error): {score.mean_recon_error:.6f}")

    # Compare to existing scores.csv
    sc = REPO_ROOT / "data/results/scores.csv"
    if not sc.exists():
        print("WARN: no scores.csv — cannot compute rank delta. Run Phase 4 first.")
        return 0
    peers: list[float] = []
    fraud_orig: float | None = None
    with sc.open() as f:
        for row in csv.DictReader(f):
            if row["cohort_id"] != ENRON_TICKER:
                continue
            if row["fraud_or_peer"] == "fraud":
                fraud_orig = float(row["score_mean"])
            else:
                peers.append(float(row["score_mean"]))

    if fraud_orig is None:
        print("WARN: no original Enron fraud score in scores.csv.")
        return 0

    orig_rank = rank_fraud_in_cohort(ENRON_TICKER, fraud_orig, peers)
    masked_rank = rank_fraud_in_cohort(ENRON_TICKER, score.mean_recon_error, peers)

    print(f"\nEnron rank (original):  {orig_rank.fraud_rank}/{orig_rank.n_total}  "
          f"pct={orig_rank.fraud_percentile:.1f}")
    print(f"Enron rank (masked):    {masked_rank.fraud_rank}/{masked_rank.n_total}  "
          f"pct={masked_rank.fraud_percentile:.1f}")

    out = {
        "ticker": ENRON_TICKER,
        "accession": ENRON_ACCESSION,
        "n_replaced_token_classes": len(ENTITY_TOKENS),
        "original_score": fraud_orig,
        "masked_score": score.mean_recon_error,
        "original_rank": orig_rank.fraud_rank,
        "masked_rank": masked_rank.fraud_rank,
        "n_total_in_cohort": orig_rank.n_total,
        "rank_delta": masked_rank.fraud_rank - orig_rank.fraud_rank,
    }
    out_path = REPO_ROOT / "data/results/entity_masking_ablation.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
