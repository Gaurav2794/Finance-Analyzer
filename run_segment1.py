"""
Segment 1 Universal Preprocessor CLI.
Processes PDF, Excel, CSV, Text/Markdown, or directory bundles,
evaluates frozen Team 1 Document Quality, Extraction, and RAG Metrics,
and outputs standardized financial_data.json ready for Segment 2 / Model ingestion.
"""

import argparse
import os
import json
from segment1_document_processing.src.pipeline import DocumentProcessingPipeline


def main():
    parser = argparse.ArgumentParser(description="Segment 1 Document Preprocessing Engine")
    parser.add_argument("--input", "-i", type=str, default="sample_data/sample_financials.xlsx", help="Path to input PDF, Excel (.xlsx/.xls), CSV, or folder")
    parser.add_argument("--output", "-o", type=str, default="outputs/financial_data.json", help="Path to output standardized JSON")
    parser.add_argument("--company", "-c", type=str, default=None, help="Company name override")
    parser.add_argument("--industry", type=str, default=None, help="Industry sector override")
    args = parser.parse_args()

    print("=" * 75)
    print(">>> SEGMENT 1: UNIVERSAL FINANCIAL DOCUMENT PREPROCESSING PIPELINE")
    print("=" * 75)
    print(f"[*] Input Path   : {args.input}")
    print(f"[*] Output Target: {args.output}")

    if not os.path.exists(args.input):
        print(f"[ERROR] Target path not found: {args.input}")
        return

    result = DocumentProcessingPipeline.process_file_or_directory(
        input_path=args.input,
        company_name=args.company,
        industry=args.industry
    )

    DocumentProcessingPipeline.save_output(result, args.output)

    doc_q = result["team1_metrics"]["document_quality"]
    ext_m = result["team1_metrics"]["extraction"]
    rag_m = result["team1_metrics"]["rag"]

    print("\n" + "=" * 75)
    print(">>> TEAM 1 FROZEN METRICS EVALUATION")
    print("=" * 75)
    print("DOCUMENT_QUALITY")
    print(f"|-- File validity           : {doc_q['file_validity']}")
    print(f"|-- Page count              : {doc_q['page_count']}")
    print(f"|-- OCR quality             : {doc_q['ocr_quality']}")
    print(f"|-- Extraction completeness : {doc_q['extraction_completeness']}")
    print(f"|-- Missing sections        : {doc_q['missing_sections'] if doc_q['missing_sections'] else 'None (All Present)'}")
    print(f"|-- Missing values          : {doc_q['missing_values']}")
    print(f"|-- Currency                : {doc_q['currency']}")
    print(f"|-- Unit                    : {doc_q['unit']}")
    print(f"+-- Period                  : {doc_q['period']}")

    print("\nEXTRACTION")
    print(f"|-- Balance Sheet values    : {ext_m['balance_sheet_values']['count']} items extracted")
    print(f"|-- Income Statement values : {ext_m['income_statement_values']['count']} items extracted")
    print(f"|-- Cash Flow values        : {ext_m['cash_flow_values']['count']} items extracted")
    print(f"+-- Disclosure values       : {ext_m['disclosure_values']['count']} notes extracted")

    print("\nRAG")
    print(f"|-- Chunk count             : {rag_m['chunk_count']}")
    print(f"|-- Retrieval relevance     : {rag_m['retrieval_relevance']}")
    print(f"|-- Top-K results           : {rag_m['top_k_results']}")
    print(f"|-- Source/page accuracy    : {rag_m['source_page_accuracy']}")
    print(f"+-- Retrieval latency       : {rag_m['retrieval_latency']}")

    print("=" * 75)
    print(f"[SUCCESS] Output written to: {os.path.abspath(args.output)}")
    print("=" * 75)


if __name__ == "__main__":
    main()
