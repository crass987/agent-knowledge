# Statistics — the engine that makes an audit honest

The single rule: **"ran it 5 times, looked at the mean" is noise.** This file is
the recipe, with the formulas `scripts/delta_stats.py` implements and the
citations that ground them.

## Which confidence interval to use

For N below a few hundred, the CLT normal interval systematically under-covers.
Bowyer et al. (ICML 2025 Spotlight, arXiv:2503.01747) compared normal (CLT),
Wilson, Clopper-Pearson and Bayesian Beta-Binomial across 80 000 synthetic
datasets at N = 3, 10, 30, 100. **Only the Bayesian credible interval and
Wilson give correct coverage at small N.** The N=30 textbook threshold is
directly debunked.

| N | Use | Notes |
|---|---|---|
| **< a few hundred** | **Wilson** or **Beta-Binomial Bayesian** (`sambowyer/bayes_evals`) | CLT under-covers; never trust a CLT interval here |
| ~thousands | `CI₉₅ = mean ± 1.96·SEM`, `SEM = √(Var(scores)/n)` | bootstrap only for a complex sampling scheme |

### Wilson score interval

```
p = passes / n
denom  = 1 + z²/n
center = (p + z²/(2n)) / denom
margin = (z / denom) · √( p(1−p)/n + z²/(4n²) )
CI     = [ max(0, center − margin), min(1, center + margin) ]
```
z = 1.96 for 95%. Correct coverage for any n ≥ 1; zero successes → lower bound
exactly 0; all pass → upper bound exactly 1.

### Beta-Binomial credible interval

Posterior with Beta(α, β) prior after observing `passes`/`n`:
`Beta(α + passes, β + n − passes)`. Default uniform prior α=β=1. Equal-tailed
95% interval = the 2.5% and 97.5% quantiles. With α=β=0.5 (Jeffreys) it is
slightly tighter near the boundaries.

## Power analysis — how many questions you need

Miller / Anthropic (arXiv:2411.00640), paired comparison at α=0.05, 80% power:
**n ≈ 969/δ²** — i.e. ~969 independent questions to detect a 3pp delta.

| Min detectable delta (δ) | ≈ questions |
|---|---|
| 3 pp | ~1000 |
| 5 pp | ~350 |
| 10 pp | ~87 |

Scales as 1/δ². `required_n_for_delta(delta, alpha, power)` reproduces this:
halving the delta needs ~4× the samples; stricter α or higher power needs more.

## Three mandatory conditions

### 1. Paired difference test on per-item results

Do **not** compare two independent confidence intervals. Frontier-model scores
correlate 0.3–0.7 across items; a paired test eliminates the variance in
question difficulty (arXiv:2411.00640).

`paired_difference_test(scores_a, scores_b)` is McNemar-style on the discordant
pairs:
- `b_only` = A fails / B passes (component helped)
- `c_only` = A passes / B fails (component hurt)
- χ² (with continuity correction) = (|b − c| − 1)² / (b + c)
- p-value = χ²₁ survival function = `erfc(√(χ²/2))`

With continuity correction, tiny discordant counts (n=4 all-aligned) do **not**
reach α=0.05 — that is correct behaviour, not a bug. Significance needs enough
discordant pairs.

### 2. Clustered standard error

When items are grouped by category, naive SE = `√(p(1−p)/N)` underestimates by
up to **3×** (arXiv:2411.00640). `clustered_se(scores)` estimates the
intra-cluster correlation (ICC) via a one-way random-effects ANOVA and applies
Kish's design effect:

```
Deff = 1 + (n̄ − 1)·ρ
SE_cluster = √( ȳ(1−ȳ)/N · Deff )
```

Homogeneous clusters → ρ→0 → Deff→1 → reduces to naive SE. Heterogeneous
clusters → ρ rises → SE inflates. This is the defensible, parameter-light way
to surface the inflation the paper reports.

### 3. At least two runs

Stochastic decoding inverts rankings: "Do Repetitions Matter?" (arXiv:2509.24086)
found **two runs remove ~83% of ranking inversions**; SE shrinks ≈ as 1/√R. One
run is never enough under stochastic decoding.

## No framework gives significance out of the box

Inspect AI is closest (`bootstrap_stderr(1000)`, clustered stderr, `Epochs`) but
has no cross-config p-value. **Export per-item data and compute statistics
externally** — `scripts/delta_stats.py` here, or `sambowyer/bayes_evals`. Never
trust a framework's pre-baked "error bar" without knowing which of the above it
implements.

## Citations

- arXiv:2503.01747 — Bowyer et al., "Don't Use the CLT in LLM Evals With Fewer
  Than a Few Hundred Datapoints" (ICML 2025 Spotlight). Wilson/Bayesian for
  small N.
- arXiv:2411.00640 — Miller / Anthropic, "Adding Error Bars to Evals". SEM,
  clustered SE, paired differences, power (n ≈ 969 for 3pp).
- arXiv:2509.24086 — "Do Repetitions Matter?". ≥2 runs remove ~83% of
  rank-inversions.
- https://github.com/sambowyer/bayes_evals — Beta-Binomial credible intervals.
- https://inspect.aisi.org.uk/metrics.html — Inspect AI stderr facilities.
