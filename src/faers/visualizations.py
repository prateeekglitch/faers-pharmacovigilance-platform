"""
Interactive Plotly Visualizations for Pharmacovigilance Analytics
"""

from typing import Dict, Any, Optional
import numpy as np
import plotly.graph_objects as go


def plot_bayesian_posterior(
    bayes_results: Dict[str, Any],
    drug_name: str = "Drug",
    event_name: str = "Event"
) -> go.Figure:
    """
    Renders the posterior probability density curve of PRR from 50,000 Beta Monte Carlo draws,
    highlighting the 95% Credible Interval and null hypothesis threshold (PRR = 1.0).
    """
    samples = bayes_results.get("samples")
    if samples is None or len(samples) == 0:
        fig = go.Figure()
        fig.update_layout(title="No simulation samples available")
        return fig

    # Compute histogram / density
    counts, bin_edges = np.histogram(samples, bins=100, density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    ci_low = bayes_results.get("ci_low", 1.0)
    ci_high = bayes_results.get("ci_high", 1.0)
    median_val = bayes_results.get("median", 1.0)
    p_gt1 = bayes_results.get("prob_greater_1", 0.0) * 100

    fig = go.Figure()

    # Full posterior curve
    fig.add_trace(go.Scatter(
        x=bin_centers,
        y=counts,
        mode='lines',
        name='Posterior Density',
        line=dict(color='#2563EB', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(37, 99, 235, 0.15)'
    ))

    # Highlight 95% Credible Interval region
    ci_mask = (bin_centers >= ci_low) & (bin_centers <= ci_high)
    if np.any(ci_mask):
        fig.add_trace(go.Scatter(
            x=bin_centers[ci_mask],
            y=counts[ci_mask],
            mode='lines',
            name='95% Credible Interval',
            line=dict(color='#1D4ED8', width=0),
            fill='tozeroy',
            fillcolor='rgba(37, 99, 235, 0.35)'
        ))

    # Reference vertical lines
    fig.add_vline(x=1.0, line_dash="dash", line_color="#EF4444", annotation_text="Null (PRR=1.0)", annotation_position="top left")
    fig.add_vline(x=median_val, line_dash="solid", line_color="#059669", annotation_text=f"Median: {median_val:.2f}", annotation_position="top right")

    fig.update_layout(
        title=f"Bayesian Beta-Binomial Posterior Distribution: {drug_name} & {event_name}<br><sup>P(PRR > 1.0) = {p_gt1:.1f}% | 95% CrI: [{ci_low:.2f}, {ci_high:.2f}]</sup>",
        xaxis_title="Proportional Reporting Ratio (PRR)",
        yaxis_title="Posterior Density",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=70, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def plot_forest_summary(
    frequentist: Dict[str, Any],
    bayes_prr: Dict[str, Any],
    bcpnn_ic: Dict[str, Any]
) -> go.Figure:
    """
    Renders a Forest Plot comparing Point Estimates and 95% Confidence / Credible Intervals.
    """
    metrics = ["Reporting Odds Ratio (ROR)", "Proportional Reporting Ratio (PRR)", "Haldane OR (+0.5)", "Bayesian PRR (Empirical Bayes)"]
    
    estimates = [
        frequentist.get("ror", 1.0),
        frequentist.get("prr", 1.0),
        frequentist.get("haldane_or", 1.0),
        bayes_prr.get("median", 1.0)
    ]
    
    lows = [
        frequentist.get("ror_ci_low", 1.0),
        frequentist.get("prr_ci_low", 1.0),
        frequentist.get("haldane_ci_low", 1.0),
        bayes_prr.get("ci_low", 1.0)
    ]
    
    highs = [
        frequentist.get("ror_ci_high", 1.0),
        frequentist.get("prr_ci_high", 1.0),
        frequentist.get("haldane_ci_high", 1.0),
        bayes_prr.get("ci_high", 1.0)
    ]

    err_plus = [h - e if (h is not None and e is not None and not np.isnan(h) and not np.isnan(e)) else 0 for h, e in zip(highs, estimates)]
    err_minus = [e - l if (l is not None and e is not None and not np.isnan(l) and not np.isnan(e)) else 0 for l, e in zip(lows, estimates)]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=estimates,
        y=metrics,
        mode='markers',
        marker=dict(color=['#2563EB', '#7C3AED', '#059669', '#EA580C'], size=12, symbol='square'),
        error_x=dict(
            type='data',
            symmetric=False,
            array=err_plus,
            arrayminus=err_minus,
            thickness=2,
            width=6,
            color='#4B5563'
        ),
        name="Estimate (95% CI/CrI)"
    ))

    fig.add_vline(x=1.0, line_dash="dash", line_color="#DC2626", annotation_text="Baseline (No Association = 1.0)", annotation_position="bottom right")

    fig.update_layout(
        title="Disproportionality Forest Plot (Point Estimates & 95% Bounds)",
        xaxis_title="Ratio Scale",
        yaxis_title="",
        xaxis_type="log",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=350
    )
    return fig


def plot_contingency_matrix(A: int, B: int, C: int, D: int) -> go.Figure:
    """
    Renders an interactive 2x2 contingency matrix heatmap.
    """
    N = A + B + C + D
    z_values = [[A, B], [C, D]]
    text_labels = [
        [f"<b>Cell A (Co-occurrence)</b><br>{A:,} cases<br>({A/N*100:.2f}%)", f"<b>Cell B (Drug Only)</b><br>{B:,} cases<br>({B/N*100:.2f}%)"],
        [f"<b>Cell C (Event Only)</b><br>{C:,} cases<br>({C/N*100:.2f}%)", f"<b>Cell D (Background)</b><br>{D:,} cases<br>({D/N*100:.2f}%)"]
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=['Target Event (Yes)', 'Other Events (No)'],
        y=['Target Drug (Yes)', 'Other Drugs (No)'],
        text=text_labels,
        texttemplate="%{text}",
        colorscale="Blues",
        showscale=False
    ))

    fig.update_layout(
        title=f"2x2 Contingency Matrix (Total Dataset N = {N:,})",
        xaxis_title="Adverse Event Occurrence",
        yaxis_title="Drug Exposure",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=320
    )
    return fig


def plot_volcano_quadrant(
    analysis_results_list: list
) -> go.Figure:
    """
    Renders a Disproportionality Volcano Plot: Effect Size (PRR) vs Significance (-log10 Fisher p-value).
    """
    fig = go.Figure()

    for item in analysis_results_list:
        label = f"{item['drug']} & {item['event']}"
        prr = item['frequentist'].get('prr', 1.0)
        p_val = max(item['frequentist'].get('fisher_pvalue', 1.0), 1e-15)
        neg_log_p = -np.log10(p_val)
        tier = item['triage'].get('tier', 'NONE')
        color = item['triage'].get('color', 'blue')

        fig.add_trace(go.Scatter(
            x=[prr],
            y=[neg_log_p],
            mode='markers+text',
            text=[label],
            textposition="top center",
            marker=dict(size=14, color=color),
            name=label
        ))

    fig.add_hline(y=-np.log10(0.05), line_dash="dash", line_color="#DC2626", annotation_text="Significance threshold (p=0.05)")
    fig.add_vline(x=2.0, line_dash="dash", line_color="#DC2626", annotation_text="FDA PRR Benchmark (>=2.0)")

    fig.update_layout(
        title="Disproportionality Volcano Plot (Effect Size vs. Statistical Significance)",
        xaxis_title="Proportional Reporting Ratio (PRR)",
        yaxis_title="-log10(Fisher's Exact p-value)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=400
    )
    return fig
