"""
FAERS & EudraVigilance Pharmacovigilance Signal Detection Package
"""

from .analytics import (
    calculate_2x2_counts,
    calculate_frequentist_metrics,
    calculate_bcpnn_ic,
    calculate_bayesian_prr,
    calculate_bayesian_ror,
    evaluate_signal_strength,
    run_full_disproportionality_analysis
)
from .deduplication import vigimatch_deduplicate_drugs, vigimatch_deduplicate_reactions
from .loader import load_faers_files, filter_files_by_quarter
from .reporting import export_excel_report
from .visualizations import (
    plot_bayesian_posterior,
    plot_forest_summary,
    plot_contingency_matrix,
    plot_volcano_quadrant
)

__all__ = [
    'calculate_2x2_counts',
    'calculate_frequentist_metrics',
    'calculate_bcpnn_ic',
    'calculate_bayesian_prr',
    'calculate_bayesian_ror',
    'evaluate_signal_strength',
    'run_full_disproportionality_analysis',
    'vigimatch_deduplicate_drugs',
    'vigimatch_deduplicate_reactions',
    'load_faers_files',
    'filter_files_by_quarter',
    'export_excel_report',
    'plot_bayesian_posterior',
    'plot_forest_summary',
    'plot_contingency_matrix',
    'plot_volcano_quadrant',
]
