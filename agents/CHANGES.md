# Changes Log

Record every major change once it's actually implemented — code, schema, architecture, scope. This is the "what actually happened" file, distinct from DECISIONS.md ("why we chose it"). Newest on top.

---

### C-006: Universal Preprocessor, Quality Evaluator & CLI Runner
- **Date:** 2026-08-17
- **Type:** Feature & Infra
- **Related decision:** D-003, D-006
- **What changed:**
  - Implemented `segment1_document_processing/src/pipeline.py` with `process_file_or_directory()` and directory bundle merging.
  - Implemented `segment1_document_processing/src/quality/quality_evaluator.py` evaluating `DOCUMENT_QUALITY` and `EXTRACTION` metrics.
  - Implemented `segment1_document_processing/src/rag/chunker.py` evaluating `RAG` metrics and generating passage chunks.
  - Created `run_segment1.py` CLI runner with formatted console tree output and JSON export.
  - Created `segment1_document_processing/tests/test_pipeline.py` with 5 passing unit tests.
- **Why:** To deliver a complete, executable, and testable Segment 1 pipeline.
- **Impact:** Ready for production ingestion of all financial documents.
- **Status:** Done

---

### C-005: Multi-Format Parsers (PDF, Excel, CSV, Text/Markdown)
- **Date:** 2026-08-17
- **Type:** Feature
- **Related decision:** D-004, D-006
- **What changed:**
  - Implemented `segment1_document_processing/src/parsers/pdf_parser.py` (supporting `pdfplumber`, `PyMuPDF`, `pypdf`).
  - Implemented `segment1_document_processing/src/parsers/excel_parser.py` (multi-sheet tab classification).
  - Implemented `segment1_document_processing/src/parsers/csv_parser.py` (single/multi-statement CSV extraction).
  - Implemented `segment1_document_processing/src/parsers/text_parser.py` (markdown & text statement and note extraction).
  - Implemented `segment1_document_processing/src/extraction/statement_detector.py` and `table_extractor.py`.
- **Why:** To parse raw documents across all four target file formats seamlessly.
- **Impact:** Any file format can now be processed into standard tabular structures.
- **Status:** Done

---

### C-004: Financial Label Mapper with ~80+ Accounting Canonical Keys
- **Date:** 2026-08-17
- **Type:** Feature
- **Related decision:** D-005
- **What changed:**
  - Implemented `segment1_document_processing/src/normalization/label_mapper.py` mapping Balance Sheet, Income Statement, and Cash Flow terminology variations into canonical keys.
- **Why:** Normalize arbitrary accounting terms from Ind AS, IFRS, and US GAAP to standard contract keys.
- **Impact:** Segment 2 rules can safely reference fixed key names.
- **Status:** Done

---

### C-003: Accounting Number, Negative Brackets & Scale Normalizer
- **Date:** 2026-08-17
- **Type:** Feature
- **Related decision:** D-005
- **What changed:**
  - Implemented `segment1_document_processing/src/normalization/number_parser.py` supporting `(1,250)`, `12,50,000`, `₹ 12.5 Cr`, `Nil`, and scale multipliers.
- **Why:** Prevent number formatting errors across Indian/US accounting styles.
- **Impact:** Robust floating-point normalization across all parsers.
- **Status:** Done

---

### C-002: Frozen Sample Contracts (`sample_financial_data.json` & `sample_review_result.json`)
- **Date:** 2026-08-17
- **Type:** Schema & Mock Data
- **Related decision:** D-001, D-002, D-003
- **What changed:**
  - Created `sample_financial_data.json` with 3-statement multi-period data, source annotations, notes, and frozen Team 1 metrics.
  - Created `sample_review_result.json` with 10 check categories, 4 metric groups, findings, and score for Segment 2/3.
- **Why:** Unblock parallel development for all segments.
- **Impact:** Unblocks Segment 2 and Segment 3.
- **Status:** Done

---

### C-001: Formal Pydantic Schema Contracts
- **Date:** 2026-08-17
- **Type:** Schema
- **Related decision:** D-001, D-003
- **What changed:**
  - Created `schema/financial_schema.py` (`FinancialDataContract`).
  - Created `schema/review_schema.py` (`ReviewResultContract`).
- **Why:** Establish programmatic type safety and runtime validation for JSON contracts.
- **Impact:** High reliability across pipeline boundaries.
- **Status:** Done
