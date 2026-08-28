"""
FAERS Pharmacovigilance Disproportionality & Bayesian Analysis Pipeline
CLI Execution Script
"""

import os
import sys
import argparse
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.faers.loader import load_faers_files
from src.faers.deduplication import vigimatch_deduplicate_drugs
from src.faers.analytics import (
    calculate_2x2_counts,
    calculate_frequentist_metrics,
    calculate_bcpnn_ic,
    calculate_bayesian_prr,
    calculate_bayesian_ror,
    evaluate_signal_strength,
    run_full_disproportionality_analysis
)
from src.faers.reporting import export_excel_report


def run_pipeline(
    drug_synonyms,
    event_synonyms,
    data_dir="./data-source",
    output_file="FAERS_Analysis_Results.xlsx",
    start_year_q=(2023, 4),
    end_year_q=(2025, 1),
    run_bayesian=True
):
    print("=" * 60)
    print("FAERS Pharmacovigilance Disproportionality Pipeline")
    print(f"Drugs: {drug_synonyms}")
    print(f"Events: {event_synonyms}")
    print(f"Data Dir: {data_dir}")
    print("=" * 60)

    df_drug, skipped_drug = load_faers_files(data_dir, "DRUG*.txt", start_year_q, end_year_q)
    df_reac, skipped_reac = load_faers_files(data_dir, "REAC*.txt", start_year_q, end_year_q)

    if df_drug.empty or df_reac.empty:
        print("Error: Could not load DRUG or REACTION records. Please verify data-source folder.")
        return

    print(f"Total DRUG records loaded: {len(df_drug):,}")
    print(f"Total REACTION records loaded: {len(df_reac):,}")

    # Standardize column names
    df_drug.columns = [c.lower() for c in df_drug.columns]
    df_reac.columns = [c.lower() for c in df_reac.columns]

    all_case_ids = set(df_drug["primaryid"].dropna().unique())

    # WHO VigiMatch Deduplication
    print("\nFiltering Primary Suspect (PS) drugs and applying VigiMatch deduplication...")
    df_drug_ps, dedup_stats = vigimatch_deduplicate_drugs(df_drug, target_synonyms=drug_synonyms)
    print(f"VigiMatch DRUG duplicates removed: {dedup_stats['duplicates_removed']:,} ({dedup_stats['initial_count']:,} -> {dedup_stats['final_count']:,})")

    # Match primary IDs for target drug
    target_drug_ids = set()
    for name in drug_synonyms:
        name_clean = name.strip().upper()
        matches = df_drug_ps[df_drug_ps["drugname_norm"] == name_clean]["primaryid"].unique()
        target_drug_ids.update(matches)

    # Match primary IDs for target event
    target_event_ids = set()
    df_reac["pt"] = df_reac["pt"].fillna("").astype(str).str.upper()
    for event_term in event_synonyms:
        event_clean = event_term.strip().upper()
        matches = df_reac[df_reac["pt"].str.contains(event_clean, regex=False)]["primaryid"].unique()
        target_event_ids.update(matches)

    # Event synonym breakdown table
    breakdown_list = []
    for event_term in event_synonyms:
        event_clean = event_term.strip().upper()
        isr_term = set(df_reac[df_reac["pt"].str.contains(event_clean, regex=False)]["primaryid"].unique())
        A_t, B_t, C_t, D_t = calculate_2x2_counts(all_case_ids, target_drug_ids, isr_term)
        breakdown_list.append({
            "Event Synonym": event_term,
            "A (Drug+Event)": A_t,
            "B (Drug+No Event)": B_t,
            "C (Event+No Drug)": C_t,
            "D (Neither)": D_t
        })
    breakdown_df = pd.DataFrame(breakdown_list)

    # 2x2 Matrix Counts
    A, B, C, D = calculate_2x2_counts(all_case_ids, target_drug_ids, target_event_ids)
    print(f"\n2x2 Contingency Matrix:\n A (Drug+Event): {A:,}\n B (Drug+No Event): {B:,}\n C (Event+No Drug): {C:,}\n D (Neither): {D:,}")

    # Run Analysis
    drug_label = ", ".join(drug_synonyms)
    event_label = ", ".join(event_synonyms)
    analysis = run_full_disproportionality_analysis(A, B, C, D, drug_label=drug_label, event_label=event_label)
    freq = analysis["frequentist"]
    bcpnn = analysis["bcpnn_ic"]
    bayes_prr = analysis["bayes_prr"]
    triage = analysis["triage"]

    print("\n--- Key Metrics ---")
    print(f"PRR = {freq['prr']:.2f} [95% CI: {freq['prr_ci_low']:.2f}, {freq['prr_ci_high']:.2f}]")
    print(f"ROR = {freq['ror']:.2f} [95% CI: {freq['ror_ci_low']:.2f}, {freq['ror_ci_high']:.2f}]")
    print(f"Fisher's Exact p-value = {freq['fisher_pvalue']:.4g}")
    print(f"Yates' Chi-Square = {freq['chi2_yates']:.2f} (p = {freq['chi2_yates_pvalue']:.4g})")
    print(f"BCPNN Information Component (IC) = {bcpnn['ic']:.2f} [95% CrI: {bcpnn['ic_025']:.2f}, {bcpnn['ic_975']:.2f}]")
    print(f"Bayesian Monte Carlo Median PRR = {bayes_prr['median']:.2f} (P(PRR > 1) = {bayes_prr['prob_greater_1']*100:.1f}%)")
    print(f"Signal Triage Tier: {triage['tier']}")

    # Export Excel
    export_excel_report(analysis, output_path=output_file, breakdown_df=breakdown_df)
    print(f"\n[SUCCESS] Exported full consulting report to '{output_file}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FAERS Pharmacovigilance Disproportionality Pipeline")
    parser.add_argument("--drugs", nargs="+", default=["capivasertib", "TRUQAP"], help="List of drug synonyms")
    parser.add_argument("--events", nargs="+", default=["Stomatitis"], help="List of event synonyms")
    parser.add_argument("--data-dir", default="./data-source", help="Path to FAERS data folder")
    parser.add_argument("--output", default="FAERS_Analysis_Results.xlsx", help="Output Excel filename")
    parser.add_argument("--bayes", action="store_true", default=True, help="Include Bayesian metrics")

    args = parser.parse_args()
    run_pipeline(args.drugs, args.events, data_dir=args.data_dir, output_file=args.output, run_bayesian=args.bayes)
