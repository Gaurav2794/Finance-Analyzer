"""
Excel Financial Statement Parser.
Reads multi-sheet Excel workbooks (.xlsx, .xls) using pandas/openpyxl,
classifies sheets by statement type, and extracts structured items across periods.
"""

import os
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from ..extraction.statement_detector import StatementDetector
from ..extraction.table_extractor import TableExtractor
from ..normalization.number_parser import NumberParser


def _evaluate_cell_formula(
    formula: Any,
    rows: List[List[Any]],
    all_sheets: Optional[Dict[str, List[List[Any]]]] = None,
    depth: int = 0,
    cur_row_idx: Optional[int] = None,
    cur_col_idx: Optional[int] = None
) -> Optional[float]:
    """Safely evaluate Excel formula expressions like =B6+B7, =SUM(B9:B14), =B8-B15."""
    if depth > 10:
        return None
    if not isinstance(formula, str) or not formula.startswith("="):
        return None
    f = formula[1:].strip()

    # 1. SUM range: e.g. SUM(B9:B14)
    m_sum = re.match(r"^SUM\(([A-Z])(\d+):([A-Z])(\d+)\)$", f, re.IGNORECASE)
    if m_sum:
        col_letter, r_start, _, r_end = m_sum.groups()
        col_idx = ord(col_letter.upper()) - ord("A")
        total = 0.0
        for r_idx in range(int(r_start) - 1, int(r_end)):
            # Avoid self-referencing if formula range includes its own cell
            if cur_row_idx is not None and cur_col_idx is not None and r_idx == cur_row_idx and col_idx == cur_col_idx:
                continue
            if r_idx < len(rows) and col_idx < len(rows[r_idx]):
                v = rows[r_idx][col_idx]
                if isinstance(v, (int, float)):
                    total += float(v)
                elif isinstance(v, str) and v.startswith("="):
                    ev = _evaluate_cell_formula(v, rows, all_sheets, depth + 1, r_idx, col_idx)
                    if ev is not None:
                        total += ev
        return total

    # 2. SUM comma list: e.g. SUM(B11,B14,B18)
    m_sum_commas = re.match(r"^SUM\(([A-Z0-9,\s]+)\)$", f, re.IGNORECASE)
    if m_sum_commas:
        cells = m_sum_commas.group(1).split(",")
        total = 0.0
        for cell in cells:
            cell = cell.strip()
            m_c = re.match(r"^([A-Z])(\d+)$", cell, re.IGNORECASE)
            if m_c:
                c_let, r_num = m_c.groups()
                c_idx = ord(c_let.upper()) - ord("A")
                r_idx = int(r_num) - 1
                if cur_row_idx is not None and cur_col_idx is not None and r_idx == cur_row_idx and c_idx == cur_col_idx:
                    continue
                if r_idx < len(rows) and c_idx < len(rows[r_idx]):
                    v = rows[r_idx][c_idx]
                    if isinstance(v, (int, float)):
                        total += float(v)
                    elif isinstance(v, str) and v.startswith("="):
                        ev = _evaluate_cell_formula(v, rows, all_sheets, depth + 1, r_idx, c_idx)
                        if ev is not None:
                            total += ev
        return total

    # 3. Cross-sheet reference: e.g. ='Income Statement'!B18
    m_cross = re.match(r"^'([^']+)'!([A-Z])(\d+)$|^([A-Za-z0-9_\s]+)!([A-Z])(\d+)$", f, re.IGNORECASE)
    if m_cross and all_sheets:
        s_name = m_cross.group(1) or m_cross.group(4)
        c_let = m_cross.group(2) or m_cross.group(5)
        r_num = m_cross.group(3) or m_cross.group(6)
        target_sheet = all_sheets.get(s_name) or all_sheets.get(s_name.strip())
        if target_sheet:
            c_idx = ord(c_let.upper()) - ord("A")
            r_idx = int(r_num) - 1
            if r_idx < len(target_sheet) and c_idx < len(target_sheet[r_idx]):
                v = target_sheet[r_idx][c_idx]
                if isinstance(v, (int, float)):
                    return float(v)
                elif isinstance(v, str) and v.startswith("="):
                    return _evaluate_cell_formula(v, target_sheet, all_sheets, depth + 1, r_idx, c_idx)

    # 4. Simple cell arithmetic: e.g. B6+B7, B8-B15, B6-B7-B8-B9
    def replace_cell(match):
        c_let, r_num = match.groups()
        c_idx = ord(c_let.upper()) - ord("A")
        r_idx = int(r_num) - 1
        if cur_row_idx is not None and cur_col_idx is not None and r_idx == cur_row_idx and c_idx == cur_col_idx:
            return "0.0"
        if r_idx < len(rows) and c_idx < len(rows[r_idx]):
            v = rows[r_idx][c_idx]
            if isinstance(v, (int, float)):
                return str(float(v))
            if isinstance(v, str) and v.startswith("="):
                ev = _evaluate_cell_formula(v, rows, all_sheets, depth + 1, r_idx, c_idx)
                if ev is not None:
                    return str(ev)
        return "0.0"

    expr = re.sub(r"([A-Z])(\d+)", replace_cell, f, flags=re.IGNORECASE)
    if re.match(r"^[\d\s\+\-\*\/\.\(\)]+$", expr):
        try:
            return float(eval(expr))
        except Exception:
            return None
    return None


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

        # Load all sheets raw rows
        all_sheets_rows: Dict[str, List[List[Any]]] = {}
        for sname in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sname, header=None)
            all_sheets_rows[sname] = df.fillna("").values.tolist()

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
            raw_rows = all_sheets_rows.get(sheet_name, [])
            if not raw_rows:
                continue

            # Evaluate any formula cells in rows
            rows: List[List[Any]] = []
            for r_idx, r in enumerate(raw_rows):
                row_evaluated = []
                for c_idx, c in enumerate(r):
                    if isinstance(c, str) and c.startswith("="):
                        evaluated = _evaluate_cell_formula(c, raw_rows, all_sheets_rows, 0, r_idx, c_idx)
                        row_evaluated.append(evaluated if evaluated is not None else c)
                    else:
                        row_evaluated.append(c)
                rows.append(row_evaluated)

            # Detect statement type from sheet name first, then content
            statement_type = StatementDetector.detect_statement_type(sheet_name)
            if not statement_type:
                # Check content only if sheet is not an auxiliary/test sheet
                sheet_text = " ".join([str(cell) for row in rows[:5] for cell in row])
                statement_type = StatementDetector.detect_statement_type(sheet_text)

            # Only default if workbook has a single sheet with no explicit title
            if not statement_type and len(sheet_names) == 1:
                statement_type = "balance_sheet"

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

            if statement_type == "notes":
                # Extract disclosure notes from sheet rows
                for r in rows:
                    non_empty = [str(c).strip() for c in r if str(c).strip() and str(c).strip() != "nan"]
                    if len(non_empty) >= 2:
                        note_label = non_empty[0]
                        topic = non_empty[1] if len(non_empty) > 1 else note_label
                        text_body = " — ".join(non_empty[1:]) if len(non_empty) > 2 else non_empty[-1]
                        if not any(h in note_label.lower() for h in ["particulars", "notes to financial", "evidence and related"]):
                            statements_result["notes"].append({
                                "note_number": note_label,
                                "topic": f"{note_label}: {topic}",
                                "text": text_body,
                                "source": source_info
                            })
            elif statement_type in statements_result and isinstance(statements_result[statement_type], dict):
                extracted_items = TableExtractor.parse_table_rows(
                    rows=rows,
                    section_name=statement_type,
                    source_info=source_info,
                    default_scale_multiplier=detected_multiplier
                )
                statements_result[statement_type].update(extracted_items)

        return {
            "statements": statements_result,
            "currency": detected_currency,
            "scale": detected_scale,
            "multiplier": detected_multiplier,
            "sheets_analyzed": len(sheet_names),
            "source_file": filename
        }
