# Decisions Log

Record every important architectural, design, or scope decision here — one entry per decision, newest on top. This is the "why did we do it this way" file.

---

### D-006: Universal Preprocessing Ingestion Pipeline Supporting PDF, Excel, CSV, Text/MD, and Multi-File Bundles
- **Date:** 2026-08-17
- **Status:** Accepted
- **Context:** Financial statements arrive in diverse formats (scanned/digital PDFs, multi-sheet Excel files, isolated CSVs, raw text disclosures, or folders containing multiple reports). The system needed a unified interface.
- **Options considered:**
  1. Separate disjoint scripts for each format requiring the user to specify flags.
  2. Single universal pipeline `process_file_or_directory()` that detects file format, sheet layout, and statement sections automatically.
- **Decision:** Implemented Option 2.
- **Reasoning:** Minimizes integration friction for Segment 2 and downstream consumers; downstream code only interacts with one function and receives identical standardized JSON.
- **Consequences:** Pipeline handles routing, merging multi-file folders, and normalizing scale multipliers uniformly.
- **Owner:** Segment 1 Team

---

### D-005: Dual-Key Structure and Canonical Financial Label Normalization
- **Date:** 2026-08-17
- **Status:** Accepted
- **Context:** Financial reporting uses hundreds of naming variations for identical line items (e.g. "Cash and Bank Balances" vs "Cash and Cash Equivalents"). Segment 2 needs deterministic dictionary keys, while Segment 3 Dashboard needs human-readable original labels.
- **Options considered:**
  1. Keep only raw labels in JSON.
  2. Overwrite everything with normalized snake_case keys and drop raw text.
  3. Provide a structured object with `standard_label`, `raw_labels` list, `values` dict, and `source` metadata under a canonical dictionary key.
- **Decision:** Implemented Option 3 (`{ "trade_receivables": { "standard_label": "Trade Receivables", "raw_labels": ["Sundry Debtors"], "values": { ... }, "source": { ... } } }`).
- **Reasoning:** Allows Segment 2 to run `item["values"]["FY2024"]` without string matching while preserving original names for UI audit trails.
- **Consequences:** Slightly larger JSON payload size in exchange for 100% auditability and zero ambiguity.
- **Owner:** Segment 1 Team

---

### D-004: Multi-Engine PDF Parser with Graceful Fallback
- **Date:** 2026-08-17
- **Status:** Accepted
- **Context:** Different deployment environments may have different PDF libraries installed (`pdfplumber`, `PyMuPDF`/`fitz`, `pypdf`).
- **Options considered:**
  1. Hardcode dependency on a single library.
  2. Dynamic fallback chain: `pdfplumber` (table grid extraction) $\rightarrow$ `pypdf` (text extraction) $\rightarrow$ custom line regex reconstructor.
- **Decision:** Implemented Option 2.
- **Reasoning:** Ensures the system runs out of the box in basic Python environments while automatically upgrading to high-fidelity grid extraction when `pdfplumber`/`pymupdf` are installed.
- **Consequences:** High resilience across diverse runtime environments.
- **Owner:** Segment 1 Team

---

### D-003: Frozen Team 1 Quality, Extraction, and RAG Metric Trees
- **Date:** 2026-08-17
- **Status:** Accepted
- **Context:** Requirements mandated a strictly frozen set of metrics for Team 1 before downstream model ingestion.
- **Options considered:**
  1. Ad-hoc flat metrics dictionary.
  2. Explicit 3-branch tree structure: `DOCUMENT_QUALITY`, `EXTRACTION`, `RAG`.
- **Decision:** Implemented Option 2 matching the exact specification:
  - `DOCUMENT_QUALITY`: `file_validity`, `page_count`, `ocr_quality`, `extraction_completeness`, `missing_sections`, `missing_values`, `currency`, `unit`, `period`.
  - `EXTRACTION`: `balance_sheet_values`, `income_statement_values`, `cash_flow_values`, `disclosure_values`.
  - `RAG`: `chunk_count`, `retrieval_relevance`, `top_k_results`, `source_page_accuracy`, `retrieval_latency`.
- **Reasoning:** Guarantees strict contract adherence across hackathon segments.
- **Consequences:** Evaluators in `quality_evaluator.py` and `chunker.py` directly feed this contract.
- **Owner:** Team Lead & Segment 1 Team

---

### D-002: Multi-Period Values & Line-Item Source Traceability
- **Date:** 2026-08-17
- **Status:** Accepted
- **Context:** Segment 2 requires YoY comparisons and prior-year tie-outs, while Segment 3 AI Dashboard requires page citation and footnote references.
- **Options considered:**
  1. Flat single-year values with separate historical arrays.
  2. Nested `values: { "FY2024": ..., "FY2023": ..., "FY2022": ... }` with per-item `source: { "file": ..., "page": ..., "note_ref": ... }`.
- **Decision:** Implemented Option 2.
- **Reasoning:** Allows vectorized / direct dictionary access across periods (`values["FY2024"] - values["FY2023"]`) while preserving precise page and note links.
- **Consequences:** Standardized across Balance Sheet, Income Statement, and Cash Flow Statement.
- **Owner:** Segment 1 & Segment 2 Teams

---

### D-001: 3-Segment Decoupled Integration via Frozen JSON Schema Contracts
- **Date:** 2026-08-17
- **Status:** Accepted
- **Context:** A 7-person team working across Segment 1 (Doc Processing), Segment 2 (Financial Engine), Segment 3 (AI Dashboard), and Integration/QA risks blocking each other without frozen schemas.
- **Options considered:**
  1. Synchronous development where Segment 2 waits for Segment 1's code.
  2. Contract-first frozen schema development (`financial_data.json` & `review_result.json`) with Pydantic contracts and realistic sample data.
- **Decision:** Implemented Option 2.
- **Reasoning:** All 3 segments can work 100% in parallel against frozen JSON interfaces.
- **Consequences:** Segment 1 focuses purely on ingestion/normalization; Segment 2 focuses purely on mathematical checks & ratios; Segment 3 focuses purely on dashboard & AI prompts.
- **Owner:** Team Architecture / All Leads
