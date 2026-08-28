"""
FAERS & EudraVigilance Pharmacovigilance Signal Detection Platform
Interactive Streamlit Dashboard
"""

import os
import sys
import numpy as np
import pandas as pd
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.faers.analytics import (
    calculate_frequentist_metrics,
    calculate_bcpnn_ic,
    calculate_bayesian_prr,
    calculate_bayesian_ror,
    evaluate_signal_strength,
    run_full_disproportionality_analysis,
    calculate_2x2_counts
)
from src.faers.visualizations import (
    plot_bayesian_posterior,
    plot_forest_summary,
    plot_contingency_matrix,
    plot_volcano_quadrant
)
from src.faers.reporting import export_excel_report
from src.faers.loader import load_faers_files
from src.faers.deduplication import vigimatch_deduplicate_drugs

# Streamlit Page Config
st.set_page_config(
    page_title="FAERS Pharmacovigilance Signal Detection",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Benchmark clinical case studies for instant, zero-latency exploration
BENCHMARK_CASE_STUDIES = {
    "Capivasertib (Truqap) & Stomatitis (AstraZeneca)": {
        "drug": "Capivasertib (Truqap)",
        "event": "Stomatitis / Oral Mucositis",
        "A": 24, "B": 956, "C": 5120, "D": 321800,
        "background": "AstraZeneca's AKT inhibitor Truqap approved for HR+/HER2- breast cancer. Safety surveillance detected elevated oral mucosal inflammation signals."
    },
    "Semaglutide (Ozempic/Wegovy) & Gastroparesis (Novo Nordisk)": {
        "drug": "Semaglutide (Ozempic/Wegovy)",
        "event": "Gastroparesis / Delayed Gastric Emptying",
        "A": 412, "B": 18450, "C": 1250, "D": 450000,
        "background": "GLP-1 receptor agonist surveillance investigating gastrointestinal motility reduction and post-marketing stomach paralysis reports."
    },
    "Pembrolizumab (Keytruda) & Immune Colitis (Merck)": {
        "drug": "Pembrolizumab (Keytruda)",
        "event": "Immune-Mediated Colitis",
        "A": 185, "B": 12400, "C": 1940, "D": 410000,
        "background": "PD-1 checkpoint inhibitor oncology surveillance assessing immune-related adverse events (irAEs) requiring corticosteroid intervention."
    },
    "Palbociclib (Ibrance) & Neutropenia (Pfizer)": {
        "drug": "Palbociclib (Ibrance)",
        "event": "Neutropenia / Bone Marrow Suppression",
        "A": 650, "B": 14200, "C": 4800, "D": 380000,
        "background": "CDK4/6 inhibitor post-marketing safety data confirming predictable hematologic toxicities requiring regular CBC lab monitoring."
    }
}

# Sidebar Controls
st.sidebar.title("💊 Safety Surveillance")
st.sidebar.markdown("**Pharmacovigilance Decision Analytics**")

mode = st.sidebar.radio(
    "Select Operating Mode:",
    ["📊 Benchmark Case Studies (Instant Demo)", "⚙️ Custom 2x2 Matrix Input", "📂 Live Local FAERS Data Query"]
)

if mode == "📊 Benchmark Case Studies (Instant Demo)":
    case_key = st.sidebar.selectbox("Choose Clinical Case Study:", list(BENCHMARK_CASE_STUDIES.keys()))
    case_info = BENCHMARK_CASE_STUDIES[case_key]
    drug_name = case_info["drug"]
    event_name = case_info["event"]
    A = case_info["A"]
    B = case_info["B"]
    C = case_info["C"]
    D = case_info["D"]
    clinical_note = case_info["background"]

elif mode == "⚙️ Custom 2x2 Matrix Input":
    st.sidebar.markdown("### 2x2 Contingency Counts")
    drug_name = st.sidebar.text_input("Target Drug Name:", value="Novel Oncology Drug")
    event_name = st.sidebar.text_input("Target Adverse Event:", value="Hepatotoxicity")
    A = st.sidebar.number_input("Cell A (Drug + Event):", min_value=0, value=35, step=1)
    B = st.sidebar.number_input("Cell B (Drug + Other Events):", min_value=1, value=1200, step=50)
    C = st.sidebar.number_input("Cell C (Other Drugs + Event):", min_value=1, value=4500, step=100)
    D = st.sidebar.number_input("Cell D (General Background):", min_value=1, value=350000, step=1000)
    clinical_note = "Custom parameter evaluation for ad-hoc safety review."

else:  # Live Local FAERS Data Query
    st.sidebar.markdown("### Query Local FAERS Dataset")
    drug_input = st.sidebar.text_input("Drug Synonyms (comma separated):", value="CAPIVASERTIB, TRUQAP")
    event_input = st.sidebar.text_input("MedDRA Terms (comma separated):", value="STOMATITIS")
    data_folder = st.sidebar.text_input("FAERS Data Directory:", value="./data-source")

    drug_synonyms = [s.strip().upper() for s in drug_input.split(",") if s.strip()]
    event_synonyms = [s.strip().upper() for s in event_input.split(",") if s.strip()]
    drug_name = ", ".join(drug_synonyms)
    event_name = ", ".join(event_synonyms)
    clinical_note = f"Real-time pipeline scan on FAERS data directory: `{data_folder}`."

    if st.sidebar.button("🚀 Run Live Extraction"):
        with st.spinner("Executing ETL, VigiMatch deduplication, and 2x2 matrix generation..."):
            df_drug, _ = load_faers_files(data_folder, "DRUG*.txt")
            df_reac, _ = load_faers_files(data_folder, "REAC*.txt")
            if df_drug.empty or df_reac.empty:
                st.error("Could not find DRUG or REAC files in data-source. Falling back to Capivasertib benchmark.")
                A, B, C, D = 24, 956, 5120, 321800
            else:
                df_drug_ps, _ = vigimatch_deduplicate_drugs(df_drug, drug_synonyms)
                all_ids = set(df_drug['primaryid'].dropna().unique())
                drug_ids = set(df_drug_ps[df_drug_ps['drugname_norm'].isin(drug_synonyms)]['primaryid'].unique())
                reac_matches = df_reac[df_reac['pt'].fillna('').str.upper().str.contains('|'.join(event_synonyms))]['primaryid'].unique()
                event_ids = set(reac_matches)
                A, B, C, D = calculate_2x2_counts(all_ids, drug_ids, event_ids)
    else:
        # Default starting values until button clicked
        A, B, C, D = 24, 956, 5120, 321800

# Monte Carlo Settings in Sidebar
with st.sidebar.expander("🔬 Bayesian Engine Parameters", expanded=False):
    n_samples = st.slider("Monte Carlo Simulations:", min_value=5000, max_value=50000, value=20000, step=5000)
    prior_a = st.number_input("Beta Prior Alpha (α):", min_value=0.1, value=1.0, step=0.5)
    prior_b = st.number_input("Beta Prior Beta (β):", min_value=0.1, value=1.0, step=0.5)

# Execute Statistical & Bayesian Pipeline
analysis = run_full_disproportionality_analysis(A, B, C, D, drug_label=drug_name, event_label=event_name)
freq = analysis["frequentist"]
bcpnn = analysis["bcpnn_ic"]
bayes_prr = analysis["bayes_prr"]
bayes_ror = analysis["bayes_ror"]
triage = analysis["triage"]

# Header
st.title("💊 Post-Marketing Pharmacovigilance Signal Detection")
st.markdown(
    "**End-to-End Decision Analytics System for Regulatory Surveillance (FDA FAERS & EMA EudraVigilance)**"
)

# Triage Alert Banner
alert_tier = triage["tier"]
if "HIGH" in alert_tier:
    st.error(f"🚨 **SIGNAL TRIAGE: {alert_tier}**\n\n**Action:** {triage['action']}")
elif "MODERATE" in alert_tier:
    st.warning(f"⚠️ **SIGNAL TRIAGE: {alert_tier}**\n\n**Action:** {triage['action']}")
elif "LOW" in alert_tier:
    st.info(f"ℹ️ **SIGNAL TRIAGE: {alert_tier}**\n\n**Action:** {triage['action']}")
else:
    st.success(f"✅ **SIGNAL TRIAGE: {alert_tier}**\n\n**Action:** {triage['action']}")

# Top KPI Metric Cards
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Co-occurrence (A)", f"{A:,}", help="Cases reporting both target drug and adverse event")
with col2:
    st.metric("PRR (95% CI)", f"{freq['prr']:.2f}", f"[{freq['prr_ci_low']:.2f} - {freq['prr_ci_high']:.2f}]")
with col3:
    st.metric("ROR (Odds Ratio)", f"{freq['ror']:.2f}", f"[{freq['ror_ci_low']:.2f} - {freq['ror_ci_high']:.2f}]")
with col4:
    st.metric("BCPNN IC (log₂)", f"{bcpnn['ic']:.2f}", f"IC₀₂₅: {bcpnn['ic_025']:.2f}")
with col5:
    st.metric("Bayesian P(PRR > 1)", f"{bayes_prr['prob_greater_1']*100:.1f}%", help="Posterior probability that true risk ratio exceeds 1.0")

# Main Analysis Tabs
tab_summary, tab_charts, tab_matrix, tab_methods, tab_export = st.tabs([
    "📋 Executive Summary & Case Brief",
    "📈 Statistical & Bayesian Charts",
    "🗂️ 2x2 Matrix & Data Integrity",
    "📐 Methodology & Math",
    "📥 Export Center"
])

with tab_summary:
    st.subheader(f"Clinical Case Overview: {drug_name}")
    st.markdown(f"**Target Adverse Reaction:** `{event_name}`")
    st.markdown(f"**Background Context:** {clinical_note}")

    st.markdown("---")
    st.subheader("Decision Analytics & Regulatory Triage")
    
    col_sum1, col_sum2 = st.columns(2)
    with col_sum1:
        st.markdown("#### 🔍 Disproportionality Signal Assessment")
        st.markdown(f"""
        - **Proportional Reporting Ratio (PRR):** `{freq['prr']:.2f}` (FDA Threshold: $\ge 2.0$)
        - **Yates' Corrected Chi-Square:** `{freq['chi2_yates']:.2f}` (Statistical Significance: $p = {freq['chi2_yates_pvalue']:.4g}$)
        - **Fisher's Exact Hypergeometric Test:** $p = `{freq['fisher_pvalue']:.4g}`$
        - **WHO BCPNN Information Component:** `IC = {bcpnn['ic']:.2f}` (Lower 95% Bound $\\text{{IC}}_{{0.25}} = {bcpnn['ic_025']:.2f}$)
        """)

    with col_sum2:
        st.markdown("#### ⚖️ Regulatory & Commercial Impact")
        st.markdown(f"""
        - **Safety Action:** {triage['action']}
        - **FDA 21 CFR 314.80 Compliance:** Expedited review for potential 15-day alert triage.
        - **Risk-Benefit Profile:** Monitor incidence rates vs therapeutic efficacy endpoints.
        - **Litigation & Labeling Risk:** Proactive label modification mitigates regulatory warning letter risk.
        """)

with tab_charts:
    st.subheader("Statistical & Bayesian Visualizations")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_bayes = plot_bayesian_posterior(bayes_prr, drug_name=drug_name, event_name=event_name)
        st.plotly_chart(fig_bayes, use_container_width=True)

    with chart_col2:
        fig_forest = plot_forest_summary(freq, bayes_prr, bcpnn)
        st.plotly_chart(fig_forest, use_container_width=True)

    st.markdown("---")
    volcano_list = [
        {"drug": drug_name, "event": event_name, "frequentist": freq, "triage": triage},
        {"drug": "Capivasertib", "event": "Stomatitis", "frequentist": calculate_frequentist_metrics(24, 956, 5120, 321800), "triage": {"tier": "HIGH", "color": "red"}},
        {"drug": "Semaglutide", "event": "Gastroparesis", "frequentist": calculate_frequentist_metrics(412, 18450, 1250, 450000), "triage": {"tier": "HIGH", "color": "red"}},
        {"drug": "Control Comparator", "event": "Headache", "frequentist": calculate_frequentist_metrics(5, 5000, 10000, 300000), "triage": {"tier": "NONE", "color": "green"}}
    ]
    fig_volcano = plot_volcano_quadrant(volcano_list)
    st.plotly_chart(fig_volcano, use_container_width=True)

with tab_matrix:
    st.subheader("2x2 Contingency Matrix Breakdown")
    fig_matrix = plot_contingency_matrix(A, B, C, D)
    st.plotly_chart(fig_matrix, use_container_width=True)

    st.markdown("#### Detailed Cell Counts")
    matrix_df = pd.DataFrame([
        {"Cell": "A (Drug + Event)", "Description": "Target Drug Co-occurring with Target Adverse Event", "Count": f"{A:,}"},
        {"Cell": "B (Drug + Other Events)", "Description": "Target Drug with all other adverse events", "Count": f"{B:,}"},
        {"Cell": "C (Other Drugs + Event)", "Description": "All other drugs associated with target adverse event", "Count": f"{C:,}"},
        {"Cell": "D (General Background)", "Description": "General database background (Neither target drug nor event)", "Count": f"{D:,}"},
        {"Cell": "Total (N)", "Description": "Total safety surveillance cohort size", "Count": f"{A+B+C+D:,}"}
    ])
    st.table(matrix_df)

with tab_methods:
    st.subheader("Statistical & Mathematical Methodology")
    st.markdown(r"""
    ### 1. Frequentist Metrics
    - **Reporting Odds Ratio (ROR):**
      $$\text{ROR} = \frac{A / B}{C / D} = \frac{A \cdot D}{B \cdot C}, \quad \text{SE}(\ln \text{ROR}) = \sqrt{\frac{1}{A} + \frac{1}{B} + \frac{1}{C} + \frac{1}{D}}$$
    - **Proportional Reporting Ratio (PRR):**
      $$\text{PRR} = \frac{A / (A+B)}{(A+C) / N}$$
    - **Haldane's Odds Ratio (+0.5 Continuity Correction):**
      $$\text{HOR} = \frac{(A + 0.5)(D + 0.5)}{(B + 0.5)(C + 0.5)}$$

    ### 2. Bayesian Shrinkage & Monte Carlo Simulation
    - **WHO UMC BCPNN Information Component (IC):**
      $$\text{IC} = \log_2 \left( \frac{A_{\text{obs}}}{E} \right), \quad E = \frac{(A+B)(A+C)}{N}$$
    - **Beta-Binomial Monte Carlo:**
      $$s_1 \sim \text{Beta}(1 + A, 1 + B), \quad s_2 \sim \text{Beta}(1 + C, 1 + D), \quad \text{PRR}_{\text{sim}} = \frac{s_1}{s_2}$$
    """)

with tab_export:
    st.subheader("Download Regulatory & Consulting Deliverables")
    report_filename = f"FAERS_Report_{drug_name.replace(' ', '_').replace('/', '_')}.xlsx"
    export_excel_report(analysis, output_path=report_filename)

    with open(report_filename, "rb") as f:
        st.download_button(
            label="📥 Download Multi-Sheet Excel Consulting Report",
            data=f.read(),
            file_name=report_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    st.success(f"Report ready for export: `{report_filename}`")
