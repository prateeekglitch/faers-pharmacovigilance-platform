"""
Unit Tests for FAERS File Loader & Quarter Parsing
"""

from src.faers.loader import parse_quarter_from_filename, is_in_quarter_range


def test_parse_quarter_from_filename():
    assert parse_quarter_from_filename("DRUG24Q3.txt") == (2024, 3)
    assert parse_quarter_from_filename("reac23q1.txt") == (2023, 1)
    assert parse_quarter_from_filename("random_file.csv") is None


def test_is_in_quarter_range():
    assert is_in_quarter_range("DRUG24Q2.txt", (2023, 1), (2025, 4)) is True
    assert is_in_quarter_range("DRUG22Q4.txt", (2023, 1), (2025, 4)) is False
