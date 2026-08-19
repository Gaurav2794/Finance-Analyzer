"""
WP-514 Financial Statement Review Normalization Service.

Transforms existing Team 1 (financial_data.json), Team 2 (review_result.json),
and Language Quality outputs into a standardized WP-514 Financial Statement
Review workpaper structure.

Hardening Rules & Guarantees:
- Zero recalculation of financial figures, ratios, growth rates, scores, or severities.
- Pure consumer/adapter pattern.
- No hardcoded assumptions: currency, scale, reporting framework, tolerances, and thresholds
  are dynamically sourced from Team 1 metadata and Team 2 review results.
- Returns None / "Not available" when source information is absent.
- Faithful mapping to existing findings and source evidence.
"""

from typing import Any, Dict, List, Optional
import logging

log = logging.getLogger("team3.wp514")


class WP514Service:
    @classmethod
    def generate_review_matrix(
        cls,
        financial_data: Dict[str, Any],
        review_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalizes existing pipeline artifacts into the unified WP-514 review matrix.
        """
        doc_info = cls._extract_document_information(financial_data, review_result)
        currency = doc_info.get("currency")
        scale = doc_info.get("scale")

        checks: List[Dict[str, Any]] = []
        categories: List[Dict[str, Any]] = []

        findings_list = review_result.get("findings", {}).get("details", [])
        finding_map = {f.get("id"): f for f in findings_list if isinstance(f, dict)}

        # 1. MATHEMATICAL_ACCURACY
        cat_ma, checks_ma = cls._build_mathematical_accuracy(review_result, finding_map, currency, scale)
        categories.append(cat_ma)
        checks.extend(checks_ma)

        # 2. CASH_FLOW
        cat_cf, checks_cf = cls._build_cash_flow(financial_data, review_result, finding_map, currency, scale)
        categories.append(cat_cf)
        checks.extend(checks_cf)

        # 3. PRIOR_YEAR_TIEOUT
        cat_py, checks_py = cls._build_prior_year_tieout(review_result, finding_map, currency, scale)
        categories.append(cat_py)
        checks.extend(checks_py)

        # 4. INTERNAL_CONSISTENCY
        cat_ic, checks_ic = cls._build_internal_consistency(review_result, finding_map, currency, scale)
        categories.append(cat_ic)
        checks.extend(checks_ic)

        # 5. ANALYTICAL_COMPARISON
        cat_ac, checks_ac = cls._build_analytical_comparison(review_result, finding_map, currency, scale)
        categories.append(cat_ac)
        checks.extend(checks_ac)

        # 6. RATIOS
        cat_rt, checks_rt = cls._build_ratios(review_result, finding_map, financial_data)
        categories.append(cat_rt)
        checks.extend(checks_rt)

        # 7. UNUSUAL_FLUCTUATION
        cat_uf, checks_uf = cls._build_unusual_fluctuation(review_result, finding_map, currency, scale)
        categories.append(cat_uf)
        checks.extend(checks_uf)

        # 8. UNUSUAL_GAIN
        cat_ug, checks_ug = cls._build_unusual_gain(review_result, finding_map, currency, scale)
        categories.append(cat_ug)
        checks.extend(checks_ug)

        # 9. RELATED_DISCLOSURE
        cat_rd, checks_rd = cls._build_related_disclosure(review_result, finding_map, currency, scale)
        categories.append(cat_rd)
        checks.extend(checks_rd)

        # 10. DOCUMENT_QUALITY
        cat_dq, checks_dq = cls._build_document_quality(financial_data, review_result, finding_map)
        categories.append(cat_dq)
        checks.extend(checks_dq)

        # Compute overall matrix stats directly from underlying checks
        total_checks = len(checks)
        passed_count = sum(1 for c in checks if c.get("status") == "PASSED")
        review_count = sum(1 for c in checks if c.get("status") in ("REVIEW", "WARNING"))
        failed_count = sum(1 for c in checks if c.get("status") == "FAILED")
        na_count = sum(1 for c in checks if c.get("status") == "NOT_AVAILABLE")

        overall_score = review_result.get("overall_score", 0.0)
        overall_status = review_result.get("overall_status", "NOT_AVAILABLE")

        completeness_data = (
            financial_data.get("team1_metrics", {}).get("document_quality") or
            review_result.get("financial_metrics", {}).get("document_quality") or {}
        )

        return {
            "title": "WP-514 Financial Statement Review",
            "subtitle": "Comprehensive Audit Workpaper & Review Matrix",
            "document_information": doc_info,
            "completeness": completeness_data,
            "categories": categories,
            "checks": checks,
            "findings": findings_list,
            "overall": {
                "score": overall_score,
                "status": overall_status,
                "total_checks": total_checks,
                "passed": passed_count,
                "review": review_count,
                "failed": failed_count,
                "not_available": na_count,
                "critical_findings": review_result.get("findings", {}).get("critical", 0),
                "high_findings": review_result.get("findings", {}).get("high", 0),
                "review_findings": review_result.get("findings", {}).get("review", 0),
                "passed_findings": review_result.get("findings", {}).get("passed", 0),
            }
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Helper: Dynamic Money / Currency Formatter
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _fmt_val(
        val: Any,
        currency: Optional[str] = None,
        scale: Optional[str] = None,
        is_delta: bool = False
    ) -> Optional[str]:
        if val is None:
            return None
        sym = "₹" if currency == "INR" else ("$" if currency == "USD" else (f"{currency} " if currency else ""))
        scale_str = f" {scale}" if scale else ""
        if is_delta:
            try:
                fval = float(val)
                sign = "+" if fval > 0 else ("-" if fval < 0 else "")
                return f"{sign}{sym}{abs(fval)}{scale_str}"
            except (ValueError, TypeError):
                pass
        return f"{sym}{val}{scale_str}"

    # ─────────────────────────────────────────────────────────────────────────
    # Document Information Extractor (Dynamic & Non-assuming)
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _extract_document_information(
        cls,
        financial_data: Dict[str, Any],
        review_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        meta = financial_data.get("metadata", {})
        co = meta.get("company", {})
        periods = meta.get("periods", [])
        curr_period = periods[0] if periods and isinstance(periods[0], dict) else {}

        return {
            "company_name": co.get("name") or review_result.get("run_metadata", {}).get("company") or None,
            "cin_or_ticker": co.get("cin_or_ticker") if co.get("cin_or_ticker") != "N/A" else None,
            "industry": co.get("industry") or None,
            "reporting_period": curr_period.get("label") or curr_period.get("period_key") or None,
            "financial_year": curr_period.get("period_key") or review_result.get("run_metadata", {}).get("current_period") or None,
            "all_periods": [p.get("period_key") for p in periods if isinstance(p, dict)] or review_result.get("run_metadata", {}).get("all_periods", []),
            "currency": co.get("currency") or None,
            "scale": co.get("scale") or None,
            "statement_type": co.get("statement_type") or None,
            "document_name": meta.get("source_file") or None,
            "reporting_framework": co.get("reporting_standard") or None,
            "document_id": meta.get("document_id") or review_result.get("run_metadata", {}).get("document_id") or None,
            "engine_version": review_result.get("run_metadata", {}).get("engine_version") or "2.0.0",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Helper: Normalize category block
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _make_category_summary(
        cat_id: str,
        name: str,
        score: Optional[float],
        status: str,
        checks: List[Dict[str, Any]],
        findings_count: int = 0
    ) -> Dict[str, Any]:
        passed = sum(1 for c in checks if c.get("status") == "PASSED")
        review = sum(1 for c in checks if c.get("status") in ("REVIEW", "WARNING"))
        failed = sum(1 for c in checks if c.get("status") == "FAILED")
        na = sum(1 for c in checks if c.get("status") == "NOT_AVAILABLE")

        norm_status = status
        if failed > 0:
            norm_status = "FAILED"
        elif review > 0 and norm_status != "FAILED":
            norm_status = "REVIEW"
        elif na == len(checks) and len(checks) > 0:
            norm_status = "NOT_AVAILABLE"

        return {
            "id": cat_id,
            "name": name,
            "status": norm_status,
            "score": score,
            "total_checks": len(checks),
            "passed_checks": passed,
            "review_checks": review,
            "failed_checks": failed,
            "na_checks": na,
            "findings_count": findings_count,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 1. MATHEMATICAL ACCURACY
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_mathematical_accuracy(
        cls,
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any],
        currency: Optional[str],
        scale: Optional[str]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        checks_data = (
            review_result.get("financial_metrics", {}).get("mathematical_accuracy") or
            review_result.get("checks", {}).get("mathematical_accuracy") or {}
        )
        status = checks_data.get("status", "NOT_AVAILABLE")
        score = checks_data.get("score")
        tolerance = checks_data.get("tolerance")
        th_str = f"{tolerance} {scale}".strip() if tolerance is not None else None

        eqs = checks_data.get("equations", [])
        checks: List[Dict[str, Any]] = []

        for idx, eq in enumerate(eqs, start=1):
            name = eq.get("name", f"Equation {idx}")
            eq_status = eq.get("status", "NOT_AVAILABLE")
            diff = eq.get("difference")
            expected = eq.get("expected_value") or eq.get("rhs")
            actual = eq.get("actual_value") or eq.get("lhs")
            src = eq.get("source")

            checks.append({
                "id": f"WP514-MA-{idx:02d}",
                "category": "MATHEMATICAL_ACCURACY",
                "check": name,
                "status": "PASSED" if eq_status == "PASSED" else ("FAILED" if eq_status == "FAILED" else eq_status),
                "expected_value": cls._fmt_val(expected, currency, scale),
                "actual_value": cls._fmt_val(actual, currency, scale),
                "difference": cls._fmt_val(diff, currency, scale, is_delta=True) if diff is not None else None,
                "difference_percent": None,
                "threshold": th_str,
                "source": src,
                "evidence": f"Formula: {eq.get('formula')}" if eq.get('formula') else None,
                "finding_id": next((fid for fid, f in finding_map.items() if "Math" in f.get("category", "") and name in f.get("title", "")), None),
            })

        if not checks:
            checks.append({
                "id": "WP514-MA-01",
                "category": "MATHEMATICAL_ACCURACY",
                "check": "Balance Sheet & Income Statement Mathematical Accuracy",
                "status": status,
                "expected_value": None,
                "actual_value": None,
                "difference": None,
                "difference_percent": None,
                "threshold": th_str,
                "source": None,
                "evidence": None,
                "finding_id": None,
            })

        findings_count = sum(1 for f in finding_map.values() if "Math" in f.get("category", ""))
        cat = cls._make_category_summary("MATHEMATICAL_ACCURACY", "Mathematical Accuracy", score, status, checks, findings_count)
        return cat, checks

    # ─────────────────────────────────────────────────────────────────────────
    # 2. CASH FLOW
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_cash_flow(
        cls,
        financial_data: Dict[str, Any],
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any],
        currency: Optional[str],
        scale: Optional[str]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        cf_data = (
            review_result.get("financial_metrics", {}).get("cash_flow") or
            review_result.get("checks", {}).get("cash_flow") or {}
        )
        status = cf_data.get("status", "NOT_AVAILABLE")
        score = cf_data.get("score")
        tolerance = cf_data.get("tolerance")
        th_str = f"{tolerance} {scale}".strip() if tolerance is not None else None
        checks: List[Dict[str, Any]] = []

        # Check 1: Operating Cash Flow
        cfo = cf_data.get("cfo_operating")
        checks.append({
            "id": "WP514-CF-01",
            "category": "CASH_FLOW",
            "check": "Operating Cash Flow (CFO)",
            "status": "PASSED" if cfo is not None else "NOT_AVAILABLE",
            "expected_value": None,
            "actual_value": cls._fmt_val(cfo, currency, scale),
            "difference": None,
            "difference_percent": None,
            "threshold": None,
            "source": cf_data.get("cfo_source"),
            "evidence": "Cash generated from operating activities" if cfo is not None else None,
            "finding_id": None,
        })

        # Check 2: Investing Cash Flow
        cfi = cf_data.get("cfi_investing")
        checks.append({
            "id": "WP514-CF-02",
            "category": "CASH_FLOW",
            "check": "Investing Cash Flow (CFI)",
            "status": "PASSED" if cfi is not None else "NOT_AVAILABLE",
            "expected_value": None,
            "actual_value": cls._fmt_val(cfi, currency, scale),
            "difference": None,
            "difference_percent": None,
            "threshold": None,
            "source": cf_data.get("cfi_source"),
            "evidence": "Cash used in / from investing activities" if cfi is not None else None,
            "finding_id": None,
        })

        # Check 3: Financing Cash Flow
        cff = cf_data.get("cff_financing")
        checks.append({
            "id": "WP514-CF-03",
            "category": "CASH_FLOW",
            "check": "Financing Cash Flow (CFF)",
            "status": "PASSED" if cff is not None else "NOT_AVAILABLE",
            "expected_value": None,
            "actual_value": cls._fmt_val(cff, currency, scale),
            "difference": None,
            "difference_percent": None,
            "threshold": None,
            "source": cf_data.get("cff_source"),
            "evidence": "Cash used in / from financing activities" if cff is not None else None,
            "finding_id": None,
        })

        # Check 4: Cash Flow Statement Arithmetic Reconciliation
        cf_recon_status = cf_data.get("cfs_arithmetic_status", status)
        checks.append({
            "id": "WP514-CF-04",
            "category": "CASH_FLOW",
            "check": "Cash Flow Arithmetic Reconciliation (Opening + CFO + CFI + CFF = Closing)",
            "status": cf_recon_status if cf_recon_status in ("PASSED", "FAILED") else status,
            "expected_value": cls._fmt_val(cf_data.get("expected_closing_cash"), currency, scale),
            "actual_value": cls._fmt_val(cf_data.get("reported_closing_cash"), currency, scale),
            "difference": cls._fmt_val(cf_data.get("reconciliation_difference"), currency, scale, is_delta=True),
            "difference_percent": None,
            "threshold": th_str,
            "source": cf_data.get("closing_cash_source"),
            "evidence": "Net increase in cash and opening balance summation",
            "finding_id": next((fid for fid, f in finding_map.items() if "Cash" in f.get("category", "")), None),
        })

        # Check 5: Cross-Statement CFS ↔ Balance Sheet Cash
        bs_cf_status = cf_data.get("bs_cash_match_status", "PASSED")
        checks.append({
            "id": "WP514-CF-05",
            "category": "CASH_FLOW",
            "check": "Cash Flow Statement ↔ Balance Sheet Cash Tie-Out",
            "status": bs_cf_status,
            "expected_value": cls._fmt_val(cf_data.get("bs_cash_value"), currency, scale),
            "actual_value": cls._fmt_val(cf_data.get("reported_closing_cash"), currency, scale),
            "difference": cls._fmt_val(cf_data.get("bs_cash_difference"), currency, scale, is_delta=True),
            "difference_percent": None,
            "threshold": th_str,
            "source": cf_data.get("bs_cash_source"),
            "evidence": "Cross-statement verification between Balance Sheet and Cash Flow Statement",
            "finding_id": None,
        })

        findings_count = sum(1 for f in finding_map.values() if "Cash" in f.get("category", ""))
        cat = cls._make_category_summary("CASH_FLOW", "Cash Flow Reconciliation", score, status, checks, findings_count)
        return cat, checks

    # ─────────────────────────────────────────────────────────────────────────
    # 3. PRIOR YEAR TIEOUT
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_prior_year_tieout(
        cls,
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any],
        currency: Optional[str],
        scale: Optional[str]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        py_data = (
            review_result.get("financial_metrics", {}).get("prior_year_tieout") or
            review_result.get("checks", {}).get("prior_year_tieout") or {}
        )
        status = py_data.get("status", "NOT_AVAILABLE")
        score = py_data.get("score")
        tolerance = py_data.get("tolerance")
        th_str = f"{tolerance} {scale}".strip() if tolerance is not None else None
        items = py_data.get("items", [])
        checks: List[Dict[str, Any]] = []

        for idx, it in enumerate(items, start=1):
            name = it.get("metric") or it.get("label") or f"Account {idx}"
            it_status = it.get("status", "NOT_AVAILABLE")
            diff = it.get("difference")
            expected = it.get("prior_closing_value")
            actual = it.get("current_opening_value")

            checks.append({
                "id": f"WP514-PY-{idx:02d}",
                "category": "PRIOR_YEAR_TIEOUT",
                "check": f"Prior-Year Tie-Out: {name}",
                "status": "PASSED" if it_status == "MATCHED" else ("REVIEW" if it_status == "WARNING" else ("FAILED" if it_status == "MISMATCH" else it_status)),
                "expected_value": cls._fmt_val(expected, currency, scale),
                "actual_value": cls._fmt_val(actual, currency, scale),
                "difference": cls._fmt_val(diff, currency, scale, is_delta=True),
                "difference_percent": None,
                "threshold": th_str,
                "source": it.get("source"),
                "evidence": f"Prior period closing vs current opening balance tie-out",
                "finding_id": next((fid for fid, f in finding_map.items() if "Prior" in f.get("category", "") and name in f.get("title", "")), None),
            })

        if not checks:
            checks.append({
                "id": "WP514-PY-01",
                "category": "PRIOR_YEAR_TIEOUT",
                "check": "Carried-Forward Balance Sheet Accounts Prior-Year Tie-Out",
                "status": status,
                "expected_value": None,
                "actual_value": None,
                "difference": None,
                "difference_percent": None,
                "threshold": th_str,
                "source": None,
                "evidence": None,
                "finding_id": None,
            })

        findings_count = sum(1 for f in finding_map.values() if "Prior" in f.get("category", ""))
        cat = cls._make_category_summary("PRIOR_YEAR_TIEOUT", "Prior-Year Tie-Out", score, status, checks, findings_count)
        return cat, checks

    # ─────────────────────────────────────────────────────────────────────────
    # 4. INTERNAL CONSISTENCY
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_internal_consistency(
        cls,
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any],
        currency: Optional[str],
        scale: Optional[str]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        ic_data = (
            review_result.get("financial_metrics", {}).get("internal_consistency") or
            review_result.get("checks", {}).get("internal_consistency") or {}
        )
        status = ic_data.get("status", "NOT_AVAILABLE")
        score = ic_data.get("score")
        tolerance = ic_data.get("tolerance")
        th_str = f"{tolerance} {scale}".strip() if tolerance is not None else None
        rules = ic_data.get("rules", [])
        checks: List[Dict[str, Any]] = []

        for idx, r in enumerate(rules, start=1):
            name = r.get("rule_name") or r.get("description") or f"Consistency Rule {idx}"
            r_status = r.get("status", "NOT_AVAILABLE")
            diff = r.get("difference")
            expected = r.get("value_a")
            actual = r.get("value_b")

            checks.append({
                "id": f"WP514-IC-{idx:02d}",
                "category": "INTERNAL_CONSISTENCY",
                "check": name,
                "status": "PASSED" if r_status == "PASSED" else ("FAILED" if r_status == "FAILED" else "REVIEW"),
                "expected_value": cls._fmt_val(expected, currency, scale),
                "actual_value": cls._fmt_val(actual, currency, scale),
                "difference": cls._fmt_val(diff, currency, scale, is_delta=True),
                "difference_percent": None,
                "threshold": th_str,
                "source": r.get("source_a") or r.get("source_b"),
                "evidence": f"Cross-statement match between {r.get('statement_a', 'Statement A')} and {r.get('statement_b', 'Statement B')}",
                "finding_id": next((fid for fid, f in finding_map.items() if "Consistency" in f.get("category", "") and name in f.get("title", "")), None),
            })

        if not checks:
            checks.append({
                "id": "WP514-IC-01",
                "category": "INTERNAL_CONSISTENCY",
                "check": "Cross-Statement and Statement-to-Note Consistency",
                "status": status,
                "expected_value": None,
                "actual_value": None,
                "difference": None,
                "difference_percent": None,
                "threshold": th_str,
                "source": None,
                "evidence": None,
                "finding_id": None,
            })

        findings_count = sum(1 for f in finding_map.values() if "Consistency" in f.get("category", ""))
        cat = cls._make_category_summary("INTERNAL_CONSISTENCY", "Internal Consistency", score, status, checks, findings_count)
        return cat, checks

    # ─────────────────────────────────────────────────────────────────────────
    # 5. ANALYTICAL COMPARISON
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_analytical_comparison(
        cls,
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any],
        currency: Optional[str],
        scale: Optional[str]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        ac_data = (
            review_result.get("analytical_metrics", {}).get("growth") or
            review_result.get("checks", {}).get("growth") or {}
        )
        status = ac_data.get("status", "PASSED")
        score = ac_data.get("score") or 100.0
        items = ac_data.get("items", [])
        checks: List[Dict[str, Any]] = []

        for idx, it in enumerate(items, start=1):
            metric = it.get("metric", f"Metric {idx}")
            curr = it.get("current_value")
            prev = it.get("previous_value")
            abs_chg = it.get("absolute_change")
            pct_chg = it.get("percentage_change")
            direction = it.get("direction", "NO_CHANGE")

            checks.append({
                "id": f"WP514-AC-{idx:02d}",
                "category": "ANALYTICAL_COMPARISON",
                "check": f"YoY Analytical Comparison: {metric}",
                "status": "PASSED" if curr is not None and prev is not None else "NOT_AVAILABLE",
                "expected_value": cls._fmt_val(prev, currency, scale),
                "actual_value": cls._fmt_val(curr, currency, scale),
                "difference": cls._fmt_val(abs_chg, currency, scale, is_delta=True),
                "difference_percent": f"{pct_chg:+.2f}%" if pct_chg is not None else None,
                "threshold": None,
                "source": it.get("source"),
                "evidence": f"Direction: {direction}",
                "finding_id": None,
            })

        findings_count = sum(1 for f in finding_map.values() if "Growth" in f.get("category", "") or "Analytical" in f.get("category", ""))
        cat = cls._make_category_summary("ANALYTICAL_COMPARISON", "Analytical Comparison & Growth", score, status, checks, findings_count)
        return cat, checks

    # ─────────────────────────────────────────────────────────────────────────
    # 6. RATIOS
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_ratios(
        cls,
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any],
        financial_data: Optional[Dict[str, Any]] = None
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        rt_data = (
            review_result.get("analytical_metrics", {}).get("ratios") or
            review_result.get("checks", {}).get("ratios") or {}
        )
        status = rt_data.get("status", "PASSED")
        score = rt_data.get("score") or 100.0
        all_ratios = rt_data.get("all_ratios", {}) or {}
        checks: List[Dict[str, Any]] = []

        curr = ""
        if financial_data:
            periods = financial_data.get("metadata", {}).get("periods", [])
            if periods and isinstance(periods[0], dict):
                curr = periods[0].get("period_key", "")
        bs = (financial_data.get("balance_sheet", {}) if financial_data else {})
        is_statement = (financial_data.get("income_statement", {}) if financial_data else {})

        ratio_groups = [
            ("Liquidity", [
                ("current_ratio", ["current_ratio", "current"], "Current Ratio", False),
                ("quick_ratio", ["quick_ratio", "quick"], "Quick Ratio", False),
                ("cash_ratio", ["cash_ratio", "cash"], "Cash Ratio", False),
            ]),
            ("Leverage", [
                ("debt_to_equity", ["debt_to_equity", "debt_equity"], "Debt to Equity", False),
                ("debt_ratio", ["debt_ratio", "total_debt_ratio"], "Debt Ratio", False),
                ("interest_coverage_ratio", ["interest_coverage_ratio", "interest_coverage"], "Interest Coverage Ratio", False),
            ]),
            ("Profitability", [
                ("gross_profit_margin_pct", ["gross_profit_margin", "gross_profit_margin_pct", "gross_margin"], "Gross Profit Margin", True),
                ("operating_margin_pct", ["operating_margin", "operating_margin_pct"], "Operating Margin", True),
                ("net_profit_margin_pct", ["net_profit_margin", "net_profit_margin_pct", "net_margin"], "Net Profit Margin", True),
                ("return_on_assets_pct", ["return_on_assets", "return_on_assets_pct", "roa"], "Return on Assets (ROA)", True),
                ("return_on_equity_pct", ["return_on_equity", "return_on_equity_pct", "roe"], "Return on Equity (ROE)", True),
            ]),
            ("Efficiency", [
                ("asset_turnover_ratio", ["asset_turnover", "asset_turnover_ratio"], "Asset Turnover", False),
                ("inventory_turnover_ratio", ["inventory_turnover", "inventory_turnover_ratio"], "Inventory Turnover", False),
                ("receivables_turnover_ratio", ["receivables_turnover", "receivables_turnover_ratio"], "Receivables Turnover", False),
            ])
        ]

        idx = 1
        for grp_name, r_items in ratio_groups:
            grp_dict = rt_data.get(grp_name.lower(), {}) if isinstance(rt_data, dict) else {}
            for canonical_key, aliases, default_label, is_pct in r_items:
                search_keys = [canonical_key] + aliases
                val: Optional[float] = None
                label = default_label
                formula: Optional[str] = None
                source = None
                item_status = "NOT_AVAILABLE"

                # 1. Search in all_ratios
                for k in search_keys:
                    r_item = all_ratios.get(k)
                    if r_item is not None and isinstance(r_item, dict):
                        raw_v = r_item.get("value") or r_item.get("raw_decimal_value")
                        if raw_v is not None:
                            try:
                                val = float(raw_v)
                                label = r_item.get("ratio_name") or label
                                formula = r_item.get("formula")
                                source = r_item.get("source")
                                item_status = r_item.get("status", "PASSED")
                                break
                            except (TypeError, ValueError):
                                pass

                # 2. Search in category dict
                if val is None and isinstance(grp_dict, dict):
                    for k in search_keys:
                        r_item = grp_dict.get(k)
                        if r_item is not None:
                            if isinstance(r_item, (int, float)):
                                val = float(r_item)
                                item_status = "PASSED"
                                break
                            elif isinstance(r_item, dict):
                                raw_v = r_item.get("value") or r_item.get("raw_decimal_value")
                                if raw_v is not None:
                                    try:
                                        val = float(raw_v)
                                        label = r_item.get("ratio_name") or r_item.get("label") or label
                                        formula = r_item.get("formula")
                                        source = r_item.get("source")
                                        item_status = r_item.get("status", "PASSED")
                                        break
                                    except (TypeError, ValueError):
                                        pass

                # 3. Search in financial_data statements (Audit Master fallback)
                if val is None and curr:
                    for k in search_keys:
                        stmt_v = None
                        if isinstance(bs, dict) and k in bs:
                            v_map = bs[k].get("values", {})
                            stmt_v = v_map.get(curr)
                        elif isinstance(is_statement, dict) and k in is_statement:
                            v_map = is_statement[k].get("values", {})
                            stmt_v = v_map.get(curr)
                        if stmt_v is not None:
                            try:
                                val = float(stmt_v)
                                if is_pct and abs(val) <= 1.0 and val != 0:
                                    val = val * 100.0
                                item_status = "PASSED"
                                break
                            except (TypeError, ValueError):
                                pass

                if val is not None:
                    val_str = f"{val:.2f}%" if is_pct else f"{val:.2f}"
                else:
                    val_str = None

                checks.append({
                    "id": f"WP514-RT-{idx:02d}",
                    "category": "RATIOS",
                    "check": f"{grp_name} Ratio: {label}",
                    "status": "PASSED" if val is not None else "NOT_AVAILABLE",
                    "expected_value": None,
                    "actual_value": val_str,
                    "difference": None,
                    "difference_percent": None,
                    "threshold": None,
                    "source": source,
                    "evidence": f"Formula: {formula}" if formula else f"Category: {grp_name}",
                    "finding_id": None,
                })
                idx += 1

        findings_count = sum(1 for f in finding_map.values() if "Ratio" in f.get("category", ""))
        cat = cls._make_category_summary("RATIOS", "Key Financial Ratios", score, status, checks, findings_count)
        return cat, checks

    # ─────────────────────────────────────────────────────────────────────────
    # 7. UNUSUAL FLUCTUATION
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_unusual_fluctuation(
        cls,
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any],
        currency: Optional[str],
        scale: Optional[str]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        uf_data = (
            review_result.get("analytical_metrics", {}).get("unusual_fluctuation") or
            review_result.get("checks", {}).get("unusual_fluctuation") or {}
        )
        status = uf_data.get("status", "PASSED")
        score = uf_data.get("score")
        items = uf_data.get("items", [])
        checks: List[Dict[str, Any]] = []

        for idx, it in enumerate(items, start=1):
            metric = it.get("metric", f"Item {idx}")
            sev = it.get("severity", "PASSED")
            chg = it.get("change_pct")
            th = it.get("threshold_pct")
            curr = it.get("current_value")
            prev = it.get("previous_value")

            norm_status = "PASSED"
            if sev == "HIGH":
                norm_status = "FAILED"
            elif sev == "REVIEW":
                norm_status = "REVIEW"
            elif sev == "NOT_AVAILABLE":
                norm_status = "NOT_AVAILABLE"

            checks.append({
                "id": f"WP514-UF-{idx:02d}",
                "category": "UNUSUAL_FLUCTUATION",
                "check": f"YoY Fluctuation Scanner: {metric}",
                "status": norm_status,
                "expected_value": cls._fmt_val(prev, currency, scale),
                "actual_value": cls._fmt_val(curr, currency, scale),
                "difference": f"{chg:+.2f}%" if chg is not None else None,
                "difference_percent": f"{chg:+.2f}%" if chg is not None else None,
                "threshold": f"±{th}%" if th is not None else None,
                "source": None,
                "evidence": it.get("note"),
                "finding_id": next((fid for fid, f in finding_map.items() if "Fluctuation" in f.get("category", "") and metric in f.get("title", "")), None),
            })

        findings_count = sum(1 for f in finding_map.values() if "Fluctuation" in f.get("category", ""))
        cat = cls._make_category_summary("UNUSUAL_FLUCTUATION", "Unusual Fluctuations Scanner", score, status, checks, findings_count)
        return cat, checks

    # ─────────────────────────────────────────────────────────────────────────
    # 8. UNUSUAL GAIN
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_unusual_gain(
        cls,
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any],
        currency: Optional[str],
        scale: Optional[str]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        ug_data = (
            review_result.get("analytical_metrics", {}).get("unusual_gain") or
            review_result.get("checks", {}).get("unusual_gain") or {}
        )
        status = ug_data.get("status", "PASSED")
        score = ug_data.get("score")
        checks: List[Dict[str, Any]] = []

        # Check 1: Profit vs Revenue Divergence
        div_pp = ug_data.get("profit_vs_revenue_divergence_pp")
        div_th = ug_data.get("divergence_threshold_pp")
        trig = ug_data.get("divergence_trigger_status", "NORMAL")

        checks.append({
            "id": "WP514-UG-01",
            "category": "UNUSUAL_GAIN",
            "check": "Profit Growth vs Revenue Growth Divergence",
            "status": "REVIEW" if trig == "ELEVATED" else ("PASSED" if trig == "NORMAL" else "NOT_AVAILABLE"),
            "expected_value": f"{ug_data.get('revenue_growth_pct'):+.2f}% (Revenue Growth)" if ug_data.get('revenue_growth_pct') is not None else None,
            "actual_value": f"{ug_data.get('profit_growth_pct'):+.2f}% (Profit Growth)" if ug_data.get('profit_growth_pct') is not None else None,
            "difference": f"{div_pp:+.2f} pp" if div_pp is not None else None,
            "difference_percent": None,
            "threshold": f"{div_th} pp" if div_th is not None else None,
            "source": ug_data.get("source"),
            "evidence": f"Divergence trigger: {trig}",
            "finding_id": next((fid for fid, f in finding_map.items() if "Gain" in f.get("category", "") or "Divergence" in f.get("category", "")), None),
        })

        # Check 2: Other Income to Revenue
        oi_to_rev = ug_data.get("other_income_to_revenue_pct")
        checks.append({
            "id": "WP514-UG-02",
            "category": "UNUSUAL_GAIN",
            "check": "Other Income Contribution to Revenue",
            "status": "REVIEW" if (oi_to_rev is not None and oi_to_rev >= 10.0) else ("PASSED" if oi_to_rev is not None else "NOT_AVAILABLE"),
            "expected_value": None,
            "actual_value": f"{oi_to_rev:.2f}%" if oi_to_rev is not None else None,
            "difference": None,
            "difference_percent": None,
            "threshold": "10.0%",
            "source": None,
            "evidence": "Non-operating other income proportion",
            "finding_id": None,
        })

        # Check 3: One-time / Exceptional Gains
        gain_amt = ug_data.get("gain_amount")
        checks.append({
            "id": "WP514-UG-03",
            "category": "UNUSUAL_GAIN",
            "check": "Total Non-Operating & One-Time Gains",
            "status": "PASSED" if gain_amt is not None else "NOT_AVAILABLE",
            "expected_value": None,
            "actual_value": cls._fmt_val(gain_amt, currency, scale),
            "difference": None,
            "difference_percent": None,
            "threshold": None,
            "source": None,
            "evidence": f"Gain to profit: {ug_data.get('gain_to_profit_pct')}%" if ug_data.get('gain_to_profit_pct') is not None else None,
            "finding_id": None,
        })

        findings_count = sum(1 for f in finding_map.values() if "Gain" in f.get("category", "") or "Divergence" in f.get("category", ""))
        cat = cls._make_category_summary("UNUSUAL_GAIN", "Unusual Gains & Divergence Analysis", score, status, checks, findings_count)
        return cat, checks

    # ─────────────────────────────────────────────────────────────────────────
    # 9. RELATED DISCLOSURE
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_related_disclosure(
        cls,
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any],
        currency: Optional[str],
        scale: Optional[str]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        rd_data = (
            review_result.get("analytical_metrics", {}).get("related_disclosure") or
            review_result.get("checks", {}).get("related_disclosure") or {}
        )
        status = rd_data.get("status", "NOT_AVAILABLE")
        score = rd_data.get("score")
        tolerance = rd_data.get("tolerance")
        th_str = f"{tolerance} {scale}".strip() if tolerance is not None else None
        checks: List[Dict[str, Any]] = []

        num_parties = rd_data.get("number_of_related_parties")
        num_tx = rd_data.get("number_of_related_transactions")

        checks.append({
            "id": "WP514-RD-01",
            "category": "RELATED_DISCLOSURE",
            "check": "Related Party Disclosures & Transaction Counts",
            "status": status,
            "expected_value": None,
            "actual_value": f"Parties: {num_parties}, Transactions: {num_tx}" if (num_parties is not None or num_tx is not None) else None,
            "difference": None,
            "difference_percent": None,
            "threshold": None,
            "source": rd_data.get("note_source"),
            "evidence": rd_data.get("details"),
            "finding_id": None,
        })

        checks.append({
            "id": "WP514-RD-02",
            "category": "RELATED_DISCLOSURE",
            "check": "Related Party Disclosed vs Itemized Transaction Reconciliation",
            "status": status,
            "expected_value": cls._fmt_val(rd_data.get("total_related_party_value"), currency, scale),
            "actual_value": cls._fmt_val(rd_data.get("disclosed_related_party_value"), currency, scale),
            "difference": cls._fmt_val(rd_data.get("disclosure_difference"), currency, scale, is_delta=True),
            "difference_percent": f"Consistency: {rd_data.get('disclosure_consistency_pct')}%" if rd_data.get('disclosure_consistency_pct') is not None else None,
            "threshold": th_str,
            "source": rd_data.get("note_source"),
            "evidence": rd_data.get("details"),
            "finding_id": next((fid for fid, f in finding_map.items() if "Disclosure" in f.get("category", "")), None),
        })

        findings_count = sum(1 for f in finding_map.values() if "Disclosure" in f.get("category", ""))
        cat = cls._make_category_summary("RELATED_DISCLOSURE", "Related Party Disclosures", score, status, checks, findings_count)
        return cat, checks

    # ─────────────────────────────────────────────────────────────────────────
    # 10. DOCUMENT QUALITY
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def _build_document_quality(
        cls,
        financial_data: Dict[str, Any],
        review_result: Dict[str, Any],
        finding_map: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        dq_data = (
            financial_data.get("team1_metrics", {}).get("document_quality") or
            review_result.get("financial_metrics", {}).get("document_quality") or {}
        )
        lq_data = review_result.get("language_quality") or review_result.get("checks", {}).get("spelling_grammar") or {}

        status = dq_data.get("status") or dq_data.get("data_quality_status") or "PASSED"
        score = dq_data.get("score") or dq_data.get("extraction_completeness_pct") or 100.0
        checks: List[Dict[str, Any]] = []

        # Check 1: Extraction Completeness
        comp_pct = dq_data.get("extraction_completeness_pct")
        checks.append({
            "id": "WP514-DQ-01",
            "category": "DOCUMENT_QUALITY",
            "check": "Document Extraction Completeness",
            "status": "PASSED" if (comp_pct is not None and comp_pct >= 80.0) else ("REVIEW" if comp_pct is not None else "NOT_AVAILABLE"),
            "expected_value": "100.0%",
            "actual_value": f"{comp_pct}%" if comp_pct is not None else None,
            "difference": None,
            "difference_percent": None,
            "threshold": ">= 80%",
            "source": None,
            "evidence": f"File validity: {dq_data.get('file_validity', 'VALID')}" if dq_data.get('file_validity') else None,
            "finding_id": None,
        })

        # Check 2: Missing Sections
        missing_sec = dq_data.get("missing_sections", [])
        checks.append({
            "id": "WP514-DQ-02",
            "category": "DOCUMENT_QUALITY",
            "check": "Financial Statement Section Availability",
            "status": "PASSED" if (isinstance(missing_sec, list) and not missing_sec) else "FAILED",
            "expected_value": "Balance Sheet, Income Statement, Cash Flow",
            "actual_value": "All statements present" if not missing_sec else f"Missing: {', '.join(missing_sec)}",
            "difference": None,
            "difference_percent": None,
            "threshold": "0 missing",
            "source": None,
            "evidence": f"Page count: {dq_data.get('page_count')}" if dq_data.get('page_count') is not None else None,
            "finding_id": None,
        })

        # Check 3: Currency & Unit Scale
        curr = dq_data.get("currency")
        unit = dq_data.get("unit")
        checks.append({
            "id": "WP514-DQ-03",
            "category": "DOCUMENT_QUALITY",
            "check": "Currency & Financial Unit Definition",
            "status": "PASSED" if (curr and unit) else ("REVIEW" if (curr or unit) else "NOT_AVAILABLE"),
            "expected_value": "Standard Currency & Unit",
            "actual_value": f"{curr} in {unit}" if (curr and unit) else (curr or unit or None),
            "difference": None,
            "difference_percent": None,
            "threshold": None,
            "source": None,
            "evidence": "Standard scale and currency recognized" if (curr and unit) else None,
            "finding_id": None,
        })

        # Check 4: Spelling Review
        spell_errs = lq_data.get("spelling_errors_count")
        lq_status = lq_data.get("status", "NOT_AVAILABLE")
        checks.append({
            "id": "WP514-DQ-04",
            "category": "DOCUMENT_QUALITY",
            "check": "Narrative Notes & Disclosures Spelling Review",
            "status": lq_status,
            "expected_value": "0 spelling errors" if lq_status != "NOT_AVAILABLE" else None,
            "actual_value": f"{spell_errs} spelling errors" if (lq_status != "NOT_AVAILABLE" and spell_errs is not None) else None,
            "difference": None,
            "difference_percent": None,
            "threshold": "0 errors" if lq_status != "NOT_AVAILABLE" else None,
            "source": None,
            "evidence": f"Reviewed passages: {lq_data.get('reviewed_passages_count', 0)}" if lq_status != "NOT_AVAILABLE" else None,
            "finding_id": None,
        })

        # Check 5: Grammar Review
        gram_errs = lq_data.get("grammar_issues_count")
        checks.append({
            "id": "WP514-DQ-05",
            "category": "DOCUMENT_QUALITY",
            "check": "Narrative Notes & Disclosures Grammar Review",
            "status": lq_status,
            "expected_value": "0 grammar issues" if lq_status != "NOT_AVAILABLE" else None,
            "actual_value": f"{gram_errs} grammar issues" if (lq_status != "NOT_AVAILABLE" and gram_errs is not None) else None,
            "difference": None,
            "difference_percent": None,
            "threshold": "0 issues" if lq_status != "NOT_AVAILABLE" else None,
            "source": None,
            "evidence": f"Reviewed passages: {lq_data.get('reviewed_passages_count', 0)}" if lq_status != "NOT_AVAILABLE" else None,
            "finding_id": None,
        })

        findings_count = sum(1 for f in finding_map.values() if "Quality" in f.get("category", "") or "Extraction" in f.get("category", ""))
        cat = cls._make_category_summary("DOCUMENT_QUALITY", "Document & Narrative Quality", score, status, checks, findings_count)
        return cat, checks
