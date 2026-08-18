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


def _val(statement: Dict[str, Any], key: str, period: str) -> Optional[float]:
    """Extract a value from a statement dict for the given period key."""
    entry = statement.get(key, {})
    if isinstance(entry, dict):
        v = entry.get("values", {}).get(period)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return None


def _growth_pct(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """
    DO NOT USE for UI display — growth_pct must come from Team 2.
    This is only used inside the dashboard endpoint to pull
    growth_pct from Team 2's analytical_metrics.growth.
    """
    return None  # Always get from Team 2


def _get_growth(rr: Dict[str, Any], canonical_key: str) -> Optional[float]:
    """Pull growth % from Team 2 analytical_metrics.growth.metrics."""
    try:
        metric = rr["analytical_metrics"]["growth"]["metrics"][canonical_key]
        v = metric.get("percentage_change")
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

def _ratios(rr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pull ratios from Team 2 analytical_metrics.ratios.
    Returns a flat dict compatible with the UI's RatioTile component.
    """
    try:
        r = rr["analytical_metrics"]["ratios"]
    except (KeyError, TypeError):
        return {}

    def _extract_val(group: str, *keys: str) -> Optional[float]:
        try:
            group_dict = r.get(group, {})
            for k in keys:
                item = group_dict.get(k)
                if item is not None:
                    if isinstance(item, (int, float)):
                        return round(float(item), 4)
                    if isinstance(item, dict):
                        v = item.get("value") or item.get("raw_decimal_value")
                        if v is not None:
                            return round(float(v), 4)
        except (ValueError, TypeError):
            pass
        return None

    return {
        # Liquidity
        "current_ratio": _extract_val("liquidity", "current_ratio"),
        "quick_ratio": _extract_val("liquidity", "quick_ratio"),
        "cash_ratio": _extract_val("liquidity", "cash_ratio"),
        # Leverage
        "debt_to_equity": _extract_val("leverage", "debt_to_equity"),
        "debt_ratio": _extract_val("leverage", "debt_ratio"),
        "interest_coverage_ratio": _extract_val("leverage", "interest_coverage_ratio"),
        # Profitability
        "gross_profit_margin_pct": _extract_val("profitability", "gross_profit_margin", "gross_profit_margin_pct"),
        "operating_margin_pct": _extract_val("profitability", "operating_margin", "operating_margin_pct"),
        "net_margin_pct": _extract_val("profitability", "net_profit_margin", "net_profit_margin_pct"),
        "return_on_assets_pct": _extract_val("profitability", "return_on_assets", "return_on_assets_pct"),
        "roe_pct": _extract_val("profitability", "return_on_equity", "return_on_equity_pct"),
        # Efficiency
        "asset_turnover_ratio": _extract_val("efficiency", "asset_turnover", "asset_turnover_ratio"),
        "receivables_turnover_ratio": _extract_val("efficiency", "receivables_turnover", "receivables_turnover_ratio"),
        "days_sales_outstanding": _extract_val("efficiency", "days_sales_outstanding"),
        "inventory_turnover_ratio": _extract_val("efficiency", "inventory_turnover", "inventory_turnover_ratio"),
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


def _growth_rates(rr: Dict[str, Any]) -> Dict[str, Any]:
    try:
        metrics = rr["analytical_metrics"]["growth"]["metrics"]
        return {k: v.get("percentage_change") for k, v in metrics.items()
                if isinstance(v, dict)}
    except (KeyError, TypeError):
        return {}


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
        "currency": company.get("currency", "INR"),
        "unit": company.get("scale", "Crores"),
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
        "extracted_notes": fd.get("extracted_notes_and_disclosures", []),
        "team1_metrics": fd.get("team1_metrics", {}),
    }

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
                "current": _val(is_statement, "revenue_from_operations", curr),
                "previous": _val(is_statement, "revenue_from_operations", prev),
                "growth_pct": _get_growth(rr, "revenue"),
            },
            "gross_profit": {
                "current": _val(is_statement, "gross_profit", curr),
                "previous": _val(is_statement, "gross_profit", prev),
                "growth_pct": _get_growth(rr, "gross_profit"),
            },
            "expenses": {
                "current": _val(is_statement, "total_expenses", curr),
                "previous": _val(is_statement, "total_expenses", prev),
                "growth_pct": _get_growth(rr, "total_expenses"),
            },
            "operating_profit": {
                "current": _val(is_statement, "operating_profit", curr),
                "previous": _val(is_statement, "operating_profit", prev),
                "growth_pct": _get_growth(rr, "operating_profit"),
            },
            "net_profit": {
                "current": _val(is_statement, "profit_for_the_period", curr),
                "previous": _val(is_statement, "profit_for_the_period", prev),
                "growth_pct": _get_growth(rr, "net_profit"),
            },
            "assets": {
                "current": _val(bs, "total_assets", curr),
                "previous": _val(bs, "total_assets", prev),
                "growth_pct": _get_growth(rr, "assets"),
            },
            "liabilities": {
                "current": _val(bs, "total_liabilities", curr),
                "previous": _val(bs, "total_liabilities", prev),
                "growth_pct": _get_growth(rr, "liabilities"),
            },
            "equity": {
                "current": _val(bs, "total_equity", curr),
                "previous": _val(bs, "total_equity", prev),
                "growth_pct": _get_growth(rr, "equity"),
            },
            "cash": {
                "current": _val(bs, "cash_and_cash_equivalents", curr),
                "previous": _val(bs, "cash_and_cash_equivalents", prev),
                "growth_pct": _get_growth(rr, "cash"),
            },
            "debt": {
                "current": _val(bs, "total_debt", curr) or _val(bs, "long_term_borrowings", curr),
                "previous": _val(bs, "total_debt", prev) or _val(bs, "long_term_borrowings", prev),
                "growth_pct": _get_growth(rr, "debt"),
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

        # Ratios (from Team 2)
        "ratios": _ratios(rr),

        # Analytics (from Team 2)
        "growth_rates": _growth_rates(rr),
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
