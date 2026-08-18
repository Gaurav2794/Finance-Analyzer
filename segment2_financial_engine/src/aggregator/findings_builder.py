"""
Findings Builder.

Aggregates findings from all 10 check results into a unified, de-duplicated
list of FindingDetail objects matching the ReviewResultContract schema.

Severity mapping:
  Check status CRITICAL / HIGH items  → CRITICAL / HIGH finding
  Check "REVIEW" items                → REVIEW finding
  All checks PASSED                   → PASSED finding per check
"""

from typing import Any, Dict, List


_FINDING_COUNTER: List[int] = [0]


def _next_id() -> str:
    _FINDING_COUNTER[0] += 1
    return f"FINDING-{_FINDING_COUNTER[0]:03d}"


def reset_counter() -> None:
    """Reset counter between engine runs."""
    _FINDING_COUNTER[0] = 0


def build(check_results: Dict[str, Any], financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        check_results  : dict of {check_name: result_dict} from all 10 checks
        financial_data : original Phase 1 data for source lookup

    Returns:
        FindingsSummary dict matching ReviewResultContract.findings
    """
    reset_counter()
    details: List[Dict[str, Any]] = []
    counts = {"critical": 0, "high": 0, "review": 0, "passed": 0}

    for check_name, result in check_results.items():
        status = result.get("status", "SKIPPED")
        if status == "SKIPPED":
            continue

        category = _check_to_category(check_name)

        # --- Math Accuracy: per-equation findings ---
        if check_name == "mathematical_accuracy":
            for eq_name, eq in result.get("equations", {}).items():
                if not isinstance(eq, dict):
                    continue
                if eq.get("status") == "SKIPPED":
                    continue
                diff = eq.get("difference", 0) or 0
                formula = eq.get("formula", eq_name)
                if diff > 0.01:
                    sev = "HIGH"
                    counts["high"] += 1
                    details.append({
                        "id":          _next_id(),
                        "severity":    sev,
                        "category":    "MATH_ACCURACY",
                        "title":       f"Equation mismatch: {formula}",
                        "description": f"Calculated vs reported difference: {diff} Cr",
                        "source":      eq.get("source"),
                    })
                else:
                    counts["passed"] += 1

        # --- Cash Flow ---
        elif check_name == "cash_flow_reconciliation":
            cf_status = result.get("cash_reconciliation_status", "")
            bs_cf     = result.get("bs_cash_vs_cf_cash_status", "")
            if cf_status == "MISMATCH":
                counts["high"] += 1
                diff = result.get("cash_difference", 0)
                details.append({
                    "id":          _next_id(),
                    "severity":    "HIGH",
                    "category":    "CASH_FLOW",
                    "title":       "Cash Flow Statement does not reconcile",
                    "description": f"Expected closing cash differs by {diff} Cr",
                    "source":      None,
                })
            elif cf_status == "RECONCILED":
                counts["passed"] += 1
            if bs_cf == "MISMATCH":
                counts["high"] += 1
                details.append({
                    "id":          _next_id(),
                    "severity":    "HIGH",
                    "category":    "CASH_FLOW",
                    "title":       "Balance Sheet Cash ≠ Cash Flow Closing Cash",
                    "description": "The cash balance on the BS does not match the closing balance on the CFS.",
                    "source":      None,
                })
            elif bs_cf == "MATCHED":
                counts["passed"] += 1

        # --- Prior Year Tie-Out ---
        elif check_name == "prior_year_tieout":
            for item in result.get("items", []):
                s = item.get("tie_out_status")
                if s == "MISMATCH":
                    counts["high"] += 1
                    details.append({
                        "id":          _next_id(),
                        "severity":    "HIGH",
                        "category":    "PRIOR_YEAR_TIEOUT",
                        "title":       f"Prior year mismatch: {item.get('line_item')}",
                        "description": f"Opening balance ≠ prior year closing, Δ={item.get('difference')} Cr",
                        "source":      None,
                    })
                elif s == "MATCHED":
                    counts["passed"] += 1

        # --- Internal Consistency ---
        elif check_name == "internal_consistency":
            for comp in result.get("comparisons", []):
                s = comp.get("status")
                if s == "MISMATCH":
                    counts["high"] += 1
                    details.append({
                        "id":          _next_id(),
                        "severity":    "HIGH",
                        "category":    "INTERNAL_CONSISTENCY",
                        "title":       f"Cross-statement mismatch: {comp.get('check')}",
                        "description": f"Δ={comp.get('difference', 'N/A')} Cr between sources",
                        "source":      None,
                    })
                elif s == "MATCHED":
                    counts["passed"] += 1

        # --- Unusual Fluctuations ---
        elif check_name == "unusual_fluctuations":
            for item in result.get("items", []):
                sev = item.get("severity")
                if sev in ("HIGH", "REVIEW"):
                    counts[sev.lower()] += 1
                    details.append({
                        "id":          _next_id(),
                        "severity":    sev,
                        "category":    "UNUSUAL_FLUCTUATION",
                        "title":       f"{item.get('metric')} {item.get('direction', '')} by {item.get('change_pct')}%",
                        "description": (
                            f"{item.get('metric')} changed from {item.get('previous_value')} "
                            f"to {item.get('current_value')} ({item.get('change_pct')}%)."
                        ),
                        "source":      None,
                    })
                elif sev == "PASSED":
                    counts["passed"] += 1

        # --- Unusual Gain ---
        elif check_name == "unusual_gain_analysis":
            trig = result.get("divergence_trigger_status", "")
            if trig == "ELEVATED":
                counts["review"] += 1
                div = result.get("profit_vs_revenue_divergence_pp")
                details.append({
                    "id":          _next_id(),
                    "severity":    "REVIEW",
                    "category":    "UNUSUAL_GAIN",
                    "title":       f"Profit growth outpaces revenue growth by {div}pp",
                    "description": (
                        f"Net profit grew {result.get('profit_growth_pct')}% vs "
                        f"revenue growth of {result.get('revenue_growth_pct')}%."
                    ),
                    "source": None,
                })
            elif trig == "NORMAL":
                counts["passed"] += 1

        # --- Related Disclosure ---
        elif check_name == "related_disclosure":
            if status == "REVIEW":
                counts["review"] += 1
                for issue in result.get("issues", []):
                    details.append({
                        "id":          _next_id(),
                        "severity":    "REVIEW",
                        "category":    "RELATED_DISCLOSURE",
                        "title":       "Related Party Disclosure concern",
                        "description": issue,
                        "source":      result.get("note_source"),
                    })
            elif status == "PASSED":
                counts["passed"] += 1

        # --- Document Quality ---
        elif check_name == "document_quality":
            for issue in result.get("issues", []):
                sev = "CRITICAL" if "CRITICAL" in issue else "HIGH" if "HIGH" in issue else "REVIEW"
                counts[sev.lower()] += 1
                details.append({
                    "id":          _next_id(),
                    "severity":    sev,
                    "category":    "DOCUMENT_QUALITY",
                    "title":       "Document quality concern",
                    "description": issue,
                    "source":      None,
                })
            if not result.get("issues"):
                counts["passed"] += 1

        else:
            # Generic fallback
            if status == "PASSED":
                counts["passed"] += 1

    return {
        "critical": counts["critical"],
        "high":     counts["high"],
        "review":   counts["review"],
        "passed":   counts["passed"],
        "details":  details,
    }


def _check_to_category(check_name: str) -> str:
    mapping = {
        "mathematical_accuracy":     "MATH_ACCURACY",
        "cash_flow_reconciliation":  "CASH_FLOW",
        "prior_year_tieout":         "PRIOR_YEAR_TIEOUT",
        "internal_consistency":      "INTERNAL_CONSISTENCY",
        "analytical_metrics":        "ANALYTICAL",
        "financial_ratios":          "RATIOS",
        "unusual_fluctuations":      "UNUSUAL_FLUCTUATION",
        "unusual_gain_analysis":     "UNUSUAL_GAIN",
        "related_disclosure":        "RELATED_DISCLOSURE",
        "document_quality":          "DOCUMENT_QUALITY",
    }
    return mapping.get(check_name, check_name.upper())
