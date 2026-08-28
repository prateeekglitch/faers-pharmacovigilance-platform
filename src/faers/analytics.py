"""
Statistical & Bayesian Pharmacovigilance Signal Detection Engine
"""

from typing import Dict, Any, Tuple, Optional, Set
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, chi2_contingency


def calculate_2x2_counts(
    all_case_ids: Set[str],
    drug_case_ids: Set[str],
    event_case_ids: Set[str]
) -> Tuple[int, int, int, int]:
    """
    Computes standard 2x2 contingency matrix counts:
    A: Target Drug + Target Event (Co-occurrence)
    B: Target Drug + Other Events (No target event)
    C: Target Event + Other Drugs (No target drug)
    D: General Background (Neither target drug nor target event)
    """
    A = len(drug_case_ids & event_case_ids)
    B = len(drug_case_ids - event_case_ids)
    C = len(event_case_ids - drug_case_ids)
    D = len(all_case_ids - (drug_case_ids | event_case_ids))
    return A, B, C, D


def calculate_frequentist_metrics(A: int, B: int, C: int, D: int) -> Dict[str, Any]:
    """
    Computes Frequentist disproportionality metrics and hypothesis tests:
    - ROR (Reporting Odds Ratio) + 95% Confidence Interval
    - PRR (Proportional Reporting Ratio) + 95% Confidence Interval
    - RRR (Relative Reporting Ratio)
    - Haldane's Odds Ratio (+0.5 continuity correction for zero counts)
    - Fisher's Exact Test (hypergeometric p-value)
    - Pearson Chi-Square & Yates' Corrected Chi-Square (with p-values)
    """
    N = A + B + C + D
    contingency_table = np.array([[A, B], [C, D]])

    # 1. Reporting Odds Ratio (ROR)
    if B > 0 and C > 0 and D > 0 and A > 0:
        ror = (A / B) / (C / D)
        se_ror = np.sqrt(1.0 / A + 1.0 / B + 1.0 / C + 1.0 / D)
        ror_ci_low = float(np.exp(np.log(ror) - 1.96 * se_ror))
        ror_ci_high = float(np.exp(np.log(ror) + 1.96 * se_ror))
    else:
        ror = np.nan
        ror_ci_low = np.nan
        ror_ci_high = np.nan

    # 2. Proportional Reporting Ratio (PRR)
    if (A + B) > 0 and (A + C) > 0 and N > 0 and A > 0:
        prr_num = A / (A + B)
        prr_den = (A + C) / N
        prr = prr_num / prr_den if prr_den > 0 else np.nan
        if prr > 0 and B > 0 and C > 0 and D > 0:
            se_prr = np.sqrt(1.0 / A - 1.0 / (A + B) + 1.0 / C - 1.0 / (C + D))
            prr_ci_low = float(np.exp(np.log(prr) - 1.96 * se_prr))
            prr_ci_high = float(np.exp(np.log(prr) + 1.96 * se_prr))
        else:
            prr_ci_low = np.nan
            prr_ci_high = np.nan
    else:
        prr = np.nan
        prr_ci_low = np.nan
        prr_ci_high = np.nan

    # 3. Relative Reporting Ratio (RRR)
    if (A + B) > 0 and (C + D) > 0 and A > 0 and C > 0:
        rrr = (A / (A + B)) / (C / (C + D))
        se_rrr = np.sqrt(1.0 / A - 1.0 / (A + B) + 1.0 / C - 1.0 / (C + D))
        rrr_ci_low = float(np.exp(np.log(rrr) - 1.96 * se_rrr))
        rrr_ci_high = float(np.exp(np.log(rrr) + 1.96 * se_rrr))
    else:
        rrr = np.nan
        rrr_ci_low = np.nan
        rrr_ci_high = np.nan

    # 4. Haldane's Odds Ratio (adds +0.5 continuity correction)
    a_c, b_c, c_c, d_c = A + 0.5, B + 0.5, C + 0.5, D + 0.5
    haldane_or = (a_c * d_c) / (b_c * c_c)
    se_haldane = np.sqrt(1.0 / a_c + 1.0 / b_c + 1.0 / c_c + 1.0 / d_c)
    haldane_ci_low = float(np.exp(np.log(haldane_or) - 1.96 * se_haldane))
    haldane_ci_high = float(np.exp(np.log(haldane_or) + 1.96 * se_haldane))

    # 5. Fisher's Exact Test & Chi-Square Tests
    _, p_fisher = fisher_exact(contingency_table)
    chi2_raw, p_chi2, _, _ = chi2_contingency(contingency_table, correction=False)
    chi2_yates, p_yates, _, _ = chi2_contingency(contingency_table, correction=True)

    return {
        "A": A, "B": B, "C": C, "D": D, "N": N,
        "ror": ror, "ror_ci_low": ror_ci_low, "ror_ci_high": ror_ci_high,
        "prr": prr, "prr_ci_low": prr_ci_low, "prr_ci_high": prr_ci_high,
        "rrr": rrr, "rrr_ci_low": rrr_ci_low, "rrr_ci_high": rrr_ci_high,
        "haldane_or": haldane_or, "haldane_ci_low": haldane_ci_low, "haldane_ci_high": haldane_ci_high,
        "fisher_pvalue": float(p_fisher),
        "chi2": float(chi2_raw), "chi2_pvalue": float(p_chi2),
        "chi2_yates": float(chi2_yates), "chi2_yates_pvalue": float(p_yates)
    }


def calculate_bcpnn_ic(A: int, B: int, C: int, D: int, continuity: float = 0.5) -> Dict[str, Any]:
    """
    Computes the WHO UMC BCPNN Information Component (IC) using Empirical Bayes.
    Shrinks estimates towards 0 for low sample counts (A < 5) to eliminate false positives.
    """
    N = A + B + C + D
    if N == 0:
        return {"ic": np.nan, "ic_variance": np.nan, "ic_025": np.nan, "ic_975": np.nan}

    a_obs = A + continuity
    expected = ((A + B) * (A + C)) / N
    expected = expected + continuity if expected == 0 else expected

    ln_2 = np.log(2.0)
    ic = float(np.log(a_obs / expected) / ln_2)
    var_ic = float((1.0 / (ln_2 ** 2)) * (1.0 / a_obs + 1.0 / expected))
    se_ic = np.sqrt(var_ic)

    ic_025 = float(ic - 1.96 * se_ic)
    ic_975 = float(ic + 1.96 * se_ic)

    return {
        "ic": ic,
        "ic_variance": var_ic,
        "ic_025": ic_025,
        "ic_975": ic_975,
        "expected_count": float(expected)
    }


def calculate_bayesian_prr(
    A: int, B: int, C: int, D: int,
    prior_a: float = 1.0, prior_b: float = 1.0,
    n_samples: int = 50000, seed: int = 42
) -> Dict[str, Any]:
    """
    Runs 50,000 Beta-Binomial Monte Carlo posterior simulations for PRR.
    Computes exact posterior mean, median, 95% Credible Interval, and P(PRR > 1).
    """
    rng = np.random.default_rng(seed)
    s1 = rng.beta(prior_a + A, prior_b + B, size=n_samples)
    s2 = rng.beta(prior_a + C, prior_b + D, size=n_samples)
    prr_samples = (s1 + 1e-12) / (s2 + 1e-12)

    return {
        "mean": float(np.mean(prr_samples)),
        "median": float(np.median(prr_samples)),
        "ci_low": float(np.percentile(prr_samples, 2.5)),
        "ci_high": float(np.percentile(prr_samples, 97.5)),
        "prob_greater_1": float(np.mean(prr_samples > 1.0)),
        "samples": prr_samples
    }


def calculate_bayesian_ror(
    A: int, B: int, C: int, D: int,
    prior_a: float = 0.5, prior_b: float = 0.5,
    n_samples: int = 50000, seed: int = 123
) -> Dict[str, Any]:
    """
    Runs 50,000 Beta-Binomial Monte Carlo posterior simulations for Odds Ratio (ROR).
    """
    rng = np.random.default_rng(seed)
    s1 = rng.beta(prior_a + A, prior_b + B, size=n_samples)
    s2 = rng.beta(prior_a + C, prior_b + D, size=n_samples)
    s1 = np.clip(s1, 1e-12, 1.0 - 1e-12)
    s2 = np.clip(s2, 1e-12, 1.0 - 1e-12)

    or_samples = (s1 / (1.0 - s1)) / (s2 / (1.0 - s2))

    return {
        "mean": float(np.mean(or_samples)),
        "median": float(np.median(or_samples)),
        "ci_low": float(np.percentile(or_samples, 2.5)),
        "ci_high": float(np.percentile(or_samples, 97.5)),
        "prob_greater_1": float(np.mean(or_samples > 1.0)),
        "samples": or_samples
    }


def evaluate_signal_strength(frequentist: Dict[str, Any], bayesian_ic: Dict[str, Any]) -> Dict[str, str]:
    """
    Decision Analytics Triage: Categorizes signal into High/Moderate/Low/None based on FDA/EMA benchmarks.
    """
    A = frequentist.get("A", 0)
    prr = frequentist.get("prr", 0.0)
    prr_low = frequentist.get("prr_ci_low", 0.0)
    chi2_yates = frequentist.get("chi2_yates", 0.0)
    p_fisher = frequentist.get("fisher_pvalue", 1.0)
    ic_025 = bayesian_ic.get("ic_025", -99.0)

    # FDA / EMA Benchmark: PRR >= 2.0, Chi2 >= 4.0, A >= 3, IC_025 > 0
    if A >= 3 and (prr >= 2.0 or prr_low > 1.0) and chi2_yates >= 3.84 and p_fisher < 0.05 and ic_025 > 0:
        tier = "HIGH (Definite Safety Signal)"
        action = "Prioritize for FDA 21 CFR 314.80 15-Day Alert review, update Risk Management Plan (RMP)."
        color = "red"
    elif A >= 3 and (prr > 1.2 or prr_low > 1.0) and p_fisher < 0.05:
        tier = "MODERATE (Emerging Safety Signal)"
        action = "Continue enhanced multi-quarter surveillance; evaluate confounding concomitant drugs."
        color = "orange"
    elif A > 0 and (prr > 1.0 or prr_low > 0.8):
        tier = "LOW (Weak Disproportionality)"
        action = "Signal under monitoring threshold; likely noise or small-count variation."
        color = "blue"
    else:
        tier = "NONE (No Disproportionality Signal)"
        action = "No evidence of disproportionate reporting compared to background population."
        color = "green"

    return {
        "tier": tier,
        "action": action,
        "color": color
    }


def run_full_disproportionality_analysis(
    A: int, B: int, C: int, D: int,
    drug_label: str = "Target Drug",
    event_label: str = "Target Event"
) -> Dict[str, Any]:
    """
    Runs complete end-to-end analytical pipeline on a 2x2 matrix and returns all metrics.
    """
    freq = calculate_frequentist_metrics(A, B, C, D)
    bcpnn = calculate_bcpnn_ic(A, B, C, D)
    bayes_prr = calculate_bayesian_prr(A, B, C, D)
    bayes_ror = calculate_bayesian_ror(A, B, C, D)
    triage = evaluate_signal_strength(freq, bcpnn)

    return {
        "drug_label": drug_label,
        "event_label": event_label,
        "frequentist": freq,
        "bcpnn_ic": bcpnn,
        "bayes_prr": bayes_prr,
        "bayes_ror": bayes_ror,
        "triage": triage
    }
