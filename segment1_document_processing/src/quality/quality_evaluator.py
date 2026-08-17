"""
Team 1 Quality Evaluator.
Strictly implements the frozen Team 1 Metrics Tree:

DOCUMENT_QUALITY
├── File validity
├── Page count
├── OCR quality
├── Extraction completeness
├── Missing sections
├── Missing values
├── Currency
├── Unit
└── Period

EXTRACTION
├── Balance Sheet values
├── Income Statement values
├── Cash Flow values
└── Disclosure values

RAG
├── Chunk count
├── Retrieval relevance
├── Top-K results
├── Source/page accuracy
└── Retrieval latency
"""

from typing import Dict, Any, List


class QualityEvaluator:
    @classmethod
    def evaluate_quality(
        cls,
        balance_sheet: Dict[str, Any],
        income_statement: Dict[str, Any],
        cash_flow: Dict[str, Any],
        notes: List[Dict[str, Any]],
        file_validity: str,
        page_count: int,
        ocr_quality: float,
        currency: str,
        unit: str,
        periods: List[str]
    ) -> Dict[str, Any]:
        # 1. Missing sections detection
        missing_sections = []
        if not balance_sheet or len(balance_sheet) == 0:
            missing_sections.append("Balance Sheet")
        if not income_statement or len(income_statement) == 0:
            missing_sections.append("Income Statement")
        if not cash_flow or len(cash_flow) == 0:
            missing_sections.append("Cash Flow Statement")

        total_extracted_items = len(balance_sheet) + len(income_statement) + len(cash_flow)
        
        # Expected baseline of core line items across the 3 statements
        expected_items = 25
        completeness_pct = min(100.0, round((total_extracted_items / max(expected_items, 1)) * 100, 1))

        # Check for missing/null values
        missing_values_count = 0
        for section in [balance_sheet, income_statement, cash_flow]:
            for key, obj in section.items():
                if isinstance(obj, dict) and "values" in obj:
                    vals = obj["values"]
                    if not vals or all(v is None for v in vals.values()):
                        missing_values_count += 1

        # Build DOCUMENT_QUALITY block
        document_quality = {
            "file_validity": file_validity,
            "page_count": max(page_count, 1),
            "ocr_quality": round(ocr_quality, 3),
            "extraction_completeness": f"{completeness_pct}%",
            "extraction_completeness_pct": completeness_pct,
            "missing_sections": missing_sections,
            "missing_values": missing_values_count,
            "currency": currency,
            "unit": unit,
            "period": periods,
            "data_quality_status": "EXCELLENT" if completeness_pct >= 85 and not missing_sections else ("GOOD" if completeness_pct >= 60 else "NEEDS_REVIEW")
        }

        # Build EXTRACTION block
        extraction = {
            "balance_sheet_values": {
                "count": len(balance_sheet),
                "extracted_keys": list(balance_sheet.keys())
            },
            "income_statement_values": {
                "count": len(income_statement),
                "extracted_keys": list(income_statement.keys())
            },
            "cash_flow_values": {
                "count": len(cash_flow),
                "extracted_keys": list(cash_flow.keys())
            },
            "disclosure_values": {
                "count": len(notes),
                "topics": [n.get("topic", "") for n in notes[:10]]
            }
        }

        return {
            "document_quality": document_quality,
            "extraction": extraction
        }
