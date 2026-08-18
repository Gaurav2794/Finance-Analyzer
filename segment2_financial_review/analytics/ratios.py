"""
Financial Ratios Suite Engine.

Computes 4 key ratio categories:
1. Liquidity: Current Ratio, Quick Ratio
2. Leverage: Debt-to-Equity, Debt Ratio
3. Profitability: Gross Profit Margin, Operating Margin, Net Profit Margin, ROA, ROE
4. Efficiency: Asset Turnover, Inventory Turnover, Receivables Turnover (only when data exists)

Features:
- Prefers average balances (Assets/Equity/Inventory/Receivables) for ROA, ROE, and Turnover when multi-period data is present.
- Pure deterministic calculations using Decimal.
- Never fabricates missing inputs.
- Safe division (returns None / ZERO_DENOMINATOR status on zero denominator).
- Returns formula, numerator, denominator, status, source evidence for each ratio.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})

RatioStatus = Literal["COMPUTED", "NOT_AVAILABLE", "ZERO_DENOMINATOR", "DATA_INSUFFICIENT"]


class SourceTrace(BaseModel):
    """Provenance tracking for line items."""
    model_config = _DECIMAL_CONFIG

    file: Optional[str] = None
    page: Optional[int] = None
    table_index: Optional[int] = None
    note_ref: Optional[str] = None
    raw_label: Optional[str] = None
    bbox: Optional[List[float]] = None


class RatioDetail(BaseModel):
    """Detailed record of a single financial ratio calculation."""
    model_config = _DECIMAL_CONFIG

    ratio_name: str
    canonical_key: str
    category: Literal["Liquidity", "Leverage", "Profitability", "Efficiency"]
    value: Optional[float] = None
    raw_decimal_value: Optional[Decimal] = None
    formula: str
    numerator: Optional[Decimal] = None
    denominator: Optional[Decimal] = None
    numerator_label: str
    denominator_label: str
    period: str
    status: RatioStatus
    source: Optional[SourceTrace] = None
    details: Optional[str] = None


class RatiosResult(BaseModel):
    """Complete output of the Financial Ratios Suite Engine."""
    model_config = _DECIMAL_CONFIG

    period: str
    liquidity: Dict[str, RatioDetail] = Field(default_factory=dict)
    leverage: Dict[str, RatioDetail] = Field(default_factory=dict)
    profitability: Dict[str, RatioDetail] = Field(default_factory=dict)
    efficiency: Dict[str, RatioDetail] = Field(default_factory=dict)
    efficiency_data_sufficient: bool = False
    all_ratios: Dict[str, RatioDetail] = Field(default_factory=dict)
    ratios_computed_count: int = 0
    total_ratios_count: int = 0
    score: float = 0.0
    status: Literal["COMPUTED", "PARTIAL", "NOT_AVAILABLE"]


# ---------------------------------------------------------------------------
# Helper: Safe Decimal extractor
# ---------------------------------------------------------------------------

def _to_decimal(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _find_nested_item(d: Dict[str, Any], key: str, depth: int = 0) -> Optional[Dict[str, Any]]:
    if depth > 3 or not isinstance(d, dict):
        return None
    for k, v in d.items():
        if k == key and isinstance(v, dict):
            return v
        if isinstance(v, dict):
            found = _find_nested_item(v, key, depth + 1)
            if found is not None:
                return found
    return None


def get_value(data: Dict[str, Any], statement: str, key: str, period: str) -> Optional[Decimal]:
    stmt_dict = data.get(statement, {})
    if not isinstance(stmt_dict, dict):
        return None

    item = stmt_dict.get(key)
    if item is None:
        item = _find_nested_item(stmt_dict, key)

    if item is None or not isinstance(item, dict):
        return None

    if "values" not in item:
        for sub_val in item.values():
            if isinstance(sub_val, dict) and "values" in sub_val:
                item = sub_val
                break

    values_dict = item.get("values")
    if not isinstance(values_dict, dict):
        return None

    return _to_decimal(values_dict.get(period))


def get_source(data: Dict[str, Any], statement: str, key: str) -> Optional[SourceTrace]:
    stmt_dict = data.get(statement, {})
    if not isinstance(stmt_dict, dict):
        return None

    item = stmt_dict.get(key)
    if item is None:
        item = _find_nested_item(stmt_dict, key)

    if item is None or not isinstance(item, dict):
        return None

    src = item.get("source")
    if isinstance(src, dict):
        return SourceTrace(
            file=src.get("file"),
            page=src.get("page"),
            table_index=src.get("table_index"),
            note_ref=src.get("note_ref"),
            raw_label=src.get("raw_label") or item.get("standard_label"),
            bbox=src.get("bbox"),
        )
    return None


def get_periods(data: Dict[str, Any]) -> List[str]:
    periods = [p.get("period_key") for p in data.get("metadata", {}).get("periods", []) if isinstance(p, dict) and "period_key" in p]
    if periods:
        return sorted(periods, reverse=True)
    bs = data.get("balance_sheet", {})
    if isinstance(bs, dict):
        for v in bs.values():
            if isinstance(v, dict) and "values" in v and isinstance(v["values"], dict):
                return sorted(list(v["values"].keys()), reverse=True)
    return ["FY_CURRENT"]


# ---------------------------------------------------------------------------
# Master Financial Ratios Engine
# ---------------------------------------------------------------------------

class FinancialRatiosEngine:
    """
    Computes Liquidity, Leverage, Profitability, and Efficiency ratios.
    """

    @classmethod
    def evaluate(
        cls,
        data: Dict[str, Any],
        period: Optional[str] = None,
    ) -> RatiosResult:
        periods = get_periods(data)
        curr = period or (periods[0] if periods else "FY_CURRENT")
        prev = periods[1] if len(periods) > 1 else None

        # ------------------------------------------------------------------
        # 1. Extract Balance Sheet Variables
        # ------------------------------------------------------------------
        tca = get_value(data, "balance_sheet", "total_current_assets", curr)
        tcl = get_value(data, "balance_sheet", "total_current_liabilities", curr)
        inv_curr = get_value(data, "balance_sheet", "inventories", curr)
        inv_prev = get_value(data, "balance_sheet", "inventories", prev) if prev else None
        tr_curr = get_value(data, "balance_sheet", "trade_receivables", curr)
        tr_prev = get_value(data, "balance_sheet", "trade_receivables", prev) if prev else None

        ta_curr = get_value(data, "balance_sheet", "total_assets", curr)
        ta_prev = get_value(data, "balance_sheet", "total_assets", prev) if prev else None

        te_curr = get_value(data, "balance_sheet", "total_equity", curr)
        te_prev = get_value(data, "balance_sheet", "total_equity", prev) if prev else None

        lt_debt = get_value(data, "balance_sheet", "long_term_borrowings", curr)
        st_debt = get_value(data, "balance_sheet", "short_term_borrowings", curr)
        total_debt: Optional[Decimal] = None
        if lt_debt is not None and st_debt is not None:
            total_debt = lt_debt + st_debt
        elif lt_debt is not None:
            total_debt = lt_debt
        elif st_debt is not None:
            total_debt = st_debt
        else:
            total_debt = get_value(data, "balance_sheet", "total_debt", curr)

        # ------------------------------------------------------------------
        # 2. Extract Income Statement Variables
        # ------------------------------------------------------------------
        rev = get_value(data, "income_statement", "revenue_from_operations", curr)
        if rev is None:
            rev = get_value(data, "income_statement", "revenue", curr)
        cogs = get_value(data, "income_statement", "cost_of_materials_consumed", curr)
        if cogs is None:
            cogs = get_value(data, "income_statement", "cogs", curr)
        if cogs is None:
            cogs = get_value(data, "income_statement", "cost_of_goods_sold", curr)
        gp = get_value(data, "income_statement", "gross_profit", curr)
        if gp is None and rev is not None and cogs is not None:
            gp = rev - cogs

        op = get_value(data, "income_statement", "operating_profit", curr)
        if op is None:
            op = get_value(data, "income_statement", "operating_income", curr)
        pat = get_value(data, "income_statement", "profit_for_the_period", curr)
        if pat is None:
            pat = get_value(data, "income_statement", "net_profit", curr)

        # ------------------------------------------------------------------
        # 3. Calculate Averages when multi-period balances are available
        # ------------------------------------------------------------------
        avg_assets = (ta_curr + ta_prev) / Decimal("2") if (ta_curr is not None and ta_prev is not None) else ta_curr
        avg_equity = (te_curr + te_prev) / Decimal("2") if (te_curr is not None and te_prev is not None) else te_curr
        avg_inv = (inv_curr + inv_prev) / Decimal("2") if (inv_curr is not None and inv_prev is not None) else inv_curr
        avg_tr = (tr_curr + tr_prev) / Decimal("2") if (tr_curr is not None and tr_prev is not None) else tr_curr

        # Provenance helpers
        src_tca = get_source(data, "balance_sheet", "total_current_assets")
        src_ta = get_source(data, "balance_sheet", "total_assets")
        src_te = get_source(data, "balance_sheet", "total_equity")
        src_rev = get_source(data, "income_statement", "revenue_from_operations")
        src_pat = get_source(data, "income_statement", "profit_for_the_period")

        liquidity: Dict[str, RatioDetail] = {}
        leverage: Dict[str, RatioDetail] = {}
        profitability: Dict[str, RatioDetail] = {}
        efficiency: Dict[str, RatioDetail] = {}

        # ------------------------------------------------------------------
        # A. LIQUIDITY RATIOS
        # ------------------------------------------------------------------
        # 1. Current Ratio = TCA / TCL
        liquidity["current_ratio"] = cls._calc_ratio(
            ratio_name="Current Ratio",
            canonical_key="current_ratio",
            category="Liquidity",
            formula="Total Current Assets / Total Current Liabilities",
            numerator=tca,
            denominator=tcl,
            numerator_label="Total Current Assets",
            denominator_label="Total Current Liabilities",
            period=curr,
            source=src_tca,
            is_percentage=False,
        )

        # 2. Quick Ratio = (TCA - Inventory) / TCL
        quick_assets = (tca - inv_curr) if (tca is not None and inv_curr is not None) else None
        liquidity["quick_ratio"] = cls._calc_ratio(
            ratio_name="Quick Ratio",
            canonical_key="quick_ratio",
            category="Liquidity",
            formula="(Total Current Assets - Inventories) / Total Current Liabilities",
            numerator=quick_assets,
            denominator=tcl,
            numerator_label="Quick Assets (TCA - Inventory)",
            denominator_label="Total Current Liabilities",
            period=curr,
            source=src_tca,
            is_percentage=False,
        )

        # ------------------------------------------------------------------
        # B. LEVERAGE RATIOS
        # ------------------------------------------------------------------
        # 1. Debt to Equity = Total Debt / Total Equity
        leverage["debt_to_equity"] = cls._calc_ratio(
            ratio_name="Debt-to-Equity",
            canonical_key="debt_to_equity",
            category="Leverage",
            formula="Total Debt / Total Equity",
            numerator=total_debt,
            denominator=te_curr,
            numerator_label="Total Debt",
            denominator_label="Total Equity",
            period=curr,
            source=src_te,
            is_percentage=False,
        )

        # 2. Debt Ratio = Total Debt / Total Assets
        leverage["debt_ratio"] = cls._calc_ratio(
            ratio_name="Debt Ratio",
            canonical_key="debt_ratio",
            category="Leverage",
            formula="Total Debt / Total Assets",
            numerator=total_debt,
            denominator=ta_curr,
            numerator_label="Total Debt",
            denominator_label="Total Assets",
            period=curr,
            source=src_ta,
            is_percentage=False,
        )

        # ------------------------------------------------------------------
        # C. PROFITABILITY RATIOS
        # ------------------------------------------------------------------
        # 1. Gross Profit Margin (%) = GP / Revenue * 100
        profitability["gross_profit_margin"] = cls._calc_ratio(
            ratio_name="Gross Profit Margin",
            canonical_key="gross_profit_margin_pct",
            category="Profitability",
            formula="(Gross Profit / Revenue) * 100",
            numerator=gp,
            denominator=rev,
            numerator_label="Gross Profit",
            denominator_label="Revenue from Operations",
            period=curr,
            source=src_rev,
            is_percentage=True,
        )

        # 2. Operating Margin (%) = OpProfit / Revenue * 100
        profitability["operating_margin"] = cls._calc_ratio(
            ratio_name="Operating Margin",
            canonical_key="operating_margin_pct",
            category="Profitability",
            formula="(Operating Profit / Revenue) * 100",
            numerator=op,
            denominator=rev,
            numerator_label="Operating Profit",
            denominator_label="Revenue from Operations",
            period=curr,
            source=src_rev,
            is_percentage=True,
        )

        # 3. Net Profit Margin (%) = Net Profit / Revenue * 100
        profitability["net_profit_margin"] = cls._calc_ratio(
            ratio_name="Net Profit Margin",
            canonical_key="net_profit_margin_pct",
            category="Profitability",
            formula="(Net Profit / Revenue) * 100",
            numerator=pat,
            denominator=rev,
            numerator_label="Net Profit (PAT)",
            denominator_label="Revenue from Operations",
            period=curr,
            source=src_pat,
            is_percentage=True,
        )

        # 4. ROA (%) = Net Profit / Average Total Assets * 100
        profitability["return_on_assets"] = cls._calc_ratio(
            ratio_name="Return on Assets (ROA)",
            canonical_key="return_on_assets_pct",
            category="Profitability",
            formula="(Net Profit / Average Total Assets) * 100",
            numerator=pat,
            denominator=avg_assets,
            numerator_label="Net Profit (PAT)",
            denominator_label="Average Total Assets" if ta_prev is not None else "Total Assets",
            period=curr,
            source=src_pat,
            is_percentage=True,
        )

        # 5. ROE (%) = Net Profit / Average Total Equity * 100
        profitability["return_on_equity"] = cls._calc_ratio(
            ratio_name="Return on Equity (ROE)",
            canonical_key="return_on_equity_pct",
            category="Profitability",
            formula="(Net Profit / Average Total Equity) * 100",
            numerator=pat,
            denominator=avg_equity,
            numerator_label="Net Profit (PAT)",
            denominator_label="Average Total Equity" if te_prev is not None else "Total Equity",
            period=curr,
            source=src_pat,
            is_percentage=True,
        )

        # ------------------------------------------------------------------
        # D. EFFICIENCY RATIOS (only when sufficient data exists)
        # ------------------------------------------------------------------
        # 1. Asset Turnover = Revenue / Average Total Assets
        efficiency["asset_turnover"] = cls._calc_ratio(
            ratio_name="Asset Turnover",
            canonical_key="asset_turnover",
            category="Efficiency",
            formula="Revenue / Average Total Assets",
            numerator=rev,
            denominator=avg_assets,
            numerator_label="Revenue from Operations",
            denominator_label="Average Total Assets" if ta_prev is not None else "Total Assets",
            period=curr,
            source=src_rev,
            is_percentage=False,
        )

        # 2. Inventory Turnover = COGS / Average Inventories
        efficiency["inventory_turnover"] = cls._calc_ratio(
            ratio_name="Inventory Turnover",
            canonical_key="inventory_turnover",
            category="Efficiency",
            formula="COGS / Average Inventories",
            numerator=cogs,
            denominator=avg_inv,
            numerator_label="Cost of Materials Consumed (COGS)",
            denominator_label="Average Inventories" if inv_prev is not None else "Inventories",
            period=curr,
            source=src_rev,
            is_percentage=False,
        )

        # 3. Receivables Turnover = Revenue / Average Trade Receivables
        efficiency["receivables_turnover"] = cls._calc_ratio(
            ratio_name="Receivables Turnover",
            canonical_key="receivables_turnover",
            category="Efficiency",
            formula="Revenue / Average Trade Receivables",
            numerator=rev,
            denominator=avg_tr,
            numerator_label="Revenue from Operations",
            denominator_label="Average Trade Receivables" if tr_prev is not None else "Trade Receivables",
            period=curr,
            source=src_rev,
            is_percentage=False,
        )

        efficiency_sufficient = all(r.status == "COMPUTED" for r in efficiency.values())

        # Consolidate all ratios
        all_ratios: Dict[str, RatioDetail] = {}
        all_ratios.update(liquidity)
        all_ratios.update(leverage)
        all_ratios.update(profitability)
        all_ratios.update(efficiency)

        computed_count = sum(1 for r in all_ratios.values() if r.status == "COMPUTED")
        total_count = len(all_ratios)
        score = round((computed_count / total_count * 100.0), 2) if total_count > 0 else 0.0

        overall_status: Literal["COMPUTED", "PARTIAL", "NOT_AVAILABLE"] = "COMPUTED"
        if computed_count == 0:
            overall_status = "NOT_AVAILABLE"
        elif computed_count < total_count:
            overall_status = "PARTIAL"

        return RatiosResult(
            period=curr,
            liquidity=liquidity,
            leverage=leverage,
            profitability=profitability,
            efficiency=efficiency,
            efficiency_data_sufficient=efficiency_sufficient,
            all_ratios=all_ratios,
            ratios_computed_count=computed_count,
            total_ratios_count=total_count,
            score=score,
            status=overall_status,
        )

    @classmethod
    def _calc_ratio(
        cls,
        ratio_name: str,
        canonical_key: str,
        category: Literal["Liquidity", "Leverage", "Profitability", "Efficiency"],
        formula: str,
        numerator: Optional[Decimal],
        denominator: Optional[Decimal],
        numerator_label: str,
        denominator_label: str,
        period: str,
        source: Optional[SourceTrace],
        is_percentage: bool = False,
    ) -> RatioDetail:
        if numerator is None or denominator is None:
            missing = []
            if numerator is None:
                missing.append(numerator_label)
            if denominator is None:
                missing.append(denominator_label)
            return RatioDetail(
                ratio_name=ratio_name,
                canonical_key=canonical_key,
                category=category,
                value=None,
                raw_decimal_value=None,
                formula=formula,
                numerator=numerator,
                denominator=denominator,
                numerator_label=numerator_label,
                denominator_label=denominator_label,
                period=period,
                status="NOT_AVAILABLE" if category != "Efficiency" else "DATA_INSUFFICIENT",
                source=source,
                details=f"Missing input: {', '.join(missing)}.",
            )

        if denominator == 0:
            return RatioDetail(
                ratio_name=ratio_name,
                canonical_key=canonical_key,
                category=category,
                value=None,
                raw_decimal_value=None,
                formula=formula,
                numerator=numerator,
                denominator=denominator,
                numerator_label=numerator_label,
                denominator_label=denominator_label,
                period=period,
                status="ZERO_DENOMINATOR",
                source=source,
                details=f"Denominator ({denominator_label}) is zero.",
            )

        raw_val = numerator / denominator
        if is_percentage:
            raw_val = raw_val * Decimal("100")
            float_val = round(float(raw_val), 2)
        else:
            float_val = round(float(raw_val), 4)

        return RatioDetail(
            ratio_name=ratio_name,
            canonical_key=canonical_key,
            category=category,
            value=float_val,
            raw_decimal_value=raw_val,
            formula=formula,
            numerator=numerator,
            denominator=denominator,
            numerator_label=numerator_label,
            denominator_label=denominator_label,
            period=period,
            status="COMPUTED",
            source=source,
            details=f"Computed {ratio_name} = {float_val}{'%' if is_percentage else ''}.",
        )


def run(data: Dict[str, Any], period: Optional[str] = None) -> RatiosResult:
    return FinancialRatiosEngine.evaluate(data, period=period)
