"""
Financial Review Engine Schema Contract (Team 2 Output Contract)
Consumed by Segment 3 (AI + Dashboard) to render metrics, check results, findings, and score.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class LiquidityMetrics(BaseModel):
    current_ratio: float
    quick_ratio: float
    cash_ratio: Optional[float] = None


class LeverageMetrics(BaseModel):
    debt_to_equity: float
    debt_ratio: float
    interest_coverage_ratio: Optional[float] = None


class ProfitabilityMetrics(BaseModel):
    gross_profit_margin_pct: float
    operating_margin_pct: float
    net_profit_margin_pct: float
    return_on_assets_pct: float
    return_on_equity_pct: float


class EfficiencyMetrics(BaseModel):
    asset_turnover_ratio: Optional[float] = None
    receivables_turnover_ratio: Optional[float] = None
    days_sales_outstanding: Optional[float] = None
    inventory_turnover_ratio: Optional[float] = None


class FinancialMetricsGroup(BaseModel):
    liquidity: LiquidityMetrics
    leverage: LeverageMetrics
    profitability: ProfitabilityMetrics
    efficiency: EfficiencyMetrics


class UnusualFluctuationItem(BaseModel):
    metric: str
    current_value: float
    previous_value: float
    change_pct: float
    threshold_pct: float
    severity: str  # HIGH, MEDIUM, LOW, PASSED
    direction: str  # INCREASE, DECREASE
    note: Optional[str] = None


class UnusualGainAnalysis(BaseModel):
    profit_growth_pct: float
    revenue_growth_pct: float
    profit_vs_revenue_divergence_pp: float
    other_income_growth_pct: float
    other_income_to_revenue_pct: float
    total_gain_amount: float
    gain_to_profit_pct: float
    investment_gain: float
    asset_disposal_gain: float
    one_time_gain: float
    divergence_trigger_status: str


class AnalyticalMetricsGroup(BaseModel):
    growth_rates: Dict[str, float]
    unusual_fluctuations: List[UnusualFluctuationItem]
    unusual_gain_analysis: UnusualGainAnalysis


class FindingDetail(BaseModel):
    id: str
    severity: str  # CRITICAL, HIGH, REVIEW, PASSED
    category: str
    title: str
    description: str
    source: Optional[Dict[str, Any]] = None


class FindingsSummary(BaseModel):
    critical: int
    high: int
    review: int
    passed: int
    details: Optional[List[FindingDetail]] = Field(default_factory=list)


class ReviewResultContract(BaseModel):
    metadata: Dict[str, Any]
    financial_metrics: FinancialMetricsGroup
    analytical_metrics: AnalyticalMetricsGroup
    checks: Dict[str, Any]  # 10 check category blocks
    findings: FindingsSummary
    overall_score: float
