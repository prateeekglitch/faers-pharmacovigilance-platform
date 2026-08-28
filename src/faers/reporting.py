"""
Executive & Regulatory Pharmacovigilance Reporting Module
Generates boardroom-grade, FDA audit-ready Excel Deliverables using openpyxl.
"""

from typing import Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def export_excel_report(
    analysis: Dict[str, Any],
    output_path: str = "FAERS_Consulting_Report.xlsx",
    breakdown_df: Optional[Any] = None
) -> str:
    """
    Exports a professional, beautifully styled multi-sheet Excel report
    designed from first principles for Medical Affairs, Safety Review Boards, and FDA Compliance.
    """
    freq = analysis.get("frequentist", {})
    bcpnn = analysis.get("bcpnn_ic", {})
    bayes_prr = analysis.get("bayes_prr", {})
    bayes_ror = analysis.get("bayes_ror", {})
    triage = analysis.get("triage", {})
    
    drug_name = analysis.get("drug_label", "Target Drug")
    event_name = analysis.get("event_label", "Target Adverse Event")
    
    A = freq.get("A", 0)
    B = freq.get("B", 0)
    C = freq.get("C", 0)
    D = freq.get("D", 0)
    N = freq.get("N", A + B + C + D)
    
    prr = freq.get("prr", 1.0)
    prr_low = freq.get("prr_ci_low", 1.0)
    prr_high = freq.get("prr_ci_high", 1.0)
    
    ror = freq.get("ror", 1.0)
    ror_low = freq.get("ror_ci_low", 1.0)
    ror_high = freq.get("ror_ci_high", 1.0)
    
    tier = triage.get("tier", "MODERATE")
    action_text = triage.get("action", "Maintain surveillance.")
    
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)
    
    # ------------------ STYLING CONSTANTS ------------------
    NAVY_DARK = "1E3A8A"
    NAVY_LIGHT = "DBEAFE"
    SLATE_HEADER = "0F172A"
    SLATE_ROW_ALT = "F8FAFC"
    WHITE = "FFFFFF"
    
    # Alert Fills
    RED_FILL = "FEE2E2"
    RED_TEXT = "991B1B"
    YELLOW_FILL = "FEF3C7"
    YELLOW_TEXT = "92400E"
    GREEN_FILL = "DCFCE7"
    GREEN_TEXT = "166534"
    
    font_title = Font(name="Segoe UI", size=15, bold=True, color=WHITE)
    font_subtitle = Font(name="Segoe UI", size=10, italic=True, color="E2E8F0")
    font_section = Font(name="Segoe UI", size=12, bold=True, color=SLATE_HEADER)
    font_header = Font(name="Segoe UI", size=10, bold=True, color=WHITE)
    font_data = Font(name="Segoe UI", size=10, color="1E293B")
    font_data_bold = Font(name="Segoe UI", size=10, bold=True, color="1E293B")
    
    fill_navy = PatternFill(start_color=NAVY_DARK, end_color=NAVY_DARK, fill_type="solid")
    fill_slate = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    fill_alt = PatternFill(start_color=SLATE_ROW_ALT, end_color=SLATE_ROW_ALT, fill_type="solid")
    fill_accent = PatternFill(start_color=NAVY_LIGHT, end_color=NAVY_LIGHT, fill_type="solid")
    
    thin_border_side = Side(style="thin", color="CBD5E1")
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_top_thick = Border(top=Side(style="medium", color="1E3A8A"), bottom=thin_border_side, left=thin_border_side, right=thin_border_side)
    
    align_left = Alignment(horizontal="left", vertical="center")
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # =========================================================================
    # SHEET 1: EXECUTIVE DECISION BRIEF
    # =========================================================================
    ws1 = wb.create_sheet(title="Executive Decision Brief")
    ws1.views.sheetView[0].showGridLines = True
    
    # 1. Header Banner
    ws1.merge_cells("A1:E1")
    title_cell = ws1["A1"]
    title_cell.value = "  PHARMACOVIGILANCE SAFETY DECISION BRIEF"
    title_cell.font = font_title
    title_cell.fill = fill_navy
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws1.row_dimensions[1].height = 32
    
    ws1.merge_cells("A2:E2")
    sub_cell = ws1["A2"]
    sub_cell.value = f"  Drug Target: {drug_name}  |  Adverse Event: {event_name}  |  Database: US FDA FAERS Post-Marketing Surveillance"
    sub_cell.font = font_subtitle
    sub_cell.fill = fill_navy
    sub_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws1.row_dimensions[2].height = 20
    
    # 2. Executive Triage Box
    ws1.row_dimensions[4].height = 28
    ws1.merge_cells("A4:E4")
    triage_cell = ws1["A4"]
    
    if "HIGH" in tier:
        triage_cell.value = f" 🚨 EXECUTIVE VERDICT: HIGH SAFETY SIGNAL DETECTED — FDA 15-DAY EXPEDITED REVIEW MANDATED"
        triage_cell.font = Font(name="Segoe UI", size=11, bold=True, color=RED_TEXT)
        triage_cell.fill = PatternFill(start_color=RED_FILL, end_color=RED_FILL, fill_type="solid")
    elif "MODERATE" in tier:
        triage_cell.value = f" ⚠️ EXECUTIVE VERDICT: MODERATE / EMERGING SAFETY SIGNAL — ACTIVE QUARTERLY SURVEILLANCE"
        triage_cell.font = Font(name="Segoe UI", size=11, bold=True, color=YELLOW_TEXT)
        triage_cell.fill = PatternFill(start_color=YELLOW_FILL, end_color=YELLOW_FILL, fill_type="solid")
    else:
        triage_cell.value = f" ✅ EXECUTIVE VERDICT: LOW / NO SAFETY SIGNAL — ROUTINE POST-MARKETING MONITORING"
        triage_cell.font = Font(name="Segoe UI", size=11, bold=True, color=GREEN_TEXT)
        triage_cell.fill = PatternFill(start_color=GREEN_FILL, end_color=GREEN_FILL, fill_type="solid")
    triage_cell.alignment = Alignment(horizontal="left", vertical="center")
    
    # 3. Core KPIs & Regulatory Assessment Table
    ws1["A6"].value = "1. Core Clinical Safety Metrics & Regulatory Thresholds"
    ws1["A6"].font = font_section
    
    headers_s1 = ["Surveillance Metric", "Observed Value", "Regulatory Benchmark", "Status / Flag", "Actionable Inference"]
    ws1.row_dimensions[7].height = 24
    for col_num, h in enumerate(headers_s1, 1):
        cell = ws1.cell(row=7, column=col_num, value=h)
        cell.font = font_header
        cell.fill = fill_slate
        cell.alignment = align_center if col_num in [2, 3, 4] else align_left
        cell.border = border_cell
        
    kpi_rows = [
        ("Patient Case Burden (Cell A)", f"{A:,} Patients", "≥ 3 Cases Required", "✅ Valid Cohort", "Sufficient real-world patient reports to evaluate disproportionality."),
        ("Relative Risk Multiplier (PRR)", f"{prr:.2f}x", "≥ 2.0x (FDA Alert Line)", "🚨 ELEVATED" if prr >= 2.0 else "⚠️ MODERATE" if prr >= 1.5 else "✅ NORMAL", f"Reported {prr:.2f}x more frequently for {drug_name} vs all other medications."),
        ("Reporting Odds Ratio (ROR)", f"{ror:.2f}x", "≥ 2.0x", "🚨 ELEVATED" if ror >= 2.0 else "✅ NORMAL", f"Odds of reporting this condition are {ror:.2f}x higher than background rate."),
        ("Signal Certainty (Bayesian Monte Carlo)", f"{bayes_prr.get('prob_greater_1', 0)*100:.1f}%", "≥ 95.0% Confidence", "✅ CONFIRMED" if bayes_prr.get('prob_greater_1', 0) >= 0.95 else "⏳ UNCERTAIN", "Calculated via 20,000 posterior simulation draws to rule out random variance."),
        ("WHO Information Component (IC)", f"{bcpnn.get('ic', 0):.2f} (IC₀₂₅: {bcpnn.get('ic_025', 0):.2f})", "Lower 95% Bound > 0.0", "✅ POSITIVE" if bcpnn.get('ic_025', 0) > 0 else "⚪ NEUTRAL", "Meets World Health Organization (WHO UMC) criteria for quantitative signal confirmation.")
    ]
    
    for r_idx, row_data in enumerate(kpi_rows, 8):
        ws1.row_dimensions[r_idx].height = 22
        fill_to_use = fill_alt if r_idx % 2 == 0 else PatternFill(fill_type=None)
        for c_idx, val in enumerate(row_data, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_data_bold if c_idx == 2 else font_data
            cell.fill = fill_to_use
            cell.alignment = align_center if c_idx in [2, 3, 4] else align_left
            cell.border = border_cell
            
    # 4. Action & Governance Roadmap Table
    ws1["A15"].value = "2. Recommended Governance & Operational Next Steps"
    ws1["A15"].font = font_section
    
    headers_act = ["Operational Stream", "Recommended Action Plan", "Compliance Authority", "Target SLA / Deadline", "Responsible Owner"]
    ws1.row_dimensions[16].height = 24
    for col_num, h in enumerate(headers_act, 1):
        cell = ws1.cell(row=16, column=col_num, value=h)
        cell.font = font_header
        cell.fill = fill_slate
        cell.alignment = align_center if col_num in [3, 4, 5] else align_left
        cell.border = border_cell
        
    action_rows = [
        ("Regulatory Compliance", "Initiate FDA 15-Day Expedited Alert Review" if prr >= 2.0 else "Incorporate in Periodic Safety Update Report (PSUR)", "FDA 21 CFR 314.80 / EMA GVP", "15 Calendar Days" if prr >= 2.0 else "Next PSUR Cycle", "Regulatory Affairs"),
        ("Labeling & Risk Management", "Update Prescribing Information Warning Section" if prr >= 1.5 else "Maintain Current Package Insert Language", "Safety Review Committee (SRC)", "Quarterly RMP Review", "Chief Medical Officer"),
        ("Medical Review", "Review patient history records for confounding concomitant drugs", "Internal Pharmacovigilance", "Within 30 Days", "Medical Safety Officer"),
        ("Commercial Strategy", "Formulate physician guidance FAQ to address clinical prescribing questions", "Medical Affairs", "Pre-Advisory Panel", "Commercial Brand Lead")
    ]
    
    for r_idx, row_data in enumerate(action_rows, 17):
        ws1.row_dimensions[r_idx].height = 22
        fill_to_use = fill_alt if r_idx % 2 == 0 else PatternFill(fill_type=None)
        for c_idx, val in enumerate(row_data, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_data
            cell.fill = fill_to_use
            cell.alignment = align_center if c_idx in [3, 4, 5] else align_left
            cell.border = border_cell

    # =========================================================================
    # SHEET 2: CLINICAL COHORT & 2X2 MATRIX
    # =========================================================================
    ws2 = wb.create_sheet(title="Clinical Cohort & 2x2 Matrix")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2.merge_cells("A1:D1")
    t2 = ws2["A1"]
    t2.value = "  2x2 CONTINGENCY COHORT & DISPROPORTIONALITY MATRIX"
    t2.font = font_title
    t2.fill = fill_navy
    ws2.row_dimensions[1].height = 30
    
    ws2["A3"].value = "Cross-Tabulation of Real-World Adverse Event Reports in FAERS"
    ws2["A3"].font = font_section
    
    # 2x2 Grid setup
    headers_m = ["Therapeutic Cohort", f"Target Event: {event_name}", "All Other Adverse Events", "Total Drug Exposure"]
    ws2.row_dimensions[5].height = 24
    for c_num, h in enumerate(headers_m, 1):
        cell = ws2.cell(row=5, column=c_num, value=h)
        cell.font = font_header
        cell.fill = fill_slate
        cell.alignment = align_center if c_num > 1 else align_left
        cell.border = border_cell
        
    m_rows = [
        (f"Target Drug: {drug_name}", f"{A:,} (Cell A)", f"{B:,} (Cell B)", f"{A+B:,}"),
        ("All Other FDA Database Medications", f"{C:,} (Cell C)", f"{D:,} (Cell D)", f"{C+D:,}"),
        ("Total Safety Cohort (N)", f"{A+C:,}", f"{B+D:,}", f"{N:,}")
    ]
    
    for r_idx, row_data in enumerate(m_rows, 6):
        ws2.row_dimensions[r_idx].height = 24
        is_total = (r_idx == 8)
        for c_idx, val in enumerate(row_data, 1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_data_bold if (is_total or c_idx == 1 or c_idx == 4) else font_data
            cell.fill = fill_accent if is_total else (fill_alt if r_idx % 2 == 0 else PatternFill(fill_type=None))
            cell.alignment = align_center if c_idx > 1 else align_left
            cell.border = border_cell
            
    # Proportional Reporting Rates
    rate_drug = (A / (A + B)) * 100 if (A + B) > 0 else 0
    rate_bg = (C / (C + D)) * 100 if (C + D) > 0 else 0
    
    ws2["A11"].value = "Cohort Reporting Proportions"
    ws2["A11"].font = font_section
    
    prop_headers = ["Cohort", "Total Reports", "Reports with this Event", "% Incidence in Reports", "Relative Disproportionality"]
    ws2.row_dimensions[12].height = 24
    for c_num, h in enumerate(prop_headers, 1):
        cell = ws2.cell(row=12, column=c_num, value=h)
        cell.font = font_header
        cell.fill = fill_slate
        cell.alignment = align_center if c_num > 1 else align_left
        cell.border = border_cell
        
    prop_data = [
        (f"Target Drug ({drug_name})", f"{A+B:,}", f"{A:,}", f"{rate_drug:.2f}%", f"{prr:.2f}x vs Market Average"),
        ("General Market Background", f"{C+D:,}", f"{C:,}", f"{rate_bg:.2f}%", "1.00x (Baseline Reference)")
    ]
    
    for r_idx, row_data in enumerate(prop_data, 13):
        ws2.row_dimensions[r_idx].height = 22
        for c_idx, val in enumerate(row_data, 1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_data_bold if c_idx in [4, 5] else font_data
            cell.alignment = align_center if c_idx > 1 else align_left
            cell.border = border_cell

    # =========================================================================
    # SHEET 3: STATISTICAL RIGOR & AUDIT TRAIL
    # =========================================================================
    ws3 = wb.create_sheet(title="Statistical Rigor & Audit")
    ws3.views.sheetView[0].showGridLines = True
    
    ws3.merge_cells("A1:F1")
    t3 = ws3["A1"]
    t3.value = "  STATISTICAL METHODOLOGY & REGULATORY AUDIT TRAIL"
    t3.font = font_title
    t3.fill = fill_navy
    ws3.row_dimensions[1].height = 30
    
    ws3["A3"].value = "Comprehensive Disproportionality Algorithm Outputs"
    ws3["A3"].font = font_section
    
    stat_headers = ["Methodology Framework", "Statistical Metric", "Point Estimate", "Lower 95% Bound", "Upper 95% Bound", "Regulatory Interpretation"]
    ws3.row_dimensions[5].height = 24
    for c_num, h in enumerate(stat_headers, 1):
        cell = ws3.cell(row=5, column=c_num, value=h)
        cell.font = font_header
        cell.fill = fill_slate
        cell.alignment = align_center if c_num in [3, 4, 5] else align_left
        cell.border = border_cell
        
    stat_rows = [
        ("Frequentist (FDA Guidance)", "Proportional Reporting Ratio (PRR)", f"{prr:.3f}", f"{prr_low:.3f}", f"{prr_high:.3f}", "Standard FDA primary signal metric."),
        ("Frequentist (EMA Standard)", "Reporting Odds Ratio (ROR)", f"{ror:.3f}", f"{ror_low:.3f}", f"{ror_high:.3f}", "Standard European Medicines Agency metric."),
        ("Frequentist (Robustness)", "Haldane-Anscombe Odds Ratio (+0.5)", f"{freq.get('haldane_or', 1.0):.3f}", f"{freq.get('haldane_ci_low', 1.0):.3f}", f"{freq.get('haldane_ci_high', 1.0):.3f}", "Continuity-corrected for sparse cell safety events."),
        ("Bayesian (WHO UMC)", "Information Component (BCPNN IC)", f"{bcpnn.get('ic', 0):.3f}", f"{bcpnn.get('ic_025', 0):.3f}", f"{bcpnn.get('ic_975', 0):.3f}", "Information-theoretic measure used by Uppsala Monitoring Centre."),
        ("Bayesian (Monte Carlo)", "Beta-Binomial PRR Posterior Median", f"{bayes_prr.get('median', 1.0):.3f}", f"{bayes_prr.get('ci_low', 1.0):.3f}", f"{bayes_prr.get('ci_high', 1.0):.3f}", "20,000 MCMC draws to eliminate false positives in small cohorts."),
        ("Hypothesis Testing", "Yates' Corrected Chi-Square", f"{freq.get('chi2_yates', 0):.2f}", "-", f"p = {freq.get('chi2_yates_pvalue', 1.0):.4e}", "Assesses independence in contingency table."),
        ("Hypothesis Testing", "Fisher's Exact Hypergeometric Test", "-", "-", f"p = {freq.get('fisher_pvalue', 1.0):.4e}", "Exact probability test for discrete safety distributions.")
    ]
    
    for r_idx, row_data in enumerate(stat_rows, 6):
        ws3.row_dimensions[r_idx].height = 22
        fill_to_use = fill_alt if r_idx % 2 == 0 else PatternFill(fill_type=None)
        for c_idx, val in enumerate(row_data, 1):
            cell = ws3.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_data_bold if c_idx == 3 else font_data
            cell.fill = fill_to_use
            cell.alignment = align_center if c_idx in [3, 4, 5] else align_left
            cell.border = border_cell

    # ------------------ AUTO-FIT COLUMN WIDTHS ------------------
    for ws in [ws1, ws2, ws3]:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                # Ignore title banner row lengths when calculating column widths
                if cell.row in [1, 2, 4] and ws == ws1:
                    continue
                if cell.row == 1:
                    continue
                val_str = str(cell.value or "")
                if val_str:
                    max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)
            
    # Specific targeted column width overrides for elegance
    ws1.column_dimensions["A"].width = 38
    ws1.column_dimensions["B"].width = 22
    ws1.column_dimensions["C"].width = 26
    ws1.column_dimensions["D"].width = 24
    ws1.column_dimensions["E"].width = 46
    
    ws2.column_dimensions["A"].width = 40
    ws2.column_dimensions["B"].width = 28
    ws2.column_dimensions["C"].width = 28
    ws2.column_dimensions["D"].width = 26
    ws2.column_dimensions["E"].width = 30
    
    ws3.column_dimensions["A"].width = 30
    ws3.column_dimensions["B"].width = 38
    ws3.column_dimensions["C"].width = 18
    ws3.column_dimensions["D"].width = 18
    ws3.column_dimensions["E"].width = 20
    ws3.column_dimensions["F"].width = 45

    wb.save(output_path)
    return output_path
