"""
PDF Financial Statement Parser.
Extracts financial text and tables from Digital PDFs using pypdf, pdfplumber, or PyMuPDF.
Classifies statements by page, extracts row line items, and tracks source page numbers.
"""

import os
import re
from typing import Dict, Any, List, Optional
from ..extraction.statement_detector import StatementDetector
from ..extraction.table_extractor import TableExtractor
from ..normalization.number_parser import NumberParser


class PDFParser:
    @classmethod
    def _extract_pages_pypdf(cls, file_path: str) -> List[Dict[str, Any]]:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        pages_data = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_data.append({
                "page_number": i + 1,
                "text": text,
                "tables": []
            })
        return pages_data

    @classmethod
    def _extract_pages_pdfplumber(cls, file_path: str) -> List[Dict[str, Any]]:
        import pdfplumber
        pages_data = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                tables = page.extract_tables() or []
                pages_data.append({
                    "page_number": i + 1,
                    "text": text,
                    "tables": tables
                })
        return pages_data

    @classmethod
    def _parse_text_lines_to_table(cls, text: str) -> List[List[str]]:
        """
        Converts plain extracted text with tab/multi-space column layouts into table rows.
        """
        rows: List[List[str]] = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Split by 2 or more spaces or tabs
            cols = re.split(r"\s{2,}|\t", line)
            if len(cols) >= 2:
                rows.append([c.strip() for c in cols])
            elif len(cols) == 1:
                # Try finding numbers at the end of line e.g., 'Revenue from operations 3,480.00 2,950.00'
                num_matches = list(re.finditer(r"\(?-?[\d,]+(?:\.\d+)?\)?", line))
                if num_matches and len(num_matches) >= 1:
                    first_num_start = num_matches[0].start()
                    label = line[:first_num_start].strip()
                    nums = [m.group(0).strip() for m in num_matches]
                    if label:
                        rows.append([label] + nums)
        return rows

    @classmethod
    def parse_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Parses a PDF financial statement into structured statements and notes.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)

        # 1. Extract raw pages
        pages_data = []
        try:
            pages_data = cls._extract_pages_pdfplumber(file_path)
        except (ImportError, Exception):
            try:
                pages_data = cls._extract_pages_pypdf(file_path)
            except Exception as e:
                raise RuntimeError(f"Failed to extract PDF contents: {str(e)}")

        statements_result: Dict[str, Any] = {
            "balance_sheet": {},
            "income_statement": {},
            "cash_flow_statement": {},
            "notes": []
        }

        detected_currency = "INR"
        detected_scale = "Crores"
        detected_multiplier = 10000000.0

        for page in pages_data:
            page_num = page["page_number"]
            page_text = page["text"]
            page_tables = page.get("tables", [])

            # Statement detection
            statement_type = StatementDetector.detect_statement_type(page_text)

            # Currency & scale detection
            curr, sc, mult = NumberParser.detect_currency_and_scale(page_text)
            if sc != "Absolute":
                detected_currency, detected_scale, detected_multiplier = curr, sc, mult

            if statement_type and statement_type in statements_result:
                source_info = {
                    "file": filename,
                    "page": page_num,
                    "table_index": 0
                }

                # If pdfplumber extracted explicit table grids
                if page_tables:
                    for tbl_idx, tbl in enumerate(page_tables):
                        source_info["table_index"] = tbl_idx
                        extracted = TableExtractor.parse_table_rows(
                            rows=tbl,
                            section_name=statement_type,
                            source_info=source_info,
                            default_scale_multiplier=detected_multiplier
                        )
                        statements_result[statement_type].update(extracted)
                else:
                    # Fallback to text table parsing
                    text_rows = cls._parse_text_lines_to_table(page_text)
                    if text_rows:
                        extracted = TableExtractor.parse_table_rows(
                            rows=text_rows,
                            section_name=statement_type,
                            source_info=source_info,
                            default_scale_multiplier=detected_multiplier
                        )
                        statements_result[statement_type].update(extracted)

            elif statement_type == "notes" or "note" in page_text.lower():
                # Extract note text blocks
                note_matches = re.finditer(r"(Note\s*\d+[a-z]?[\s:–—]+[^\n]+)\n(.*?)(?=(?:Note\s*\d+|$))", page_text, re.DOTALL | re.IGNORECASE)
                for nm in note_matches:
                    title_line = nm.group(1).strip()
                    body_text = nm.group(2).strip()
                    if body_text:
                        statements_result["notes"].append({
                            "note_number": title_line.split(":")[0].strip(),
                            "topic": title_line,
                            "text": body_text[:400],
                            "source": {"file": filename, "page": page_num}
                        })

        return {
            "statements": statements_result,
            "currency": detected_currency,
            "scale": detected_scale,
            "multiplier": detected_multiplier,
            "total_pages": len(pages_data),
            "source_file": filename
        }
