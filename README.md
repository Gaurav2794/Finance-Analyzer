# Financial Statement Analyzer & Review Engine

> An intelligent, end-to-end pipeline that ingests financial documents (PDF, Excel, CSV, Markdown), normalizes them into a structured JSON contract, runs 10 automated financial review checks, computes ratios, detects anomalies, and produces a scored audit report — all without any LLM.

---

## What Does This Do?

You give it a financial statement (annual report PDF, Excel workbook, CSV export, or Markdown file).  
It gives you back a complete, machine-readable review with:

- Extracted Balance Sheet, Income Statement, and Cash Flow numbers
- 15 financial ratios (Liquidity, Leverage, Profitability, Efficiency)
- Year-over-year growth rates
- Automated checks: math accuracy, cash reconciliation, prior year tie-out, anomaly detection
- A single overall score from 0 to 100
- Every finding tagged CRITICAL / HIGH / REVIEW / PASSED

---

## System Architecture

```
 Your Financial Document (PDF / Excel / CSV / Markdown)
                        |
                        v
 ┌──────────────────────────────────────────────────────┐
 │  SEGMENT 1 — Document Processing Pipeline            │
 │  • Parses PDF, Excel, CSV, Text/MD                   │
 │  • Normalizes accounting numbers & labels            │
 │  • Extracts 3 financial statements                   │
 │  • Chunks footnotes for RAG indexing                 │
 │  • Evaluates document quality metrics                │
 └──────────────────────────────────────────────────────┘
                        |
                  financial_data.json
                        |
                        v
 ┌──────────────────────────────────────────────────────┐
 │  SEGMENT 2 — Financial Review Engine                 │
 │  • 10 automated check categories                     │
 │  • 15 financial ratios across 4 groups               │
 │  • YoY growth & unusual fluctuation detection        │
 │  • Findings aggregator & weighted scorer (0-100)     │
 └──────────────────────────────────────────────────────┘
                        |
                  review_result.json
                        |
                        v
 ┌──────────────────────────────────────────────────────┐
 │  SEGMENT 3 — AI Narrative & Dashboard  [PLANNED]     │
 │  • Executive summary generation (LLM)                │
 │  • Interactive findings dashboard                    │
 │  • Source citation drawer (page/note links)          │
 └──────────────────────────────────────────────────────┘
```

---

## Prerequisites

- **Python 3.10 or higher**
- **pip** (comes with Python)
- Git (to clone the repo)

---

## Installation

**Step 1 — Clone the repository**
```bash
git clone https://github.com/Gaurav2794/Finance-Analyzer.git
cd Finance-Analyzer
```

**Step 2 — (Recommended) Create a virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

**Step 3 — Install dependencies**
```bash
pip install -r requirements.txt
```

That's it. No API keys, no cloud services, no configuration files needed.

---

## Quick Start

### Run Segment 1 — Extract Financial Data

Provide any supported financial document and get a structured JSON output:

```bash
# From an Excel workbook
python run_segment1.py --input sample_data/sample_financials.xlsx --output outputs/financial_data.json

# From a CSV file
python run_segment1.py --input sample_data/sample_balance_sheet.csv --output outputs/financial_data.json

# From a Markdown / Text report
python run_segment1.py --input sample_data/sample_report.md --output outputs/financial_data.json

# From a PDF (digital, not scanned)
python run_segment1.py --input my_annual_report.pdf --output outputs/financial_data.json
```

### Run Segment 2 — Financial Review & Scoring

Takes the `financial_data.json` from Segment 1 and runs all 10 checks:

```bash
# Default (reads from outputs/financial_data.json)
python run_segment2.py

# Explicit paths
python run_segment2.py --input outputs/financial_data.json --output outputs/review_result.json

# With verbose debug logging
python run_segment2.py --input outputs/financial_data.json --output outputs/review_result.json --verbose

# Custom anomaly detection threshold (default: 8.0 percentage points)
python run_segment2.py --input outputs/financial_data.json --output outputs/review_result.json --divergence-threshold 10.0
```

**Console output looks like:**
```
+----------------------------------------------------------+
  TEAM 2 FINANCIAL REVIEW -- RESULTS SUMMARY
+----------------------------------------------------------+
  Document  : DOC-2024-001
  Company   : Acme Corp Ltd.
  Period    : FY2024
+----------------------------------------------------------+
  Overall Score  :  94.5 / 100
  Overall Status :  EXCELLENT
  Integrity Flag :  v None
+----------------------------------------------------------+
  Findings
    CRITICAL : 0
    HIGH     : 0
    REVIEW   : 1
    PASSED   : 16
+----------------------------------------------------------+
```

### Run the Full Pipeline (Segment 1 + Segment 2)

```bash
# One-liner: extract then review
python run_segment1.py --input sample_data/sample_financials.xlsx --output outputs/financial_data.json && python run_segment2.py
```

---

## Running Tests

```bash
# Segment 1 — Document processing tests
python -m unittest segment1_document_processing/tests/test_pipeline.py

# Segment 2 — Financial review engine tests (12 test classes, T01-T12)
python -m unittest segment2_financial_engine/tests/test_review_engine.py

# Run all tests
python -m unittest discover -s . -p "test_*.py" -v
```

---

## What Gets Checked (Segment 2 — 10 Review Categories)

| # | Check | What It Does |
|---|---|---|
| 1 | **Mathematical Accuracy** | Verifies Assets = Liabilities + Equity, Gross Profit, Operating Income, Net Income equations |
| 2 | **Cash Flow Reconciliation** | Opening + CFO + CFI + CFF = Closing Cash; BS Cash == CFS Cash |
| 3 | **Prior Year Tie-Out** | Opening balance of current year == closing balance of prior year |
| 4 | **Internal Consistency** | Cross-checks figures that appear in multiple statements |
| 5 | **Analytical / YoY Growth** | Revenue, profit, and asset growth rates year-over-year |
| 6 | **Financial Ratios** | 15 ratios: Current, Quick, D/E, ROE, ROA, DSO, Inventory Turnover, etc. |
| 7 | **Unusual Fluctuations** | Flags >50% YoY changes as HIGH; 25-50% as REVIEW |
| 8 | **Unusual Gain Detection** | Detects profit growth outpacing revenue growth (audit signal) |
| 9 | **Related-Party Disclosures** | Checks existence and completeness of related-party notes |
| 10 | **Document Quality Gate** | Validates extraction completeness & OCR quality from Segment 1 |

---

## Financial Ratios Computed

| Group | Ratios |
|---|---|
| **Liquidity** | Current Ratio, Quick Ratio, Cash Ratio |
| **Leverage** | Debt-to-Equity, Debt Ratio, Interest Coverage Ratio |
| **Profitability** | Gross Margin %, Operating Margin %, Net Margin %, ROA %, ROE % |
| **Efficiency** | Asset Turnover, Receivables Turnover, Days Sales Outstanding, Inventory Turnover |

---

## Supported Input Formats

| Format | Extension | Notes |
|---|---|---|
| Excel Workbook | `.xlsx`, `.xls` | Multi-sheet; auto-detects Balance Sheet, P&L, Cash Flow tabs |
| CSV | `.csv` | Single or multi-statement CSV exports |
| PDF (Digital) | `.pdf` | Uses `pdfplumber` + `PyMuPDF` fallback; not for scanned/image PDFs |
| Text / Markdown | `.txt`, `.md` | Structured financial reports in plain text |

---

## Output Files

| File | Description |
|---|---|
| `outputs/financial_data.json` | Segment 1 output — normalized 3-statement financial data with source tracking |
| `outputs/review_result.json` | Segment 2 output — 10 check results, ratios, findings, and overall score |
| `sample_financial_data.json` | Reference frozen contract (use to test Segment 2 without running Segment 1) |
| `sample_review_result.json` | Reference frozen review output |

---

## Repository Structure

```
Finance-Analyzer/
├── agents/                              # Project memory & documentation
│   ├── CONTEXT.md                       # Architecture & glossary
│   ├── CHECKLIST.md                     # Task completion tracker
│   ├── DECISIONS.md                     # Architectural decisions log
│   ├── CHANGES.md                       # Change history
│   ├── IMPLEMENTATION_PLAN.md           # Multi-phase roadmap
│   └── phase2.md                        # Phase 2 complete documentation
│
├── schema/
│   ├── financial_schema.py              # Pydantic contract for financial_data.json
│   └── review_schema.py                 # Pydantic contract for review_result.json
│
├── segment1_document_processing/        # SEGMENT 1
│   ├── src/
│   │   ├── normalization/
│   │   │   ├── number_parser.py         # Accounting number normalizer
│   │   │   └── label_mapper.py          # 80+ label → canonical key mapper
│   │   ├── extraction/
│   │   │   ├── statement_detector.py    # Detects statement type from text
│   │   │   └── table_extractor.py       # Matrix extractor & period aligner
│   │   ├── parsers/
│   │   │   ├── pdf_parser.py            # PDF ingestion (pdfplumber + PyMuPDF)
│   │   │   ├── excel_parser.py          # Multi-sheet Excel parser
│   │   │   ├── csv_parser.py            # CSV financial parser
│   │   │   └── text_parser.py           # Markdown / plain text parser
│   │   ├── rag/
│   │   │   └── chunker.py               # Footnote/disclosure RAG chunker
│   │   ├── quality/
│   │   │   └── quality_evaluator.py     # Document quality metrics evaluator
│   │   └── pipeline.py                  # Master ingestion orchestrator
│   └── tests/
│       └── test_pipeline.py             # Segment 1 unit & integration tests
│
├── segment2_financial_engine/           # SEGMENT 2
│   ├── src/
│   │   ├── loader.py                    # Safe field accessors & period resolution
│   │   ├── engine.py                    # ReviewEngine master orchestrator
│   │   ├── checks/
│   │   │   ├── math_accuracy.py         # Check 1: Accounting equations
│   │   │   ├── cash_flow_review.py      # Check 2: Cash flow reconciliation
│   │   │   ├── prior_year_tieout.py     # Check 3: Prior year opening/closing
│   │   │   ├── internal_consistency.py  # Check 4: Cross-statement consistency
│   │   │   ├── analytical_engine.py     # Check 5: YoY growth analysis
│   │   │   ├── ratios.py                # Check 6: 15 financial ratios
│   │   │   ├── unusual_fluctuations.py  # Check 7: HIGH/REVIEW flagging
│   │   │   ├── unusual_gain.py          # Check 8: Profit vs revenue divergence
│   │   │   ├── related_disclosure.py    # Check 9: Related-party notes
│   │   │   └── document_quality_guard.py# Check 10: Quality gate
│   │   └── aggregator/
│   │       ├── findings_builder.py      # Unified findings aggregator
│   │       └── scorer.py                # Weighted 0-100 scorer
│   └── tests/
│       └── test_review_engine.py        # 12 test classes (T01-T12)
│
├── sample_data/                         # Test financial files (Excel, CSV, MD)
├── outputs/                             # Generated JSON outputs (gitignored)
├── run_segment1.py                      # Segment 1 CLI entry point
├── run_segment2.py                      # Segment 2 CLI entry point
├── sample_financial_data.json           # Reference Segment 1 output contract
├── sample_review_result.json            # Reference Segment 2 output contract
└── requirements.txt                     # Python dependencies
```

---

## Scoring System

The overall score (0–100) is a weighted average across all 10 checks:

| Check | Weight |
|---|---|
| Mathematical Accuracy | 20% |
| Cash Flow Reconciliation | 15% |
| Prior Year Tie-Out | 10% |
| Internal Consistency | 10% |
| Analytical / YoY Growth | 10% |
| Financial Ratios | 10% |
| Unusual Fluctuations | 10% |
| Unusual Gain Detection | 5% |
| Related-Party Disclosures | 5% |
| Document Quality | 5% |

> Checks that are SKIPPED (due to missing data) are excluded from the denominator so they do not unfairly penalise the document.

**Score Bands:**

| Score | Status |
|---|---|
| 90–100 | EXCELLENT |
| 75–89 | GOOD |
| 50–74 | ATTENTION REQUIRED |
| 0–49 | HIGH RISK |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'pdfplumber'`**  
Run `pip install -r requirements.txt` from inside the `Finance-Analyzer/` directory.

**`FileNotFoundError: outputs/financial_data.json not found`**  
Run Segment 1 first (`python run_segment1.py ...`) before running Segment 2.

**`git: not recognized`** or wrong git repo errors  
Always run git commands from inside `Finance-Analyzer/`, not the parent folder:
```bash
cd Finance-Analyzer
git status
```

**PDF not extracting correctly**  
This pipeline works best with **digital PDFs** (text-selectable). Scanned image PDFs require an OCR tool (not included) as a pre-processing step.

---

## Roadmap

| Phase | Status | Description |
|---|---|---|
| Phase 1 — Schema & Contracts | ✅ Complete | Frozen JSON contracts, Pydantic models, sample datasets |
| Phase 2 — Segment 1 (Document Processing) | ✅ Complete | PDF/Excel/CSV/MD ingestion, normalization, quality metrics |
| Phase 2 — Segment 2 (Review Engine) | ✅ Complete | 10 checks, 15 ratios, anomaly detection, 0-100 scoring |
| Phase 3 — Segment 3 (AI Dashboard) | 🔄 Planned | LLM summaries, interactive dashboard, citation drawer |
| Phase 4 — End-to-End Integration | 🔄 Planned | Unified pipeline, regression tests, performance benchmarks |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `pandas` | >=2.0.0 | Data manipulation & table extraction |
| `openpyxl` | >=3.1.0 | Excel workbook reading (.xlsx) |
| `pdfplumber` | >=0.11.0 | Primary PDF text & table extraction |
| `pymupdf` | >=1.24.0 | PDF fallback renderer (PyMuPDF / fitz) |
| `pypdf` | >=4.0.0 | PDF metadata & page reading |
| `pydantic` | >=2.0.0 | JSON schema validation (V2 API) |

---

## License

MIT License — free to use, modify, and distribute.
