"""
Segment 2 Review Engine — Master Orchestrator.

Wires all 10 check modules, the findings builder, and the scorer into one
ReviewEngine class. Produces a ReviewResultContract-compliant dict that
can be serialised directly to review_result.json.

Usage:
    from segment2_financial_engine.src.engine import ReviewEngine
    result = ReviewEngine.run("outputs/financial_data.json")
    ReviewEngine.save(result, "outputs/review_result.json")
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from .loader import load, current_and_previous, get_company_info, get_periods

from .checks import (
    math_accuracy,
    cash_flow_review,
    prior_year_tieout,
    internal_consistency,
    analytical_engine,
    ratios,
    unusual_fluctuations,
    unusual_gain,
    related_disclosure,
    document_quality_guard,
)
from .aggregator import findings_builder, scorer


class ReviewEngine:
    """
    Main entry point for Phase 2 Financial Review.

    Call ReviewEngine.run(input_path) to process a financial_data.json file.
    """

    ENGINE_VERSION = "2.0.0"

    @classmethod
    def run(cls, input_path: str) -> Dict[str, Any]:
        """
        Run all 10 checks and return a ReviewResultContract-compliant dict.

        Args:
            input_path : path to financial_data.json (Phase 1 output)

        Returns:
            dict matching schema/review_schema.py ReviewResultContract
        """
        data = load(input_path)
        curr, prev, base = current_and_previous(data)
        company = get_company_info(data)

        # ------------------------------------------------------------------
        # Run all 10 checks
        # ------------------------------------------------------------------
        check_results: Dict[str, Any] = {
            "mathematical_accuracy":    math_accuracy.run(data),
            "cash_flow_reconciliation": cash_flow_review.run(data),
            "prior_year_tieout":        prior_year_tieout.run(data),
            "internal_consistency":     internal_consistency.run(data),
            "analytical_metrics":       analytical_engine.run(data),
            "financial_ratios":         ratios.run(data),
            "unusual_fluctuations":     unusual_fluctuations.run(data),
            "unusual_gain_analysis":    unusual_gain.run(data),
            "related_disclosure":       related_disclosure.run(data),
            "document_quality":         document_quality_guard.run(data),
        }

        # ------------------------------------------------------------------
        # Extract structured metric groups from check results
        # ------------------------------------------------------------------
        ratios_result  = check_results["financial_ratios"]
        analytic_result = check_results["analytical_metrics"]
        ug_result      = check_results["unusual_gain_analysis"]

        financial_metrics = {
            "liquidity":      ratios_result.get("liquidity",      {}),
            "leverage":       ratios_result.get("leverage",       {}),
            "profitability":  ratios_result.get("profitability",  {}),
            "efficiency":     ratios_result.get("efficiency",     {}),
        }

        analytical_metrics = {
            "growth_rates":          analytic_result.get("growth_rates",         {}),
            "unusual_fluctuations":  analytic_result.get("unusual_fluctuations", []),
            "unusual_gain_analysis": {
                k: v for k, v in ug_result.items()
                if k not in ("score", "status", "reason", "issues")
            },
        }

        # ------------------------------------------------------------------
        # Checks block (mirrors sample_review_result.json structure)
        # ------------------------------------------------------------------
        checks_block = {
            "mathematical_accuracy": check_results["mathematical_accuracy"],
            "cash_flow":             check_results["cash_flow_reconciliation"],
            "prior_year_tieout":     check_results["prior_year_tieout"],
            "internal_consistency":  check_results["internal_consistency"],
            "related_disclosure":    check_results["related_disclosure"],
            "document_quality":      check_results["document_quality"],
        }

        # ------------------------------------------------------------------
        # Findings aggregation & scoring
        # ------------------------------------------------------------------
        findings = findings_builder.build(check_results, data)
        overall  = scorer.compute(check_results)

        # ------------------------------------------------------------------
        # Assemble final ReviewResultContract
        # ------------------------------------------------------------------
        doc_id  = data.get("metadata", {}).get("document_id", "UNKNOWN")
        src_file = data.get("metadata", {}).get("source_file", "UNKNOWN")

        return {
            "metadata": {
                "review_id":          f"REV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "document_id":        doc_id,
                "source_file":        src_file,
                "company_name":       company.get("name", "Unknown"),
                "review_timestamp":   datetime.now(timezone.utc).isoformat(),
                "engine_version":     cls.ENGINE_VERSION,
                "analyzed_periods": {
                    "current_period":  curr,
                    "previous_period": prev,
                    "base_period":     base,
                },
            },
            "financial_metrics":  financial_metrics,
            "analytical_metrics": analytical_metrics,
            "checks":             checks_block,
            "findings":           findings,
            "overall_score":      overall,
        }

    @classmethod
    def save(cls, result: Dict[str, Any], output_path: str) -> None:
        """Serialise review result dict to JSON on disk."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
