"""
Language Quality / Spelling & Grammar Review Engine.

Performs deterministic spelling and grammatical consistency review of extracted
narrative text, accounting policies, notes, and disclosures.

Rules & Protections:
- Never flags financial terminology, acronyms, standard abbreviations, or accounting concepts.
- Whitelists company names, proper nouns, numerical amounts, and currency units.
- Generates structured, evidence-backed issues with line/section/page provenance.
- Returns NOT_AVAILABLE when no narrative text exists.
- Fully deterministic without requiring external network access or heavy binary dependencies.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field


IssueType = Literal["SPELLING", "GRAMMAR"]
CheckStatus = Literal["PASSED", "FAILED", "WARNING", "NOT_AVAILABLE"]


class SourceContext(BaseModel):
    """Provenance tracking for a language issue."""
    model_config = ConfigDict(extra="allow")

    page: Optional[int] = None
    section: Optional[str] = None
    file: Optional[str] = None
    text: Optional[str] = None


class LanguageIssueDetail(BaseModel):
    """Detailed record of a single spelling or grammar issue."""
    model_config = ConfigDict(extra="allow")

    type: IssueType
    text: str
    suggestion: str
    description: str
    source: SourceContext


class LanguageQualityResult(BaseModel):
    """Complete output of the Language Quality / Spelling & Grammar Engine."""
    model_config = ConfigDict(extra="allow")

    spelling_errors_count: int = 0
    grammar_issues_count: int = 0
    reviewed_passages_count: int = 0
    score: float = 100.0
    status: CheckStatus
    details: List[LanguageIssueDetail] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Financial & Accounting Lexicon Whitelist
# ─────────────────────────────────────────────────────────────────────────────

FINANCIAL_LEXICON: Set[str] = {
    # Standards & Bodies
    "gaap", "ifrs", "ind", "indian", "indas", "ind-as", "mca", "sebi", "icai", "pcaob", "sec",
    "iasb", "fasb", "cin", "din", "pan", "gstin", "gst", "tin", "tan", "tds",
    
    # Financial Statements & Metrics
    "ebitda", "ebit", "pbt", "pat", "roa", "roe", "roce", "eps", "nav", "cagr",
    "cogs", "opex", "capex", "d&a", "wip", "cwip", "ppe", "ppes", "nca", "ncl",
    "ca", "cl", "fcf", "cfs", "cfo", "cfi", "cff", "fy", "cy", "py", "yoy", "qoq",
    "q1", "q2", "q3", "q4", "h1", "h2",
    
    # Indian & International Units & Scales
    "crore", "crores", "lakh", "lakhs", "inr", "usd", "eur", "gbp", "jpy", "aud",
    "sgd", "cny", "chf", "bps", "pp",
    
    # Financial Terminology & Accounting Nouns
    "debenture", "debentures", "amortisation", "amortization", "amortise", "amortised",
    "amortize", "amortized", "depreciation", "depreciate", "depreciated",
    "receivable", "receivables", "payable", "payables", "inventories", "inventory",
    "borrowing", "borrowings", "leasehold", "freehold", "subordinated", "unsecured",
    "secured", "reconciliation", "reconcile", "reconciled", "derecognition", "derecognise",
    "derecognize", "derecognised", "derecognized", "impairment", "impaired",
    "goodwill", "contingencies", "contingency", "contingent", "segmental", "segment",
    "carrying", "realisable", "realizable", "indemnification", "annexure", "standalone",
    "consolidated", "disinvestment", "remittance", "statutory", "actuarial", "gratuity",
    "superannuation", "encashment", "hedging", "derivative", "derivatives", "notional",
    "prepayment", "prepayments", "syndicated", "consortium", "hypothecation",
    "mortgage", "mortgages", "pledged", "encumbrance", "encumbrances", "unencumbered",
    "solvency", "liquidity", "leverage", "profitability", "equity", "liabilities",
    "assets", "turnover", "working", "capital", "provision", "provisions",
    "reserves", "surplus", "retained", "earnings", "accrual", "accruals", "accrued",
    "dividend", "dividends", "annuity", "annuities", "collateral", "collaterals",
    "coupon", "coupons", "yield", "yields", "inter-alia", "pari-passu", "pro-rata",
    "mutatis-mutandis", "bonafide", "prima-facie", "ad-hoc",
    
    # Common Business & Audit Vocabulary
    "auditor", "auditors", "audit", "audited", "unaudited", "review", "reviewed",
    "compliance", "compliant", "governance", "internal", "control", "controls",
    "disclosures", "disclosure", "disclosed", "statement", "statements", "policy",
    "policies", "standard", "standards", "framework", "frameworks", "schedule",
    "schedules", "annexure", "annexures", "balance", "balances", "sheet", "sheets",
    "income", "expenditure", "expense", "expenses", "revenue", "profit", "loss",
    "losses", "gain", "gains", "margin", "margins", "cash", "flow", "flows",
    "notes", "note", "basis", "preparation", "fair", "value", "values", "historical",
    "cost", "costs", "method", "methods", "useful", "lives", "residual", "contract",
    "contracts", "customer", "customers", "vendor", "vendors", "employee", "employees",
    "benefits", "tax", "taxation", "taxes", "deferred", "current", "non-current",
    "tangible", "intangible", "subsidiary", "subsidiaries", "associate", "associates",
    "joint", "venture", "ventures", "investment", "investments", "property", "plant",
    "equipment", "obligation", "obligations", "settlement", "settled", "measured",
    "measurement", "functional", "presentation", "currency", "material", "materiality",
    "significant", "judgment", "judgments", "estimates", "assumptions", "discount",
    "rate", "rates", "macroeconomic", "indicators", "sensitivity", "analysis",
}

# Standard English dictionary words commonly appearing in corporate reports
STANDARD_DICTIONARY: Set[str] = {
    "a", "about", "above", "accordance", "across", "act", "actual", "add", "addition", "additional",
    "adequate", "adjust", "adjusted", "adjustment", "adjustments", "after", "again", "against",
    "all", "allow", "allowance", "allowances", "also", "although", "amount", "amounts", "among", "an",
    "and", "annual", "any", "applicable", "apply", "applied", "appropriate", "approval",
    "approved", "are", "as", "at", "available", "average", "based", "be", "been",
    "before", "being", "below", "between", "both", "business", "by", "can", "case",
    "certain", "change", "changed", "changes", "company", "companies", "complete",
    "completed", "condition", "conditions", "consider", "considered", "consideration", "consist",
    "consists", "consisted", "consistent", "contain", "contains", "contained",
    "continue", "continued", "coverage", "coverages", "credit", "date", "debt", "december", "decrease",
    "decreased", "deem", "deemed", "default", "demand", "depreciation", "described",
    "detail", "details", "determine", "determined", "direct", "directly", "director",
    "directors", "due", "during", "each", "early", "effective", "either", "end",
    "ended", "ending", "entity", "entities", "equal", "equipment", "estimate",
    "estimated", "evaluate", "evaluated", "event", "events", "exceed", "exceeded",
    "except", "exchange", "exchanges", "exchanged", "executive", "exist", "existing",
    "expect", "expects", "expected", "exposure", "factor", "factors", "fail", "failed",
    "failure", "fair", "fees", "figure", "figures", "file", "filed", "filing", "filings",
    "final", "finance", "financial", "first", "fiscal", "following", "for", "form",
    "former", "forth", "found", "from", "full", "fund", "funds", "further", "future",
    "general", "generally", "given", "grant", "granted", "group", "had", "has", "have",
    "having", "held", "herein", "higher", "highest", "hold", "holds", "holding", "holdings", "how", "however", "if",
    "impact", "impacts", "in", "include", "includes", "included", "including",
    "increase", "increased", "increases", "increasing", "incur", "incurred", "indicate",
    "indicated", "indicates", "individual", "industry", "information", "initial",
    "input", "inputs", "interest", "into", "is", "issue", "issued", "issues",
    "item", "items", "its", "key", "known", "last", "least", "less", "level",
    "levels", "like", "likely", "limit", "limited", "line", "lines", "liquid",
    "listed", "long", "longer", "low", "lower", "lowest", "made", "main", "maintain", "maintains", "maintained", "major", "make", "makes", "making",
    "manage", "managed", "management", "manner", "many", "march", "market", "markets",
    "may", "mean", "meaning", "means", "measure", "measured", "meet", "meets", "member",
    "members", "might", "minimum", "month", "months", "more", "most", "move", "moved",
    "movement", "movements", "must", "nature", "near", "necessary", "need", "needed",
    "needs", "net", "new", "next", "no", "non", "none", "nor", "not", "note", "noted",
    "notes", "number", "numbers", "obtain", "obtained", "occur", "occurred", "occurs",
    "of", "off", "officer", "officers", "often", "on", "one", "only", "open", "opening",
    "operate", "operated", "operates", "operating", "operation", "operations", "order",
    "ordinary", "other", "others", "otherwise", "our", "out", "outstanding", "over",
    "overall", "own", "owned", "paid", "paragraph", "part", "particular", "particularly",
    "parties", "party", "past", "payable", "payables", "payment", "payments", "per",
    "percent", "percentage", "performance", "period", "periods", "place", "plan",
    "plans", "plant", "policy", "policies", "position", "positions", "possible",
    "potential", "practice", "practices", "premium", "prepare", "prepared", "preparation",
    "present", "presented", "presentation", "previous", "previously", "price", "prices",
    "primary", "principal", "prior", "pro", "procedure", "procedures", "proceeds",
    "process", "processes", "product", "products", "profit", "profits", "program",
    "programs", "project", "projects", "promise", "promises", "promised", "promising",
    "property", "proportion", "provide", "provided", "provides", "providing", "provision",
    "provisions", "public", "purpose", "purposes", "rate", "rates", "ratio", "ratios",
    "reach", "reached", "real", "realize", "realized", "reason", "reasonable", "reasons",
    "receipt", "receipts", "receive", "received", "receives", "receiving", "receivable",
    "receivables", "recognize", "recognized", "recognise", "recognised", "record",
    "recorded", "records", "recover", "recoverable", "recovered", "reduce", "reduced",
    "reflect", "reflects", "reflected", "reflecting", "regard", "regarding", "regular",
    "relate", "related", "relates", "relating", "remain",
    "remained", "remains", "report", "reported", "reporting", "reports", "represent",
    "represented", "represents", "require", "required", "requirement", "requirements",
    "requires", "reserve", "reserves", "respect", "respective", "result", "resulted",
    "resulting", "results", "return", "returned", "returns", "review", "reviewed",
    "right", "rights", "risk", "risks", "rule", "rules", "same", "say", "said",
    "scale", "scope", "section", "sections", "secure", "secured", "security",
    "securities", "see", "seen", "separate", "separately", "service", "services",
    "set", "settle", "settled", "settlement", "several", "shall", "share", "shares",
    "shareholder", "shareholders", "short", "should", "show", "showed", "shown",
    "shows", "sign", "signed", "significant", "significantly", "similar", "since",
    "single", "so", "some", "source", "sources", "specific", "specifically", "stated",
    "statement", "statements", "status", "statutory", "stock", "structure", "subject",
    "subsequent", "subsidiary", "subsidiaries", "such", "sum", "summary", "support",
    "supported", "system", "systems", "table", "tables", "take", "taken", "term",
    "terms", "than", "that", "the", "their", "them", "then", "there", "thereof",
    "these", "they", "third", "this", "those", "three", "through", "time", "times",
    "to", "total", "totals", "trace", "trade", "transaction", "transactions",
    "transfer", "transferred", "treated", "treatment", "trend", "trends", "true",
    "two", "type", "types", "under", "underlying", "unit", "units", "unless",
    "until", "up", "upon", "use", "used", "uses", "using", "useful", "valid",
    "validity", "value", "values", "valuation", "valuations", "variable", "variables",
    "variance", "variances", "various", "vary", "varying", "version", "very",
    "via", "view", "viewed", "was", "way", "we", "were", "what", "when", "where",
    "whether", "which", "while", "who", "whom", "will", "with", "within", "without",
    "word", "words", "work", "working", "would", "year", "yearly", "years", "zero",
}

# Common spelling typo mappings in financial/business texts
KNOWN_MISSPELLINGS: Dict[str, str] = {
    "financil": "financial",
    "finacial": "financial",
    "finanical": "financial",
    "liabilites": "liabilities",
    "liabilties": "liabilities",
    "liabilty": "liability",
    "exepenses": "expenses",
    "expences": "expenses",
    "expence": "expense",
    "depresiation": "depreciation",
    "deprecition": "depreciation",
    "statemnt": "statement",
    "statment": "statement",
    "revnue": "revenue",
    "revenu": "revenue",
    "recievables": "receivables",
    "recievable": "receivable",
    "receivbles": "receivables",
    "maintanance": "maintenance",
    "maintanence": "maintenance",
    "equitiy": "equity",
    "balence": "balance",
    "balanse": "balance",
    "acounting": "accounting",
    "acconting": "accounting",
    "amout": "amount",
    "amouts": "amounts",
    "reconciliationn": "reconciliation",
    "contingentt": "contingent",
    "disclosre": "disclosure",
    "disclosur": "disclosure",
    "amoritization": "amortization",
    "amortizaton": "amortization",
    "subsidary": "subsidiary",
    "subsidaries": "subsidiaries",
    "auditt": "audit",
    "materality": "materiality",
    "siginificant": "significant",
    "signifcant": "significant",
    "guarntee": "guarantee",
    "guarenteed": "guaranteed",
    "colateral": "collateral",
}


# ─────────────────────────────────────────────────────────────────────────────
# Levenshtein Distance Helper
# ─────────────────────────────────────────────────────────────────────────────

def _levenshtein(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def _suggest_spelling(word: str) -> Optional[str]:
    """Find closest word suggestion for a misspelled word."""
    w_lower = word.lower()
    if w_lower in KNOWN_MISSPELLINGS:
        return KNOWN_MISSPELLINGS[w_lower]

    best_candidate: Optional[str] = None
    min_dist = 2  # Max edit distance 2 for words >= 5 chars
    if len(w_lower) < 5:
        min_dist = 1

    candidate_pool = FINANCIAL_LEXICON | STANDARD_DICTIONARY
    for candidate in candidate_pool:
        if abs(len(candidate) - len(w_lower)) > min_dist:
            continue
        dist = _levenshtein(w_lower, candidate)
        if dist <= min_dist:
            best_candidate = candidate
            min_dist = dist - 1
            if min_dist < 0:
                break

    return best_candidate


# ─────────────────────────────────────────────────────────────────────────────
# Grammar Rule Checks
# ─────────────────────────────────────────────────────────────────────────────

GRAMMAR_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    # 1. Subject-Verb Agreement: Plural Noun + Singular Verb
    (
        re.compile(r"\b(assets|liabilities|profits|losses|expenses|receivables|payables|borrowings|reserves)\s+(is|was|has)\b", re.IGNORECASE),
        "Subject-verb disagreement: plural subject followed by singular verb.",
        "are / were / have"
    ),
    # 2. Subject-Verb Agreement: Singular Entity + Plural Verb (in standard declarative reporting)
    (
        re.compile(r"\b(the\s+company|the\s+management|the\s+board|the\s+entity)\s+(are|were)\b", re.IGNORECASE),
        "Subject-verb disagreement: singular collective noun followed by plural verb.",
        "is / was"
    ),
    # 3. Indefinite Article Misuse: 'a' before vowel sound
    (
        re.compile(r"\b(a)\s+(asset|assets|audit|audited|auditor|auditors|equity|expense|expenses|income|impairment|obligation|obligations|operating|unusual|unsecured)\b", re.IGNORECASE),
        "Article misuse: 'a' used before vowel sound.",
        "an"
    ),
    # 4. Indefinite Article Misuse: 'an' before consonant sound
    (
        re.compile(r"\b(an)\s+(balance|company|statement|report|profit|loss|cash|flow|debt|ratio|margin|table|note|borrowing|reserve)\b", re.IGNORECASE),
        "Article misuse: 'an' used before consonant sound.",
        "a"
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Language Quality Engine
# ─────────────────────────────────────────────────────────────────────────────

class LanguageQualityEngine:
    """
    Evaluates spelling and grammatical correctness of financial narrative texts.
    """

    @classmethod
    def evaluate(cls, data: Dict[str, Any]) -> LanguageQualityResult:
        """
        Extracts narrative passages from financial_data.json and performs review.
        """
        passages: List[Dict[str, Any]] = cls._extract_passages(data)

        if not passages:
            return LanguageQualityResult(
                spelling_errors_count=0,
                grammar_issues_count=0,
                reviewed_passages_count=0,
                score=0.0,
                status="NOT_AVAILABLE",
                details=[],
                issues=["NOT_AVAILABLE: No narrative text or disclosures available for language quality review."],
            )

        # Dynamic Company/Proper noun whitelist
        custom_whitelist = set(FINANCIAL_LEXICON) | set(STANDARD_DICTIONARY)
        company_name = data.get("metadata", {}).get("company", {}).get("name", "")
        if company_name:
            for part in re.split(r"[\s,\-\.]+", company_name):
                if part:
                    custom_whitelist.add(part.lower())

        issues: List[LanguageIssueDetail] = []
        spelling_count = 0
        grammar_count = 0

        for passage in passages:
            text = passage.get("text", "").strip()
            if not text:
                continue

            page = passage.get("page")
            section = passage.get("section")
            file_name = passage.get("file")

            # 1. Grammar Checks
            grammar_issues = cls._check_grammar(text, page, section, file_name)
            for g_issue in grammar_issues:
                grammar_count += 1
                issues.append(g_issue)

            # 2. Spelling Checks
            spelling_issues = cls._check_spelling(text, custom_whitelist, page, section, file_name)
            for s_issue in spelling_issues:
                spelling_count += 1
                issues.append(s_issue)

        total_passages = len(passages)
        total_errors = spelling_count + grammar_count

        if total_errors == 0:
            score = 100.0
            status: CheckStatus = "PASSED"
        else:
            penalty = (spelling_count * 10.0) + (grammar_count * 15.0)
            score = max(0.0, round(100.0 - penalty, 2))
            status = "WARNING" if score >= 70.0 else "FAILED"

        issue_summaries = []
        for d in issues:
            issue_summaries.append(f"{d.type}: {d.text} -> {d.description}")

        return LanguageQualityResult(
            spelling_errors_count=spelling_count,
            grammar_issues_count=grammar_count,
            reviewed_passages_count=total_passages,
            score=score,
            status=status,
            details=issues,
            issues=issue_summaries,
        )

    @classmethod
    def _extract_passages(cls, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract narrative text, notes, and disclosure passages from financial_data."""
        passages: List[Dict[str, Any]] = []

        # 1. Extracted Notes and Disclosures
        notes = data.get("extracted_notes_and_disclosures", [])
        if isinstance(notes, list):
            for note in notes:
                if isinstance(note, dict):
                    text = note.get("text", "")
                    if text and len(text.strip()) > 5:
                        src = note.get("source", {}) if isinstance(note.get("source"), dict) else {}
                        passages.append({
                            "text": text,
                            "page": src.get("page"),
                            "section": f"Note {note.get('note_number', '')} - {note.get('topic', 'Disclosure')}".strip(),
                            "file": src.get("file"),
                        })

        # 2. RAG Chunks / Narrative Sections if present
        chunks = data.get("rag_chunks", []) or data.get("narrative_sections", [])
        if isinstance(chunks, list):
            for chunk in chunks:
                if isinstance(chunk, dict):
                    text = chunk.get("text", "")
                    if text and len(text.strip()) > 5:
                        src = chunk.get("source", {}) if isinstance(chunk.get("source"), dict) else {}
                        passages.append({
                            "text": text,
                            "page": src.get("page") or chunk.get("page"),
                            "section": chunk.get("topic") or chunk.get("section") or "Narrative Section",
                            "file": src.get("file") or chunk.get("file"),
                        })

        return passages

    @classmethod
    def _check_grammar(
        cls,
        text: str,
        page: Optional[int],
        section: Optional[str],
        file_name: Optional[str]
    ) -> List[LanguageIssueDetail]:
        """Detect grammatical issues including doubled words and agreement errors."""
        issues: List[LanguageIssueDetail] = []

        # Rule A: Doubled words ("the the", "in in", "for for")
        doubled_matches = re.finditer(r"\b([A-Za-z]{2,})\s+\1\b", text, re.IGNORECASE)
        for m in doubled_matches:
            matched_str = m.group(0)
            word = m.group(1)
            # Allow intentional doubled words if any (rare)
            issues.append(
                LanguageIssueDetail(
                    type="GRAMMAR",
                    text=matched_str,
                    suggestion=word,
                    description=f"Duplicate consecutive word '{word}' detected.",
                    source=SourceContext(
                        page=page,
                        section=section,
                        file=file_name,
                        text=text[:120] + ("..." if len(text) > 120 else "")
                    )
                )
            )

        # Rule B: Regex grammar patterns
        for pattern, desc, suggestion in GRAMMAR_PATTERNS:
            for m in pattern.finditer(text):
                matched_str = m.group(0)
                issues.append(
                    LanguageIssueDetail(
                        type="GRAMMAR",
                        text=matched_str,
                        suggestion=suggestion,
                        description=f"{desc} Found: '{matched_str}'.",
                        source=SourceContext(
                            page=page,
                            section=section,
                            file=file_name,
                            text=text[:120] + ("..." if len(text) > 120 else "")
                        )
                    )
                )

        return issues

    @classmethod
    def _check_spelling(
        cls,
        text: str,
        whitelist: Set[str],
        page: Optional[int],
        section: Optional[str],
        file_name: Optional[str]
    ) -> List[LanguageIssueDetail]:
        """Detect misspellings with whitelist exemptions for financial terminology."""
        issues: List[LanguageIssueDetail] = []

        # Split text into tokens
        tokens = re.findall(r"\b[A-Za-z\-']+\b", text)

        for token in tokens:
            token_clean = token.strip("'-").lower()
            if not token_clean or len(token_clean) <= 2:
                continue

            # 1. Check if known in dictionary or whitelist
            if token_clean in whitelist:
                continue

            # Check standard English inflection forms (plural, past tense, continuous, adverbs)
            is_valid_inflection = False
            for suffix in ("s", "es", "ed", "ing", "ly", "d", "ment", "ments", "tion", "tions", "able", "ible", "al", "ally", "ive", "ity", "ies"):
                if token_clean.endswith(suffix) and len(token_clean) > len(suffix) + 2:
                    base = token_clean[:-len(suffix)]
                    if base in whitelist or (suffix == "ies" and (base + "y") in whitelist) or (suffix == "ed" and (base + "e") in whitelist) or (suffix == "es" and (base + "e") in whitelist):
                        is_valid_inflection = True
                        break

            if is_valid_inflection:
                continue

            # 2. Check if hyphenated word where parts are valid
            if "-" in token_clean:
                parts = token_clean.split("-")
                if all(p in whitelist or len(p) <= 2 for p in parts):
                    continue

            # 3. Check if all uppercase acronym (e.g. EBITDA, IndAS, TDS)
            if token.isupper() or len(token) <= 3:
                continue

            # 4. Check if title case proper noun followed by standard business token
            if token[0].isupper() and token_clean not in KNOWN_MISSPELLINGS:
                # Treat Capitalized words in narrative as proper nouns/names
                continue

            # 5. Check known misspellings or fuzzy suggestion
            suggestion = _suggest_spelling(token_clean)
            if suggestion and suggestion != token_clean:
                issues.append(
                    LanguageIssueDetail(
                        type="SPELLING",
                        text=token,
                        suggestion=suggestion,
                        description=f"Potential spelling error '{token}'. Suggested replacement: '{suggestion}'.",
                        source=SourceContext(
                            page=page,
                            section=section,
                            file=file_name,
                            text=text[:120] + ("..." if len(text) > 120 else "")
                        )
                    )
                )

        return issues


def run(data: Dict[str, Any]) -> LanguageQualityResult:
    """Convenience runner for Language Quality Engine."""
    return LanguageQualityEngine.evaluate(data)
