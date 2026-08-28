"""
Unit Tests for WHO VigiMatch Deduplication Logic
"""

import pandas as pd
from src.faers.deduplication import vigimatch_deduplicate_drugs, vigimatch_deduplicate_reactions


def test_vigimatch_drug_deduplication():
    data = {
        'primaryid': ['101', '101', '102', '103'],
        'role_cod': ['PS', 'PS', 'C', 'PS'],
        'drugname': ['TRUQAP', 'TRUQAP', 'ASPIRIN', 'OZEMPIC'],
        'route': ['ORAL', 'ORAL', 'ORAL', 'SUBCUTANEOUS'],
        'dose_vbm': ['400 MG', '400 MG', '100 MG', '1 MG']
    }
    df = pd.DataFrame(data)
    deduped_df, stats = vigimatch_deduplicate_drugs(df, target_synonyms=['TRUQAP', 'CAPIVASERTIB'])

    # Case 101 has duplicate row -> 1 kept
    # Case 102 is role_cod == 'C' (concomitant) -> filtered out
    # Case 103 is role_cod == 'PS' -> kept
    assert stats["initial_count"] == 4
    assert stats["final_count"] == 2
    assert stats["duplicates_removed"] == 2


def test_vigimatch_reaction_deduplication():
    data = {
        'primaryid': ['101', '101', '102'],
        'pt': ['NAUSEA', 'NAUSEA', 'HEADACHE']
    }
    df = pd.DataFrame(data)
    deduped_df, stats = vigimatch_deduplicate_reactions(df)

    assert stats["initial_count"] == 3
    assert stats["final_count"] == 2
