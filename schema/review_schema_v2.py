"""
Financial Review Engine Schema Contract -- VERSION 2 (Team 2 Frozen Output Contract)
======================================================================================
Produced by:  Segment 2 ReviewEngine (Phase 2)
Consumed by:  Segment 3 -- AI Narrative + Dashboard

Four mandatory top-level groups
--------------------------------
  GROUP 1 -- check_results      : CheckResultsGroup
  GROUP 2 -- financial_metrics  : FinancialMetricsGroup
  GROUP 3 -- analytical_metrics : AnalyticalMetricsGroup
  GROUP 4 -- findings_and_score : FindingsAndScore

Design rules (frozen)
---------------------
  1. Pydantic models throughout -- no raw Dict[str, Any] for structured data.
  2. Decimal for every monetary / financial amount; float for ratios & percentages.
  3. Every check result is traceable to SourceTrace when available.
  4. Every FindingDetail carries a mandatory Evidence block.
  5. Missing data -> Optional[X] = None, never silent 0.
     Status literals use "NOT_AVAILABLE" where data is structurally absent.
  6. No LLM, no fabrication, no random values.
  7. All arithmetic is delegated to the engine; the schema is purely declarative.
  8. SourceTrace mirrors financial_schema.SourceTrace for cross-contract compatibility.
  9. Placed alongside review_schema.py (v1) -- does NOT replace it during transition.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ===========================================================================
# 0.  Module-level configuration
# ===========================================================================

# All Decimal values serialise as strings to preserve full precision in JSON.
_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})


# ===========================================================================
# 1.  Shared primitive types
# ===========================================================================

# ---------------------------------------------------------------------------
# Status / direction / severity literals
# ---------------------------------------------------------------------------

CheckStatus = Literal[
    "PASSED",
    "FAILED",
    "SKIPPED",
    "NOT_AVAILABLE",
    "REVIEW_REQUIRED",
    "CRITICAL",
    "REVIEW",
]

TieOutStatus    = Literal["MATCHED", "MISMATCH", "SKIPPED", "NOT_AVAILABLE"]
ReconcileStatus = Literal["RECONCILED", "MISMATCH", "SKIPPED", "NOT_AVAILABLE"]
MatchStatus     = Literal["MATCHED", "MISMATCH", "SKIPPED", "NOT_AVAILABLE"]
Direction       = Literal["INCREASE", "DECREASE", "FLAT", "NOT_AVAILABLE"]
Severity        = Literal["CRITICAL", "HIGH", "REVIEW", "PASSED", "NOT_AVAILABLE"]
AvailabilityStr = Literal["ALL_PRESENT", "PARTIAL", "NONE", "NOT_AVAILABLE"]
DataQualityStr  = Literal["GOOD", "ACCEPTABLE", "POOR", "CRITICAL", "NOT_AVAILABLE"]
ComparisonType  = Literal["CROSS_STATEMENT", "STATEMENT_NOTE", "DISCLOSURE"]
ReviewVerdict   = Literal["CLEAN", "MINOR_ISSUES", "MATERIAL_ISSUES", "CRITICAL"]
Grade           = Literal["A", "B", "C", "D", "F"]


# ---------------------------------------------------------------------------
# SourceTrace -- mirrors financial_schema.SourceTrace exactly
# ---------------------------------------------------------------------------

class SourceTrace(BaseModel):
    """
    Provenance pointer back to the source document.

    Intentionally identical to financial_schema.SourceTrace so that source
    objects extracted in Phase 1 can be forwarded here without transformation.
    """

    model_config = _DECIMAL_CONFIG

    file:        Optional[str]         = None
    page:        Optional[int]         = None
    table_index: Optional[int]         = None
    note_ref:    Optional[str]         = None
    raw_label:   Optional[str]         = None
    bbox:        Optional[List[float]] = None


# ---------------------------------------------------------------------------
# Evidence -- attached to every FindingDetail (mandatory)
# ---------------------------------------------------------------------------

class Evidence(BaseModel):
    """
    Machine-readable evidence block that supports every finding.

    Rules:
    - computed_value / reported_value use Decimal for exact representation.
    - source is optional: set when a Phase 1 SourceTrace is available.
    - raw_context is a free-form human-readable sentence for the AI narrative.
    """

    model_config = _DECIMAL_CONFIG

    computed_value:  Optional[Decimal]     = None
    reported_value:  Optional[Decimal]     = None
    difference:      Optional[Decimal]     = None
    tolerance_used:  Optional[Decimal]     = None
    formula:         Optional[str]         = None
    source:          Optional[SourceTrace] = None
    raw_context:     Optional[str]         = None


# ===========================================================================
# 2.  Review Metadata
# ===========================================================================

class AnalyzedPeriods(BaseModel):
    current_period:  Optional[str] = None
    previous_period: Optional[str] = None
    base_period:     Optional[str] = None


class ReviewMetadata(BaseModel):
    """Identifies this review run; carries over all Phase 1 document identifiers."""

    review_id:        str
    document_id:      str
    source_file:      str
    company_name:     str
    review_timestamp: str           # ISO-8601 UTC string
    engine_version:   str
    analyzed_periods: AnalyzedPeriods


# ===========================================================================
# 3.  GROUP 1 -- CHECK RESULTS
# ===========================================================================

# ---------------------------------------------------------------------------
# 3.1  Mathematical Accuracy
# ---------------------------------------------------------------------------

class MathEquationResult(BaseModel):
    """
    Result of a single accounting equation verification.

    Frozen metrics contributed:
        Total Accuracy, Subtotal Accuracy, Cross-Cast Accuracy,
        Arithmetic Accuracy, Formula Accuracy,
        Balance Sheet Reconciliation, Rounding Difference
    """

    model_config = _DECIMAL_CONFIG

    formula:     str
    lhs_value:   Optional[Decimal] = None
    rhs_value:   Optional[Decimal] = None
    difference:  Optional[Decimal] = None   # abs(lhs - rhs); None when inputs absent
    tolerance:   Decimal           = Decimal("0.01")
    is_balanced: Optional[bool]    = None
    status:      CheckStatus
    source:      Optional[SourceTrace] = None


class MathematicalAccuracyResult(BaseModel):
    """
    Frozen metrics:
        Total Accuracy, Subtotal Accuracy, Cross-Cast Accuracy,
        Arithmetic Accuracy, Formula Accuracy,
        Balance Sheet Reconciliation, Rounding Difference
    """

    model_config = _DECIMAL_CONFIG

    # --- Summary accuracy percentages ---
    total_accuracy_pct:      Optional[float]   = None
    subtotal_accuracy_pct:   Optional[float]   = None
    cross_cast_accuracy_pct: Optional[float]   = None
    arithmetic_accuracy_pct: Optional[float]   = None
    formula_accuracy_pct:    Optional[float]   = None
    rounding_difference:     Optional[Decimal] = None

    # --- Per-equation results ---
    balance_sheet_reconciliation: MathEquationResult
    gross_profit_equation:        MathEquationResult
    operating_income_equation:    MathEquationResult
    net_income_equation:          MathEquationResult

    # --- Check-level summary ---
    score:  float
    status: CheckStatus
    issues: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 3.2  Cash Flow
# ---------------------------------------------------------------------------

class CashFlowResult(BaseModel):
    """
    Frozen metrics:
        Opening Cash, Operating Cash Flow, Investing Cash Flow,
        Financing Cash Flow, Expected Closing Cash, Reported Closing Cash,
        Cash Difference, Cash Reconciliation Status,
        Balance Sheet Cash vs Cash Flow Cash
    """

    model_config = _DECIMAL_CONFIG

    opening_cash:                  Optional[Decimal] = None
    operating_cash_flow:           Optional[Decimal] = None
    investing_cash_flow:           Optional[Decimal] = None
    financing_cash_flow:           Optional[Decimal] = None
    expected_closing_cash:         Optional[Decimal] = None
    reported_closing_cash:         Optional[Decimal] = None
    cash_difference:               Optional[Decimal] = None
    cash_reconciliation_status:    ReconcileStatus
    balance_sheet_cash_vs_cf_cash: MatchStatus

    score:  float
    status: CheckStatus
    issues: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 3.3  Prior Year Tie-Out
# ---------------------------------------------------------------------------

class TieOutLineItem(BaseModel):
    """
    Tie-out result for a single carried-forward balance.

    Frozen metrics (per item):
        Opening Balance, Previous Closing Balance,
        Absolute Difference, Percentage Difference, Tie-Out Status

    Applied to:
        Cash, Debt, Equity, Retained Earnings, Assets, Liabilities,
        and other carried-forward balances.
    """

    model_config = _DECIMAL_CONFIG

    line_item:                str
    balance_item_type:        str
    opening_balance:          Optional[Decimal] = None
    previous_closing_balance: Optional[Decimal] = None
    absolute_difference:      Optional[Decimal] = None
    percentage_difference:    Optional[float]   = None
    tie_out_status:           TieOutStatus
    source:                   Optional[SourceTrace] = None


class PriorYearTieOutResult(BaseModel):
    """Aggregate result for all prior-year tie-out line items."""

    items:         List[TieOutLineItem] = Field(default_factory=list)
    items_checked: int = 0
    items_matched: int = 0
    mismatches:    int = 0
    score:         float
    status:        CheckStatus


# ---------------------------------------------------------------------------
# 3.4  Internal Consistency
# ---------------------------------------------------------------------------

class ConsistencyComparison(BaseModel):
    """
    Single cross-reference check result.

    Frozen metrics:
        Cross-Statement Matches/Mismatches,
        Statement-to-Notes Matches/Mismatches,
        Disclosure Matches/Mismatches
    """

    model_config = _DECIMAL_CONFIG

    check_label:     str
    comparison_type: ComparisonType
    amount_a:        Optional[Decimal]     = None
    amount_b:        Optional[Decimal]     = None
    difference:      Optional[Decimal]     = None
    status:          MatchStatus
    source_a:        Optional[SourceTrace] = None
    source_b:        Optional[SourceTrace] = None


class InternalConsistencyResult(BaseModel):
    """
    Frozen metrics:
        Cross-Statement Matches, Cross-Statement Mismatches,
        Statement to Notes Matches, Statement to Notes Mismatches,
        Disclosure Matches, Disclosure Mismatches
    """

    cross_statement_matches:       int = 0
    cross_statement_mismatches:    int = 0
    statement_to_notes_matches:    int = 0
    statement_to_notes_mismatches: int = 0
    disclosure_matches:            int = 0
    disclosure_mismatches:         int = 0
    comparisons:                   List[ConsistencyComparison] = Field(default_factory=list)
    notes_available:               int = 0
    score:                         float
    status:                        CheckStatus


# ---------------------------------------------------------------------------
# 3.5  Master GROUP 1 container
# ---------------------------------------------------------------------------

class CheckResultsGroup(BaseModel):
    """GROUP 1 -- CHECK RESULTS"""

    mathematical_accuracy: MathematicalAccuracyResult
    cash_flow:             CashFlowResult
    prior_year_tieout:     PriorYearTieOutResult
    internal_consistency:  InternalConsistencyResult


# ===========================================================================
# 4.  GROUP 2 -- FINANCIAL METRICS
# ===========================================================================

# ---------------------------------------------------------------------------
# 4.1  Analytical Comparison (Year-over-Year per metric)
# ---------------------------------------------------------------------------

class MetricComparison(BaseModel):
    """
    YoY comparison record for a single financial metric.

    Frozen fields:
        Current Value, Previous Value, Absolute Change,
        Percentage Change, Direction
    """

    model_config = _DECIMAL_CONFIG

    metric_name:       str
    current_value:     Optional[Decimal] = None
    previous_value:    Optional[Decimal] = None
    absolute_change:   Optional[Decimal] = None
    percentage_change: Optional[float]   = None
    direction:         Direction
    source:            Optional[SourceTrace] = None


class AnalyticalComparisonBlock(BaseModel):
    """
    Frozen metrics -- YoY comparison for every major financial metric:
        Revenue, COGS, Expenses, Gross Profit, Operating Profit,
        Net Profit, Assets, Liabilities, Equity, Cash, Debt
    """

    revenue:          MetricComparison
    cogs:             MetricComparison
    expenses:         MetricComparison
    gross_profit:     MetricComparison
    operating_profit: MetricComparison
    net_profit:       MetricComparison
    assets:           MetricComparison
    liabilities:      MetricComparison
    equity:           MetricComparison
    cash:             MetricComparison
    debt:             MetricComparison


# ---------------------------------------------------------------------------
# 4.2  Financial Ratios
# ---------------------------------------------------------------------------

class LiquidityRatios(BaseModel):
    """Frozen: Current Ratio, Quick Ratio"""
    current_ratio: Optional[float] = None
    quick_ratio:   Optional[float] = None


class LeverageRatios(BaseModel):
    """Frozen: Debt-to-Equity, Debt Ratio"""
    debt_to_equity: Optional[float] = None
    debt_ratio:     Optional[float] = None


class ProfitabilityRatios(BaseModel):
    """Frozen: Gross Profit Margin, Operating Margin, Net Profit Margin, ROA, ROE"""
    gross_profit_margin_pct: Optional[float] = None
    operating_margin_pct:    Optional[float] = None
    net_profit_margin_pct:   Optional[float] = None
    return_on_assets_pct:    Optional[float] = None
    return_on_equity_pct:    Optional[float] = None


class EfficiencyRatios(BaseModel):
    """
    Frozen (populated only when sufficient data exists):
        Asset Turnover, Inventory Turnover, Receivables Turnover

    data_sufficient is an explicit flag -- never silently skipped.
    """
    asset_turnover:       Optional[float] = None
    inventory_turnover:   Optional[float] = None
    receivables_turnover: Optional[float] = None
    data_sufficient:      bool            = False


class RatiosBlock(BaseModel):
    """All four ratio groups for the current reporting period."""
    period:        str
    liquidity:     LiquidityRatios
    leverage:      LeverageRatios
    profitability: ProfitabilityRatios
    efficiency:    EfficiencyRatios
    score:         float
    status:        CheckStatus


# ---------------------------------------------------------------------------
# 4.3  Master GROUP 2 container
# ---------------------------------------------------------------------------

class FinancialMetricsGroup(BaseModel):
    """GROUP 2 -- FINANCIAL METRICS"""
    analytical_comparison: AnalyticalComparisonBlock
    ratios:                RatiosBlock


# ===========================================================================
# 5.  GROUP 3 -- ANALYTICAL METRICS
# ===========================================================================

# ---------------------------------------------------------------------------
# 5.1  Unusual Fluctuation
# ---------------------------------------------------------------------------

class UnusualFluctuationItem(BaseModel):
    """
    Frozen fields (per scanned metric):
        Current, Previous, Change %, Threshold, Severity
    """

    model_config = _DECIMAL_CONFIG

    metric:         str
    current_value:  Optional[Decimal] = None
    previous_value: Optional[Decimal] = None
    change_pct:     Optional[float]   = None
    threshold_pct:  float
    severity:       Severity
    direction:      Direction
    note:           Optional[str]     = None


class UnusualFluctuationResult(BaseModel):
    """Exhaustive sweep of all major line items across all three statements."""
    items:                 List[UnusualFluctuationItem] = Field(default_factory=list)
    total_items_scanned:   int = 0
    high_severity_count:   int = 0
    review_severity_count: int = 0
    flagged_count:         int = 0
    score:                 float
    status:                CheckStatus


# ---------------------------------------------------------------------------
# 5.2  Unusual Gain
# ---------------------------------------------------------------------------

class UnusualGainResult(BaseModel):
    """
    Frozen metrics:
        Profit Growth %, Revenue Growth %, Profit vs Revenue Divergence,
        Other Income Growth %, Other Income / Revenue %,
        Gain Amount, Gain / Profit %,
        Investment Gain, Asset Disposal Gain, One-Time Gain
    """

    model_config = _DECIMAL_CONFIG

    profit_growth_pct:               Optional[float]   = None
    revenue_growth_pct:              Optional[float]   = None
    profit_vs_revenue_divergence_pp: Optional[float]   = None
    other_income_growth_pct:         Optional[float]   = None
    other_income_to_revenue_pct:     Optional[float]   = None
    gain_amount:                     Optional[Decimal] = None
    gain_to_profit_pct:              Optional[float]   = None
    investment_gain:                 Optional[Decimal] = None
    asset_disposal_gain:             Optional[Decimal] = None
    one_time_gain:                   Optional[Decimal] = None
    divergence_trigger_status:       str
    divergence_threshold_pp:         float             = 8.0
    score:                           float
    status:                          CheckStatus


# ---------------------------------------------------------------------------
# 5.3  Related Disclosure
# ---------------------------------------------------------------------------

class RelatedDisclosureResult(BaseModel):
    """
    Frozen metrics:
        Number of Related Parties, Number of Related Transactions,
        Total Related-Party Value, Disclosed Related-Party Value,
        Undisclosed/Mismatched Value, Disclosure Difference,
        Disclosure Consistency %
    """

    model_config = _DECIMAL_CONFIG

    number_of_related_parties:      Optional[int]         = None
    number_of_related_transactions: Optional[int]         = None
    total_related_party_value:      Optional[Decimal]     = None
    disclosed_related_party_value:  Optional[Decimal]     = None
    undisclosed_mismatched_value:   Optional[Decimal]     = None
    disclosure_difference:          Optional[Decimal]     = None
    disclosure_consistency_pct:     Optional[float]       = None
    note_reference:                 Optional[str]         = None
    note_source:                    Optional[SourceTrace] = None
    score:                          float
    status:                         CheckStatus
    issues:                         List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 5.4  Document Quality (consumes Team 1 results -- never re-computes them)
# ---------------------------------------------------------------------------

class DocumentQualityResult(BaseModel):
    """
    Frozen metrics (read directly from team1_metrics):
        Extraction Completeness %, Required Statement Availability,
        Missing Critical Values, Source Coverage %, Data Quality Status
    """
    extraction_completeness_pct:     Optional[float]  = None
    required_statement_availability: AvailabilityStr
    missing_critical_values_count:   Optional[int]    = None
    missing_sections:                List[str]         = Field(default_factory=list)
    source_coverage_pct:             Optional[float]  = None
    data_quality_status:             DataQualityStr
    score:                           float
    status:                          CheckStatus
    issues:                          List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 5.5  Master GROUP 3 container
# ---------------------------------------------------------------------------

class AnalyticalMetricsGroup(BaseModel):
    """GROUP 3 -- ANALYTICAL METRICS"""
    unusual_fluctuation: UnusualFluctuationResult
    unusual_gain:        UnusualGainResult
    related_disclosure:  RelatedDisclosureResult
    document_quality:    DocumentQualityResult


# ===========================================================================
# 6.  GROUP 4 -- FINDINGS + SCORE
# ===========================================================================

class FindingDetail(BaseModel):
    """
    A single auditable finding.

    Rules enforced:
    - evidence is always present (empty Evidence() is allowed, not None).
    - source is set whenever Phase 1 provenance data is available.
    - id follows the pattern "FINDING-NNN" (zero-padded to 3 digits).
    """
    id:          str
    severity:    Severity
    category:    str
    title:       str
    description: str
    evidence:    Evidence
    source:      Optional[SourceTrace] = None


class FindingsSummary(BaseModel):
    critical: int = 0
    high:     int = 0
    review:   int = 0
    passed:   int = 0
    details:  List[FindingDetail] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    """
    Per-check weighted scores for dashboard drilldown.
    None when the check was SKIPPED (excluded from weighted average).
    """
    mathematical_accuracy: Optional[float] = None
    cash_flow:             Optional[float] = None
    prior_year_tieout:     Optional[float] = None
    internal_consistency:  Optional[float] = None
    analytical_comparison: Optional[float] = None
    ratios:                Optional[float] = None
    unusual_fluctuation:   Optional[float] = None
    unusual_gain:          Optional[float] = None
    related_disclosure:    Optional[float] = None
    document_quality:      Optional[float] = None


class FindingsAndScore(BaseModel):
    """
    GROUP 4 -- FINDINGS + SCORE

    Grade mapping (applied by the engine, not the schema):
        90-100 -> A  (CLEAN)
        75-89  -> B  (MINOR_ISSUES)
        60-74  -> C  (MATERIAL_ISSUES)
        < 60   -> D/F (CRITICAL)
    """
    findings:        FindingsSummary
    overall_score:   float
    score_breakdown: ScoreBreakdown
    grade:           Grade
    review_verdict:  ReviewVerdict


# ===========================================================================
# 7.  Root Contract
# ===========================================================================

class ReviewResultContractV2(BaseModel):
    """
    Team 2 Final Output Contract (FROZEN -- v2.0).

    Produced by ReviewEngine.run() -> ReviewEngine.save()
    Consumed by Segment 3 (AI Narrative + Dashboard).

    Four mandatory groups:
        metadata           -- run identity & period info
        check_results      -- GROUP 1 : 4 check-category results
        financial_metrics  -- GROUP 2 : YoY analytical comparison + ratio suite
        analytical_metrics -- GROUP 3 : fluctuation, gain, disclosure, doc quality
        findings_and_score -- GROUP 4 : findings list + score + verdict
    """
    metadata:           ReviewMetadata
    check_results:      CheckResultsGroup
    financial_metrics:  FinancialMetricsGroup
    analytical_metrics: AnalyticalMetricsGroup
    findings_and_score: FindingsAndScore
