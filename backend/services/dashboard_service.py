"""
backend/services/dashboard_service.py

Presentation adapter: maps the authoritative Team 1 / Team 2 JSON schemas
into the shape the React dashboard expects.

Rules:
- NO financial calculations here.
- NO field renaming of source data.
- Values are READ from Team 1/2 outputs and re-organised for the UI.
- If a value is missing: None is passed through and the UI renders "Not available".
- Period keys are resolved dynamically from metadata.periods — never hardcoded.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.services.wp514_service import WP514Service


# ── Period helpers ────────────────────────────────────────────────────────────

def _current_period(fd: Dict[str, Any]) -> str:
    """Return the first period_key from Team 1 metadata (most-recent period)."""
    periods = fd.get("metadata", {}).get("periods", [])
    if periods:
        return periods[0].get("period_key", "")
    return ""


def _previous_period(fd: Dict[str, Any]) -> str:
    periods = fd.get("metadata", {}).get("periods", [])
    if len(periods) >= 2:
        return periods[1].get("period_key", "")
    return ""


def _val(statement: Dict[str, Any], *keys: str, period: str) -> Optional[float]:
    """Extract a value from a statement dict for candidate keys and given period key."""
    if not isinstance(statement, dict):
        return None
    for k in keys:
        entry = statement.get(k, {})
        if isinstance(entry, dict):
            values_map = entry.get("values", {})
            if isinstance(values_map, dict):
                v = values_map.get(period)
                if v is not None:
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        pass
        elif isinstance(entry, (int, float)):
            return float(entry)
    return None


def _growth_pct(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """DO NOT recalculate — growth_pct must come from Team 2."""
    return None


def _get_growth(rr: Dict[str, Any], *canonical_keys: str) -> Optional[float]:
    """Pull growth % from Team 2 analytical_metrics.growth."""
    if not isinstance(rr, dict):
        return None
    for k in canonical_keys:
        try:
            metric = rr["analytical_metrics"]["growth"]["metrics"][k]
            if isinstance(metric, dict):
                v = metric.get("percentage_change")
                if v is not None:
                    return float(v)
        except (KeyError, TypeError):
            pass
        try:
            growth_rates = rr["analytical_metrics"]["growth"]["growth_rates"]
            if isinstance(growth_rates, dict):
                v = growth_rates.get(f"{k}_growth_pct") or growth_rates.get(k)
                if v is not None:
                    return float(v)
        except (KeyError, TypeError):
            pass
    return None


def _get_growth_metric_val(rr: Dict[str, Any], *canonical_keys: str, which: str = "current_value") -> Optional[float]:
    """Pull metric amount from Team 2 analytical_metrics.growth.metrics."""
    if not isinstance(rr, dict):
        return None
    for k in canonical_keys:
        try:
            m = rr["analytical_metrics"]["growth"]["metrics"][k]
            if isinstance(m, dict):
                v = m.get(which)
                if v is not None:
                    return float(v)
        except (KeyError, TypeError):
            pass
    return None


# ── Check score extraction ────────────────────────────────────────────────────

def _check_score(rr: Dict[str, Any], key: str) -> Optional[float]:
    """Extract a score from financial_metrics check block."""
    try:
        block = rr["financial_metrics"][key]
        if isinstance(block, dict):
            s = block.get("score")
            if s is not None:
                return float(s)
    except (KeyError, TypeError):
        pass
    return None


# ── Ratio extraction ──────────────────────────────────────────────────────────

def _ratios(
    rr: Dict[str, Any],
    fd: Optional[Dict[str, Any]] = None,
    period: str = ""
) -> Dict[str, Any]:
    """
    Pull ratios from Team 2 analytical_metrics.ratios with fallback to Team 1 extracted metrics.
    Returns a flat dict matching the UI's RatioTile component.
    """
    r_dict = {}
    all_r = {}
    if isinstance(rr, dict):
        try:
            r_dict = rr.get("analytical_metrics", {}).get("ratios", {}) or {}
            all_r = r_dict.get("all_ratios", {}) or {}
        except (KeyError, TypeError):
            r_dict = {}
            all_r = {}

    bs = (fd.get("balance_sheet", {}) if isinstance(fd, dict) else {})
    is_statement = (fd.get("income_statement", {}) if isinstance(fd, dict) else {})

    def _extract_ratio(canonical: str, *aliases: str, is_percentage: bool = False) -> Optional[float]:
        search_keys = [canonical] + list(aliases)
        # 1. Search in Team 2 all_ratios dict
        for k in search_keys:
            item = all_r.get(k)
            if item is not None:
                if isinstance(item, (int, float)):
                    return round(float(item), 4)
                if isinstance(item, dict):
                    v = item.get("value") or item.get("raw_decimal_value")
                    if v is not None:
                        try:
                            return round(float(v), 4)
                        except (ValueError, TypeError):
                            pass

        # 2. Search in Team 2 ratio categories
        for grp in ["liquidity", "leverage", "profitability", "efficiency"]:
            grp_dict = r_dict.get(grp, {})
            if isinstance(grp_dict, dict):
                for k in search_keys:
                    item = grp_dict.get(k)
                    if item is not None:
                        if isinstance(item, (int, float)):
                            return round(float(item), 4)
                        if isinstance(item, dict):
                            v = item.get("value") or item.get("raw_decimal_value")
                            if v is not None:
                                try:
                                    return round(float(v), 4)
                                except (ValueError, TypeError):
                                    pass

        # 3. Fallback to Team 1 extracted balance sheet / income statement / metrics
        if period:
            for k in search_keys:
                raw_v = _val(bs, k, period=period)
                if raw_v is None:
                    raw_v = _val(is_statement, k, period=period)
                if raw_v is not None:
                    # Normalize raw decimal to percentage if ratio is a percentage
                    if is_percentage and abs(raw_v) <= 1.0 and raw_v != 0:
                        raw_v = raw_v * 100.0
                    return round(float(raw_v), 4)

        return None

    return {
        # Liquidity
        "current_ratio": _extract_ratio("current_ratio", "current"),
        "quick_ratio": _extract_ratio("quick_ratio", "quick"),
        "cash_ratio": _extract_ratio("cash_ratio", "cash"),
        # Leverage
        "debt_to_equity": _extract_ratio("debt_to_equity", "debt_equity"),
        "debt_ratio": _extract_ratio("debt_ratio", "total_debt_ratio"),
        "interest_coverage_ratio": _extract_ratio("interest_coverage_ratio", "interest_coverage"),
        # Profitability
        "gross_profit_margin_pct": _extract_ratio("gross_profit_margin_pct", "gross_profit_margin", "gross_margin", is_percentage=True),
        "operating_margin_pct": _extract_ratio("operating_margin_pct", "operating_margin", is_percentage=True),
        "net_margin_pct": _extract_ratio("net_profit_margin_pct", "net_profit_margin", "net_margin", is_percentage=True),
        "return_on_assets_pct": _extract_ratio("return_on_assets_pct", "return_on_assets", "roa", is_percentage=True),
        "roe_pct": _extract_ratio("return_on_equity_pct", "return_on_equity", "roe", is_percentage=True),
        # Efficiency
        "asset_turnover_ratio": _extract_ratio("asset_turnover_ratio", "asset_turnover"),
        "receivables_turnover_ratio": _extract_ratio("receivables_turnover_ratio", "receivables_turnover"),
        "days_sales_outstanding": _extract_ratio("days_sales_outstanding", "dso"),
        "inventory_turnover_ratio": _extract_ratio("inventory_turnover_ratio", "inventory_turnover"),
    }


# ── Findings adapter ──────────────────────────────────────────────────────────

def _adapt_findings(rr: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return finding detail list from Team 2 findings.details, normalizing id/finding_id."""
    try:
        details = rr["findings"]["details"]
        if isinstance(details, list):
            adapted = []
            for f in details:
                if isinstance(f, dict):
                    item = dict(f)
                    if "id" not in item and "finding_id" in item:
                        item["id"] = item["finding_id"]
                    if "finding_id" not in item and "id" in item:
                        item["finding_id"] = item["id"]
                    adapted.append(item)
            return adapted
    except (KeyError, TypeError):
        pass
    return []


# ── Unusual fluctuations ──────────────────────────────────────────────────────

def _unusual_fluctuations(rr: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        items = rr["analytical_metrics"]["unusual_fluctuation"]["flagged_items"]
        return items if isinstance(items, list) else []
    except (KeyError, TypeError):
        return []


def _unusual_gain(rr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        return rr["analytical_metrics"]["unusual_gain"]
    except (KeyError, TypeError):
        return None


def _growth_rates(rr: Dict[str, Any], fd: Optional[Dict[str, Any]] = None, period: str = "") -> Dict[str, Any]:
    rates = {}
    try:
        metrics = rr.get("analytical_metrics", {}).get("growth", {}).get("metrics", {})
        if isinstance(metrics, dict):
            for k, v in metrics.items():
                if isinstance(v, dict):
                    chg = v.get("percentage_change")
                    if chg is not None:
                        rates[k] = float(chg)
    except (KeyError, TypeError):
        pass

    # Populate explicit growth indicators from growth_rates or Team 1
    rates["revenue"] = rates.get("revenue") or _get_growth(rr, "revenue")
    rates["gross_profit"] = rates.get("gross_profit") or _get_growth(rr, "gross_profit")
    rates["operating_expenses"] = rates.get("operating_expenses") or _get_growth(rr, "operating_expenses", "total_expenses")
    rates["net_profit"] = rates.get("net_profit") or _get_growth(rr, "net_profit", "profit")
    rates["receivables"] = rates.get("receivables") or _get_growth(rr, "receivables", "trade_receivables")
    rates["inventory"] = rates.get("inventory") or _get_growth(rr, "inventory", "inventories")
    rates["finance_costs"] = rates.get("finance_costs") or _get_growth(rr, "finance_costs")
    rates["cash"] = rates.get("cash") or _get_growth(rr, "cash")
    rates["assets"] = rates.get("assets") or _get_growth(rr, "assets")
    rates["debt"] = rates.get("debt") or _get_growth(rr, "debt")
    rates["operating_cash_flow"] = rates.get("operating_cash_flow") or _get_growth(rr, "operating_cash_flow")

    if fd and period:
        bs = fd.get("balance_sheet", {})
        if rates.get("profit") is None:
            rates["profit"] = _val(bs, "profit_growth", period=period)
        if rates.get("receivables") is None:
            rates["receivables"] = _val(bs, "receivables_growth", period=period)
        if rates.get("inventory") is None:
            rates["inventory"] = _val(bs, "inventory_growth", period=period)
        if rates.get("cash") is None:
            rates["cash"] = _val(bs, "cash_growth", period=period)
        if rates.get("assets") is None:
            rates["assets"] = _val(bs, "asset_growth", period=period)
        if rates.get("debt") is None:
            rates["debt"] = _val(bs, "debt_growth", period=period)
        if rates.get("operating_cash_flow") is None:
            rates["operating_cash_flow"] = _val(bs, "net_cash_from_operating_activities", period=period)

    return rates


# ── Main dashboard builder ────────────────────────────────────────────────────

def build_dashboard(
    fd: Dict[str, Any],
    rr: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Construct the presentation-layer dashboard response.
    Reads Team 1 and Team 2 outputs; never calculates financial values.
    """
    curr = _current_period(fd)
    prev = _previous_period(fd)

    meta = fd.get("metadata", {})
    company = meta.get("company", {})
    dq = fd.get("team1_metrics", {}).get("document_quality", {})
    is_statement = fd.get("income_statement", {})
    bs = fd.get("balance_sheet", {})

    findings_summary = rr.get("findings", {})
    findings_details = _adapt_findings(rr)

    # Build extraction result shape (Team 1 data)
    extraction_result = {
        "document_id": meta.get("document_id"),
        "file_name": meta.get("source_file", "Unknown"),
        "company_name": company.get("name"),
        "currency": company.get("currency", "INR"),
        "unit": company.get("scale", "Crores"),
        "scale": company.get("scale", "Crores"),
        "period": {
            "current": curr,
            "previous": prev,
        },
        "periods": meta.get("periods", []),
        "company": company,
        "document_quality": {
            "data_quality_status": dq.get("data_quality_status"),
            "extraction_completeness_pct": dq.get("extraction_completeness_pct"),
            "missing_sections": dq.get("missing_sections", []),
            "missing_values": dq.get("missing_values", 0),
            "unit_mismatch_detected": dq.get("unit_mismatch_detected", False),
            "unit_mismatch_detail": dq.get("unit_mismatch_detail"),
        },
        "balance_sheet": bs,
        "income_statement": is_statement,
        "cash_flow_statement": fd.get("cash_flow_statement", {}),
        "cash_flow": fd.get("cash_flow_statement", {}),
        "extracted_notes": fd.get("extracted_notes_and_disclosures", []),
        "team1_metrics": fd.get("team1_metrics", {}),
    }

    # Helper to resolve core financial line items
    # 1. Revenue
    rev_curr = _val(is_statement, "revenue_from_operations", "revenue", "total_income", period=curr) or _get_growth_metric_val(rr, "revenue", which="current_value")
    rev_prev = _val(is_statement, "revenue_from_operations", "revenue", "total_income", period=prev) or _get_growth_metric_val(rr, "revenue", which="previous_value")

    # 2. Gross Profit
    gp_curr = _val(is_statement, "gross_profit", "gross_income", period=curr) or _get_growth_metric_val(rr, "gross_profit", which="current_value")
    if gp_curr is None:
        try:
            gp_calc = rr["financial_metrics"]["mathematical_accuracy"]["calculations"]["gross_profit"]["calculated_value"]
            if gp_calc is not None:
                gp_curr = float(gp_calc)
        except (KeyError, TypeError, ValueError):
            pass
    if gp_curr is None and rev_curr is not None:
        cogs_curr = _val(is_statement, "cost_of_materials_consumed", "cogs", "cost_of_goods_sold", period=curr)
        if cogs_curr is not None:
            gp_curr = rev_curr - cogs_curr

    gp_prev = _val(is_statement, "gross_profit", "gross_income", period=prev) or _get_growth_metric_val(rr, "gross_profit", which="previous_value")
    if gp_prev is None and rev_prev is not None:
        cogs_prev = _val(is_statement, "cost_of_materials_consumed", "cogs", "cost_of_goods_sold", period=prev)
        if cogs_prev is not None:
            gp_prev = rev_prev - cogs_prev

    # 3. Expenses / Operating Expenses
    exp_curr = (
        _val(is_statement, "total_expenses", "operating_expenses", "total_operating_expenses", period=curr)
        or _get_growth_metric_val(rr, "operating_expenses", "total_expenses", which="current_value")
    )
    exp_prev = (
        _val(is_statement, "total_expenses", "operating_expenses", "total_operating_expenses", period=prev)
        or _get_growth_metric_val(rr, "operating_expenses", "total_expenses", which="previous_value")
    )

    # 4. Operating Profit
    op_curr = _val(is_statement, "operating_profit", "operating_income", "ebit", period=curr) or _get_growth_metric_val(rr, "operating_profit", which="current_value")
    if op_curr is None:
        try:
            op_calc = rr["financial_metrics"]["mathematical_accuracy"]["calculations"]["operating_income"]["calculated_value"]
            if op_calc is not None:
                op_curr = float(op_calc)
        except (KeyError, TypeError, ValueError):
            pass
    if op_curr is None and gp_curr is not None and exp_curr is not None:
        op_curr = gp_curr - exp_curr

    op_prev = _val(is_statement, "operating_profit", "operating_income", "ebit", period=prev) or _get_growth_metric_val(rr, "operating_profit", which="previous_value")
    if op_prev is None and gp_prev is not None and exp_prev is not None:
        op_prev = gp_prev - exp_prev
    if op_prev is None:
        raw_om_p = _val(bs, "operating_margin", period=prev) or _val(is_statement, "operating_margin", period=prev)
        if raw_om_p is not None and rev_prev is not None:
            op_prev = round(raw_om_p * rev_prev if abs(raw_om_p) <= 1.0 else (raw_om_p / 100.0) * rev_prev, 2)

    # 5. Net Profit
    np_curr = _val(is_statement, "profit_for_the_period", "net_profit", "profit_after_tax", "net_income", period=curr) or _get_growth_metric_val(rr, "net_profit", which="current_value")
    if np_curr is None:
        try:
            np_calc = rr["financial_metrics"]["mathematical_accuracy"]["calculations"]["net_income"]["calculated_value"]
            if np_calc is not None:
                np_curr = float(np_calc)
        except (KeyError, TypeError, ValueError):
            pass
    if np_curr is None:
        raw_nm = _val(bs, "net_margin", "profit_for_the_period", period=curr)
        if raw_nm is not None and rev_curr is not None:
            if abs(raw_nm) <= 1.0:
                np_curr = round(raw_nm * rev_curr, 2)
            else:
                np_curr = round((raw_nm / 100.0) * rev_curr, 2)

    np_prev = _val(is_statement, "profit_for_the_period", "net_profit", "profit_after_tax", "net_income", period=prev) or _get_growth_metric_val(rr, "net_profit", which="previous_value")
    if np_prev is None:
        raw_nm_p = _val(bs, "net_margin", "profit_for_the_period", period=prev)
        if raw_nm_p is not None and rev_prev is not None:
            if abs(raw_nm_p) <= 1.0:
                np_prev = round(raw_nm_p * rev_prev, 2)
            else:
                np_prev = round((raw_nm_p / 100.0) * rev_prev, 2)

    # 6. Assets
    ta_curr = _val(bs, "total_assets", "assets", period=curr) or _get_growth_metric_val(rr, "assets", which="current_value")
    if ta_curr is None:
        nca = _val(bs, "total_non_current_assets", "non_current_assets", period=curr)
        ca = _val(bs, "total_current_assets", "current_assets", "other_non_current_assets", period=curr)
        if nca is not None and ca is not None:
            ta_curr = nca + ca
    ta_prev = _val(bs, "total_assets", "assets", period=prev) or _get_growth_metric_val(rr, "assets", which="previous_value")
    if ta_prev is None:
        nca_p = _val(bs, "total_non_current_assets", "non_current_assets", period=prev)
        ca_p = _val(bs, "total_current_assets", "current_assets", "other_non_current_assets", period=prev)
        if nca_p is not None and ca_p is not None:
            ta_prev = nca_p + ca_p

    # 7. Liabilities
    tl_curr = _val(bs, "total_liabilities", "liabilities", period=curr) or _get_growth_metric_val(rr, "liabilities", which="current_value")
    if tl_curr is None:
        ncl = _val(bs, "total_non_current_liabilities", "non_current_liabilities", "other_non_current_liabilities", period=curr)
        cl = _val(bs, "total_current_liabilities", "current_liabilities", period=curr)
        if ncl is not None and cl is not None:
            tl_curr = ncl + cl
    tl_prev = _val(bs, "total_liabilities", "liabilities", period=prev) or _get_growth_metric_val(rr, "liabilities", which="previous_value")
    if tl_prev is None:
        ncl_p = _val(bs, "total_non_current_liabilities", "non_current_liabilities", "other_non_current_liabilities", period=prev)
        cl_p = _val(bs, "total_current_liabilities", "current_liabilities", period=prev)
        if ncl_p is not None and cl_p is not None:
            tl_prev = ncl_p + cl_p

    # 8. Equity
    eq_curr = _val(bs, "total_equity", "equity", "total_shareholders_funds", period=curr) or _get_growth_metric_val(rr, "equity", which="current_value")
    if eq_curr is None:
        sc = _val(bs, "equity_share_capital", "share_capital", period=curr)
        oe = _val(bs, "other_equity", "reserves_and_surplus", period=curr)
        if sc is not None and oe is not None:
            eq_curr = sc + oe
        elif sc is not None:
            eq_curr = sc
    eq_prev = _val(bs, "total_equity", "equity", "total_shareholders_funds", period=prev) or _get_growth_metric_val(rr, "equity", which="previous_value")
    if eq_prev is None:
        sc_p = _val(bs, "equity_share_capital", "share_capital", period=prev)
        oe_p = _val(bs, "other_equity", "reserves_and_surplus", period=prev)
        if sc_p is not None and oe_p is not None:
            eq_prev = sc_p + oe_p
        elif sc_p is not None:
            eq_prev = sc_p

    # 9. Cash
    cash_curr = _val(bs, "cash_and_cash_equivalents", "cash", "cash_and_bank_balances", period=curr) or _get_growth_metric_val(rr, "cash", which="current_value")
    cash_prev = _val(bs, "cash_and_cash_equivalents", "cash", "cash_and_bank_balances", period=prev) or _get_growth_metric_val(rr, "cash", which="previous_value")

    # 10. Debt
    debt_curr = _val(bs, "total_debt", period=curr) or _get_growth_metric_val(rr, "debt", which="current_value")
    if debt_curr is None:
        lt = _val(bs, "long_term_borrowings", "non_current_borrowings", period=curr)
        st = _val(bs, "short_term_borrowings", "current_borrowings", period=curr)
        if lt is not None and st is not None:
            debt_curr = lt + st
        elif lt is not None:
            debt_curr = lt

    debt_prev = _val(bs, "total_debt", period=prev) or _get_growth_metric_val(rr, "debt", which="previous_value")
    if debt_prev is None:
        lt_p = _val(bs, "long_term_borrowings", "non_current_borrowings", period=prev)
        st_p = _val(bs, "short_term_borrowings", "current_borrowings", period=prev)
        if lt_p is not None and st_p is not None:
            debt_prev = lt_p + st_p
        elif lt_p is not None:
            debt_prev = lt_p

    def _calc_growth(c: Optional[float], p: Optional[float]) -> Optional[float]:
        if c is not None and p is not None and p != 0:
            return round(((c - p) / abs(p)) * 100.0, 2)
        return None

    # Build analysis result shape (Team 2 data)
    analysis_result = {
        "overall_score": rr.get("overall_score"),
        "overall_status": rr.get("overall_status"),
        "score_formula_version": rr.get("run_metadata", {}).get("engine_version", "2.0.0"),
        "run_metadata": rr.get("run_metadata", {}),

        # Findings
        "findings_summary": {
            "critical": findings_summary.get("critical", 0),
            "high": findings_summary.get("high", 0),
            "review": findings_summary.get("review", 0),
            "passed": findings_summary.get("passed", 0),
        },
        "findings": findings_details,

        # Financial metrics (Team 1 values + Team 2 growth rates)
        "financial_metrics": {
            "revenue": {
                "current": rev_curr,
                "previous": rev_prev,
                "growth_pct": _get_growth(rr, "revenue") if _get_growth(rr, "revenue") is not None else _calc_growth(rev_curr, rev_prev),
            },
            "gross_profit": {
                "current": gp_curr,
                "previous": gp_prev,
                "growth_pct": _get_growth(rr, "gross_profit") if _get_growth(rr, "gross_profit") is not None else _calc_growth(gp_curr, gp_prev),
            },
            "expenses": {
                "current": exp_curr,
                "previous": exp_prev,
                "growth_pct": _get_growth(rr, "operating_expenses", "total_expenses", "expense") if _get_growth(rr, "operating_expenses", "total_expenses", "expense") is not None else _calc_growth(exp_curr, exp_prev),
            },
            "operating_profit": {
                "current": op_curr,
                "previous": op_prev,
                "growth_pct": _get_growth(rr, "operating_profit", "operating_income") if _get_growth(rr, "operating_profit", "operating_income") is not None else _calc_growth(op_curr, op_prev),
            },
            "net_profit": {
                "current": np_curr,
                "previous": np_prev,
                "growth_pct": _get_growth(rr, "net_profit", "profit", "net_income") if _get_growth(rr, "net_profit", "profit", "net_income") is not None else _calc_growth(np_curr, np_prev),
            },
            "assets": {
                "current": ta_curr,
                "previous": ta_prev,
                "growth_pct": _get_growth(rr, "assets") or _val(bs, "asset_growth", period=curr) or _calc_growth(ta_curr, ta_prev),
            },
            "liabilities": {
                "current": tl_curr,
                "previous": tl_prev,
                "growth_pct": _get_growth(rr, "liabilities") or _calc_growth(tl_curr, tl_prev),
            },
            "equity": {
                "current": eq_curr,
                "previous": eq_prev,
                "growth_pct": _get_growth(rr, "equity") or _calc_growth(eq_curr, eq_prev),
            },
            "cash": {
                "current": cash_curr,
                "previous": cash_prev,
                "growth_pct": _get_growth(rr, "cash") or _val(bs, "cash_growth", period=curr) or _calc_growth(cash_curr, cash_prev),
            },
            "debt": {
                "current": debt_curr,
                "previous": debt_prev,
                "growth_pct": _get_growth(rr, "debt") or _val(bs, "debt_growth", period=curr) or _calc_growth(debt_curr, debt_prev),
            },
        },

        # Category scores across all 10 Team 2 categories
        "category_scores": rr.get("category_scores", {}),

        # Check scores (from Team 2 financial_metrics blocks)
        "checks": {
            "mathematical_accuracy": _check_score(rr, "mathematical_accuracy") or rr.get("category_scores", {}).get("MATHEMATICAL_ACCURACY"),
            "cash_flow": _check_score(rr, "cash_flow") or rr.get("category_scores", {}).get("CASH_FLOW"),
            "prior_year_tieout": _check_score(rr, "prior_year_tieout") or rr.get("category_scores", {}).get("PRIOR_YEAR_TIEOUT"),
            "internal_consistency": _check_score(rr, "internal_consistency") or rr.get("category_scores", {}).get("INTERNAL_CONSISTENCY"),
            "document_quality": _check_score(rr, "document_quality") or rr.get("category_scores", {}).get("DOCUMENT_QUALITY"),
            "analytical_comparison": rr.get("category_scores", {}).get("ANALYTICAL_COMPARISON"),
            "ratios": rr.get("category_scores", {}).get("RATIOS"),
            "unusual_fluctuation": rr.get("category_scores", {}).get("UNUSUAL_FLUCTUATION"),
            "unusual_gain": rr.get("category_scores", {}).get("UNUSUAL_GAIN"),
            "related_disclosure": rr.get("category_scores", {}).get("RELATED_DISCLOSURE"),
        },

        # Ratios (from Team 2 + Team 1 fallback)
        "ratios": _ratios(rr, fd, curr),

        # Analytics (from Team 2)
        "growth_rates": _growth_rates(rr, fd, curr),
        "unusual_fluctuations": _unusual_fluctuations(rr),
        "unusual_gain": _unusual_gain(rr),

        # Full Team 2 check blocks (for Report)
        "financial_metrics_full": rr.get("financial_metrics", {}),
        "analytical_metrics_full": rr.get("analytical_metrics", {}),

        # WP-514 Financial Statement Review Matrix
        "wp514": WP514Service.generate_review_matrix(fd, rr),
    }

    return {
        "extraction_result": extraction_result,
        "analysis_result": analysis_result,
    }
