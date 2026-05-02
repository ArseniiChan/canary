"""Tests for engine/stats.py."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.stats import (
    aggregate_hit_rates,
    bootstrap_rank_ci,
    leave_one_fraud_out,
    mann_whitney_fraud_vs_peers,
    null_permutation_p,
    rank_fraud_in_cohort,
)


def test_rank_fraud_in_cohort_top():
    res = rank_fraud_in_cohort("X", fraud_score=10.0, peer_scores=[1.0, 2.0, 3.0])
    assert res.fraud_rank == 1
    assert res.hit_at_1 == 1
    assert res.hit_at_3 == 1
    assert res.hit_at_5 == 1
    assert res.fraud_percentile == 100.0


def test_rank_fraud_in_cohort_bottom():
    res = rank_fraud_in_cohort("X", fraud_score=0.5, peer_scores=[1.0, 2.0, 3.0])
    assert res.fraud_rank == 4  # 4 of 4
    assert res.hit_at_1 == 0
    assert res.hit_at_3 == 0
    assert res.fraud_percentile == 0.0


def test_rank_fraud_in_cohort_random_baseline_correct():
    res = rank_fraud_in_cohort("X", fraud_score=2.5, peer_scores=[1.0, 2.0, 3.0])
    n = 4
    assert res.random_hit1 == 1.0 / n
    assert res.random_hit3 == 3.0 / n
    assert res.random_hit5 == 1.0  # min(5, 4) = 4, /4 = 1


def test_mann_whitney_fraud_higher():
    fraud = np.array([0.9, 1.0, 1.1, 1.2])
    peers = np.array([0.1, 0.2, 0.3, 0.4])
    res = mann_whitney_fraud_vs_peers("X", fraud, peers)
    assert res.p_value < 0.05
    assert res.rank_biserial_effect > 0


def test_mann_whitney_fraud_lower():
    fraud = np.array([0.1, 0.2, 0.3, 0.4])
    peers = np.array([0.9, 1.0, 1.1, 1.2])
    res = mann_whitney_fraud_vs_peers("X", fraud, peers)
    # one-sided "greater" should be near 1.0 if fraud is actually lower
    assert res.p_value > 0.5
    assert res.rank_biserial_effect < 0


def test_bootstrap_rank_ci_is_within_range():
    rng_seed = 42
    res = bootstrap_rank_ci("X", 10.0, [1.0, 2.0, 3.0, 4.0, 5.0], n_bootstrap=200, seed=rng_seed)
    assert 1 <= res.lower_95 <= res.upper_95
    assert res.point == 1


def test_null_permutation_p_uniform():
    res = null_permutation_p("X", 5.0, [1.0, 2.0, 3.0, 4.0], n_permutations=2000, seed=42)
    # Observed rank is 1 (fraud is highest); under uniform, P(permuted rank <= 1) = 1/5 = 0.2
    assert 0.15 <= res.p_le_observed <= 0.25
    assert res.observed_rank == 1


def test_aggregate_hit_rates_averages_across_cohorts():
    rs = [
        rank_fraud_in_cohort("A", 10.0, [1.0, 2.0, 3.0]),  # rank 1
        rank_fraud_in_cohort("B", 0.5, [1.0, 2.0, 3.0]),    # rank 4
    ]
    agg = aggregate_hit_rates(rs)
    assert agg["hit_at_1"] == 0.5  # 1 of 2
    assert agg["hit_at_3"] == 0.5  # rank 4 not in top 3 — only A counts
    assert agg["hit_at_5"] == 1.0  # both within top 5


def test_leave_one_fraud_out_returns_n_aggregates():
    rs = [
        rank_fraud_in_cohort("A", 10.0, [1.0, 2.0, 3.0]),
        rank_fraud_in_cohort("B", 0.5, [1.0, 2.0, 3.0]),
        rank_fraud_in_cohort("C", 5.0, [1.0, 2.0, 3.0]),
    ]
    out = leave_one_fraud_out(rs)
    assert len(out) == 3
    removed = {ticker for ticker, _ in out}
    assert removed == {"A", "B", "C"}
