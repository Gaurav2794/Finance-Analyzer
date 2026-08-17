# Financial Statement Analyzer & Review Engine

An automated, intelligent financial statement extraction, normalization, and review platform for Hackathon & enterprise analytics.

---

## 🏛️ System Architecture

```text
                               +---------------------------------------------+
                               |     SEGMENT 1: DOCUMENT PROCESSING          |
                               | (PDF / Excel / CSV / Text / MD Ingestion)   |
                               +---------------------------------------------+
                                                     |
                                                     | financial_data.json
                                                     v
                               +---------------------------------------------+
                               |    SEGMENT 2: FINANCIAL REVIEW ENGINE       |
                               | (10 Check Categories, Ratios & Anomalies)   |
                               +---------------------------------------------+
                                                     |
                                                     | review_result.json
                                                     v
                               +---------------------------------------------+
                               |        SEGMENT 3: AI + DASHBOARD            |
                               | (Executive Insights, Auditing & Citing)     |
                               +---------------------------------------------+
```

---

## 🚀 Segment 1: Universal Preprocessor & Extractor

### Key Features
- **Multi-Format Ingestion:** Digital PDFs (`pdfplumber`, `PyMuPDF`, `pypdf`), Multi-sheet Excel workbooks (`.xlsx`, `.xls`), CSVs, and Text/Markdown reports.
- **Accounting Number Normalization:** Converts brackets `(1,250)` to `-1250`, handles Indian notation `12,50,000` and magnitude scale multipliers (`Crores`, `Lakhs`, `Millions`).
- **Label Mapping:** Maps 80+ Ind AS, IFRS, and US GAAP line-item variations into deterministic canonical dictionary keys.
- **Traceability:** Every extracted line item preserves `{ "file": "...", "page": N, "note_ref": "..." }`.
- **Disclosure RAG Chunker:** Indexes footnotes and disclosures into semantic passages with citation tracking.

### Frozen Team 1 Metrics Tree
```text
DOCUMENT_QUALITY
|-- File validity
|-- Page count
|-- OCR quality
|-- Extraction completeness
|-- Missing sections
|-- Missing values
|-- Currency
|-- Unit
+-- Period

EXTRACTION
|-- Balance Sheet values
|-- Income Statement values
|-- Cash Flow values
+-- Disclosure values

RAG
|-- Chunk count
|-- Retrieval relevance
|-- Top-K results
|-- Source/page accuracy
+-- Retrieval latency
```

---

## 📂 Repository Layout

```text
.
├── agents/                           # Persistent memory & project tracking
│   ├── CONTEXT.md                    # System architecture & glossary
│   ├── CHECKLIST.md                  # Task completion checklist
│   ├── DECISIONS.md                  # Logged architectural decisions (D-001 to D-006)
│   ├── CHANGES.md                    # Change history (C-001 to C-006)
│   └── IMPLEMENTATION_PLAN.md        # Multi-phase roadmap & milestones
├── schema/
│   ├── financial_schema.py           # Team 1 Pydantic output contract
│   └── review_schema.py              # Team 2 Pydantic review contract
├── segment1_document_processing/
│   ├── src/
│   │   ├── normalization/            # number_parser.py, label_mapper.py
│   │   ├── extraction/               # statement_detector.py, table_extractor.py
│   │   ├── parsers/                  # pdf_parser.py, excel_parser.py, csv_parser.py, text_parser.py
│   │   ├── rag/                      # chunker.py (RAG indexing)
│   │   ├── quality/                  # quality_evaluator.py (Quality metrics tree)
│   │   └── pipeline.py               # Master universal ingestion orchestrator
│   └── tests/
│       └── test_pipeline.py          # Unit & integration tests
├── sample_data/                      # Test financial files (Excel, CSV, MD)
├── outputs/                          # Generated financial_data.json outputs
├── run_segment1.py                   # CLI entry point
├── sample_financial_data.json        # Reference frozen Team 1 JSON contract
└── sample_review_result.json         # Reference frozen Team 2 JSON contract
```

---

## ⚡ Quick Start

### 1. Installation
```bash
pip install -r requirements.txt # or: pip install pandas openpyxl pdfplumber pymupdf pypdf pydantic
```

### 2. Running Segment 1 Preprocessor
```bash
# Ingest Excel workbook
python run_segment1.py --input sample_data/sample_financials.xlsx --output outputs/financial_data.json

# Ingest CSV financial statement
python run_segment1.py --input sample_data/sample_balance_sheet.csv --output outputs/financial_data.json

# Ingest Markdown / Text report
python run_segment1.py --input sample_data/sample_report.md --output outputs/financial_data.json
```

### 3. Run Unit Tests
```bash
python segment1_document_processing/tests/test_pipeline.py
```
