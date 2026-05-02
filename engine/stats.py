"""Statistical analysis: per-fraud rank, Mann-Whitney U, bootstrap CI,
null permutation, leave-one-fraud-out sensitivity.

The functions in this module are deterministic given a seed, so the validation
script can be re-run reproducibly. They consume the per-filing scores produced
by ``engine.scoring`` and the per-sentence error arrays where needed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import mannwhitneyu


@dataclass
class CohortRankResult:
    cohort_id: str
    n_total: int  # fraud + clean peers
    fraud_score: float
    fraud_rank: int  # 1 = highest score (most novel)
    fraud_percentile: float  # in [0, 100]
    hit_at_1: int
    hit_at_3: int
    hit_at_5: int
    random_hit1: float  # = 1/n
    random_hit3: float  # = min(3,n)/n
    random_hit5: float  # = min(5,n)/n


@dataclass
class MannWhitneyResult:
    cohort_id: str
    u_statistic: float
    p_value: float
    rank_biserial_effect: float  # in [-1, 1]; positive = fraud > peers
    n_fraud_sentences: int
    n_peer_sentences: int


@dataclass
class BootstrapCI:
    cohort_id: str
    metric: str  # "rank" or other
    point: float
    lower_95: float
    upper_95: float
    n_bootstrap: int


@dataclass
class NullPermutationResult:
    cohort_id: str
    observed_rank: int
    p_le_observed: float  # P(permuted rank <= observed) under H0
    n_permutations: int


def rank_fraud_in_cohort(
    cohort_id: str,
    fraud_score: float,
    peer_scores: list[float] | np.ndarray,
) -> CohortRankResult:
    peers = np.asarray(peer_scores, dtype=float)
    all_scores = np.concatenate([[fraud_score], peers])
    # rank 1 = highest score (most "novel" / most reconstruction error)
    order = np.argsort(-all_scores, kind="stable")
    rank = int(np.where(order == 0)[0][0]) + 1
    n = int(all_scores.shape[0])
    pct = 100.0 * (1.0 - (rank - 1) / max(n - 1, 1)) if n > 1 else 100.0
    return CohortRankResult(
        cohort_id=cohort_id,
        n_total=n,
        fraud_score=float(fraud_score),
        fraud_rank=rank,
        fraud_percentile=float(pct),
        hit_at_1=int(rank <= 1),
        hit_at_3=int(rank <= 3),
        hit_at_5=int(rank <= 5),
        random_hit1=1.0 / n,
        random_hit3=min(3, n) / n,
        random_hit5=min(5, n) / n,
    )


def mann_whitney_fraud_vs_peers(
    cohort_id: str,
    fraud_per_sentence: np.ndarray,
    peer_per_sentence_concat: np.ndarray,
) -> MannWhitneyResult:
    """Mann-Whitney U on fraud sentence reconstruction errors vs. peer sentence
    reconstruction errors.

    Effect size: rank-biserial correlation = (2 * U / (n_fraud * n_peer)) - 1,
    in [-1, 1]; positive values mean fraud sentences tend to have higher
    reconstruction error than peer sentences.
    """
    a = np.asarray(fraud_per_sentence, dtype=float).ravel()
    b = np.asarray(peer_per_sentence_concat, dtype=float).ravel()
    if a.size == 0 or b.size == 0:
        return MannWhitneyResult(cohort_id, float("nan"), float("nan"), float("nan"),
                                 int(a.size), int(b.size))
    u, p = mannwhitneyu(a, b, alternative="greater")
    eff = (2.0 * u / (a.size * b.size)) - 1.0
    return MannWhitneyResult(
        cohort_id=cohort_id,
        u_statistic=float(u),
        p_value=float(p),
        rank_biserial_effect=float(eff),
        n_fraud_sentences=int(a.size),
        n_peer_sentences=int(b.size),
    )


def bootstrap_rank_ci(
    cohort_id: str,
    fraud_score: float,
    peer_scores: list[float] | np.ndarray,
    *,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> BootstrapCI:
    """Filing-level bootstrap CI on the fraud's rank within the cohort.

    Each iteration resamples peer filings WITH replacement to a cohort of
    the same size, recomputes the fraud's rank, and the 95% CI is taken
    from the empirical rank distribution.
    """
    peers = np.asarray(peer_scores, dtype=float)
    rng = np.random.default_rng(seed)
    ranks: list[int] = []
    for _ in range(n_bootstrap):
        sample = rng.choice(peers, size=peers.shape[0], replace=True)
        all_scores = np.concatenate([[fraud_score], sample])
        order = np.argsort(-all_scores, kind="stable")
        ranks.append(int(np.where(order == 0)[0][0]) + 1)
    arr = np.asarray(ranks, dtype=float)
    point = rank_fraud_in_cohort(cohort_id, fraud_score, peers).fraud_rank
    return BootstrapCI(
        cohort_id=cohort_id,
        metric="rank",
        point=float(point),
        lower_95=float(np.percentile(arr, 2.5)),
        upper_95=float(np.percentile(arr, 97.5)),
        n_bootstrap=n_bootstrap,
    )


def null_permutation_p(
    cohort_id: str,
    fraud_score: float,
    peer_scores: list[float] | np.ndarray,
    *,
    n_permutations: int = 1000,
    seed: int = 42,
) -> NullPermutationResult:
    """Within-cohort null permutation: shuffle the 'fraud' label and compute
    the empirical p-value of P(permuted rank <= observed rank).

    Under H0 (fraud and peers are exchangeable), the rank assigned to a
    randomly chosen filing is uniformly distributed over {1, ..., n}.
    Comparing the observed rank against this distribution gives a clean
    one-sided p-value for the 'fraud's rank is at least as extreme as observed'
    null.
    """
    peers = np.asarray(peer_scores, dtype=float)
    obs = rank_fraud_in_cohort(cohort_id, fraud_score, peers).fraud_rank
    rng = np.random.default_rng(seed)
    all_scores = np.concatenate([[fraud_score], peers])
    n_le = 0
    for _ in range(n_permutations):
        # Choose a random index as the 'fraud' position
        idx = int(rng.integers(0, all_scores.shape[0]))
        # Compute that index's rank under the same scoring
        order = np.argsort(-all_scores, kind="stable")
        permuted_rank = int(np.where(order == idx)[0][0]) + 1
        if permuted_rank <= obs:
            n_le += 1
    return NullPermutationResult(
        cohort_id=cohort_id,
        observed_rank=int(obs),
        p_le_observed=float(n_le / n_permutations),
        n_permutations=n_permutations,
    )


def aggregate_hit_rates(rank_results: list[CohortRankResult]) -> dict[str, float]:
    """Aggregate hit@k across cohorts (sum of hits / number of cohorts)."""
    if not rank_results:
        return {"hit_at_1": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0,
                "random_hit_at_1": 0.0, "random_hit_at_3": 0.0, "random_hit_at_5": 0.0}
    n = len(rank_results)
    return {
        "hit_at_1": sum(r.hit_at_1 for r in rank_results) / n,
        "hit_at_3": sum(r.hit_at_3 for r in rank_results) / n,
        "hit_at_5": sum(r.hit_at_5 for r in rank_results) / n,
        "random_hit_at_1": sum(r.random_hit1 for r in rank_results) / n,
        "random_hit_at_3": sum(r.random_hit3 for r in rank_results) / n,
        "random_hit_at_5": sum(r.random_hit5 for r in rank_results) / n,
    }


def leave_one_fraud_out(
    rank_results: list[CohortRankResult],
) -> list[tuple[str, dict[str, float]]]:
    out: list[tuple[str, dict[str, float]]] = []
    for i, r in enumerate(rank_results):
        rest = rank_results[:i] + rank_results[i + 1 :]
        out.append((r.cohort_id, aggregate_hit_rates(rest)))
    return out
