"""Phase 6 (post-hoc, council-recommended) — entity-masking ablation across the
5 cohorts that have autoencoders.

The pre-registered ablation targeted Enron only, but Enron has no LOCO+
time-controlled autoencoder. This post-hoc version replays the same logic
on HRC, LEH, TYC, VRX, WCOM. For each fraud filing, replace company-name +
key-executive + auditor tokens with the literal token ``[ENTITY]``, recompute
the MD&A embeddings against MiniLM, score against the existing cohort
autoencoder, and recompute the fraud's rank within the cohort.

Strict label: this is post-hoc and exploratory. It is not part of the frozen
pre-registered analysis; the ranks reported here do not displace the primary
results in scores.csv / per_fraud_metrics.json. The goal is defensive evidence
on whether MiniLM pretraining contamination on literal name tokens is driving
the fraud-filing reconstruction error.

Output: data/results/entity_masking_posthoc.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.autoencoder import MODEL_DIR, load_cohort_autoencoder
from engine.embeddings import EmbeddingEngine
from engine.parsing import split_sentences
from engine.scoring import score_filing
from engine.stats import (
    bootstrap_rank_ci,
    rank_fraud_in_cohort,
)

ENTITY_TOKENS_BY_COHORT: dict[str, list[str]] = {
    "LEH": [
        "Lehman", "Lehman Brothers", "Fuld", "Callan", "McDade", "Gregory",
        "Russo", "Ernst & Young", "Ernst and Young", "E&Y", "Repo 105",
    ],
    "HRC": [
        "HealthSouth", "Scrushy", "Owens", "Beam", "Carmichael",
        "Ernst & Young", "Ernst and Young",
    ],
    "TYC": [
        "Tyco", "Kozlowski", "Dennis Kozlowski", "Swartz", "Belnick",
        "ADT", "PricewaterhouseCoopers", "PwC",
    ],
    "VRX": [
        "Valeant", "Pearson", "Schiller", "Philidor", "Rosiello",
        "Ackman", "Pershing Square", "PricewaterhouseCoopers", "PwC",
        "Bausch", "Bausch & Lomb", "Salix",
    ],
    "WCOM": [
        "WorldCom", "Ebbers", "Bernie Ebbers", "Sullivan", "Scott Sullivan",
        "Cooper", "MCI", "Andersen", "Arthur Andersen",
    ],
}

REPLACEMENT = "[ENTITY]"


def mask(text: str, tokens: list[str]) -> str:
    if not tokens:
        return text
    pat = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in tokens) + r")\b", re.IGNORECASE)
    return pat.sub(REPLACEMENT, text)


def main() -> int:
    cohorts = json.loads((REPO_ROOT / "data/processed/cohorts.json").read_text())["cohorts"]
    fraud_manifest = json.loads((REPO_ROOT / "data/processed/fraud_manifest.json").read_text())
    fraud_by_ticker = {f["ticker"]: f for f in fraud_manifest["frauds"] if f["status"] == "OK"}

    # Reuse the existing scores.csv to get peer scores per cohort
    import csv
    scores_csv = REPO_ROOT / "data/results/scores.csv"
    peers_by_cohort: dict[str, list[float]] = {}
    fraud_orig_by_cohort: dict[str, float] = {}
    with scores_csv.open() as f:
        for row in csv.DictReader(f):
            cid = row["cohort_id"]
            if row["fraud_or_peer"] == "fraud":
                fraud_orig_by_cohort[cid] = float(row["score_mean"])
            else:
                peers_by_cohort.setdefault(cid, []).append(float(row["score_mean"]))

    engine = EmbeddingEngine()

    out: list[dict] = []
    for cid, tokens in ENTITY_TOKENS_BY_COHORT.items():
        cohort = next(c for c in cohorts if c["fraud_ticker"] == cid)
        fraud = fraud_by_ticker[cid]
        parsed_path = REPO_ROOT / f"data/processed/parsed/{fraud['accession'].replace('-', '')}.txt"
        if not parsed_path.exists():
            print(f"[{cid}] parsed file missing — skipping")
            continue
        body = parsed_path.read_text(encoding="utf-8")

        original_mentions = sum(
            len(re.findall(rf"\b{re.escape(t)}\b", body, re.IGNORECASE)) for t in tokens
        )
        masked_body = mask(body, tokens)
        post_mask_mentions = sum(
            len(re.findall(rf"\b{re.escape(t)}\b", masked_body, re.IGNORECASE)) for t in tokens
        )
        sents = split_sentences(masked_body)
        if not sents:
            print(f"[{cid}] no sentences after masking — skipping")
            continue

        masked_acc = fraud["accession"] + "__masked_posthoc"
        fe = engine.encode_filing(masked_acc, sents)

        model_path = MODEL_DIR / f"{cid}.pt"
        if not model_path.exists():
            print(f"[{cid}] no autoencoder — skipping")
            continue
        model = load_cohort_autoencoder(model_path)
        sf = score_filing(masked_acc, fe.embeddings, model)
        masked_score = sf.mean_recon_error

        peers = np.asarray(peers_by_cohort[cid], dtype=float)
        orig_score = fraud_orig_by_cohort[cid]
        orig_rank = rank_fraud_in_cohort(cid, orig_score, peers)
        masked_rank = rank_fraud_in_cohort(cid, masked_score, peers)
        boot = bootstrap_rank_ci(cid, masked_score, peers, n_bootstrap=1000, seed=42)

        record = {
            "ticker": cid,
            "accession": fraud["accession"],
            "n_token_classes_masked": len(tokens),
            "n_mentions_replaced_approx": original_mentions - post_mask_mentions,
            "original_score": orig_score,
            "masked_score": masked_score,
            "original_rank": orig_rank.fraud_rank,
            "masked_rank": masked_rank.fraud_rank,
            "n_total_in_cohort": orig_rank.n_total,
            "rank_delta": masked_rank.fraud_rank - orig_rank.fraud_rank,
            "masked_boot_lower_95": boot.lower_95,
            "masked_boot_upper_95": boot.upper_95,
        }
        out.append(record)
        print(
            f"[{cid}] tokens={len(tokens):>2}  replacements~{record['n_mentions_replaced_approx']:>3}  "
            f"orig_rank={orig_rank.fraud_rank}/{orig_rank.n_total}  "
            f"masked_rank={masked_rank.fraud_rank}/{masked_rank.n_total}  "
            f"delta={record['rank_delta']:+d}"
        )

    out_path = REPO_ROOT / "data/results/entity_masking_posthoc.json"
    out_path.write_text(json.dumps({"per_fraud": out, "label": "post-hoc; not pre-registered"}, indent=2) + "\n")
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
