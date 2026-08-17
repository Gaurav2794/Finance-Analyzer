"""
Text & Markdown Document Parser.
Handles plain text (.txt), Markdown (.md), and JSON financial reports/disclosures.
"""

import os
import re
import json
from typing import Dict, Any, List
from ..extraction.statement_detector import StatementDetector
from ..extraction.table_extractor import TableExtractor
from ..normalization.number_parser import NumberParser


class TextDocumentParser:
    @classmethod
    def parse_file(cls, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                raw_json = json.load(f)
            # If already standardized or dictionary
            return {
                "statements": {
                    "balance_sheet": raw_json.get("balance_sheet", {}),
                    "income_statement": raw_json.get("income_statement", {}),
                    "cash_flow_statement": raw_json.get("cash_flow_statement", {}),
                    "notes": raw_json.get("extracted_notes_and_disclosures", [])
                },
                "currency": raw_json.get("metadata", {}).get("company", {}).get("currency", "INR"),
                "scale": raw_json.get("metadata", {}).get("company", {}).get("scale", "Crores"),
                "multiplier": raw_json.get("metadata", {}).get("company", {}).get("multiplier", 10000000.0),
                "total_pages": 1,
                "source_file": filename
            }

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        statements_result: Dict[str, Any] = {
            "balance_sheet": {},
            "income_statement": {},
            "cash_flow_statement": {},
            "notes": []
        }

        curr, sc, mult = NumberParser.detect_currency_and_scale(content[:1500])

        # Split content into major sections by markdown headers or blank lines
        sections = re.split(r"\n(?=#{1,3}\s+|\b(?:BALANCE SHEET|STATEMENT OF PROFIT|CASH FLOW|NOTES TO)\b)", content, flags=re.IGNORECASE)

        for sec_idx, sec_text in enumerate(sections):
            sec_text = sec_text.strip()
            if not sec_text:
                continue

            statement_type = StatementDetector.detect_statement_type(sec_text[:300])
            source_info = {"file": filename, "page": sec_idx + 1, "table_index": 0}

            if statement_type in ["balance_sheet", "income_statement", "cash_flow_statement"]:
                # Parse markdown table or tab/space delimited table
                lines = sec_text.split("\n")
                table_rows: List[List[str]] = []
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("|---") or line.startswith("==="):
                        continue
                    if "|" in line:
                        cells = [c.strip() for c in line.split("|") if c.strip() != ""]
                        if cells:
                            table_rows.append(cells)
                    else:
                        cols = re.split(r"\s{2,}|\t", line)
                        if len(cols) >= 2:
                            table_rows.append([c.strip() for c in cols])

                if table_rows:
                    extracted = TableExtractor.parse_table_rows(
                        rows=table_rows,
                        section_name=statement_type,
                        source_info=source_info,
                        default_scale_multiplier=mult
                    )
                    statements_result[statement_type].update(extracted)

            elif statement_type == "notes" or "note" in sec_text[:100].lower():
                # Extract disclosure notes
                note_matches = re.finditer(r"(Note\s*\d+[a-z]?[\s:–—]+[^\n]+)\n(.*?)(?=(?:Note\s*\d+|$))", sec_text, re.DOTALL | re.IGNORECASE)
                has_notes = False
                for nm in note_matches:
                    has_notes = True
                    statements_result["notes"].append({
                        "note_number": nm.group(1).split(":")[0].strip(),
                        "topic": nm.group(1).strip(),
                        "text": nm.group(2).strip()[:500],
                        "source": source_info
                    })
                if not has_notes and len(sec_text) > 30:
                    statements_result["notes"].append({
                        "note_number": f"Note {len(statements_result['notes'])+1}",
                        "topic": sec_text.split("\n")[0][:80],
                        "text": sec_text[:500],
                        "source": source_info
                    })

        return {
            "statements": statements_result,
            "currency": curr,
            "scale": sc,
            "multiplier": mult,
            "total_pages": max(len(sections), 1),
            "source_file": filename
        }
