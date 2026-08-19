"""
Segment 1 Document Processing Pipeline.
Universal Preprocessing & Ingestion Engine for PDF, Excel, CSV, Text/Markdown, and Folders.
Generates standardized financial JSON with frozen Team 1 Quality, Extraction, and RAG Metrics.
"""

import os
import re
import json
import glob
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from .parsers.csv_parser import CSVParser
from .parsers.excel_parser import ExcelParser
from .parsers.pdf_parser import PDFParser
from .parsers.text_parser import TextDocumentParser
from .rag.chunker import DocumentChunker
from .quality.quality_evaluator import QualityEvaluator


class DocumentProcessingPipeline:
    @classmethod
    def process_file_or_directory(
        cls,
        input_path: str,
        company_name: Optional[str] = None,
        cin_or_ticker: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Universal processor supporting:
        - PDF documents (.pdf)
        - Excel workbooks (.xlsx, .xls)
        - CSV single/multi-statement files (.csv)
        - Text / Markdown reports (.txt, .md, .json)
        - Directories / Folders containing multiple financial files
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input path not found: {input_path}")

        # If a directory was provided, process all files inside and merge
        if os.path.isdir(input_path):
            return cls._process_directory(input_path, company_name, cin_or_ticker, industry)

        file_ext = os.path.splitext(input_path)[1].lower()
        file_name = os.path.basename(input_path)

        bs_items: Dict[str, Any] = {}
        is_items: Dict[str, Any] = {}
        cf_items: Dict[str, Any] = {}
        notes_items: List[Dict[str, Any]] = []

        currency = "INR"
        scale = "Crores"
        multiplier = 10000000.0
        page_count = 1
        ocr_quality = 1.0
        file_validity = "VALID_DIGITAL_DOCUMENT"

        # 1. Dispatch parser based on file extension
        if file_ext == ".csv":
            file_validity = "VALID_CSV"
            parsed_data = CSVParser.parse_file(input_path)
            stmt = parsed_data["statement_type"]
            currency, scale, multiplier = parsed_data["currency"], parsed_data["scale"], parsed_data["multiplier"]
            if stmt == "income_statement":
                is_items = parsed_data["items"]
            elif stmt == "cash_flow_statement":
                cf_items = parsed_data["items"]
            else:
                bs_items = parsed_data["items"]

        elif file_ext in [".xlsx", ".xls"]:
            file_validity = "VALID_EXCEL_WORKBOOK"
            parsed_data = ExcelParser.parse_file(input_path)
            stmts = parsed_data["statements"]
            currency, scale, multiplier = parsed_data["currency"], parsed_data["scale"], parsed_data["multiplier"]
            page_count = parsed_data["sheets_analyzed"]
            bs_items = stmts.get("balance_sheet", {})
            is_items = stmts.get("income_statement", {})
            cf_items = stmts.get("cash_flow_statement", {})
            notes_items = stmts.get("notes", [])

        elif file_ext == ".pdf":
            file_validity = "VALID_DIGITAL_PDF"
            ocr_quality = 0.98
            parsed_data = PDFParser.parse_file(input_path)
            stmts = parsed_data["statements"]
            currency, scale, multiplier = parsed_data["currency"], parsed_data["scale"], parsed_data["multiplier"]
            page_count = parsed_data["total_pages"]
            bs_items = stmts.get("balance_sheet", {})
            is_items = stmts.get("income_statement", {})
            cf_items = stmts.get("cash_flow_statement", {})
            notes_items = stmts.get("notes", [])

        elif file_ext in [".txt", ".md", ".json"]:
            file_validity = "VALID_STRUCTURED_TEXT"
            parsed_data = TextDocumentParser.parse_file(input_path)
            stmts = parsed_data["statements"]
            currency, scale, multiplier = parsed_data["currency"], parsed_data["scale"], parsed_data["multiplier"]
            page_count = parsed_data["total_pages"]
            bs_items = stmts.get("balance_sheet", {})
            is_items = stmts.get("income_statement", {})
            cf_items = stmts.get("cash_flow_statement", {})
            notes_items = stmts.get("notes", [])
        else:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported: .pdf, .xlsx, .xls, .csv, .txt, .md, .json")

        return cls._assemble_payload(
            file_name=file_name,
            file_validity=file_validity,
            page_count=page_count,
            ocr_quality=ocr_quality,
            currency=currency,
            scale=scale,
            multiplier=multiplier,
            bs_items=bs_items,
            is_items=is_items,
            cf_items=cf_items,
            notes_items=notes_items,
            company_name=company_name,
            cin_or_ticker=cin_or_ticker,
            industry=industry
        )

    @classmethod
    def _process_directory(
        cls,
        dir_path: str,
        company_name: Optional[str],
        cin_or_ticker: Optional[str],
        industry: Optional[str]
    ) -> Dict[str, Any]:
        """Merges multiple statement files in a folder into a single unified statement."""
        all_files = glob.glob(os.path.join(dir_path, "*.*"))
        valid_extensions = [".pdf", ".xlsx", ".xls", ".csv", ".txt", ".md", ".json"]
        files_to_process = [f for f in all_files if os.path.splitext(f)[1].lower() in valid_extensions]

        bs_items: Dict[str, Any] = {}
        is_items: Dict[str, Any] = {}
        cf_items: Dict[str, Any] = {}
        notes_items: List[Dict[str, Any]] = []

        currency = "INR"
        scale = "Crores"
        multiplier = 10000000.0
        total_pages = 0

        for fpath in files_to_process:
            sub_res = cls.process_file_or_directory(fpath)
            bs_items.update(sub_res.get("balance_sheet", {}))
            is_items.update(sub_res.get("income_statement", {}))
            cf_items.update(sub_res.get("cash_flow_statement", {}))
            notes_items.extend(sub_res.get("extracted_notes_and_disclosures", []))
            total_pages += sub_res.get("team1_metrics", {}).get("document_quality", {}).get("page_count", 1)

        return cls._assemble_payload(
            file_name=os.path.basename(os.path.normpath(dir_path)),
            file_validity="VALID_MULTI_FILE_BUNDLE",
            page_count=max(total_pages, len(files_to_process)),
            ocr_quality=0.98,
            currency=currency,
            scale=scale,
            multiplier=multiplier,
            bs_items=bs_items,
            is_items=is_items,
            cf_items=cf_items,
            notes_items=notes_items,
            company_name=company_name,
            cin_or_ticker=cin_or_ticker,
            industry=industry
        )

    @classmethod
    def _assemble_payload(
        cls,
        file_name: str,
        file_validity: str,
        page_count: int,
        ocr_quality: float,
        currency: str,
        scale: str,
        multiplier: float,
        bs_items: Dict[str, Any],
        is_items: Dict[str, Any],
        cf_items: Dict[str, Any],
        notes_items: List[Dict[str, Any]],
        company_name: Optional[str],
        cin_or_ticker: Optional[str],
        industry: Optional[str]
    ) -> Dict[str, Any]:
        # 1. Identify distinct fiscal periods
        all_periods = set()
        for item_dict in [bs_items, is_items, cf_items]:
            for key, obj in item_dict.items():
                if isinstance(obj, dict) and "values" in obj:
                    all_periods.update(obj["values"].keys())

        period_list = sorted(list(all_periods), reverse=True)
        if not period_list:
            period_list = ["FY2024", "FY2023"]

        period_objects = [
            {
                "period_key": p,
                "label": f"Fiscal Year {p.replace('FY', '')}",
                "is_audited": True
            }
            for p in period_list
        ]

        # 2. RAG Chunking
        rag_output = DocumentChunker.chunk_disclosures(notes_items)

        # 3. Quality & Extraction Evaluation
        quality_eval = QualityEvaluator.evaluate_quality(
            balance_sheet=bs_items,
            income_statement=is_items,
            cash_flow=cf_items,
            notes=notes_items,
            file_validity=file_validity,
            page_count=page_count,
            ocr_quality=ocr_quality,
            currency=currency,
            unit=scale,
            periods=period_list
        )

        inferred_company = company_name
        if not inferred_company and notes_items:
            for n in notes_items:
                t = n.get("text", "")
                m = re.search(r"\b([A-Z][A-Za-z0-9\s,\.&'-]+?\s+(?:Ltd\.?|Limited|Inc\.?|Corp\.?|LLC|Pvt\.?\s*Ltd\.?))\b", t)
                if m:
                    inferred_company = m.group(1).strip()
                    break
        if not inferred_company:
            cleaned_name = file_name.split(".")[0]
            cleaned_name = re.sub(r"_(ALL_PASS|Test|Test_Suite|Clean_Test_Dataset|Finance_Analyzer|Huge_Test_Data).*", "", cleaned_name, flags=re.IGNORECASE)
            inferred_company = cleaned_name.replace("_", " ").title()

        return {
            "metadata": {
                "document_id": f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "source_file": file_name,
                "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                "parser_version": "1.0.0",
                "company": {
                    "name": inferred_company,
                    "cin_or_ticker": cin_or_ticker or "N/A",
                    "industry": industry or "General Industry",
                    "reporting_standard": "Ind AS / IFRS",
                    "statement_type": "Consolidated",
                    "currency": currency,
                    "scale": scale,
                    "multiplier": multiplier
                },
                "periods": period_objects
            },
            "team1_metrics": {
                "document_quality": quality_eval["document_quality"],
                "extraction": quality_eval["extraction"],
                "rag": rag_output["rag_metrics"]
            },
            "rag_chunks": rag_output["chunks"],
            "balance_sheet": bs_items,
            "income_statement": is_items,
            "cash_flow_statement": cf_items,
            "extracted_notes_and_disclosures": notes_items
        }

    # Backward compatibility alias
    @classmethod
    def process_file(cls, *args, **kwargs):
        return cls.process_file_or_directory(*args, **kwargs)

    @classmethod
    def save_output(cls, data: Dict[str, Any], output_path: str) -> None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
