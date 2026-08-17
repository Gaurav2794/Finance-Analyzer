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
        Identifies column indexes corresponding to fiscal periods like FY2024, FY2023, 2024, 2023.
        Returns map: {col_index: 'FY2024'}
        """
        period_map = {}
        for idx, col in enumerate(header_row):
            if not col:
                continue
            col_str = str(col).strip()
            
            # Check FY format: FY2024 or FY24
            fy_match = cls.FY_PATTERN.search(col_str)
            if fy_match:
                raw_fy = fy_match.group(1).replace(" ", "").upper()
                if len(raw_fy) == 4:  # FY24 -> FY2024
                    raw_fy = f"FY20{raw_fy[2:]}"
                period_map[idx] = raw_fy
                continue

            # Check 4-digit Year format: 2024, 2023
            yr_match = cls.YEAR_PATTERN.search(col_str)
            if yr_match:
                yr = yr_match.group(1)
                period_map[idx] = f"FY{yr}"
                continue

        # If only 2 numeric data columns were found without explicit year in headers, assign default FY2024 & FY2023
        return period_map

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

        # 1. Find Header Row
        header_idx = -1
        period_cols: Dict[int, str] = {}

        for i, row in enumerate(rows[:5]):
            cols = [str(cell) for cell in row]
            detected_periods = cls.identify_period_columns(cols)
            if len(detected_periods) >= 1:
                header_idx = i
                period_cols = detected_periods
                break

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
            if not raw_label or raw_label.lower() in ["particulars", "line item", "description", "assets", "liabilities"]:
                continue

            # Check if col 1 is a Note column
            note_ref = None
            if len(row) > 1 and str(row[1]).strip().isdigit():
                note_ref = f"Note {str(row[1]).strip()}"

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
                item_obj = {
                    "standard_label": raw_label,
                    "raw_labels": [raw_label],
                    "values": values_dict,
                    "source": {
                        "file": source_info.get("file", "unknown"),
                        "page": source_info.get("page", 1),
                        "table_index": source_info.get("table_index", 0),
                        "note_ref": note_ref
                    }
                }
                extracted_items[std_key] = item_obj

        return extracted_items
