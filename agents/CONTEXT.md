# Project Context

Fast orientation for anyone (or any agent) starting a session.

---

## What this project is
An automated Financial Statement Analysis and Review Engine that ingests financial documents (PDFs, Excel workbooks, CSVs, Text/MD reports), normalizes raw line items into canonical accounting data (`financial_data.json`), executes 10 comprehensive analytical check categories (`review_result.json`), and feeds an interactive AI-powered dashboard.

## Current state
- **Segment 1 (Document Processing):** COMPLETE & TESTED. Universal ingestion for PDF, Excel, CSV, Text/MD, and folder bundles is implemented with accounting normalizers, RAG chunker, and frozen Team 1 Quality/Extraction/RAG metric evaluators.
- **Segment 2 (Financial Review Engine):** Schema and contract frozen (`sample_review_result.json` & `schema/review_schema.py`). Ready for rule and math engine implementation.
- **Segment 3 (AI + Dashboard):** Contract frozen. Ready for UI and LLM synthesis implementation.

## Tech stack
- **Language:** Python 3.12+
- **Parsing & Ingestion:** `pdfplumber`, `PyMuPDF` (`fitz`), `pypdf`, `pandas`, `openpyxl`
- **Data Validation & Schemas:** `pydantic` (v2)
- **Downstream Review & Analytics (Segment 2):** Python math / rule engines, NumPy / Pandas
- **Dashboard / Frontend (Segment 3):** Web App / Streamlit / React (Tailwind/CSS)
- **OS / Shell:** Windows / PowerShell

## Repo / folder layout
```text
NPN-cog/
├── agents/                           # Cross-session persistent memory & governance
│   ├── CONTEXT.md                    # System overview & fast orientation
│   ├── CHECKLIST.md                  # Task-level completion tracker
│   ├── DECISIONS.md                  # Architectural & technical decisions (D-00X)
│   ├── CHANGES.md                    # Implemented changes history (C-00X)
│   └── IMPLEMENTATION_PLAN.md        # Multi-phase roadmap & milestones
├── schema/
│   ├── financial_schema.py           # Segment 1 output Pydantic contract
│   └── review_schema.py              # Segment 2 output Pydantic contract
├── segment1_document_processing/
│   ├── src/
│   │   ├── normalization/            # number_parser.py, label_mapper.py
│   │   ├── extraction/               # statement_detector.py, table_extractor.py
│   │   ├── parsers/                  # pdf_parser.py, excel_parser.py, csv_parser.py, text_parser.py
│   │   ├── rag/                      # chunker.py (disclosure indexing & RAG metrics)
│   │   ├── quality/                  # quality_evaluator.py (Team 1 quality metrics)
│   │   └── pipeline.py               # Master universal ingestion orchestrator
│   └── tests/                        # test_pipeline.py (unit & integration tests)
├── sample_data/                      # Test CSVs, Excel files, Markdown reports
├── outputs/                          # Generated financial_data.json outputs
├── run_segment1.py                   # Segment 1 CLI runner
├── sample_financial_data.json        # Reference frozen Team 1 JSON contract
└── sample_review_result.json         # Reference frozen Team 2 JSON contract
```

## Key constraints
- **Contract Freezing:** Do not alter the top-level keys of `financial_data.json` or `review_result.json` without updating both Pydantic schemas and logging a decision in `DECISIONS.md`.
- **Boundary Separation:** Segment 1 extracts, cleans, normalizes, and chunks; it does NOT calculate financial correctness (Assets = Liab + Equity, ratios, anomalies). That belongs exclusively to Segment 2.
- **Traceability:** Every extracted financial line item and disclosure note must preserve `{ "file": "...", "page": N, "note_ref": "..." }`.

## Glossary
| Term | Meaning |
|---|---|
| `financial_data.json` | Segment 1 output contract containing normalized 3-statement data, metadata, quality metrics, and RAG chunks. |
| `review_result.json` | Segment 2 output contract containing 10 check category evaluations, financial ratios, analytical growth rates, and scores. |
| `Ind AS / IFRS` | Indian Accounting Standards / International Financial Reporting Standards terminology. |
| `Tie-out` | Validating that opening balances of period $T$ equal closing balances of period $T-1$. |
| `Divergence` | Disconnect between Net Profit Growth % and Revenue Growth % signaling non-operational gains. |

## Where to look for more
- Full decision history → `agents/DECISIONS.md`
- Full change history → `agents/CHANGES.md`
- Roadmap → `agents/IMPLEMENTATION_PLAN.md`
- Active tasks → `agents/CHECKLIST.md`
