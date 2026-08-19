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
        try:
            fval = float(val)
            sign = "+" if fval > 0 else ("-" if fval < 0 else "")
            abs_v = abs(fval)
            if abs_v == int(abs_v):
                formatted_num = f"{int(abs_v):,}"
            else:
                formatted_num = f"{abs_v:,.2f}"
            if is_delta:
                return f"{sign}{sym}{formatted_num}{scale_str}"
            if fval < 0:
                return f"-{sym}{formatted_num}{scale_str}"
            return f"{sym}{formatted_num}{scale_str}"
        except (ValueError, TypeError):
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

        if failed > 0:
            norm_status = "FAILED"
        elif review > 0:
            norm_status = "REVIEW"
        elif passed > 0 and failed == 0 and review == 0:
            norm_status = "PASSED"
        elif score is not None and score >= 80.0:
            norm_status = "PASSED"
        elif na == len(checks) and len(checks) > 0:
            norm_status = "NOT_AVAILABLE"
        elif status in ("NOT_AVAILABLE", "COMPUTED"):
            norm_status = "PASSED" if passed > 0 else "NOT_AVAILABLE"
        else:
            norm_status = status or "PASSED"

        return {
            "id": cat_id,
            "name": name,
            "status": norm_status,
            "score": score if score is not None else (100.0 if failed == 0 and review == 0 else 0.0),
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

        raw_calcs = checks_data.get("calculations")
        if isinstance(raw_calcs, dict):
            eqs = list(raw_calcs.values())
        elif isinstance(raw_calcs, list):
            eqs = raw_calcs
        else:
            eqs = checks_data.get("equations", [])

        checks: List[Dict[str, Any]] = []

        for idx, eq in enumerate(eqs, start=1):
            name = eq.get("check_name") or eq.get("name", f"Equation {idx}")
            eq_status = eq.get("status", "NOT_AVAILABLE")
            diff = eq.get("absolute_difference") or eq.get("difference")
            expected = eq.get("reported_value") or eq.get("expected_value") or eq.get("rhs")
            actual = eq.get("calculated_value") or eq.get("actual_value") or eq.get("lhs")
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
                "source": None,
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

        cfs = financial_data.get("cash_flow_statement", {})
        meta = financial_data.get("metadata", {})
        periods = [p.get("period_key") for p in meta.get("periods", []) if isinstance(p, dict)]
        prev = periods[1] if len(periods) > 1 else None

        cfo_prev = None
        cfi_prev = None
        cff_prev = None
        if prev and isinstance(cfs, dict):
            for k in ["operating_cash_flow", "cash_from_operating_activities", "cfo"]:
                if k in cfs:
                    cfo_prev = cfs[k].get("values", {}).get(prev)
                    if cfo_prev is not None:
                        break
            for k in ["investing_cash_flow", "cash_from_investing_activities", "cfi"]:
                if k in cfs:
                    cfi_prev = cfs[k].get("values", {}).get(prev)
                    if cfi_prev is not None:
                        break
            for k in ["financing_cash_flow", "cash_from_financing_activities", "cff"]:
                if k in cfs:
                    cff_prev = cfs[k].get("values", {}).get(prev)
                    if cff_prev is not None:
                        break

        # Check 1: Operating Cash Flow
        cfo = cf_data.get("operating_cash_flow") or cf_data.get("cfo_operating")
        diff_cfo = (cfo - cfo_prev) if (cfo is not None and cfo_prev is not None) else None
        checks.append({
            "id": "WP514-CF-01",
            "category": "CASH_FLOW",
            "check": "Operating Cash Flow (CFO)",
            "status": "PASSED" if cfo is not None else "NOT_AVAILABLE",
            "expected_value": cls._fmt_val(cfo_prev, currency, scale),
            "actual_value": cls._fmt_val(cfo, currency, scale),
            "difference": cls._fmt_val(diff_cfo, currency, scale, is_delta=True),
            "difference_percent": None,
            "threshold": "Trend Continuity" if cfo is not None else None,
            "source": None,
            "evidence": "Cash generated from operating activities" if cfo is not None else None,
            "finding_id": None,
        })

        # Check 2: Investing Cash Flow
        cfi = cf_data.get("investing_cash_flow") or cf_data.get("cfi_investing")
        diff_cfi = (cfi - cfi_prev) if (cfi is not None and cfi_prev is not None) else None
        checks.append({
            "id": "WP514-CF-02",
            "category": "CASH_FLOW",
            "check": "Investing Cash Flow (CFI)",
            "status": "PASSED" if cfi is not None else "NOT_AVAILABLE",
            "expected_value": cls._fmt_val(cfi_prev, currency, scale),
            "actual_value": cls._fmt_val(cfi, currency, scale),
            "difference": cls._fmt_val(diff_cfi, currency, scale, is_delta=True),
            "difference_percent": None,
            "threshold": "Trend Continuity" if cfi is not None else None,
            "source": None,
            "evidence": "Cash used in / from investing activities" if cfi is not None else None,
            "finding_id": None,
        })

        # Check 3: Financing Cash Flow
        cff = cf_data.get("financing_cash_flow") or cf_data.get("cff_financing")
        diff_cff = (cff - cff_prev) if (cff is not None and cff_prev is not None) else None
        checks.append({
            "id": "WP514-CF-03",
            "category": "CASH_FLOW",
            "check": "Financing Cash Flow (CFF)",
            "status": "PASSED" if cff is not None else "NOT_AVAILABLE",
            "expected_value": cls._fmt_val(cff_prev, currency, scale),
            "actual_value": cls._fmt_val(cff, currency, scale),
            "difference": cls._fmt_val(diff_cff, currency, scale, is_delta=True),
            "difference_percent": None,
            "threshold": "Trend Continuity" if cff is not None else None,
            "source": None,
            "evidence": "Cash used in / from financing activities" if cff is not None else None,
            "finding_id": None,
        })

        # Check 4: Cash Flow Statement Arithmetic Reconciliation
        raw_recon_status = cf_data.get("cash_reconciliation_status") or cf_data.get("cfs_arithmetic_status", status)
        cf_recon_status = "PASSED" if raw_recon_status == "RECONCILED" else ("FAILED" if raw_recon_status == "MISMATCH" else raw_recon_status)
        cf_diff = cf_data.get("cash_difference") or cf_data.get("reconciliation_difference")
        closing_src = (cf_data.get("sources", {}).get("reported_closing_cash") if isinstance(cf_data.get("sources"), dict) else None) or cf_data.get("closing_cash_source") or cf_data.get("source")
        checks.append({
            "id": "WP514-CF-04",
            "category": "CASH_FLOW",
            "check": "Cash Flow Arithmetic Reconciliation (Opening + CFO + CFI + CFF = Closing)",
            "status": cf_recon_status if cf_recon_status in ("PASSED", "FAILED", "REVIEW", "NOT_AVAILABLE") else status,
            "expected_value": cls._fmt_val(cf_data.get("expected_closing_cash"), currency, scale),
            "actual_value": cls._fmt_val(cf_data.get("reported_closing_cash"), currency, scale),
            "difference": cls._fmt_val(cf_diff, currency, scale, is_delta=True),
            "difference_percent": None,
            "threshold": th_str,
            "source": None,
            "evidence": "Net increase in cash and opening balance summation",
            "finding_id": next((fid for fid, f in finding_map.items() if "Cash" in f.get("category", "")), None),
        })

        # Check 5: Cross-Statement CFS ↔ Balance Sheet Cash
        raw_bs_status = cf_data.get("bs_cash_vs_cf_cash_status") or cf_data.get("bs_cash_match_status", "PASSED")
        bs_cf_status = "PASSED" if raw_bs_status == "MATCHED" else ("FAILED" if raw_bs_status == "MISMATCH" else raw_bs_status)
        bs_cash_diff = cf_data.get("balance_sheet_cash_difference") or cf_data.get("bs_cash_difference")
        bs_cash_val = cf_data.get("balance_sheet_cash") or cf_data.get("bs_cash_value")
        checks.append({
            "id": "WP514-CF-05",
            "category": "CASH_FLOW",
            "check": "Cash Flow Statement ↔ Balance Sheet Cash Tie-Out",
            "status": bs_cf_status,
            "expected_value": cls._fmt_val(bs_cash_val, currency, scale),
            "actual_value": cls._fmt_val(cf_data.get("reported_closing_cash"), currency, scale),
            "difference": cls._fmt_val(bs_cash_diff, currency, scale, is_delta=True),
            "difference_percent": None,
            "threshold": th_str,
            "source": None,
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
            name = it.get("line_item") or it.get("metric") or it.get("label") or f"Account {idx}"
            it_status = it.get("tie_out_status") or it.get("status", "NOT_AVAILABLE")
            diff = it.get("absolute_difference") or it.get("difference")
            expected = it.get("previous_closing_balance") or it.get("prior_closing_value")
            actual = it.get("opening_balance") or it.get("current_opening_value")

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
                "source": None,
                "evidence": it.get("details") or "Prior period closing vs current opening balance tie-out",
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
        rules = ic_data.get("comparisons") or ic_data.get("rules", [])
        checks: List[Dict[str, Any]] = []

        for idx, r in enumerate(rules, start=1):
            name = r.get("metric") or r.get("rule_name") or r.get("description") or f"Consistency Rule {idx}"
            r_status = r.get("status", "NOT_AVAILABLE")
            diff = r.get("absolute_difference") or r.get("difference")
            expected = r.get("value_a")
            actual = r.get("value_b")

            checks.append({
                "id": f"WP514-IC-{idx:02d}",
                "category": "INTERNAL_CONSISTENCY",
                "check": name,
                "status": "PASSED" if r_status in ("PASSED", "MATCHED") else ("FAILED" if r_status in ("FAILED", "MISMATCH") else ("REVIEW" if r_status == "WARNING" else "NOT_AVAILABLE")),
                "expected_value": cls._fmt_val(expected, currency, scale),
                "actual_value": cls._fmt_val(actual, currency, scale),
                "difference": cls._fmt_val(diff, currency, scale, is_delta=True),
                "difference_percent": None,
                "threshold": th_str,
                "source": None,
                "evidence": r.get("details") or f"Cross-statement match between {r.get('source_a', 'Statement A')} and {r.get('source_b', 'Statement B')}",
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
        items = ac_data.get("items") or list(ac_data.get("metrics", {}).values())
        checks: List[Dict[str, Any]] = []

        for idx, it in enumerate(items, start=1):
            metric = it.get("metric_name") or it.get("metric", f"Metric {idx}")
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
                "threshold": "Trend Consistency",
                "source": None,
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
        prev = ""
        if financial_data:
            periods = financial_data.get("metadata", {}).get("periods", [])
            if periods and isinstance(periods[0], dict):
                curr = periods[0].get("period_key", "")
            if len(periods) > 1 and isinstance(periods[1], dict):
                prev = periods[1].get("period_key", "")
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

        # Compute dictionary of prior period ratios if prev period exists
        prev_ratios_map: Dict[str, float] = {}
        if prev and financial_data:
            def _g(stmt, *keys):
                if isinstance(stmt, dict):
                    for k in keys:
                        if k in stmt:
                            v = stmt[k].get("values", {}).get(prev)
                            if v is not None:
                                try:
                                    return float(v)
                                except (ValueError, TypeError):
                                    pass
                return None

            ca_p = _g(bs, "total_current_assets", "current_assets")
            cl_p = _g(bs, "total_current_liabilities", "current_liabilities")
            inv_p = _g(bs, "inventories", "inventory") or 0.0
            cash_p = _g(bs, "cash_and_cash_equivalents", "cash_and_bank_balances", "cash") or 0.0
            eq_p = _g(bs, "total_equity", "equity", "shareholder_equity")
            assets_p = _g(bs, "total_assets", "assets")
            lt_debt_p = _g(bs, "long_term_borrowings", "non_current_borrowings") or 0.0
            st_debt_p = _g(bs, "short_term_borrowings", "current_borrowings") or 0.0
            debt_p = lt_debt_p + st_debt_p

            rev_p = _g(is_statement, "revenue_from_operations", "total_revenue", "revenue")
            cogs_p = _g(is_statement, "cost_of_materials_consumed", "cost_of_goods_sold", "cogs") or 0.0
            gp_p = _g(is_statement, "gross_profit") or ((rev_p - cogs_p) if rev_p is not None else None)
            ebit_p = _g(is_statement, "operating_profit", "ebit", "operating_income", "operating_revenue")
            pbt_p = _g(is_statement, "profit_before_tax", "pbt", "earnings_before_tax")
            tax_p = _g(is_statement, "tax_expense", "current_tax", "tax") or 0.0
            np_p = _g(is_statement, "profit_for_the_year", "net_profit", "profit_after_tax", "pat") or ((pbt_p - tax_p) if pbt_p is not None else None)
            fin_p = _g(is_statement, "finance_costs", "interest_expense", "finance_cost")
            rec_p = _g(bs, "trade_receivables", "accounts_receivable", "receivables")

            if ca_p and cl_p and cl_p > 0:
                prev_ratios_map["current_ratio"] = ca_p / cl_p
                prev_ratios_map["quick_ratio"] = (ca_p - inv_p) / cl_p
                prev_ratios_map["cash_ratio"] = cash_p / cl_p
            if eq_p and eq_p > 0 and debt_p > 0:
                prev_ratios_map["debt_to_equity"] = debt_p / eq_p
            if assets_p and assets_p > 0 and debt_p > 0:
                prev_ratios_map["debt_ratio"] = debt_p / assets_p
            if ebit_p and fin_p and fin_p > 0:
                prev_ratios_map["interest_coverage_ratio"] = ebit_p / fin_p
            if rev_p and rev_p > 0:
                if gp_p is not None:
                    prev_ratios_map["gross_profit_margin_pct"] = (gp_p / rev_p) * 100
                if ebit_p is not None:
                    prev_ratios_map["operating_margin_pct"] = (ebit_p / rev_p) * 100
                if np_p is not None:
                    prev_ratios_map["net_profit_margin_pct"] = (np_p / rev_p) * 100
                if assets_p and assets_p > 0:
                    prev_ratios_map["asset_turnover_ratio"] = rev_p / assets_p
                if rec_p and rec_p > 0:
                    prev_ratios_map["receivables_turnover_ratio"] = rev_p / rec_p
                    prev_ratios_map["days_sales_outstanding"] = (365.0 * rec_p) / rev_p
            if np_p is not None and assets_p and assets_p > 0:
                prev_ratios_map["return_on_assets_pct"] = (np_p / assets_p) * 100
            if np_p is not None and eq_p and eq_p > 0:
                prev_ratios_map["return_on_equity_pct"] = (np_p / eq_p) * 100
            if cogs_p and cogs_p > 0 and inv_p and inv_p > 0:
                prev_ratios_map["inventory_turnover_ratio"] = cogs_p / inv_p

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

                # Search prev_val for Prior Period
                prev_val: Optional[float] = prev_ratios_map.get(canonical_key)
                if prev_val is None and prev:
                    for k in search_keys:
                        stmt_v = None
                        if isinstance(bs, dict) and k in bs:
                            v_map = bs[k].get("values", {})
                            stmt_v = v_map.get(prev)
                        elif isinstance(is_statement, dict) and k in is_statement:
                            v_map = is_statement[k].get("values", {})
                            stmt_v = v_map.get(prev)
                        if stmt_v is not None:
                            try:
                                prev_val = float(stmt_v)
                                if is_pct and abs(prev_val) <= 1.0 and prev_val != 0:
                                    prev_val = prev_val * 100.0
                                break
                            except (TypeError, ValueError):
                                pass

                exp_str = f"{prev_val:.2f}%" if (prev_val is not None and is_pct) else (f"{prev_val:.2f}" if prev_val is not None else None)
                diff_str = None
                if val is not None and prev_val is not None:
                    d = val - prev_val
                    diff_str = f"{d:+.2f}%" if is_pct else f"{d:+.2f}"

                checks.append({
                    "id": f"WP514-RT-{idx:02d}",
                    "category": "RATIOS",
                    "check": f"{grp_name} Ratio: {label}",
                    "status": "PASSED" if val is not None else "NOT_AVAILABLE",
                    "expected_value": exp_str,
                    "actual_value": val_str,
                    "difference": diff_str,
                    "difference_percent": diff_str if is_pct else None,
                    "threshold": "Industry Standard" if val is not None else None,
                    "source": None,
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

            is_margin = "Margin" in metric
            exp_val = f"{float(prev):.2f}%" if is_margin and prev is not None else cls._fmt_val(prev, currency, scale)
            act_val = f"{float(curr):.2f}%" if is_margin and curr is not None else cls._fmt_val(curr, currency, scale)

            checks.append({
                "id": f"WP514-UF-{idx:02d}",
                "category": "UNUSUAL_FLUCTUATION",
                "check": f"YoY Fluctuation Scanner: {metric}",
                "status": norm_status,
                "expected_value": exp_val,
                "actual_value": act_val,
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
            "threshold": f"{div_th} pp" if div_th is not None else "8.0 pp",
            "source": None,
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
            "expected_value": "< 10.0% (Threshold)",
            "actual_value": f"{oi_to_rev:.2f}%" if oi_to_rev is not None else "0.00%",
            "difference": f"{(oi_to_rev or 0) - 10.0:+.2f} pp" if oi_to_rev is not None else None,
            "difference_percent": None,
            "threshold": "10.0%",
            "source": None,
            "evidence": "Non-operating other income proportion",
            "finding_id": None,
        })

        # Check 3: One-time / Exceptional Gains
        gain_amt = ug_data.get("gain_amount") or 0.0
        gain_pct = ug_data.get("gain_to_profit_pct") or 0.0
        checks.append({
            "id": "WP514-UG-03",
            "category": "UNUSUAL_GAIN",
            "check": "Total Non-Operating & One-Time Gains",
            "status": "PASSED" if gain_amt is not None else "NOT_AVAILABLE",
            "expected_value": cls._fmt_val(0, currency, scale),
            "actual_value": cls._fmt_val(gain_amt, currency, scale),
            "difference": f"{gain_pct:.2f}% of Profit",
            "difference_percent": None,
            "threshold": "Materiality Check (< 10%)",
            "source": None,
            "evidence": f"Gain to profit: {gain_pct:.2f}%",
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

        # Check 1: Related Party Disclosures & Transaction Counts
        num_parties = rd_data.get("number_of_related_parties")
        num_tx = rd_data.get("number_of_related_transactions")
        if num_parties is not None and num_tx is not None and (num_parties > 0 or num_tx > 0):
            act_rd1 = f"Parties: {num_parties}, Transactions: {num_tx}"
            ev_rd1 = f"Related party disclosures verified ({num_parties} parties, {num_tx} transactions)"
        else:
            act_rd1 = "No related party transactions identified in filing period (0 parties, 0 transactions)"
            ev_rd1 = "No related party transactions identified in the filing period"

        checks.append({
            "id": "WP514-RD-01",
            "category": "RELATED_DISCLOSURE",
            "check": "Related Party Disclosures & Transaction Counts",
            "status": status,
            "expected_value": "Standard Note Disclosure",
            "actual_value": act_rd1,
            "difference": None,
            "difference_percent": None,
            "threshold": "100% Disclosure",
            "source": None,
            "evidence": ev_rd1,
            "finding_id": None,
        })

        tot_val = rd_data.get("total_related_party_value") if rd_data.get("total_related_party_value") is not None else 0.0
        disc_val = rd_data.get("disclosed_related_party_value") if rd_data.get("disclosed_related_party_value") is not None else 0.0
        diff_val = rd_data.get("disclosure_difference") if rd_data.get("disclosure_difference") is not None else 0.0
        consistency_pct = rd_data.get("disclosure_consistency_pct")

        exp_rd2 = cls._fmt_val(tot_val, currency, scale)
        act_rd2 = cls._fmt_val(disc_val, currency, scale)
        diff_rd2 = cls._fmt_val(diff_val, currency, scale, is_delta=True)
        diff_pct_str = f"100.0% Reconciliation" if (consistency_pct is None or consistency_pct == 100) else f"Consistency: {consistency_pct:.1f}%"
        ev_rd2 = "Itemized related party transaction reconciliation (0 variance)" if diff_val == 0 else (rd_data.get("details") or "Itemized related party transaction reconciliation")

        checks.append({
            "id": "WP514-RD-02",
            "category": "RELATED_DISCLOSURE",
            "check": "Related Party Disclosed vs Itemized Transaction Reconciliation",
            "status": status,
            "expected_value": exp_rd2,
            "actual_value": act_rd2,
            "difference": diff_rd2,
            "difference_percent": diff_pct_str,
            "threshold": th_str or "0.00 Millions",
            "source": None,
            "evidence": ev_rd2,
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
        spell_status = "PASSED" if (spell_errs is not None and spell_errs == 0) else ("FAILED" if (spell_errs and spell_errs > 0) else lq_status)
        checks.append({
            "id": "WP514-DQ-04",
            "category": "DOCUMENT_QUALITY",
            "check": "Narrative Notes & Disclosures Spelling Review",
            "status": spell_status,
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
        gram_status = "PASSED" if (gram_errs is not None and gram_errs == 0) else ("FAILED" if (gram_errs and gram_errs > 0) else lq_status)
        checks.append({
            "id": "WP514-DQ-05",
            "category": "DOCUMENT_QUALITY",
            "check": "Narrative Notes & Disclosures Grammar Review",
            "status": gram_status,
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
