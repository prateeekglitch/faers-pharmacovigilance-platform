"""
Deduplication & Medical Ontology Normalization (WHO VigiMatch Standard)
"""

import hashlib
from typing import List, Tuple, Dict, Optional
import pandas as pd


def normalize_drug_name(raw_name: str, synonym_mappings: Optional[Dict[str, str]] = None) -> str:
    """
    Standardize drug names and map brand names / synonyms to active ingredients.
    """
    if not isinstance(raw_name, str) or not raw_name.strip():
        return ""
    
    clean = raw_name.strip().upper()
    if synonym_mappings:
        for brand_or_alias, generic in synonym_mappings.items():
            if brand_or_alias.upper() in clean:
                return generic.upper()
    return clean


def vigimatch_deduplicate_drugs(
    df_drug: pd.DataFrame,
    target_synonyms: Optional[List[str]] = None,
    filter_primary_suspect: bool = True
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Applies WHO VigiMatch-style deduplication to FAERS DRUG records.
    Filters for Primary Suspect (PS) drugs and removes multi-entry duplicate rows.
    """
    if df_drug.empty:
        return df_drug, {"initial_count": 0, "final_count": 0, "duplicates_removed": 0}

    initial_count = len(df_drug)
    working_df = df_drug.copy()

    # Standardize column names to lowercase
    working_df.columns = [c.lower() for c in working_df.columns]

    # Filter for Primary Suspect (role_cod == 'PS')
    if filter_primary_suspect and 'role_cod' in working_df.columns:
        working_df['role_cod'] = working_df['role_cod'].fillna('').astype(str).str.upper()
        working_df = working_df[working_df['role_cod'] == 'PS']

    # Ensure required columns exist
    if 'drugname' not in working_df.columns:
        working_df['drugname'] = ''
    working_df['drugname'] = working_df['drugname'].fillna('').astype(str).str.upper()

    # Normalize drug name
    if target_synonyms:
        synonym_map = {s: target_synonyms[0] for s in target_synonyms}
        working_df['drugname_norm'] = working_df['drugname'].apply(
            lambda name: normalize_drug_name(name, synonym_map)
        )
    else:
        working_df['drugname_norm'] = working_df['drugname']

    # Ensure deduplication key fields exist
    dedup_cols = ['primaryid', 'drugname_norm', 'route', 'dose_vbm']
    for col in dedup_cols:
        if col not in working_df.columns:
            working_df[col] = ''
        working_df[col] = working_df[col].fillna('').astype(str)

    # Sort by primaryid and drop duplicates
    deduped_df = working_df.sort_values(by='primaryid').drop_duplicates(subset=dedup_cols).reset_index(drop=True)
    final_count = len(deduped_df)
    duplicates_removed = initial_count - final_count

    stats = {
        "initial_count": initial_count,
        "ps_filtered_count": len(working_df),
        "final_count": final_count,
        "duplicates_removed": duplicates_removed
    }
    return deduped_df, stats


def vigimatch_deduplicate_reactions(df_reac: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Deduplicates FAERS REACTION (REAC) records by primary ID and MedDRA Preferred Term (PT).
    """
    if df_reac.empty:
        return df_reac, {"initial_count": 0, "final_count": 0, "duplicates_removed": 0}

    initial_count = len(df_reac)
    working_df = df_reac.copy()
    working_df.columns = [c.lower() for c in working_df.columns]

    if 'primaryid' not in working_df.columns:
        working_df['primaryid'] = ''
    if 'pt' not in working_df.columns:
        working_df['pt'] = ''

    working_df['primaryid'] = working_df['primaryid'].fillna('').astype(str)
    working_df['pt'] = working_df['pt'].fillna('').astype(str).str.upper()

    deduped_df = working_df.drop_duplicates(subset=['primaryid', 'pt']).reset_index(drop=True)
    final_count = len(deduped_df)

    stats = {
        "initial_count": initial_count,
        "final_count": final_count,
        "duplicates_removed": initial_count - final_count
    }
    return deduped_df, stats


def generate_demographic_hash(row: pd.Series, fields: List[str]) -> str:
    """
    Generates a SHA-256 demographic hash key for multi-source registry deduplication.
    """
    concat_str = "|".join([str(row.get(f, '')).strip().upper() for f in fields])
    return hashlib.sha256(concat_str.encode('utf-8')).hexdigest()
