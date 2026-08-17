"""
Excel Financial Statement Parser.
Reads multi-sheet Excel workbooks (.xlsx, .xls) using pandas/openpyxl,
classifies sheets by statement type, and extracts structured items across periods.
"""

import os
from typing import Dict, Any, List
import pandas as pd
from ..extraction.statement_detector import StatementDetector
from ..extraction.table_extractor import TableExtractor
from ..normalization.number_parser import NumberParser


class ExcelParser:
    @classmethod
    def parse_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Parses an Excel workbook into categorized financial statements.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names

        statements_result: Dict[str, Any] = {
            "balance_sheet": {},
            "income_statement": {},
            "cash_flow_statement": {},
            "notes": []
        }

        detected_currency = "INR"
        detected_scale = "Crores"
        detected_multiplier = 10000000.0

        for sheet_idx, sheet_name in enumerate(sheet_names):
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            rows = df.fillna("").values.tolist()

            if not rows:
                continue

            # Detect statement type from sheet name first, then content
            statement_type = StatementDetector.detect_statement_type(sheet_name)
            if not statement_type:
                sheet_text = " ".join([str(cell) for row in rows[:5] for cell in row])
                statement_type = StatementDetector.detect_statement_type(sheet_text)

            if not statement_type:
                statement_type = "balance_sheet"  # Default if single sheet

            # Check currency/scale in header
            header_sample = " ".join([str(c) for r in rows[:8] for c in r])
            curr, sc, mult = NumberParser.detect_currency_and_scale(header_sample)
            if sc != "Absolute":
                detected_currency, detected_scale, detected_multiplier = curr, sc, mult

            source_info = {
                "file": filename,
                "sheet": sheet_name,
                "page": sheet_idx + 1,
                "table_index": 0
            }

            extracted_items = TableExtractor.parse_table_rows(
                rows=rows,
                section_name=statement_type,
                source_info=source_info,
                default_scale_multiplier=detected_multiplier
            )

            if statement_type in statements_result:
                statements_result[statement_type].update(extracted_items)

        return {
            "statements": statements_result,
            "currency": detected_currency,
            "scale": detected_scale,
            "multiplier": detected_multiplier,
            "sheets_analyzed": len(sheet_names),
            "source_file": filename
        }
