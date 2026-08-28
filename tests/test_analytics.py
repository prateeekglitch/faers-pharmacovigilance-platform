"""
Unit Tests for Statistical and Bayesian Analytics Engine
"""

import pytest
import numpy as np
from src.faers.analytics import (
    calculate_2x2_counts,
    calculate_frequentist_metrics,
    calculate_bcpnn_ic,
    calculate_bayesian_prr,
    calculate_bayesian_ror,
    evaluate_signal_strength,
    run_full_disproportionality_analysis
)


def test_calculate_2x2_counts():
    all_cases = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}
    drug_cases = {"1", "2", "3", "4"}
    event_cases = {"3", "4", "5", "6"}

    A, B, C, D = calculate_2x2_counts(all_cases, drug_cases, event_cases)
    assert A == 2  # {3, 4}
    assert B == 2  # {1, 2}
    assert C == 2  # {5, 6}
    assert D == 4  # {7, 8, 9, 10}
    assert A + B + C + D == 10


def test_frequentist_metrics_standard():
    # Benchmark 2x2 table: A=24, B=1000, C=5000, D=500000
    A, B, C, D = 24, 1000, 5000, 500000
    metrics = calculate_frequentist_metrics(A, B, C, D)

    # ROR = (24 / 1000) / (5000 / 500000) = 0.024 / 0.01 = 2.4
    assert np.isclose(metrics["ror"], 2.4, atol=0.01)
    assert metrics["ror_ci_low"] < metrics["ror"] < metrics["ror_ci_high"]
    assert metrics["prr"] > 1.0
    assert metrics["fisher_pvalue"] < 0.05
    assert metrics["chi2_yates"] > 3.84


def test_frequentist_metrics_zero_count_edge_case():
    # When A = 0, standard ROR is undefined but Haldane OR handles it cleanly
    A, B, C, D = 0, 100, 200, 50000
    metrics = calculate_frequentist_metrics(A, B, C, D)

    assert np.isnan(metrics["ror"])
    assert metrics["haldane_or"] > 0
    assert not np.isnan(metrics["haldane_ci_low"])
    assert not np.isnan(metrics["haldane_ci_high"])


def test_bcpnn_information_component():
    A, B, C, D = 24, 1000, 5000, 500000
    res = calculate_bcpnn_ic(A, B, C, D)

    assert "ic" in res
    assert "ic_025" in res
    assert "ic_975" in res
    assert res["ic_025"] < res["ic"] < res["ic_975"]
    assert res["expected_count"] > 0


def test_bayesian_prr_monte_carlo():
    A, B, C, D = 24, 1000, 5000, 500000
    res = calculate_bayesian_prr(A, B, C, D, n_samples=10000, seed=42)

    assert 0.0 <= res["prob_greater_1"] <= 1.0
    assert res["ci_low"] < res["median"] < res["ci_high"]
    assert len(res["samples"]) == 10000


def test_signal_triage_evaluation():
    # Strong signal: high PRR, high chi2, significant p-value
    strong_freq = {
        "A": 30, "prr": 3.5, "prr_ci_low": 2.1,
        "chi2_yates": 15.2, "fisher_pvalue": 0.0001
    }
    strong_bcpnn = {"ic_025": 1.2}
    triage_high = evaluate_signal_strength(strong_freq, strong_bcpnn)
    assert "HIGH" in triage_high["tier"]

    # Null signal
    null_freq = {
        "A": 2, "prr": 0.8, "prr_ci_low": 0.3,
        "chi2_yates": 0.1, "fisher_pvalue": 0.75
    }
    null_bcpnn = {"ic_025": -1.5}
    triage_null = evaluate_signal_strength(null_freq, null_bcpnn)
    assert "NONE" in triage_null["tier"]
