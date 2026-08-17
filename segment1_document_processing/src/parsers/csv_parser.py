"""
CSV Financial Statement Parser.
Reads CSV financial data, detects statement types, and extracts structured items.
"""

import csv
import os
from typing import Dict, Any, List
from ..extraction.statement_detector import StatementDetector
from ..extraction.table_extractor import TableExtractor
from ..normalization.number_parser import NumberParser


class CSVParser:
    @classmethod
    def parse_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Parses a financial CSV file into intermediate structured statement tables.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        rows: List[List[str]] = []

        with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append([cell.strip() for cell in row])

        # Detect statement type from header rows or filename
        header_text = " ".join([" ".join(r) for r in rows[:10]])
        detected_statement = StatementDetector.detect_statement_type(header_text)
        if not detected_statement:
            detected_statement = StatementDetector.detect_statement_type(filename)
        if not detected_statement:
            detected_statement = "balance_sheet"  # Default fallback

        # Detect scale and currency
        currency, scale, multiplier = NumberParser.detect_currency_and_scale(header_text)

        source_info = {
            "file": filename,
            "page": 1,
            "table_index": 0
        }

        extracted_items = TableExtractor.parse_table_rows(
            rows=rows,
            section_name=detected_statement,
            source_info=source_info,
            default_scale_multiplier=multiplier
        )

        return {
            "statement_type": detected_statement,
            "currency": currency,
            "scale": scale,
            "multiplier": multiplier,
            "items": extracted_items,
            "raw_rows_count": len(rows),
            "source_file": filename
        }
