# Checklist

Running, living checklist of everything that needs doing. Group by phase/area, check off as completed.

---

## Phase 1: Contract Freezing & Schema Specifications (Segment 1 & 2 Contracts)
- [x] Freeze `financial_data.json` contract with multi-period & source tracking
- [x] Freeze `review_result.json` contract with 10 review metric categories
- [x] Define Pydantic schema model `schema/financial_schema.py`
- [x] Define Pydantic schema model `schema/review_schema.py`
- [x] Provide full sample dataset in `sample_financial_data.json`
- [x] Provide full sample dataset in `sample_review_result.json`

## Phase 2: Segment 1 — Document Processing Pipeline
- [x] Implement accounting number & scale normalizer (`number_parser.py`)
- [x] Implement accounting label mapping engine (`label_mapper.py`)
- [x] Implement statement type detector (`statement_detector.py`)
- [x] Implement table matrix extractor & period aligner (`table_extractor.py`)
- [x] Implement CSV financial parser (`csv_parser.py`)
- [x] Implement multi-sheet Excel workbook parser (`excel_parser.py`)
- [x] Implement digital PDF parser with table/text extraction (`pdf_parser.py`)
- [x] Implement text / markdown / JSON parser (`text_parser.py`)
- [x] Implement disclosure footnote chunker & RAG evaluator (`chunker.py`)
- [x] Implement Team 1 Quality & Extraction evaluator (`quality_evaluator.py`)
- [x] Build master orchestrator `DocumentProcessingPipeline` (`pipeline.py`)
- [x] Build CLI runner `run_segment1.py`
- [x] Write unit & integration test suite (`tests/test_pipeline.py`)
- [x] Verify end-to-end execution on Excel, CSV, and Markdown test data

## Phase 3: Segment 2 — Financial Review & Rules Engine
- [ ] Set up `segment2_financial_engine/` package structure
- [ ] Implement Mathematical Accuracy & Core Equations Engine (`math_accuracy.py`)
  - [ ] Balance Sheet Reconciliation: `Assets = Liabilities + Equity`
  - [ ] `Gross Profit = Revenue - COGS`
  - [ ] `Operating Income = Gross Profit - Operating Expenses`
  - [ ] `Net Income = Operating Income + Other Income - Finance Costs - Tax`
- [ ] Implement Cash Flow Reconciliation Engine (`cash_flow_review.py`)
  - [ ] `Expected Closing Cash = Opening Cash + CFO + CFI + CFF`
  - [ ] Cash difference & BS Cash vs CF Cash verification
- [ ] Implement Prior Year Tie-Out Engine (`prior_year_tieout.py`)
  - [ ] Match opening balances with previous closing balances
- [ ] Implement Internal Consistency & Cross-Statement Engine (`internal_consistency.py`)
- [ ] Implement Analytical Comparison & YoY Growth Engine (`analytical_engine.py`)
- [ ] Implement Financial Ratios Calculator (`ratios.py`) (Liquidity, Leverage, Profitability, Efficiency)
- [ ] Implement Unusual Fluctuation & Severity Classifier (`unusual_fluctuations.py`)
- [ ] Implement Unusual Gain & Divergence Detector (`unusual_gain.py`)
- [ ] Implement Related-Party Disclosure Verifier (`related_disclosure.py`)
- [ ] Implement Document Quality Consumer Gatekeeper (`document_quality_guard.py`)
- [ ] Implement Master Review Engine & Scoring Aggregator (`review_engine.py`)
- [ ] Write unit tests for Segment 2 financial review rules

## Phase 4: Segment 3 — AI Analysis & Dashboard
- [ ] Set up `segment3_ai_dashboard/` package structure
- [ ] Implement LLM Prompt Engine for summarizing findings & explaining anomalies
- [ ] Build interactive financial dashboard (Executive Overview, Statement Explorer, 10 Check Results, Findings)
- [ ] Integrate source citation drawer (highlighting page/note references from JSON)

## Phase 5: Integration, QA & End-to-End Orchestration
- [ ] End-to-end integration runner: `PDF/Excel -> Segment 1 -> Segment 2 -> Segment 3`
- [ ] QA test with real-world corporate annual reports
- [ ] Performance benchmarking & latency optimization

## Dropped
- *(None)*
