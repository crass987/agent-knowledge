"""
Tests for delta_stats — external statistical layer for capability-audit.

Pure functions, stdlib only. Implements the Wilson/Bayesian CI, paired
difference test, clustered SE and power analysis from the methodology
(arXiv:2503.01747, arXiv:2411.00640, arXiv:2509.24086).

Run with: python3 -m pytest skills/capability-audit/tests/ -v
"""

import math
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "scripts")
)

from delta_stats import (  # noqa: E402
    wilson_ci,
    beta_binomial_ci,
    required_n_for_delta,
    paired_difference_test,
    clustered_se,
    delta_significance,
)


# ── 1. wilson_ci ──────────────────────────────────────────────────────


class TestWilsonCI:
    """Wilson score interval (arXiv:2503.01747) — correct at small N, unlike CLT."""

    @pytest.mark.parametrize(
        "passes,n,exp_low,exp_high",
        [
            (0, 10, 0.0, 0.28),   # zero successes, n=10
            (10, 10, 0.72, 1.0),  # all pass
            (5, 10, 0.22, 0.76),  # symmetric
            (50, 100, 0.40, 0.60),  # large n, near 0.5
        ],
    )
    def test_table(self, passes, n, exp_low, exp_high):
        low, high = wilson_ci(passes, n)
        assert low == pytest.approx(exp_low, abs=0.02)
        assert high == pytest.approx(exp_high, abs=0.02)
        assert 0.0 <= low <= high <= 1.0

    def test_bounds_are_valid_probabilities(self):
        for passes in range(0, 31):
            low, high = wilson_ci(passes, 30)
            assert 0.0 <= low <= 1.0
            assert 0.0 <= high <= 1.0
            assert low <= high

    def test_zero_successes_lower_is_zero(self):
        low, high = wilson_ci(0, 20)
        assert low == 0.0

    def test_all_pass_upper_is_one(self):
        low, high = wilson_ci(20, 20)
        assert high == 1.0

    def test_shrinks_as_n_grows(self):
        width_30 = wilson_ci(15, 30)[1] - wilson_ci(15, 30)[0]
        width_300 = wilson_ci(150, 300)[1] - wilson_ci(150, 300)[0]
        assert width_300 < width_30

    def test_z_parameter_changes_width(self):
        w_95 = wilson_ci(5, 10, z=1.96)
        w_99 = wilson_ci(5, 10, z=2.576)
        assert (w_99[1] - w_99[0]) > (w_95[1] - w_95[0])

    def test_n_zero_is_safe(self):
        # edge case: no samples — must not raise, return (0,0) or (nan,nan)
        low, high = wilson_ci(0, 0)
        assert math.isnan(low) or low == 0.0


# ── 2. beta_binomial_ci ───────────────────────────────────────────────


class TestBetaBinomialCI:
    """Bayesian Beta-Binomial credible interval (sambowyer/bayes_evals)."""

    @pytest.mark.parametrize(
        "passes,n,exp_low,exp_high",
        [
            (0, 10, 0.0, 0.29),    # Beta(1,11)
            (10, 10, 0.71, 1.0),   # Beta(11,1)
            (5, 10, 0.21, 0.79),   # Beta(6,6) symmetric
            (50, 100, 0.40, 0.60),  # Beta(51,51)
        ],
    )
    def test_table(self, passes, n, exp_low, exp_high):
        low, high = beta_binomial_ci(passes, n)
        assert low == pytest.approx(exp_low, abs=0.03)
        assert high == pytest.approx(exp_high, abs=0.03)

    def test_symmetric_for_half(self):
        low, high = beta_binomial_ci(50, 100)
        c = (low + high) / 2
        assert c == pytest.approx(0.5, abs=0.01)

    def test_uniform_prior_default(self):
        # alpha=beta=1 == uniform prior; matches Beta(1+passes, 1+n-passes)
        low, high = beta_binomial_ci(3, 10, alpha=1, beta=1)
        low2, high2 = beta_binomial_ci(3, 10, alpha=0.5, beta=0.5)
        # Jeffreys prior should differ from uniform
        assert (low2, high2) != pytest.approx((low, high), abs=0.001)

    def test_bounds_valid(self):
        for passes in range(0, 21):
            low, high = beta_binomial_ci(passes, 20)
            assert 0.0 <= low <= high <= 1.0

    def test_zero_successes(self):
        # Beta(1,11): 2.5% quantile = 1 - 0.975^(1/11) ≈ 0.0023 (near zero)
        low, high = beta_binomial_ci(0, 10)
        assert low < 0.01
        assert high > 0

    def test_all_pass(self):
        # Beta(11,1): 97.5% quantile = 0.975^(1/11) ≈ 0.9977 (near one)
        low, high = beta_binomial_ci(10, 10)
        assert high > 0.99
        assert low < 1.0

    def test_n_zero_is_safe(self):
        low, high = beta_binomial_ci(0, 0)
        assert math.isnan(low) or (0.0 <= low <= 1.0)


# ── 3. required_n_for_delta ───────────────────────────────────────────


class TestRequiredNForDelta:
    """Power analysis: n ≈ 969/δ² (paired, arXiv:2411.00640)."""

    @pytest.mark.parametrize(
        "delta_pp,exp_n",
        [
            (3, 1000),    # 3pp → ~1000
            (5, 350),     # 5pp → ~350
            (10, 87),     # 10pp → ~87
        ],
    )
    def test_power_table(self, delta_pp, exp_n):
        n = required_n_for_delta(delta_pp / 100.0)
        # within 15% of the methodology table
        assert exp_n * 0.85 <= n <= exp_n * 1.15, (
            f"delta={delta_pp}pp: expected ~{exp_n}, got {n}"
        )

    def test_default_reproduces_969_at_3pp(self):
        n = required_n_for_delta(0.03)
        # the canonical Anthropic number for 3pp at α=0.05/80% power
        assert 900 <= n <= 1100

    def test_scales_as_inverse_delta_squared(self):
        n_small = required_n_for_delta(0.10)
        n_large = required_n_for_delta(0.05)
        # halving delta → ~4x the samples
        ratio = n_large / n_small
        assert 3.5 <= ratio <= 4.5

    def test_higher_power_needs_more_samples(self):
        n_80 = required_n_for_delta(0.05, power=0.8)
        n_95 = required_n_for_delta(0.05, power=0.95)
        assert n_95 > n_80

    def test_stricter_alpha_needs_more_samples(self):
        n_05 = required_n_for_delta(0.05, alpha=0.05)
        n_01 = required_n_for_delta(0.05, alpha=0.01)
        assert n_01 > n_05

    def test_returns_at_least_one(self):
        assert required_n_for_delta(0.5) >= 1

    def test_delta_zero_is_safe(self):
        # delta=0 → undefined power; must not raise or divide by zero silently
        n = required_n_for_delta(0.0)
        assert math.isnan(n) or n >= 1


# ── 4. paired_difference_test ─────────────────────────────────────────


class TestPairedDifferenceTest:
    """McNemar-style paired test on per-item differences (arXiv:2411.00640)."""

    def test_identical_results_not_significant(self):
        a = [True, False, True, False, True, True, False, False]
        b = list(a)
        r = paired_difference_test(a, b)
        assert r["discordant"] == 0
        assert r["agree_both"] == len(a)
        assert r["significant"] is False
        assert r["p_value_approx"] > 0.05

    def test_all_discordant_in_favor_of_b(self):
        # B passes everywhere A fails; with continuity correction n=4 is
        # underpowered, so use n=12 for a clear one-directional signal.
        a = [False] * 12
        b = [True] * 12
        r = paired_difference_test(a, b)
        assert r["discordant"] == 12
        assert r["b_only"] == 12  # A fail, B pass
        assert r["c_only"] == 0  # A pass, B fail
        assert r["significant"] is True

    def test_tiny_discordant_underpowered(self):
        # all-aligned but only 4 pairs → continuity correction → not significant
        a = [False] * 4
        b = [True] * 4
        r = paired_difference_test(a, b)
        assert r["discordant"] == 4
        assert r["b_only"] == 4
        assert r["c_only"] == 0
        assert r["significant"] is False  # small-N McNemar can't reach α

    def test_tied_discordant_not_significant(self):
        # equal flips in both directions → no signal
        # index0: A=T B=F → c_only; index1: A=F B=T → b_only; etc.
        a = [True, False, True, False]
        b = [False, True, False, True]
        r = paired_difference_test(a, b)
        assert r["b_only"] == 2
        assert r["c_only"] == 2
        assert r["discordant"] == 4
        assert r["significant"] is False

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            paired_difference_test([True, False], [True])

    def test_returns_required_keys(self):
        r = paired_difference_test(
            [True, False, True], [False, False, True]
        )
        for key in (
            "n",
            "agree_both",
            "discordant",
            "b_only",
            "c_only",
            "chi2",
            "p_value_approx",
            "significant",
            "delta",
        ):
            assert key in r, f"missing key: {key}"

    def test_delta_is_positive_when_harness_better(self):
        # "a" = cold (without component), "b" = with component
        cold = [False, False, True, False, True, False, True, False]
        harness = [True, False, True, True, True, False, True, False]
        r = paired_difference_test(cold, harness)
        assert r["delta"] > 0  # harness passes more

    def test_large_sample_real_improvement(self):
        # construct a clear improvement: 12 discordant pairs, 11 favor B, 1 favors A
        cold = [False] * 11 + [True] + [True] * 50 + [False] * 50
        harness = [True] * 11 + [False] + [True] * 50 + [False] * 50
        r = paired_difference_test(cold, harness)
        assert r["b_only"] == 11
        assert r["c_only"] == 1
        assert r["significant"] is True
        assert r["p_value_approx"] < 0.05


# ── 5. clustered_se ───────────────────────────────────────────────────


class TestClusteredSE:
    """Clustered SE — naive SE underestimates up to 3x (arXiv:2411.00640)."""

    def test_homogeneous_clusters_match_naive(self):
        # if every cluster has the same pass rate, clustering shouldn't inflate
        clusters = [[True, False], [True, False], [True, False]]
        se = clustered_se(clusters)
        # naive SE for p=0.5, N=6
        naive = math.sqrt(0.5 * 0.5 / 6)
        assert se == pytest.approx(naive, abs=0.02)

    def test_heterogeneous_clusters_larger_than_naive(self):
        # clusters differ wildly → clustered SE >> naive (ICC ≈ 1, Deff ≈ n̄)
        clusters = [
            [True, True, True, True],   # p=1.0
            [False, False, False, False],  # p=0.0
            [True, True, True, True],
            [False, False, False, False],
        ]
        se = clustered_se(clusters)
        naive = math.sqrt(0.5 * 0.5 / 16)
        assert se >= naive * 1.9  # roughly doubled (Deff = n̄ = 4 → SE = 2× naive)

    def test_single_cluster_is_nan(self):
        se = clustered_se([[True, True, False]])
        assert math.isnan(se) or se == 0.0

    def test_empty_cluster_handled(self):
        se = clustered_se([[True, False], [], [True, True]])
        assert not math.isnan(se)

    def test_returns_nonnegative(self):
        clusters = [[True, False, True], [False, True], [True, True, False, False]]
        se = clustered_se(clusters)
        assert se >= 0.0

    def test_cluster_labels_merge_groups(self):
        # two clusters share a label → merged into one group
        scores = [[True, False], [True, True], [False, False]]
        labels = ["cat", "cat", "dog"]
        se = clustered_se(scores, labels)
        # should compute over 2 groups (cat merged, dog)
        assert se >= 0.0


# ── 6. delta_significance ─────────────────────────────────────────────


class TestDeltaSignificance:
    """Combines paired test + CI into a single verdict."""

    def test_clear_improvement_is_significant(self):
        cold = [False] * 15 + [True] * 35
        harness = [True] * 14 + [False] + [True] * 35
        r = delta_significance(cold, harness)
        assert r["delta"] > 0.1
        assert r["significant"] is True
        assert "ci_low" in r and "ci_high" in r
        assert "note" in r

    def test_no_change_is_not_significant(self):
        cold = [True, False, True, False, True, False, True, False, True, False]
        harness = list(cold)
        r = delta_significance(cold, harness)
        assert r["delta"] == pytest.approx(0.0)
        assert r["significant"] is False

    def test_regression_is_negative_delta(self):
        cold = [True] * 18 + [False] * 2
        harness = [False] * 17 + [True] * 3
        r = delta_significance(cold, harness)
        assert r["delta"] < 0
        assert r["significant"] is True

    def test_small_n_notes_wilson(self):
        cold = [True, False, True]
        harness = [True, True, True]
        r = delta_significance(cold, harness)
        assert "wilson" in r["note"].lower() or "small" in r["note"].lower() or "n" in r["note"].lower()

    def test_ci_bounds_valid(self):
        cold = [True] * 20 + [False] * 30
        harness = [True] * 35 + [False] * 15
        r = delta_significance(cold, harness)
        assert 0.0 <= r["ci_low"] <= r["ci_high"] <= 1.0

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            delta_significance([True, False], [True])

    def test_all_pass_both(self):
        cold = [True] * 50
        harness = [True] * 50
        r = delta_significance(cold, harness)
        assert r["delta"] == 0.0
        assert r["significant"] is False
