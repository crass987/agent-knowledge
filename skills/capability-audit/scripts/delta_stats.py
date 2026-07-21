#!/usr/bin/env python3
"""
delta_stats — external statistical layer for the capability-audit skill.

Stdlib only. Implements the Wilson / Beta-Binomial intervals, the paired
difference test (McNemar-style), clustered standard errors and the power
analysis that the methodology requires. The methodology rejects the naive
"run 5 times, look at the mean" approach; these functions are what makes an
audit honest.

Grounding:
  - Wilson score interval & why CLT under-covers at small N: arXiv:2503.01747
  - Power n ≈ 969/δ², paired-differences, clustered SE:    arXiv:2411.00640
  - ≥2 runs remove ~83% of rank inversions:                arXiv:2509.24086

Usage:
    from delta_stats import wilson_ci, delta_significance
    low, high = wilson_ci(passes=42, n=100)

This module is a library. The skill orchestrates runs; it never holds stats
state in its head — it calls these pure functions on per-item results.

Run tests:  python3 -m pytest skills/capability-audit/tests/ -v
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "wilson_ci",
    "beta_binomial_ci",
    "required_n_for_delta",
    "paired_difference_test",
    "clustered_se",
    "delta_significance",
]


# ── numeric helpers (stdlib has no scipy) ──────────────────────────────


def _lanczos_log_gamma(x: float) -> float:
    """Lanczos approximation for log(Γ(x)), x > 0."""
    g = 7
    p = [
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7,
    ]
    if x < 0.5:
        # reflection formula
        return math.log(math.pi / math.sin(math.pi * x)) - _lanczos_log_gamma(1.0 - x)
    x -= 1.0
    a = p[0]
    t = x + g + 0.5
    for i in range(1, g + 2):
        a += p[i] / (x + i)
    return 0.5 * math.log(2.0 * math.pi) + (x + 0.5) * math.log(t) - t + math.log(a)


def _betacf(a: float, b: float, x: float) -> float:
    """Continued-fraction expansion for the incomplete beta function (Lentz)."""
    fpmin = 1e-30
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, 301):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-10:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = _lanczos_log_gamma(a + b) - _lanczos_log_gamma(a) - _lanczos_log_gamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def _beta_ppf(a: float, b: float, q: float) -> float:
    """Inverse of the regularized incomplete beta (quantile) via bisection.

    Robust and dependency-free; ~40 iterations gives <1e-6 precision on [0,1].
    """
    if q <= 0.0:
        return 0.0
    if q >= 1.0:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if _betai(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _norm_ppf(p: float) -> float:
    """Inverse standard-normal CDF (Acklam's rational approximation)."""
    if p <= 0.0:
        return float("-inf")
    if p >= 1.0:
        return float("inf")
    a = [
        -3.969683028665376e+01,
        2.209460984245205e+02,
        -2.759285104469687e+02,
        1.383577518672690e+02,
        -3.066479806614716e+01,
        2.506628277459239e+00,
    ]
    b = [
        -5.447609879822406e+01,
        1.615858368580409e+02,
        -1.556989798598866e+02,
        6.680131188771972e+01,
        -1.328068155288572e+01,
    ]
    c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e+00,
        -2.549732539343734e+00,
        4.374664141464968e+00,
        2.938163982698783e+00,
    ]
    d = [
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e+00,
        3.754408661907416e+00,
    ]
    plow = 0.02425
    phigh = 1.0 - plow
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        num = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
        den = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        x = num / den
    elif p <= phigh:
        q = p - 0.5
        r = q * q
        num = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
        den = ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0
        x = num / den
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        num = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
        den = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        x = -num / den
    return x


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


# ── 1. confidence intervals ───────────────────────────────────────────


def wilson_ci(passes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Correct coverage at small N; the CLT normal interval systematically
    under-covers below a few hundred datapoints (arXiv:2503.01747).

    Returns (low, high) in [0, 1]. For n == 0 returns (nan, nan).
    """
    if n <= 0:
        return (float("nan"), float("nan"))
    p = passes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n))
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return (low, high)


def beta_binomial_ci(
    passes: int, n: int, alpha: float = 1.0, beta: float = 1.0
) -> Tuple[float, float]:
    """Equal-tailed 95% Beta-Binomial Bayesian credible interval.

    Posterior: Beta(alpha + passes, beta + n - passes). With the default
    uniform prior (alpha=beta=1) this is the sambowyer/bayes_evals interval
    recommended alongside Wilson for small-N LLM evals (arXiv:2503.01747).

    Returns (low, high) in [0, 1]. For n == 0 returns (nan, nan).
    """
    if n <= 0:
        return (float("nan"), float("nan"))
    a = alpha + passes
    b = beta + (n - passes)
    low = _beta_ppf(a, b, 0.025)
    high = _beta_ppf(a, b, 0.975)
    return (low, high)


# ── 2. power analysis ─────────────────────────────────────────────────


# Paired-difference variance factor calibrated to Miller/Anthropic
# (arXiv:2411.00640): n ≈ 969 independent questions for a 3pp detectable
# delta at α=0.05 / 80% power. (1.96 + 0.84)² × factor = 969 × 0.03² → factor
# ≈ 0.1112. Scales with (z_α/2 + z_β)² when alpha/power change.
_PAIRED_VAR_FACTOR = 0.1112


def required_n_for_delta(
    delta: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Minimum questions to detect a true success-rate delta, paired design.

    Mirrors arXiv:2411.00640: n scales as 1/δ². At defaults (α=0.05, 80%
    power) a 3pp delta needs ~1000 questions, 5pp ~350, 10pp ~87.

    `delta` is a proportion (0.03 for 3 percentage points). Returns >= 1.
    delta <= 0 is undefined; returns NaN to flag it.
    """
    if delta <= 0.0:
        return float("nan")  # type: ignore[return-value]
    z_alpha = _norm_ppf(1.0 - alpha / 2.0)
    z_beta = _norm_ppf(power)
    n = (z_alpha + z_beta) ** 2 * _PAIRED_VAR_FACTOR / (delta ** 2)
    return max(1, int(math.ceil(n)))


# ── 3. paired difference test (McNemar) ───────────────────────────────


def paired_difference_test(
    scores_a: Sequence[bool], scores_b: Sequence[bool], alpha: float = 0.05
) -> Dict[str, float]:
    """Per-item paired test on pass/fail differences (McNemar-style).

    Compares two configs on the SAME probe items: scores_a = "cold" (without
    the component), scores_b = "with harness". Comparing two independent CIs
    is wrong — frontier-model scores correlate 0.3–0.7 across items, so the
    paired test eliminates question-difficulty variance (arXiv:2411.00640).

    Discordant pairs:  b_only = A fails / B passes  (component helped)
                       c_only = A passes / B fails  (component hurt)
    χ² (with continuity correction) = (|b - c| - 1)² / (b + c)
    p-value from the χ²₁ survival function via erfc.

    Returns dict with n, agree_both, discordant, b_only, c_only, chi2,
    p_value_approx, significant, delta (= p_B - p_A).
    """
    n = len(scores_a)
    if n != len(scores_b):
        raise ValueError(
            f"paired test requires equal-length lists: {n} vs {len(scores_b)}"
        )
    b_only = c_only = 0
    agree_both = 0
    sum_a = sum_b = 0
    for a, b in zip(scores_a, scores_b):
        ba = bool(a)
        bb = bool(b)
        sum_a += int(ba)
        sum_b += int(bb)
        if ba and not bb:
            c_only += 1  # A passes, B fails (component hurt)
        elif bb and not ba:
            b_only += 1  # A fails, B passes (component helped)
        else:
            agree_both += 1
    discordant = b_only + c_only
    # McNemar with continuity correction; guard discordant == 0
    if discordant > 0:
        chi2 = (abs(b_only - c_only) - 1.0) ** 2 / discordant
        chi2 = max(0.0, chi2)
        # χ²₁ survival function = erfc(sqrt(χ²/2))
        p_value = math.erfc(math.sqrt(chi2 / 2.0))
    else:
        chi2 = 0.0
        p_value = 1.0
    delta = (sum_b / n if n else 0.0) - (sum_a / n if n else 0.0)
    return {
        "n": n,
        "agree_both": agree_both,
        "discordant": discordant,
        "b_only": b_only,
        "c_only": c_only,
        "chi2": chi2,
        "p_value_approx": p_value,
        "significant": bool(p_value < alpha and discordant > 0),
        "delta": delta,
    }


# ── 4. clustered standard error ───────────────────────────────────────


def clustered_se(
    scores: Sequence[Sequence[bool]],
    cluster_labels: Optional[Sequence] = None,
) -> float:
    """Cluster-robust standard error of the overall pass-rate.

    Treating grouped items (e.g. probes by category) as independent inflates
    the SE up to 3× vs the naive sqrt(p(1-p)/N) — naive SE silently
    underestimates uncertainty when items within a cluster correlate
    (arXiv:2411.00640).

    `scores` is a list of clusters; each cluster is a list of bool pass/fail
    results. If `cluster_labels` is given (one label per cluster, parallel to
    `scores`), clusters sharing a label are merged first — use this when the
    outer list splits one logical group across entries.

    Method: estimate the intra-cluster correlation (ICC) via a one-way random
    effects ANOVA, then apply Kish's design effect  Deff = 1 + (n̄−1)·ρ.
    SE_cluster = sqrt(ȳ(1−ȳ)/N · Deff). When clusters are homogeneous, ρ→0,
    Deff→1 and this reduces to the naive SE; when clusters differ, ρ rises
    and the SE inflates. Returns NaN when fewer than 2 groups or N < 2.
    """
    if not scores:
        return float("nan")
    # Merge by label if provided.
    if cluster_labels is not None and len(cluster_labels) == len(scores):
        groups: Dict[object, List[bool]] = {}
        for label, items in zip(cluster_labels, scores):
            groups.setdefault(label, []).extend(bool(x) for x in items)
        merged = list(groups.values())
    else:
        merged = [list(c) for c in scores if len(c) > 0]

    m = len(merged)
    if m < 2:
        return float("nan")
    n_per = [len(g) for g in merged]
    N = sum(n_per)
    if N < 2:
        return float("nan")
    p_g = [sum(1 for x in g if x) / len(g) for g in merged]
    p_hat = sum(sum(1 for x in g if x) for g in merged) / N  # overall rate

    # One-way random-effects mean squares.
    ss_between = sum(n_g * (pg - p_hat) ** 2 for n_g, pg in zip(n_per, p_g))
    msb = ss_between / (m - 1)
    ss_within = sum(
        sum((float(x) - pg) ** 2 for x in g)
        for g, pg in zip(merged, p_g)
    )
    denom_w = (N - m)
    msw = ss_within / denom_w if denom_w > 0 else 0.0

    n_bar = N / m
    if msb + (n_bar - 1) * msw > 0:
        rho = (msb - msw) / (msb + (n_bar - 1) * msw)
        rho = max(0.0, rho)  # negative ICC → treat as 0 (no clustering effect)
    else:
        rho = 0.0
    deff = 1.0 + (n_bar - 1.0) * rho
    var_naive = p_hat * (1.0 - p_hat) / N
    return math.sqrt(max(0.0, var_naive * deff))


# ── 5. combined verdict ───────────────────────────────────────────────


def delta_significance(
    scores_cold: Sequence[bool],
    scores_harness: Sequence[bool],
    alpha: float = 0.05,
) -> Dict[str, float]:
    """One-call verdict: is the with-harness config really better?

    Combines the paired difference test (does the component move per-item
    outcomes beyond noise?) with a Wilson CI on the with-harness rate (how
    uncertain is that rate?). This is the function the skill's Phase 4 calls
    on exported per-item data from Inspect/LangSmith — no framework gives a
    significance test out of the box (arXiv:2411.00640).

    `scores_cold` = results WITHOUT the component; `scores_harness` = WITH.
    Returns dict with delta, ci_low, ci_high (Wilson on the harness rate),
    p_value, significant, and a note flagging the small-N / silent-quadrant
    caveats the methodology demands.
    """
    n = len(scores_cold)
    if n != len(scores_harness):
        raise ValueError(
            f"equal-length lists required: {n} vs {len(scores_harness)}"
        )
    paired = paired_difference_test(scores_cold, scores_harness, alpha=alpha)
    passes_h = sum(1 for x in scores_harness if x)
    ci_low, ci_high = wilson_ci(passes_h, n) if n > 0 else (float("nan"), float("nan"))

    notes = []
    if n < 30:
        notes.append("n<30: Wilson CI used (CLT under-covers); do not trust a CLT interval here")
    if n > 0:
        power_target = required_n_for_delta(max(1e-6, abs(paired["delta"]) or 1e-6))
        if n < power_target * 0.5:
            notes.append(
                f"n={n} below the ~{power_target} needed to resolve this delta at 80% power — likely underpowered"
            )
    if paired["discordant"] == 0:
        notes.append("zero discordant pairs — configs are indistinguishable on this probe set")
    if not notes:
        notes.append("paired McNemar; Wilson CI on harness rate")

    return {
        "n": n,
        "delta": paired["delta"],
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_value": paired["p_value_approx"],
        "significant": paired["significant"],
        "discordant": paired["discordant"],
        "note": "; ".join(notes),
    }


if __name__ == "__main__":
    # Smoke test when run directly.
    import json

    demo = {
        "wilson_42_of_100": wilson_ci(42, 100),
        "beta_42_of_100": beta_binomial_ci(42, 100),
        "required_n_3pp": required_n_for_delta(0.03),
        "required_n_5pp": required_n_for_delta(0.05),
        "required_n_10pp": required_n_for_delta(0.10),
    }
    print(json.dumps(demo, indent=2, default=lambda v: round(v, 4) if isinstance(v, float) else v))
