"""
Consulting & Regulatory Reporting Module
"""

from typing import Dict, Any, Optional
import pandas as pd


def export_excel_report(
    analysis: Dict[str, Any],
    output_path: str = "FAERS_Consulting_Report.xlsx",
    breakdown_df: Optional[pd.DataFrame] = None
) -> str:
    """
    Exports a comprehensive multi-sheet Excel consulting report for regulatory review.
    """
    freq = analysis.get("frequentist", {})
    bcpnn = analysis.get("bcpnn_ic", {})
    bayes_prr = analysis.get("bayes_prr", {})
    bayes_ror = analysis.get("bayes_ror", {})
    triage = analysis.get("triage", {})

    # Sheet 1: Executive Summary
    exec_summary_data = [
        {"Section": "Drug Exposure", "Detail": analysis.get("drug_label", "")},
        {"Section": "Adverse Event", "Detail": analysis.get("event_label", "")},
        {"Section": "Signal Triage Tier", "Detail": triage.get("tier", "")},
        {"Section": "Recommended Action", "Detail": triage.get("action", "")},
        {"Section": "Co-occurrence Cases (Cell A)", "Detail": f"{freq.get('A', 0):,}"},
        {"Section": "Total Population (N)", "Detail": f"{freq.get('N', 0):,}"},
        {"Section": "Proportional Reporting Ratio (PRR)", "Detail": f"{freq.get('prr', 0):.2f} (95% CI: [{freq.get('prr_ci_low', 0):.2f}, {freq.get('prr_ci_high', 0):.2f}])"},
        {"Section": "Reporting Odds Ratio (ROR)", "Detail": f"{freq.get('ror', 0):.2f} (95% CI: [{freq.get('ror_ci_low', 0):.2f}, {freq.get('ror_ci_high', 0):.2f}])"},
        {"Section": "Fisher's Exact p-value", "Detail": f"{freq.get('fisher_pvalue', 1.0):.4g}"},
        {"Section": "WHO BCPNN Information Component (IC)", "Detail": f"{bcpnn.get('ic', 0):.2f} (95% CrI: [{bcpnn.get('ic_025', 0):.2f}, {bcpnn.get('ic_975', 0):.2f}])"},
        {"Section": "Bayesian Monte Carlo P(PRR > 1.0)", "Detail": f"{bayes_prr.get('prob_greater_1', 0)*100:.1f}%"}
    ]
    df_exec = pd.DataFrame(exec_summary_data)

    # Sheet 2: Detailed 2x2 Matrix
    matrix_data = [
        {"Metric": "Cell A (Target Drug + Target Event)", "Count": freq.get("A", 0)},
        {"Metric": "Cell B (Target Drug + Other Events)", "Count": freq.get("B", 0)},
        {"Metric": "Cell C (Other Drugs + Target Event)", "Count": freq.get("C", 0)},
        {"Metric": "Cell D (General Background)", "Count": freq.get("D", 0)},
        {"Metric": "Total Safety Records Evaluated (N)", "Count": freq.get("N", 0)}
    ]
    df_matrix = pd.DataFrame(matrix_data)

    # Sheet 3: Statistical Metrics
    stats_data = [
        {"Framework": "Frequentist", "Metric": "ROR", "Value": freq.get("ror", 0), "Lower 95% CI": freq.get("ror_ci_low", 0), "Upper 95% CI": freq.get("ror_ci_high", 0)},
        {"Framework": "Frequentist", "Metric": "PRR", "Value": freq.get("prr", 0), "Lower 95% CI": freq.get("prr_ci_low", 0), "Upper 95% CI": freq.get("prr_ci_high", 0)},
        {"Framework": "Frequentist", "Metric": "RRR", "Value": freq.get("rrr", 0), "Lower 95% CI": freq.get("rrr_ci_low", 0), "Upper 95% CI": freq.get("rrr_ci_high", 0)},
        {"Framework": "Frequentist", "Metric": "Haldane OR (+0.5)", "Value": freq.get("haldane_or", 0), "Lower 95% CI": freq.get("haldane_ci_low", 0), "Upper 95% CI": freq.get("haldane_ci_high", 0)},
        {"Framework": "Bayesian", "Metric": "BCPNN IC (log2)", "Value": bcpnn.get("ic", 0), "Lower 95% CI": bcpnn.get("ic_025", 0), "Upper 95% CI": bcpnn.get("ic_975", 0)},
        {"Framework": "Bayesian", "Metric": "Beta Monte Carlo PRR (Median)", "Value": bayes_prr.get("median", 0), "Lower 95% CI": bayes_prr.get("ci_low", 0), "Upper 95% CI": bayes_prr.get("ci_high", 0)},
        {"Framework": "Bayesian", "Metric": "Beta Monte Carlo ROR (Median)", "Value": bayes_ror.get("median", 0), "Lower 95% CI": bayes_ror.get("ci_low", 0), "Upper 95% CI": bayes_ror.get("ci_high", 0)}
    ]
    df_stats = pd.DataFrame(stats_data)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_exec.to_excel(writer, sheet_name="Executive_Summary", index=False)
        df_matrix.to_excel(writer, sheet_name="2x2_Contingency_Matrix", index=False)
        df_stats.to_excel(writer, sheet_name="Statistical_Metrics", index=False)
        if breakdown_df is not None and not breakdown_df.empty:
            breakdown_df.to_excel(writer, sheet_name="Event_Synonym_Breakdown", index=False)

    return output_path
