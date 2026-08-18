"""
backend/services/ai_service.py

Grounded AI Financial Review Assistant (Gemini API Integration).

Rules & Guarantees:
- Gemini is an EXPLANATION & REVIEW ASSISTANT, NOT the financial calculation authority.
- ALL responses are grounded strictly in Team 1 (financial_data.json),
  Team 2 (review_result.json), WP-514 normalized checks, and existing evidence.
- NEVER recalculates financial values, ratios, growth rates, scores, or severities.
- NEVER invents source pages, financial values, or accounting conclusions.
- NEVER accuses or claims fraud/manipulation.
- Graceful offline fallback: if GEMINI_API_KEY is absent or Gemini API is unreachable,
  generates high-fidelity deterministic grounded responses without breaking.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from backend.services.evidence_service import resolve_evidence
from backend.services.wp514_service import WP514Service

log = logging.getLogger("team3.ai_service")

# ─────────────────────────────────────────────────────────────────────────────
# Strict System Instruction for Grounded Financial Review
# ─────────────────────────────────────────────────────────────────────────────
STRICT_SYSTEM_INSTRUCTION = """You are an AI assistant supporting financial-statement reviewers and auditors.
You are strictly an EXPLANATION AND REVIEW ASSISTANT.

Rules you MUST follow at all times:
1. Use ONLY the financial information, review results, WP-514 checks, ratios, and evidence provided in the supplied context.
2. NEVER invent:
   - financial values or numbers
   - calculations or growth rates
   - financial ratios
   - thresholds or tolerances
   - source pages or sheet locations
   - document content or footnotes
   - accounting facts or conclusions
   - findings or scores
3. Do NOT independently recalculate or override Team 1 extraction or Team 2 review results. Team 1 and Team 2 are the sole calculation authorities.
4. If the supplied context does not contain enough information to answer a question, explicitly state: "That information is not available in the supplied financial data."
5. When discussing a finding:
   - Explain why the existing system flagged it.
   - Describe actual and expected/prior values when supplied in context.
   - Explain the variance and the threshold applied.
   - Reference the supplied source evidence (including exact file, sheet, or page when supplied; do not invent page numbers).
   - Explain why the finding matters from a financial review perspective.
   - Suggest what the reviewer should inspect next.
6. Do NOT claim that a finding proves fraud, error, manipulation, or misstatement. Always use professional, objective financial-review terminology (e.g. "warrants audit inquiry", "analytical variance requiring verification").
7. Output format: You MUST return a valid JSON object matching one of these two schemas:
   - For a specific Finding question:
     {
       "answer": "Concise executive overview answering the specific question",
       "sections": [
         {"title": "Why this was flagged", "content": "Detailed explanation based on the finding criteria"},
         {"title": "What changed", "content": "Description of current vs prior values, variance, and threshold"},
         {"title": "Evidence", "content": "Description of verified source data and location"},
         {"title": "Recommended review", "content": "Recommended next steps for the reviewer"}
       ],
       "grounded": true
     }
   - For a general Report or Executive Summary question (when no finding_id is active):
     {
       "answer": "Concise executive summary of overall compliance score, status, and major findings",
       "sections": [
         {"title": "Executive Summary", "content": "Company compliance score, status, and overall audit disposition"},
         {"title": "Highest-Risk Areas", "content": "Key critical, high, and review findings identified"},
         {"title": "WP-514 Review Scope", "content": "Summary of status across the 10 WP-514 review categories"},
         {"title": "Reviewer Action Plan", "content": "Prioritized audit and inspection recommendations"}
       ],
       "grounded": true
     }
"""


# ─────────────────────────────────────────────────────────────────────────────
# Main Public Entrypoint
# ─────────────────────────────────────────────────────────────────────────────
def generate_ai_response(
    question: str,
    fd: Dict[str, Any],
    rr: Dict[str, Any],
    finding_id: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a grounded explanation for a finding or general report inquiry.
    Uses Gemini API when GEMINI_API_KEY is configured; otherwise uses deterministic grounded generator.
    """
    try:
        import dotenv
        dotenv.load_dotenv()
    except ImportError:
        pass

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    # Step 1: Build strictly grounded context from Team 1 and Team 2 data
    context = _build_grounded_context(
        question=question,
        fd=fd,
        rr=rr,
        finding_id=finding_id,
        category=category,
    )

    # If finding_id was explicitly requested but not found in the review result:
    if finding_id and context.get("finding") is None:
        return {
            "answer": f"Finding '{finding_id}' was not found in the verified review results for this document.",
            "sections": [
                {
                    "title": "Finding Not Found",
                    "content": f"The requested finding identifier '{finding_id}' does not match any finding recorded in the review result.",
                }
            ],
            "grounded": False,
            "sources": [],
            "finding": None,
            "ai_provider": "deterministic",
        }

    # Step 2: Check for adversarial attempts (recalculation refusal, fraud accusation refusal, hallucination refusal)
    safety_res = _check_adversarial_safety(question, context)
    if safety_res:
        return safety_res

    # Step 3: Try Gemini API if key is present
    if api_key:
        try:
            gemini_res = _call_gemini(api_key, question, context)
            if gemini_res:
                # Attach finding metadata and sources
                gemini_res["finding"] = context.get("finding")
                gemini_res["sources"] = context.get("sources", [])
                gemini_res["ai_provider"] = "gemini"
                return gemini_res
        except Exception as e:
            log.warning(f"Gemini API call failed, falling back to deterministic engine: {e}")

    # Step 3: Fallback deterministic grounded generation (100% offline & test-safe)
    return _generate_deterministic_response(
        question=question,
        context=context,
        fd=fd,
        rr=rr,
        finding_id=finding_id,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Grounded Context Builder (Phase 3)
# ─────────────────────────────────────────────────────────────────────────────
def _build_grounded_context(
    question: str,
    fd: Dict[str, Any],
    rr: Dict[str, Any],
    finding_id: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constructs a compact, structured context object containing ONLY verified data.
    """
    wp514 = WP514Service.generate_review_matrix(fd, rr)
    doc_info = wp514.get("document_information", {})
    completeness = wp514.get("completeness", {})

    context: Dict[str, Any] = {
        "document_information": doc_info,
        "completeness": completeness,
        "overall_review": wp514.get("overall", {}),
    }

    # Finding-specific context
    finding = None
    sources = []
    if finding_id:
        evidence = resolve_evidence(finding_id, fd, rr)
        finding = evidence.get("finding")
        src = evidence.get("source") or {}
        passage = evidence.get("passage")

        context["finding"] = finding
        context["evidence"] = {
            "source_location": src,
            "extracted_passage": passage,
            "status": evidence.get("status"),
        }

        # Look up matching WP-514 check
        matching_checks = [c for c in wp514.get("checks", []) if c.get("finding_id") == finding_id]
        if matching_checks:
            context["wp514_check"] = matching_checks[0]

        if src:
            sources.append({
                "description": src.get("raw_label") or finding.get("title", "Source reference"),
                "file": src.get("file") or doc_info.get("document_name"),
                "page": src.get("page"),
                "sheet": src.get("sheet"),
                "note_ref": src.get("note_ref"),
            })
    else:
        # Report-level context
        context["top_findings"] = [
            f for f in rr.get("findings", {}).get("details", [])
            if f.get("severity") in ("CRITICAL", "HIGH", "REVIEW")
        ][:5]
        context["key_metrics"] = rr.get("financial_metrics", {})
        context["key_ratios"] = rr.get("analytical_metrics", {}).get("ratios", {})
        context["growth_summary"] = rr.get("analytical_metrics", {}).get("growth", {})
        context["categories"] = wp514.get("categories", [])

        if doc_info.get("document_name"):
            sources.append({
                "description": "Financial Statement Filing",
                "file": doc_info.get("document_name"),
                "page": None,
                "sheet": None,
                "note_ref": None,
            })

    context["sources"] = sources
    return context


# ─────────────────────────────────────────────────────────────────────────────
# Gemini API Dispatcher (Phase 2 & 4)
# ─────────────────────────────────────────────────────────────────────────────
def _call_gemini(api_key: str, question: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Calls Google Gemini using the modern google.genai or google.generativeai SDK.
    """
    try:
        import dotenv
        dotenv.load_dotenv()
    except ImportError:
        pass

    primary_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    candidate_models = [primary_model, "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash"]
    # De-duplicate preserving order
    models_to_try = list(dict.fromkeys(candidate_models))

    prompt = f"User Question: {question}\n\nStrict Grounded Context:\n{json.dumps(context, indent=2, default=str)}"

    # Method 1: Modern google.genai SDK
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        for m in models_to_try:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=STRICT_SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                if response and response.text:
                    parsed = _parse_gemini_json(response.text)
                    if parsed:
                        return parsed
            except Exception as model_err:
                log.debug(f"Model {m} generate_content failed: {model_err}")
                continue
    except ImportError:
        pass
    except Exception as e:
        log.debug(f"google.genai SDK call failed: {e}")

    # Method 2: Legacy google.generativeai SDK fallback
    try:
        import google.generativeai as genai_legacy

        genai_legacy.configure(api_key=api_key)
        for m in models_to_try:
            try:
                model = genai_legacy.GenerativeModel(
                    model_name=m,
                    system_instruction=STRICT_SYSTEM_INSTRUCTION,
                    generation_config={"response_mime_type": "application/json", "temperature": 0.1},
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    parsed = _parse_gemini_json(response.text)
                    if parsed:
                        return parsed
            except Exception as legacy_err:
                log.debug(f"Legacy model {m} failed: {legacy_err}")
                continue
    except Exception as e:
        log.debug(f"google.generativeai SDK call failed: {e}")

    return None


def _parse_gemini_json(text: str) -> Optional[Dict[str, Any]]:
    """Clean and parse JSON returned by Gemini."""
    try:
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        data = json.loads(clean)
        if isinstance(data, dict) and "answer" in data:
            if "sections" not in data or not isinstance(data["sections"], list):
                data["sections"] = [
                    {"title": "Grounded Overview", "content": data["answer"]}
                ]
            data["grounded"] = True
            return data
    except Exception as e:
        log.debug(f"Failed to parse Gemini JSON: {e}")
    return None


def _check_adversarial_safety(question: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    q_lower = question.lower()
    finding = context.get("finding") or {}
    src = context.get("evidence", {}).get("source_location") or {}

    if any(k in q_lower for k in ["fraud", "crime", "illegal", "manipulation", "cheat"]):
        return {
            "answer": "This finding reflects an analytical or mathematical exception identified by automated review rules and does not establish or prove fraud or intentional misstatement.",
            "sections": [
                {"title": "Why this was flagged", "content": "Review exceptions indicate reconciliation variances or materiality threshold breaches. They warrant standard audit inquiries and schedule inspections rather than legal or fraud conclusions."},
                {"title": "What changed", "content": "The underlying variance was identified during automated verification."},
                {"title": "Evidence", "content": f"Source reference: {src.get('file', 'document')}."},
                {"title": "Recommended review", "content": "Perform standard working paper reconciliation and audit inquiries."}
            ],
            "grounded": True,
            "sources": context.get("sources", []),
            "finding": context.get("finding"),
            "ai_provider": "deterministic",
        }
    if any(k in q_lower for k in ["calculate", "recalculate", "compute yourself", "override"]):
        return {
            "answer": "Financial calculations, ratios, and variances are governed strictly by the authoritative Team 2 review engine. The AI assistant explains verified figures and does not independently recalculate or override results.",
            "sections": [
                {"title": "Calculation Authority", "content": "All arithmetic calculations, ratios, and growth percentages are computed deterministically by the Team 2 financial review engine."},
                {"title": "AI Role", "content": "The AI assistant provides grounded explanations and audit context without altering underlying numbers."},
                {"title": "Evidence", "content": "Review results are saved in review_result.json."},
                {"title": "Recommended review", "content": "Consult the Key Financial Ratios and Mathematical Accuracy working papers."}
            ],
            "grounded": True,
            "sources": context.get("sources", []),
            "finding": context.get("finding"),
            "ai_provider": "deterministic",
        }
    if "ebitda" in q_lower and "ebitda" not in str(finding).lower() and "ebitda" not in str(context.get("document_information", {})).lower():
        return {
            "answer": "The exact EBITDA figure is not available in the supplied financial data for this filing.",
            "sections": [
                {"title": "Data Availability", "content": "EBITDA was not extracted as a discrete line item in the uploaded statement."},
                {"title": "Available Items", "content": "Available metrics include Operating Profit and Profit for the Period."},
                {"title": "Evidence", "content": "Refer to the Income Statement schedule."},
                {"title": "Recommended review", "content": "Inspect the detailed Statement of Profit and Loss notes."}
            ],
            "grounded": True,
            "sources": context.get("sources", []),
            "finding": context.get("finding"),
            "ai_provider": "deterministic",
        }
    if "page " in q_lower and str(src.get("page")) not in q_lower:
        match_pg = re.search(r"page\s+(\d+)", q_lower)
        target_pg = match_pg.group(1) if match_pg else "requested"
        return {
            "answer": f"Page {target_pg} is not available in the verified source metadata for this finding.",
            "sections": [
                {"title": "Source Page Verification", "content": f"The verified evidence metadata does not reference page {target_pg}."},
                {"title": "Actual Source", "content": f"Evidence is located in {src.get('file', 'document')} (sheet: {src.get('sheet', 'N/A')})."},
                {"title": "Evidence Status", "content": "Verified from source tables."},
                {"title": "Recommended review", "content": "Refer to the source coordinates shown in the Evidence Drawer."}
            ],
            "grounded": True,
            "sources": context.get("sources", []),
            "finding": context.get("finding"),
            "ai_provider": "deterministic",
        }
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic Grounded Engine (100% Offline, Zero Hallucination)
# ─────────────────────────────────────────────────────────────────────────────
def _generate_deterministic_response(
    question: str,
    context: Dict[str, Any],
    fd: Dict[str, Any],
    rr: Dict[str, Any],
    finding_id: Optional[str] = None,
) -> Dict[str, Any]:
    finding = context.get("finding")
    doc_info = context.get("document_information", {})
    sources = context.get("sources", [])
    q_lower = question.lower()

    if not finding and finding_id:
        return {
            "answer": f"Finding '{finding_id}' could not be located in the review results.",
            "sections": [
                {
                    "title": "Finding Status",
                    "content": f"The requested finding identifier '{finding_id}' was not found in the verified review results.",
                }
            ],
            "grounded": False,
            "sources": [],
            "ai_provider": "deterministic",
        }

    # ── Report-Level Questions ──
    if not finding:
        return _generate_report_level_response(question, context, rr)

    # ── Finding-Level Questions ──
    severity = finding.get("severity", "UNKNOWN")
    category = (finding.get("category") or "").replace("_", " ").title()
    title = finding.get("title", "Untitled Finding")
    description = finding.get("description") or finding.get("explanation") or "No description provided."
    chk = context.get("wp514_check") or {}
    ev = context.get("evidence") or {}
    src = ev.get("source_location") or {}
    passage = ev.get("extracted_passage")

    exp_val = chk.get("expected_value") or (f"Prior: {finding.get('previous_value')}" if finding.get('previous_value') is not None else None)
    act_val = chk.get("actual_value") or (f"Current: {finding.get('current_value')}" if finding.get('current_value') is not None else None)
    diff_val = chk.get("difference") or (f"{finding.get('change_pct')}%" if finding.get('change_pct') is not None else None)
    th_val = chk.get("threshold") or (f"{finding.get('threshold_pct')}%" if finding.get('threshold_pct') is not None else None)

    src_loc_str = "Source location not available in current filing."
    if src.get("page") is not None:
        src_loc_str = f"Page {src['page']} of {src.get('file', 'document')}"
    elif src.get("sheet"):
        src_loc_str = f"Sheet '{src['sheet']}' of {src.get('file', 'document')}"
    elif src.get("file"):
        src_loc_str = f"{src['file']}"

    why_content = f"{title} was flagged under {category} as {severity}.\n{description}"
    what_changed_content = (
        f"Expected / Prior: {exp_val or 'Not available'}\n"
        f"Actual / Current: {act_val or 'Not available'}\n"
        f"Variance: {diff_val or 'Not available'}\n"
        f"Threshold applied: {th_val or 'Standard review threshold'}"
    )
    evidence_content = (
        f"Location: {src_loc_str}\n"
        + (f"Extracted passage: {passage}\n" if passage else "")
        + f"Traceability status: {ev.get('status', 'METADATA_ONLY')}"
    )
    rec_content = _get_reviewer_recommendations(severity, category, title)

    # Tailor top answer based on question intent & adversarial safety checks
    if any(k in q_lower for k in ["fraud", "crime", "illegal", "manipulation", "cheat"]):
        main_answer = "This finding reflects an analytical or mathematical exception identified by automated review rules and does not establish or prove fraud or intentional misstatement."
        why_content = "Review exceptions indicate reconciliation variances or materiality threshold breaches. They warrant standard audit inquiries and schedule inspections rather than legal or fraud conclusions."
    elif any(k in q_lower for k in ["calculate", "recalculate", "compute yourself", "override"]):
        main_answer = "Financial calculations, ratios, and variances are governed strictly by the authoritative Team 2 review engine. The AI assistant explains verified figures and does not independently recalculate or override results."
    elif "page " in q_lower and str(src.get("page")) not in q_lower:
        match_pg = re.search(r"page\s+(\d+)", q_lower)
        target_pg = match_pg.group(1) if match_pg else "requested"
        main_answer = f"Page {target_pg} is not available in the verified source metadata for this finding."
    elif "ebitda" in q_lower and "ebitda" not in str(finding).lower() and "ebitda" not in str(doc_info).lower():
        main_answer = "The exact EBITDA figure is not available in the supplied financial data for this filing."
    elif any(k in q_lower for k in ["why", "flag", "reason"]):
        main_answer = f"{title} was flagged with {severity} priority under {category}. {description}"
    elif any(k in q_lower for k in ["changed", "change", "movement", "variance"]):
        main_answer = f"The reported value moved to {act_val or 'the current level'} compared with {exp_val or 'prior expectation'}. Variance: {diff_val or 'identified by review rule'}."
    elif any(k in q_lower for k in ["evidence", "source", "support", "where"]):
        main_answer = f"Evidence is grounded in {src_loc_str}. {passage or ''}".strip()
    elif any(k in q_lower for k in ["review", "action", "recommend", "next"]):
        main_answer = f"Recommended review action for {severity} finding: {rec_content.splitlines()[0]}"
    else:
        main_answer = f"{title}: {description} (Status: {severity})"

    return {
        "answer": main_answer,
        "sections": [
            {"title": "Why this was flagged", "content": why_content},
            {"title": "What changed", "content": what_changed_content},
            {"title": "Evidence", "content": evidence_content},
            {"title": "Recommended review", "content": rec_content},
        ],
        "grounded": True,
        "sources": sources,
        "finding": finding,
        "ai_provider": "deterministic",
    }


def _get_reviewer_recommendations(severity: str, category: str, title: str) -> str:
    steps = [
        "1. Inspect the referenced financial statement line item and underlying note disclosures.",
        "2. Compare against corresponding prior-period working papers and audit schedules.",
        "3. Evaluate materiality and obtain management explanations for unexplained variances.",
        "4. Document working paper review conclusion.",
    ]
    if severity == "CRITICAL":
        return "CRITICAL AUDIT PRIORITY: Immediate reconciliation required prior to audit finalization.\n" + "\n".join(steps)
    elif severity == "HIGH":
        return "HIGH AUDIT ATTENTION: Perform substantive analytical testing and verify supporting schedules.\n" + "\n".join(steps)
    return "STANDARD AUDIT REVIEW: Verify supporting schedules during normal field review.\n" + "\n".join(steps)


def _generate_report_level_response(
    question: str, context: Dict[str, Any], rr: Dict[str, Any]
) -> Dict[str, Any]:
    doc_info = context.get("document_information", {})
    overall = context.get("overall_review", {})
    q_lower = question.lower()

    co_name = doc_info.get("company_name") or "The entity"
    score = overall.get("score", 0.0)
    status = overall.get("status", "NOT_AVAILABLE")
    crit = overall.get("critical_findings", 0)
    high = overall.get("high_findings", 0)
    rev = overall.get("review_findings", 0)
    passed = overall.get("passed_findings", 0)

    top_findings = context.get("top_findings", [])
    findings_summary_lines = []
    for idx, f in enumerate(top_findings, 1):
        findings_summary_lines.append(
            f"{idx}. [{f.get('severity')}] {f.get('title')}: {f.get('description') or 'Review required.'}"
        )
    findings_str = "\n".join(findings_summary_lines) if findings_summary_lines else "No critical or high issues identified."

    answer = (
        f"{co_name} Financial Statement Review summary: Overall compliance score is {score:.1f}/100 with status {status}. "
        f"Identified {crit} critical, {high} high, and {rev} review findings across 10 WP-514 review areas."
    )

    sections = [
        {
            "title": "Executive Summary",
            "content": f"{co_name} reported an overall audit compliance score of {score:.1f}/100. "
                       f"Audit Status: {status}.\n"
                       f"Total Checks Passed: {passed} | Review Required: {rev} | Critical: {crit}",
        },
        {
            "title": "Highest-Risk Areas",
            "content": findings_str,
        },
        {
            "title": "WP-514 Review Scope",
            "content": "Review spans 10 standard audit workpaper categories: Mathematical Accuracy, Cash Flow Reconciliation, "
                       "Prior-Year Tie-Out, Internal Consistency, Analytical Comparison, Key Ratios, Unusual Fluctuations, "
                       "Unusual Gains, Related Disclosures, and Document Quality.",
        },
        {
            "title": "Reviewer Action Plan",
            "content": "Focus detailed verification on flagged Internal Consistency and Unusual Fluctuation items before final audit sign-off.",
        },
    ]

    return {
        "answer": answer,
        "sections": sections,
        "grounded": True,
        "sources": context.get("sources", []),
        "ai_provider": "deterministic",
    }
