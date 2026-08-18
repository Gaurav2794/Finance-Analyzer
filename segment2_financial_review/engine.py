"""
Segment 2 Financial Review Engine.

Orchestrates the full Team 2 review pipeline against a Team 1 financial_data.json.

Architecture:
    financial_data.json
            ↓
    Input Validation (schema guard)
            ↓
    Document Quality Gate (Team 1 metrics passthrough)
            ↓
    Financial Review Modules (deterministic, Decimal-based)
       ├── Mathematical Accuracy
       ├── Cash Flow Reconciliation
       ├── Prior-Year Tie-Out
       └── Internal Consistency
            ↓
    Analytical Review Modules
       ├── Analytical Comparison (YoY Growth)
       ├── Financial Ratios
       ├── Unusual Fluctuation
       ├── Unusual Gain
       └── Related Party Disclosure
            ↓
    Finding Engine  →  per-finding classification + scoring
            ↓
    Scoring Engine  →  weighted overall score + band
            ↓
    review_result.json

Rules:
    - Does NOT touch Team 1 code.
    - Does NOT duplicate extraction logic.
    - No LLM calls.
    - Never fabricates missing values.
    - Preserves source / page evidence end-to-end.
    - Fully deterministic and reproducible.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

# ── Check Engines ────────────────────────────────────────────────────────────
from segment2_financial_review.checks.mathematical_accuracy import MathematicalAccuracyEngine
from segment2_financial_review.checks.cash_flow import CashFlowEngine
from segment2_financial_review.checks.prior_year_tieout import PriorYearTieOutEngine
from segment2_financial_review.checks.internal_consistency import InternalConsistencyEngine

# ── Analytics Engines ────────────────────────────────────────────────────────
from segment2_financial_review.analytics.growth import AnalyticalComparisonEngine
from segment2_financial_review.analytics.ratios import FinancialRatiosEngine
from segment2_financial_review.analytics.unusual_fluctuation import UnusualFluctuationScanner
from segment2_financial_review.analytics.unusual_gain import UnusualGainEngine
from segment2_financial_review.analytics.related_disclosure import RelatedDisclosureEngine

# ── Findings & Scoring ───────────────────────────────────────────────────────
from segment2_financial_review.findings.finding_engine import FindingEngine


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

_LOG_FMT = "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s"
logging.basicConfig(format=_LOG_FMT, datefmt="%H:%M:%S")
log = logging.getLogger("segment2.engine")


# ─────────────────────────────────────────────────────────────────────────────
# Input Schema Validation (lightweight guard — not a full schema replication)
# ─────────────────────────────────────────────────────────────────────────────

class _PeriodSchema(BaseModel):
    period_key: str
    label: Optional[str] = None
    is_audited: Optional[bool] = None


class _CompanySchema(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None
    scale: Optional[str] = None
    reporting_standard: Optional[str] = None


class _MetadataSchema(BaseModel):
    document_id: str
    periods: List[_PeriodSchema] = Field(default_factory=list)
    company: Optional[_CompanySchema] = None
    extraction_timestamp: Optional[str] = None
    parser_version: Optional[str] = None

    @field_validator("periods")
    @classmethod
    def at_least_one_period(cls, v: list) -> list:
        if not v:
            raise ValueError("financial_data.json must contain at least one period in metadata.periods")
        return v


class FinancialDataInputSchema(BaseModel):
    """
    Lightweight Pydantic guard for Team 1 output.
    Validates that the minimum required top-level keys are present.
    Does NOT re-validate every extracted line item — Team 1 owns that contract.
    """
    model_config = ConfigDict(extra="allow")

    metadata: _MetadataSchema
    balance_sheet: Dict[str, Any]
    income_statement: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Document Quality Gate (reads from team1_metrics — never recomputes)
# ─────────────────────────────────────────────────────────────────────────────

class _DocumentQualityResult:
    """
    Thin wrapper around team1_metrics.document_quality.
    Produces a score and status without re-extracting anything.
    """

    def __init__(self, data: Dict[str, Any]):
        dq = data.get("team1_metrics", {}).get("document_quality", {})
        self.extraction_completeness_pct: Optional[float] = dq.get("extraction_completeness_pct")
        self.missing_critical_values_count: int = int(dq.get("missing_values", 0) or 0)
        self.missing_sections: List[str] = dq.get("missing_sections", []) or []
        self.data_quality_status: str = dq.get("data_quality_status", "UNKNOWN")
        self.required_statement_availability: str = self._check_availability(data)
        self.issues: List[str] = []
        self.score: float = self._compute_score()
        self.status: str = self._compute_status()

    @staticmethod
    def _check_availability(data: Dict[str, Any]) -> str:
        has_bs = bool(data.get("balance_sheet"))
        has_is = bool(data.get("income_statement"))
        has_cf = bool(data.get("cash_flow_statement"))
        if has_bs and has_is and has_cf:
            return "ALL_PRESENT"
        if has_bs and has_is:
            return "PARTIAL"
        return "INCOMPLETE"

    def _compute_score(self) -> float:
        base = self.extraction_completeness_pct or 0.0
        penalty = min(50.0, self.missing_critical_values_count * 5.0)
        if self.required_statement_availability == "INCOMPLETE":
            penalty += 30.0
        elif self.required_statement_availability == "PARTIAL":
            penalty += 10.0
        return max(0.0, round(base - penalty, 2))

    def _compute_status(self) -> str:
        if self.score >= 80:
            return "PASSED"
        if self.score >= 60:
            return "WARNING"
        if self.score > 0:
            return "FAILED"
        return "NOT_AVAILABLE"

    def model_dump(self) -> Dict[str, Any]:
        return {
            "extraction_completeness_pct": self.extraction_completeness_pct,
            "required_statement_availability": self.required_statement_availability,
            "missing_critical_values_count": self.missing_critical_values_count,
            "missing_sections": self.missing_sections,
            "data_quality_status": self.data_quality_status,
            "score": self.score,
            "status": self.status,
            "issues": self.issues,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Decimal-safe JSON serialiser
# ─────────────────────────────────────────────────────────────────────────────

class _DecimalEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def _to_json_safe(obj: Any) -> Any:
    """Recursively convert Decimal, Pydantic models to JSON-safe types."""
    if obj is None:
        return None
    if isinstance(obj, Decimal):
        return str(obj)
    if hasattr(obj, "model_dump"):
        return _to_json_safe(obj.model_dump())
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(i) for i in obj]
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# Master Engine
# ─────────────────────────────────────────────────────────────────────────────

class Segment2Engine:
    """
    Team 2 Financial Review Orchestrator.

    Usage:
        engine = Segment2Engine(verbosity=logging.INFO)
        result = engine.run(data_dict)
        engine.save(result, "outputs/review_result.json")
    """

    def __init__(self, verbosity: int = logging.INFO):
        log.setLevel(verbosity)

    # ── Step helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _step(name: str) -> None:
        log.info("  ┣━ Running: %s", name)

    @staticmethod
    def _ok(name: str, detail: str = "") -> None:
        log.info("  ┃  ✓ %s%s", name, f" — {detail}" if detail else "")

    @staticmethod
    def _warn(name: str, detail: str = "") -> None:
        log.warning("  ┃  ⚠ %s%s", name, f" — {detail}" if detail else "")

    @staticmethod
    def _safe_run(name: str, fn, *args, **kwargs):
        """Run an engine safely; return None on any exception."""
        try:
            result = fn(*args, **kwargs)
            return result
        except Exception as exc:
            log.error("  ┃  ✗ %s FAILED: %s", name, exc)
            return None

    # ── Input validation ──────────────────────────────────────────────────────

    def validate_input(self, data: Dict[str, Any]) -> FinancialDataInputSchema:
        log.info("  ┣━ Validating input schema …")
        try:
            validated = FinancialDataInputSchema(**data)
            periods = [p.period_key for p in validated.metadata.periods]
            log.info("  ┃  ✓ Schema valid — document_id=%s, periods=%s",
                     validated.metadata.document_id, periods)
            return validated
        except ValidationError as exc:
            log.error("  ┃  ✗ Input validation failed:\n%s", exc)
            raise

    # ── Main run ──────────────────────────────────────────────────────────────

    def run(
        self,
        data: Dict[str, Any],
        fluctuation_thresholds: Optional[Dict[str, float]] = None,
        divergence_threshold_pp: float = 8.0,
    ) -> Dict[str, Any]:
        """
        Run the full Team 2 pipeline.

        Parameters
        ----------
        data:
            The parsed financial_data.json dict from Team 1.
        fluctuation_thresholds:
            Optional override for unusual fluctuation thresholds.
        divergence_threshold_pp:
            Threshold for profit-vs-revenue divergence in percentage points.

        Returns
        -------
        The canonical Team 2 output contract dict (JSON-serialisable).
        """
        t_start = time.perf_counter()
        log.info("━" * 60)
        log.info("  Team 2 Financial Review Engine — START")
        log.info("━" * 60)

        # Step 1: Input validation
        self.validate_input(data)

        meta = data.get("metadata", {})
        doc_id = meta.get("document_id", "UNKNOWN")
        company = (meta.get("company") or {}).get("name", "Unknown Company")
        periods = [p.get("period_key") for p in meta.get("periods", []) if isinstance(p, dict)]
        curr_period = periods[0] if periods else "FY_CURRENT"

        log.info("  Document : %s", doc_id)
        log.info("  Company  : %s", company)
        log.info("  Periods  : %s", periods)
        log.info("━" * 60)

        # Step 2: Document Quality Gate
        self._step("Document Quality Gate")
        dq_result = _DocumentQualityResult(data)
        if dq_result.status in ("FAILED", "NOT_AVAILABLE"):
            self._warn("Document Quality Gate", f"status={dq_result.status}, score={dq_result.score}")
        else:
            self._ok("Document Quality Gate", f"score={dq_result.score}, status={dq_result.status}")

        # Step 3: Mathematical Accuracy
        self._step("Mathematical Accuracy")
        math_result = self._safe_run(
            "Mathematical Accuracy",
            MathematicalAccuracyEngine.evaluate, data
        )
        if math_result:
            self._ok("Mathematical Accuracy", f"score={math_result.score:.1f}, status={math_result.status}")

        # Step 4: Cash Flow Reconciliation
        self._step("Cash Flow Reconciliation")
        cf_result = self._safe_run(
            "Cash Flow Reconciliation",
            CashFlowEngine.evaluate, data
        )
        if cf_result:
            self._ok("Cash Flow Reconciliation", f"score={cf_result.score:.1f}, status={cf_result.status}")

        # Step 5: Prior-Year Tie-Out
        self._step("Prior-Year Tie-Out")
        py_result = self._safe_run(
            "Prior-Year Tie-Out",
            PriorYearTieOutEngine.evaluate, data
        )
        if py_result:
            self._ok("Prior-Year Tie-Out", f"score={py_result.score:.1f}, status={py_result.status}")

        # Step 6: Internal Consistency
        self._step("Internal Consistency")
        ic_result = self._safe_run(
            "Internal Consistency",
            InternalConsistencyEngine.evaluate, data
        )
        if ic_result:
            self._ok("Internal Consistency", f"score={ic_result.score:.1f}, status={ic_result.status}")

        # Step 7: Analytical Comparison (YoY Growth)
        self._step("Analytical Comparison")
        growth_result = self._safe_run(
            "Analytical Comparison",
            AnalyticalComparisonEngine.evaluate, data
        )
        if growth_result:
            self._ok("Analytical Comparison",
                     f"computed={growth_result.metrics_computed}/{growth_result.total_metrics_evaluated}")

        # Step 8: Financial Ratios
        self._step("Financial Ratios")
        ratios_result = self._safe_run(
            "Financial Ratios",
            FinancialRatiosEngine.evaluate, data
        )
        if ratios_result:
            self._ok("Financial Ratios",
                     f"ratios={ratios_result.ratios_computed_count}/{ratios_result.total_ratios_count}, "
                     f"status={ratios_result.status}")

        # Step 9: Unusual Fluctuation
        self._step("Unusual Fluctuation")
        uf_result = self._safe_run(
            "Unusual Fluctuation",
            UnusualFluctuationScanner.evaluate,
            data,
            thresholds=fluctuation_thresholds,
        )
        if uf_result:
            self._ok("Unusual Fluctuation",
                     f"flagged={uf_result.flagged_count}/{uf_result.total_items_scanned}, "
                     f"status={uf_result.status}")

        # Step 10: Unusual Gain
        self._step("Unusual Gain")
        ug_result = self._safe_run(
            "Unusual Gain",
            UnusualGainEngine.evaluate,
            data,
            divergence_threshold_pp=divergence_threshold_pp,
        )
        if ug_result:
            self._ok("Unusual Gain",
                     f"trigger={ug_result.divergence_trigger_status}, status={ug_result.status}")

        # Step 11: Related Disclosure
        self._step("Related Party Disclosure")
        rd_result = self._safe_run(
            "Related Party Disclosure",
            RelatedDisclosureEngine.evaluate, data
        )
        if rd_result:
            self._ok("Related Party Disclosure",
                     f"consistency={rd_result.disclosure_consistency_pct}%, status={rd_result.status}")

        log.info("━" * 60)
        log.info("  Generating Findings & Scoring …")

        # Step 12: Finding Engine + Scoring
        engine_results = {
            "mathematical_accuracy": math_result,
            "cash_flow":             cf_result,
            "prior_year_tieout":     py_result,
            "internal_consistency":  ic_result,
            "growth":                growth_result,
            "ratios":                ratios_result,
            "unusual_fluctuation":   uf_result,
            "unusual_gain":          ug_result,
            "related_disclosure":    rd_result,
            "document_quality":      dq_result,
        }

        output = FindingEngine.run(engine_results)

        # Enrich output with run metadata
        elapsed = round(time.perf_counter() - t_start, 3)
        output["run_metadata"] = {
            "document_id":          doc_id,
            "company":              company,
            "current_period":       curr_period,
            "all_periods":          periods,
            "run_timestamp":        datetime.now(timezone.utc).isoformat(),
            "engine_version":       "2.0.0",
            "elapsed_seconds":      elapsed,
        }

        # Override checks/financial_metrics/analytical_metrics with engine raw output
        output["financial_metrics"] = {
            "mathematical_accuracy": _to_json_safe(math_result),
            "cash_flow":             _to_json_safe(cf_result),
            "prior_year_tieout":     _to_json_safe(py_result),
            "internal_consistency":  _to_json_safe(ic_result),
            "document_quality":      _to_json_safe(dq_result.model_dump()),
        }
        output["analytical_metrics"] = {
            "growth":                _to_json_safe(growth_result),
            "ratios":                _to_json_safe(ratios_result),
            "unusual_fluctuation":   _to_json_safe(uf_result),
            "unusual_gain":          _to_json_safe(ug_result),
            "related_disclosure":    _to_json_safe(rd_result),
        }

        log.info("━" * 60)
        log.info("  COMPLETE in %.3fs", elapsed)
        log.info("  Overall Score  : %.2f", output["overall_score"])
        log.info("  Overall Status : %s", output["overall_status"])
        log.info("  Findings — CRITICAL: %d  HIGH: %d  REVIEW: %d  PASSED: %d",
                 output["findings"]["critical"],
                 output["findings"]["high"],
                 output["findings"]["review"],
                 output["findings"]["passed"])
        log.info("━" * 60)

        return output

    # ── I/O helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def load(input_path: str) -> Dict[str, Any]:
        """Load and parse financial_data.json from Team 1."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        log.info("  Loading: %s", path.resolve())
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.info("  Loaded %d bytes", path.stat().st_size)
        return data

    @staticmethod
    def save(result: Dict[str, Any], output_path: str) -> None:
        """Save the canonical Team 2 output as review_result.json."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        serialisable = _to_json_safe(result)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serialisable, f, indent=2, ensure_ascii=False, cls=_DecimalEncoder)
        log.info("  Saved review_result → %s  (%d bytes)", path.resolve(), path.stat().st_size)


def run_pipeline(
    input_path: str,
    output_path: str,
    verbosity: int = logging.INFO,
    fluctuation_thresholds: Optional[Dict[str, float]] = None,
    divergence_threshold_pp: float = 8.0,
) -> Dict[str, Any]:
    """
    Convenience one-liner for the full pipeline.

    Returns the result dict and also writes it to output_path.
    """
    engine = Segment2Engine(verbosity=verbosity)
    data = engine.load(input_path)
    result = engine.run(
        data,
        fluctuation_thresholds=fluctuation_thresholds,
        divergence_threshold_pp=divergence_threshold_pp,
    )
    engine.save(result, output_path)
    return result
