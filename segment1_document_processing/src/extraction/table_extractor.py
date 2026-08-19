"""
Table Extractor & Column Alignment.
Parses multi-column financial tables, aligns fiscal period columns (FY2024, FY2023, etc.),
extracts note references, and maps rows to normalized line-item dictionaries.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..normalization.number_parser import NumberParser
from ..normalization.label_mapper import LabelMapper


class TableExtractor:
    YEAR_PATTERN = re.compile(r"\b(20\d\d|19\d\d)\b")
    FY_PATTERN = re.compile(r"\b(FY\s*20?\d\d|FY\s*\d\d)\b", re.IGNORECASE)
    NOTE_PATTERN = re.compile(r"\b(note\s*\d+[a-z]?|\b\d+\b)", re.IGNORECASE)

    @classmethod
    def identify_period_columns(cls, header_row: List[str]) -> Dict[int, str]:
        """
        Identifies column indexes corresponding to fiscal periods like FY2025, FY2024, FY2023, 2024, 2023.
        Returns map: {col_index: 'FY2025'}
        """
        period_map = {}
        for idx, col in enumerate(header_row):
            if not col:
                continue
            col_str = str(col).strip()
            # If the cell is long or contains title words like 'vs', '|', 'ltd', 'sheet', skip it
            if len(col_str) > 20 and any(w in col_str.lower() for w in ["vs", "|", "ltd", "statement", "sheet", "annual", "report", "company"]):
                continue

            # Check FY format: FY2025 or FY25
            fy_match = cls.FY_PATTERN.search(col_str)
            if fy_match:
                raw_fy = fy_match.group(1).replace(" ", "").upper()
                if len(raw_fy) == 4:  # FY24 -> FY2024
                    raw_fy = f"FY20{raw_fy[2:]}"
                period_map[idx] = raw_fy
                continue

            # Check 4-digit Year format: 2025, 2024
            yr_match = cls.YEAR_PATTERN.search(col_str)
            if yr_match:
                yr = yr_match.group(1)
                period_map[idx] = f"FY{yr}"
                continue

        return period_map

    @classmethod
    def find_best_header_row(cls, rows: List[List[Any]]) -> Tuple[int, Dict[int, str]]:
        """
        Searches the first 10 rows of a table to identify the true column header row.
        Prefers rows with >= 2 period columns at index >= 1, and rows containing 'particulars'/'description'.
        """
        best_idx = -1
        best_map: Dict[int, str] = {}
        best_score = -1

        for i, row in enumerate(rows[:10]):
            cols = [str(cell) for cell in row]
            detected_periods = cls.identify_period_columns(cols)
            if not detected_periods:
                continue

            score = len(detected_periods) * 10
            # Bonus if period columns are not at column 0 (column 0 is usually line item label)
            if 0 not in detected_periods:
                score += 25
            # Bonus if column 0 contains label header keywords
            if cols and any(w in cols[0].lower() for w in ["particular", "account", "description", "metric", "item", "line", "asset", "liabilit"]):
                score += 35

            if score > best_score:
                best_score = score
                best_idx = i
                best_map = detected_periods

        return best_idx, best_map

    @classmethod
    def parse_table_rows(
        cls,
        rows: List[List[Any]],
        section_name: str,
        source_info: Dict[str, Any],
        default_scale_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Processes table matrix (list of row lists) into standard financial dictionary.
        """
        if not rows:
            return {}

        # 1. Find the best Header Row
        header_idx, period_cols = cls.find_best_header_row(rows)

        # Fallback if header row not identified
        if not period_cols:
            period_cols = {1: "FY2024", 2: "FY2023"}
            start_row = 1 if header_idx >= 0 else 0
        else:
            start_row = header_idx + 1

        extracted_items: Dict[str, Any] = {}

        for row_idx in range(start_row, len(rows)):
            row = rows[row_idx]
            if not row or not any(row):
                continue

            # Col 0 is typically line item label
            raw_label = str(row[0]).strip() if len(row) > 0 and row[0] is not None else ""
            if not raw_label:
                continue

            # Stop extraction if row indicates start of detailed supporting schedules section
            if any(term in raw_label.lower() for term in [
                "detailed supporting schedule",
                "supporting schedule",
                "detailed cash flow supporting schedule",
                "schedule of"
            ]):
                break

            if raw_label.lower() in [
                "particulars", "line item", "description", "assets", "liabilities", "equity",
                "equity and liabilities", "non-current assets", "current assets", "revenue",
                "expenses", "operating activities", "investing activities", "financing activities"
            ]:
                continue

            # Check if any column is a Note column (e.g. "Note 15" or column 1/3)
            note_ref = None
            for c_idx, cell in enumerate(row):
                if c_idx not in period_cols:
                    c_str = str(cell).strip()
                    if c_str.lower().startswith("note ") or (c_str.isdigit() and int(c_str) < 100):
                        note_ref = c_str if c_str.lower().startswith("note ") else f"Note {c_str}"
                        break

            # Map label to standard key
            std_key, cleaned_label = LabelMapper.map_label(raw_label, section=section_name)
            if not std_key:
                continue

            # Extract numeric values across periods
            values_dict: Dict[str, Optional[float]] = {}
            has_numeric_val = False

            for col_idx, period_key in period_cols.items():
                if col_idx < len(row):
                    cell_val = row[col_idx]
                    parsed_num = NumberParser.parse_financial_number(cell_val, default_scale_multiplier)
                    values_dict[period_key] = parsed_num
                    if parsed_num is not None:
                        has_numeric_val = True
                else:
                    values_dict[period_key] = None

            if has_numeric_val:
                # Do not overwrite a populated primary statement item with an incomplete sub-item
                if std_key in extracted_items:
                    existing_vals = extracted_items[std_key].get("values", {})
                    existing_count = sum(1 for v in existing_vals.values() if v is not None)
                    new_count = sum(1 for v in values_dict.values() if v is not None)
                    if existing_count >= new_count and existing_count > 0:
                        continue

                item_obj = {
                    "standard_label": raw_label,
                    "raw_labels": [raw_label],
                    "values": values_dict,
                    "source": {
                        "file": source_info.get("file", "unknown"),
                        "sheet": source_info.get("sheet"),
                        "page": source_info.get("page", 1),
                        "table_index": source_info.get("table_index", 0),
                        "note_ref": note_ref
                    }
                }
                extracted_items[std_key] = item_obj

        return extracted_items
