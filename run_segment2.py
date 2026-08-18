"""
run_segment2.py — Team 2 Financial Review CLI Runner.

Usage:
    python run_segment2.py
    python run_segment2.py --input outputs/financial_data.json --output outputs/review_result.json
    python run_segment2.py --input outputs/financial_data.json --output outputs/review_result.json --verbose
    python run_segment2.py --input outputs/financial_data.json --output outputs/review_result.json \
                           --divergence-threshold 10.0

Options:
    --input     PATH    Path to financial_data.json (Team 1 output).
                        Default: outputs/financial_data.json
    --output    PATH    Path to write review_result.json.
                        Default: outputs/review_result.json
    --verbose           Enable debug-level logging.
    --divergence-threshold FLOAT
                        Profit-vs-revenue divergence threshold in percentage points.
                        Default: 8.0
"""

from __future__ import annotations

import argparse
import logging
import sys
import os

# Ensure project root is on sys.path when running as a script
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from segment2_financial_review.engine import run_pipeline

# ─────────────────────────────────────────────────────────────────────────────
# ANSI colour helpers (graceful fallback on Windows without ANSI support)
# ─────────────────────────────────────────────────────────────────────────────

def _colour(code: str, text: str) -> str:
    try:
        import ctypes
        # Enable ANSI on Windows 10+
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass
    return f"\033[{code}m{text}\033[0m"

_BOLD   = lambda t: _colour("1",    t)
_GREEN  = lambda t: _colour("32",   t)
_YELLOW = lambda t: _colour("33",   t)
_RED    = lambda t: _colour("31",   t)
_CYAN   = lambda t: _colour("36",   t)
_RESET  = "\033[0m"


def _status_colour(status: str) -> str:
    mapping = {
        "EXCELLENT":          _GREEN,
        "GOOD":               _GREEN,
        "ATTENTION_REQUIRED": _YELLOW,
        "HIGH_RISK":          _RED,
    }
    fn = mapping.get(status, lambda t: t)
    return fn(status)


def _severity_colour(label: str, count: int) -> str:
    if label == "CRITICAL" and count > 0:
        return _RED(f"{count}")
    if label == "HIGH" and count > 0:
        return _YELLOW(f"{count}")
    if label == "REVIEW" and count > 0:
        return _CYAN(f"{count}")
    return _GREEN(f"{count}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary printer
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(result: dict) -> None:
    findings   = result.get("findings", {})
    run_meta   = result.get("run_metadata", {})
    cat_scores = result.get("category_scores", {})

    w = 58  # box width

    def box_line(text: str = "", pad: int = 2) -> str:
        return "|" + (" " * pad) + text + (" " * (w - pad - len(_strip_ansi(text)))) + "|"

    def _strip_ansi(s: str) -> str:
        import re
        return re.sub(r"\033\[[0-9;]*m", "", s)

    sep = "+" + "-" * w + "+"
    top = "+" + "-" * w + "+"
    bot = "+" + "-" * w + "+"

    lines = [
        top,
        box_line("  TEAM 2 FINANCIAL REVIEW -- RESULTS SUMMARY", pad=0),
        sep,
        box_line(f"  Document  : {run_meta.get('document_id', 'N/A')}"),
        box_line(f"  Company   : {run_meta.get('company', 'N/A')}"),
        box_line(f"  Period    : {run_meta.get('current_period', 'N/A')}"),
        box_line(f"  Run at    : {run_meta.get('run_timestamp', 'N/A')[:19]}Z"),
        box_line(f"  Elapsed   : {run_meta.get('elapsed_seconds', '?')}s"),
        sep,
        box_line(f"  Overall Score  :  {_BOLD(str(result.get('overall_score', 0.0)))} / 100"),
        box_line(f"  Overall Status :  {_status_colour(result.get('overall_status', 'N/A'))}"),
        box_line(f"  Integrity Flag :  {'! CRITICAL OVERRIDE' if result.get('integrity_override') else 'v None'}"),
        sep,
        box_line("  Findings"),
        box_line(f"    CRITICAL : {_severity_colour('CRITICAL', findings.get('critical', 0))}"),
        box_line(f"    HIGH     : {_severity_colour('HIGH',     findings.get('high',     0))}"),
        box_line(f"    REVIEW   : {_severity_colour('REVIEW',   findings.get('review',   0))}"),
        box_line(f"    PASSED   : {_severity_colour('PASSED',   findings.get('passed',   0))}"),
        sep,
        box_line("  Category Scores"),
    ]

    for cat, score in (cat_scores or {}).items():
        s = f"{score:.1f}" if score is not None else "N/A"
        lines.append(box_line(f"    {cat:<30}  {s:>6}"))

    lines.append(bot)

    output = "\n" + "\n".join(lines) + "\n"
    try:
        sys.stdout.buffer.write(output.encode("utf-8"))
        sys.stdout.buffer.flush()
    except AttributeError:
        print(output)


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_segment2",
        description="Team 2 Financial Review Engine — CLI Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        default="outputs/financial_data.json",
        metavar="PATH",
        help="Path to financial_data.json (Team 1 output)",
    )
    parser.add_argument(
        "--output", "-o",
        default="outputs/review_result.json",
        metavar="PATH",
        help="Path to write review_result.json",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug-level logging",
    )
    parser.add_argument(
        "--divergence-threshold",
        type=float,
        default=8.0,
        metavar="FLOAT",
        help="Profit-vs-revenue divergence threshold (percentage points)",
    )
    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    verbosity = logging.DEBUG if args.verbose else logging.INFO

    try:
        result = run_pipeline(
            input_path=args.input,
            output_path=args.output,
            verbosity=verbosity,
            divergence_threshold_pp=args.divergence_threshold,
        )
        print_summary(result)
        return 0

    except FileNotFoundError as exc:
        print(f"\n  ERROR: {exc}", file=sys.stderr)
        return 2

    except Exception as exc:
        logging.getLogger("segment2.runner").exception("Unexpected error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
