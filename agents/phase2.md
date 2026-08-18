# Phase 2 — Segment 2: Financial Review & Rules Engine

Comprehensive documentation of everything built in Phase 2 (Segment 2). This phase consumes `financial_data.json` produced by Phase 1 (Segment 1) and outputs a fully structured `review_result.json` containing 10 check categories, financial ratios, anomaly findings, and an overall score (0–100).

---

## Status: COMPLETE

All 15 components delivered. Test suite T01–T12 written.

---

## Package Structure

```text
segment2_financial_engine/
├── __init__.py
├── src/
│   ├── __init__.py
│   ├── loader.py                    # Safe field accessors & period resolution
│   ├── engine.py                    # Master orchestrator (ReviewEngine)
│   ├── checks/
│   │   ├── __init__.py
│   │   ├── math_accuracy.py         # Check 1 — Core accounting equations
│   │   ├── cash_flow_review.py      # Check 2 — Cash flow reconciliation
│   │   ├── prior_year_tieout.py     # Check 3 — Prior year opening/closing match
│   │   ├── internal_consistency.py  # Check 4 — Cross-statement consistency
│   │   ├── analytical_engine.py     # Check 5 — YoY growth & fluctuations
│   │   ├── ratios.py                # Check 6 — Liquidity/Leverage/Profit/Efficiency
│   │   ├── unusual_fluctuations.py  # Check 7 — HIGH/REVIEW severity flagging
│   │   ├── unusual_gain.py          # Check 8 — Profit vs revenue divergence
│   │   ├── related_disclosure.py    # Check 9 — Related party verification
│   │   └── document_quality_guard.py# Check 10 — Team 1 quality consumer
│   └── aggregator/
│       ├── __init__.py
│       ├── findings_builder.py      # Unified findings aggregator
│       └── scorer.py                # Weighted 0-100 overall scorer
├── tests/
│   └── test_review_engine.py        # 12 test classes (T01-T12)
run_segment2.py                      # CLI entry point
```

---

## Components Built

### 1. loader.py — Financial Data Loader & Helpers

**Purpose:** Reads `financial_data.json` from Phase 1, provides safe field accessors and period resolution for all check modules. Never modifies input data. All accessors return None (not raise) when a field is absent.

**Key Functions:**

| Function | Description |
|---|---|
| `load(path)` | Load JSON from disk |
| `get_periods(data)` | Returns period keys sorted descending (most recent first) |
| `current_and_previous(data)` | Returns `(current, previous, base)` period tuple |
| `get_value(data, statement, key, period)` | Safe typed accessor — supports flat and nested layouts |
| `get_source(data, statement, key)` | Returns source provenance dict for a line item |
| `derive_total_liabilities(data, period)` | `total_assets - total_equity` fallback |
| `derive_gross_profit(data, period)` | `revenue - COGS` fallback |
| `derive_opening_cash(data, curr, prev)` | Priority: explicit key -> BS prior -> CF prior |
| `get_total_debt(data, period)` | `long_term + short_term borrowings` |
| `get_note_by_topic(data, keyword)` | Finds first matching disclosure note |
| `pct_change(current, previous)` | Safe YoY % — returns None on zero base |
| `safe_div(numerator, denominator)` | Safe division — returns None on zero denominator |

**Constants:**
- `TOLERANCE = 0.01` Cr — rounding allowance for all arithmetic checks

---

### 2. Check 1 — math_accuracy.py — Mathematical Accuracy Engine

**Purpose:** Verifies the four fundamental accounting equations. Pure arithmetic, no LLM.

**Equations Verified:**

| # | Formula | Tolerance |
|---|---|---|
| 1 | `Assets = Liabilities + Equity` (Balance Sheet Reconciliation) | 0.01 Cr |
| 2 | `Revenue - COGS = Gross Profit` | 0.01 Cr |
| 3 | `Gross Profit - Operating Expenses = Operating Income` | 0.01 Cr |
| 4 | `Operating Income + Other Income - Finance Costs - Tax = Net Income` | 0.01 Cr |

**Output Keys:** `score`, `status`, `equations`, `subtotal_accuracy_pct`, `cross_cast_accuracy_pct`, `rounding_difference`, `issues`

**Scoring:** `(equations_passed / equations_run) x 100`

---

### 3. Check 2 — cash_flow_review.py — Cash Flow Reconciliation Engine

**Purpose:** Verifies cash flow statement arithmetic and cross-checks with Balance Sheet.

**Checks Performed:**
- **Check A:** `Opening Cash + CFO + CFI + CFF = Closing Cash`
- **Check B:** `BS Cash (closing) == CF Statement Cash (closing)`

**Opening Cash Priority:** Explicit CFS key -> BS cash of prior period -> CF closing of prior period

**Output Keys:** `score`, `status`, `opening_cash`, `operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow`, `expected_closing_cash`, `reported_closing_cash`, `cash_difference`, `cash_reconciliation_status`, `bs_cash_vs_cf_cash_status`, `issues`

**Status Values:** `RECONCILED` | `MISMATCH` | `SKIPPED` | `MATCHED`

---

### 4. Check 3 — prior_year_tieout.py — Prior Year Tie-Out Engine

**Purpose:** Confirms that the opening balance of the current year equals the closing balance of the prior year for key line items.

**Line Items Checked:** `total_assets`, `total_equity`, `cash_and_cash_equivalents`, `trade_receivables`, `inventories`

**Output Keys:** `score`, `status`, `items` (each item: `line_item`, `current_opening`, `prior_closing`, `difference`, `tie_out_status`)

**Status Values per Item:** `MATCHED` | `MISMATCH` | `SKIPPED`

---

### 5. Check 4 — internal_consistency.py — Cross-Statement Consistency Engine

**Purpose:** Cross-validates figures that appear in multiple statements to detect internal contradictions.

**Cross-Checks Performed:**
- Net Income on Income Statement vs Net Income on Cash Flow Statement
- BS Cash vs CFS Closing Cash
- Prior period retained earnings continuity

**Output Keys:** `score`, `status`, `comparisons` (list), `cross_statement_mismatches`

---

### 6. Check 5 — analytical_engine.py — Analytical YoY Growth Engine

**Purpose:** Computes year-over-year growth rates and flags statistically unusual fluctuations.

**Growth Rates Computed:** `revenue_growth_pct`, `gross_profit_growth_pct`, `operating_profit_growth_pct`, `net_profit_growth_pct`, `total_assets_growth_pct`

**Output Keys:** `score`, `status`, `growth_rates`, `unusual_fluctuations`

---

### 7. Check 6 — ratios.py — Financial Ratios Suite

**Purpose:** Computes all four industry-standard ratio groups for the current reporting period using `safe_div` (no crash on zero denominators). Total: 15 ratios.

**Ratios Computed:**

| Group | Ratios |
|---|---|
| **Liquidity** | Current Ratio, Quick Ratio, Cash Ratio |
| **Leverage** | Debt-to-Equity, Debt Ratio, Interest Coverage Ratio |
| **Profitability** | Gross Margin %, Operating Margin %, Net Margin %, ROA %, ROE % |
| **Efficiency** | Asset Turnover, Receivables Turnover, Days Sales Outstanding (DSO), Inventory Turnover |

**Scoring:** `(computed_ratios / 15) x 100`

---

### 8. Check 7 — unusual_fluctuations.py — Unusual Fluctuation & Severity Classifier

**Purpose:** Detects large YoY swings in key financial line items and assigns severity.

**Severity Thresholds:**
- `HIGH` — change > 50% YoY
- `REVIEW` — change between 25–50% YoY
- `PASSED` — change <= 25% YoY

**Output Keys:** `score`, `status`, `items` (each item: `metric`, `current_value`, `previous_value`, `change_pct`, `direction`, `severity`)

---

### 9. Check 8 — unusual_gain.py — Unusual Gain & Non-Operational Divergence Engine

**Purpose:** Detects when profit growth significantly outpaces revenue growth — a key audit signal for non-operational income, one-time gains, or accounting manipulation.

**Key Metric:** `profit_vs_revenue_divergence_pp` (percentage points)

**Trigger Threshold:** Default `8.0 pp` (configurable via CLI `--divergence-threshold`)

**Output Keys:** `score`, `status`, `revenue_growth_pct`, `profit_growth_pct`, `profit_vs_revenue_divergence_pp`, `divergence_trigger_status`, `reason`

**Status Values:** `NORMAL` | `ELEVATED` | `INSUFFICIENT_DATA`

---

### 10. Check 9 — related_disclosure.py — Related-Party Disclosure Verifier

**Purpose:** Checks whether related-party disclosures exist in extracted notes and assesses completeness.

**Checks:**
- Presence of related-party note in `extracted_notes_and_disclosures`
- Content quality — detects vague or incomplete disclosures

**Output Keys:** `score`, `status`, `note_found`, `note_source`, `issues`

**Status Values:** `PASSED` | `REVIEW` | `SKIPPED`

---

### 11. Check 10 — document_quality_guard.py — Document Quality Consumer

**Purpose:** Consumes Team 1's `team1_metrics` block to gate the review on document quality.

**Checks Performed:**
- `extraction_completeness_pct` — flags if below threshold
- OCR quality signal
- Missing section detection

**Output Keys:** `score`, `status`, `extraction_completeness_pct`, `issues`

**Status Values:** `PASSED` | `REVIEW` | `CRITICAL`

---

### 12. findings_builder.py — Unified Findings Aggregator

**Purpose:** Aggregates results from all 10 checks into a single, de-duplicated findings block with unique IDs (FINDING-001, FINDING-002, ...).

**Severity Mapping:**

| Finding Type | Severity |
|---|---|
| Math equation mismatch (delta > 0.01 Cr) | HIGH |
| Cash flow reconciliation mismatch | HIGH |
| Prior year tie-out mismatch | HIGH |
| Cross-statement mismatch | HIGH |
| YoY fluctuation > 50% | HIGH |
| YoY fluctuation 25-50% | REVIEW |
| Profit/revenue divergence triggered | REVIEW |
| Related disclosure concern | REVIEW |
| Document quality critical | CRITICAL |
| All clear | PASSED |

---

### 13. scorer.py — Weighted Overall Scorer

**Purpose:** Computes the final overall review score (0–100) by weighted average of all 10 check scores. SKIPPED checks are excluded from the denominator.

**Weight Table:**

| Check | Weight |
|---|---|
| Mathematical Accuracy | 20% |
| Cash Flow Reconciliation | 15% |
| Prior Year Tie-Out | 10% |
| Internal Consistency | 10% |
| Analytical Metrics | 10% |
| Financial Ratios | 10% |
| Unusual Fluctuations | 10% |
| Unusual Gain Analysis | 5% |
| Related Disclosure | 5% |
| Document Quality | 5% |
| **Total** | **100%** |

---

### 14. engine.py — Master Review Orchestrator (ReviewEngine)

**Purpose:** Wires all 10 checks, findings builder, and scorer into one `ReviewEngine` class. Engine Version: `2.0.0`.

**API:**
```python
from segment2_financial_engine.src.engine import ReviewEngine

result = ReviewEngine.run("outputs/financial_data.json")
ReviewEngine.save(result, "outputs/review_result.json")
```

**Top-Level Output Keys:** `metadata`, `financial_metrics`, `analytical_metrics`, `checks`, `findings`, `overall_score`

---

### 15. run_segment2.py — CLI Runner

**Purpose:** Command-line entry point for running the full Segment 2 review pipeline with coloured console output.

**Usage:**
```bash
# Default
python run_segment2.py

# Explicit paths
python run_segment2.py --input outputs/financial_data.json --output outputs/review_result.json

# Verbose debug logging
python run_segment2.py --input outputs/financial_data.json --output outputs/review_result.json --verbose

# Custom divergence threshold
python run_segment2.py --input outputs/financial_data.json --output outputs/review_result.json --divergence-threshold 10.0
```

**CLI Options:**

| Option | Default | Description |
|---|---|---|
| `--input / -i` | `outputs/financial_data.json` | Input Phase 1 JSON |
| `--output / -o` | `outputs/review_result.json` | Output review JSON |
| `--verbose / -v` | false | Enable DEBUG logging |
| `--divergence-threshold` | 8.0 | Profit vs revenue divergence threshold (pp) |

**Console Output:** ANSI-coloured box showing overall score, status, integrity flag, finding counts, and per-category scores.

---

## Test Suite — test_review_engine.py

12 test classes covering every module.

| ID | Test Class | What It Tests |
|---|---|---|
| T01 | `T01_Loader` | Period resolution, safe field access, derived helpers, `pct_change`, `safe_div` |
| T02 | `T02_MathAccuracy` | Required output keys, score range, BS reconciliation key present, sample data passes |
| T03 | `T03_CashFlowReview` | Required keys, cash reconciliation status, BS/CF cash match |
| T04 | `T04_PriorYearTieOut` | Items list present, all items have valid tie_out_status |
| T05 | `T05_InternalConsistency` | Comparisons list present, zero cross-statement mismatches on sample |
| T06 | `T06_AnalyticalEngine` | Growth rate keys present, revenue growth positive for sample |
| T07 | `T07_Ratios` | All four ratio groups present, current ratio > 0, ROE > 0 |
| T08 | `T08_UnusualFluctuations` | Items is list, severity values in {HIGH, REVIEW, PASSED} |
| T09 | `T09_UnusualGain` | `divergence_trigger_status` present and valid, divergence_pp not None |
| T10 | `T10_DocumentQualityGuard` | `extraction_completeness_pct` present, sample data not CRITICAL |
| T11 | `T11_EngineEndToEnd_Sample` | Full run on `sample_financial_data.json` — all keys, score 0–100, findings valid |
| T12 | `T12_EngineEndToEnd_RealOutput` | Full run on real `outputs/financial_data.json` (skipped if file absent) |

**Run Tests:**
```bash
python -m unittest segment2_financial_engine/tests/test_review_engine.py
```

---

## Data Flow

```
financial_data.json  (Phase 1 output)
        |
        v
   loader.py           <-- Safe accessors, period resolution, arithmetic helpers
        |
        |---> math_accuracy.py          --> equations dict + score
        |---> cash_flow_review.py       --> reconciliation status + score
        |---> prior_year_tieout.py      --> items list + score
        |---> internal_consistency.py   --> comparisons list + score
        |---> analytical_engine.py      --> growth rates + score
        |---> ratios.py                 --> 4 ratio groups + score
        |---> unusual_fluctuations.py   --> flagged items + score
        |---> unusual_gain.py           --> divergence status + score
        |---> related_disclosure.py     --> disclosure status + score
        |---> document_quality_guard.py --> quality gate + score
                    |
                    v
           findings_builder.py  <-- Unified CRITICAL/HIGH/REVIEW/PASSED finding list
           scorer.py            <-- Weighted average 0-100
                    |
                    v
          ReviewEngine.run()    --> ReviewResultContract dict
                    |
                    v
        review_result.json      (Phase 3 input)
```

---

## Definition of Done (All Met)

- [x] Set up `segment2_financial_engine/` package structure
- [x] Check 1 — Mathematical Accuracy Engine (`math_accuracy.py`) — 4 equations
- [x] Check 2 — Cash Flow Reconciliation Engine (`cash_flow_review.py`) — 2 sub-checks
- [x] Check 3 — Prior Year Tie-Out Engine (`prior_year_tieout.py`) — 5 line items
- [x] Check 4 — Internal Consistency Engine (`internal_consistency.py`)
- [x] Check 5 — Analytical YoY Growth Engine (`analytical_engine.py`)
- [x] Check 6 — Financial Ratios Suite (`ratios.py`) — 15 ratios across 4 groups
- [x] Check 7 — Unusual Fluctuation Classifier (`unusual_fluctuations.py`) — HIGH/REVIEW/PASSED
- [x] Check 8 — Unusual Gain Detector (`unusual_gain.py`) — divergence trigger
- [x] Check 9 — Related-Party Disclosure Verifier (`related_disclosure.py`)
- [x] Check 10 — Document Quality Guard (`document_quality_guard.py`)
- [x] Findings Builder (`findings_builder.py`) — unified, de-duplicated aggregation
- [x] Weighted Scorer (`scorer.py`) — 0-100 with SKIPPED exclusion
- [x] Master Review Engine (`engine.py`) — ReviewEngine.run() + ReviewEngine.save()
- [x] CLI Runner (`run_segment2.py`) — all flags, coloured console output
- [x] Test Suite — 12 test classes T01-T12
- [x] Output conforms to frozen `ReviewResultContract` (`schema/review_schema.py`)
- [x] Compatible with both `sample_financial_data.json` and real Phase 1 outputs

---

## Dependencies

| Depends On | Why |
|---|---|
| Phase 1 output (`financial_data.json`) | All 10 checks read from this frozen contract |
| `schema/review_schema.py` | `ReviewResultContract` defines the output shape |
| `schema/financial_schema.py` | Defines canonical key names used by all checks |

---

## Next: Phase 3 — Segment 3: AI Narrative & Interactive Dashboard

Phase 3 will consume both `financial_data.json` and `review_result.json` to:

1. **LLM Prompt Engine** — Generate AI-written executive summaries and anomaly explanations
2. **Interactive Dashboard** — Executive Scorecard, 3-Statement Explorer, 10 Check Results, Anomaly Findings
3. **Source Citation Drawer** — Link every number directly to its PDF page / footnote reference
