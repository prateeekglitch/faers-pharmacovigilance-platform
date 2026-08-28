"""
Data Ingestion & Encoding Resilience Module for FDA FAERS & EMA Datasets
"""

import os
import glob
import re
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd


def parse_quarter_from_filename(filename: str) -> Optional[Tuple[int, int]]:
    """
    Extract (year, quarter) from standard FAERS filenames like DRUG24Q3.txt or drug23q4.txt.
    Returns (2024, 3) or None if pattern does not match.
    """
    base = os.path.basename(filename).upper()
    match = re.search(r'(\d{2})(Q[1-4])', base)
    if not match:
        return None
    year_2digit, quarter_str = match.groups()
    year = int("20" + year_2digit) if int(year_2digit) < 50 else int("19" + year_2digit)
    quarter = int(quarter_str[1])
    return (year, quarter)


def is_in_quarter_range(filename: str, start_q: Tuple[int, int], end_q: Tuple[int, int]) -> bool:
    """
    Check if a file belongs within the specified start and end quarter bounds.
    """
    parsed = parse_quarter_from_filename(filename)
    if not parsed:
        return True  # If no quarter in name, keep file
    return start_q <= parsed <= end_q


def filter_files_by_quarter(folder: str, pattern: str, start_q: Tuple[int, int], end_q: Tuple[int, int]) -> List[str]:
    """
    Find and filter files matching a glob pattern within quarter bounds.
    """
    matched = sorted(glob.glob(os.path.join(folder, pattern)) +
                     glob.glob(os.path.join(folder, pattern.upper())) +
                     glob.glob(os.path.join(folder, pattern.lower())))
    unique_files = sorted(list(set(matched)))
    return [f for f in unique_files if is_in_quarter_range(f, start_q, end_q)]


def load_single_file_with_fallback(filepath: str, sep: str = "$") -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Attempts to load a single delimited file trying UTF-8 first, then Latin-1.
    """
    for encoding in ['utf-8', 'latin1', 'cp1252']:
        try:
            df = pd.read_csv(
                filepath,
                sep=sep,
                dtype=str,
                encoding=encoding,
                on_bad_lines='skip',
                low_memory=False
            )
            return df, None
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return pd.DataFrame(), f"{filepath}: {str(e)}"
    return pd.DataFrame(), f"{filepath}: Failed all encodings (UTF-8, Latin-1, CP1252)"


def load_faers_files(
    folder: str,
    pattern: str,
    start_q: Tuple[int, int] = (2023, 1),
    end_q: Tuple[int, int] = (2025, 4),
    sep: str = "$"
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Loads all FAERS files matching pattern across the quarter range with encoding fallbacks.
    Returns (concatenated_dataframe, audit_log_of_errors).
    """
    target_files = filter_files_by_quarter(folder, pattern, start_q, end_q)
    dataframes = []
    audit_logs = []

    for file_path in target_files:
        df, err = load_single_file_with_fallback(file_path, sep=sep)
        if err:
            audit_logs.append({"file": file_path, "status": "error", "message": err})
        elif not df.empty:
            audit_logs.append({"file": file_path, "status": "success", "rows": len(df)})
            dataframes.append(df)

    if not dataframes:
        return pd.DataFrame(), audit_logs

    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df, audit_logs
