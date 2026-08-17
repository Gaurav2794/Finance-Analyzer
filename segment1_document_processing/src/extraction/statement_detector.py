"""
Statement Detector.
Identifies financial statement type (Balance Sheet, Income Statement, Cash Flow, Notes)
from text headers, sheet names, table rows, and structural keywords.
"""

import re
from typing import List, Optional, Tuple


class StatementDetector:
    BALANCE_SHEET_KEYWORDS = [
        r"balance\s*sheet",
        r"statement\s*of\s*financial\s*position",
        r"total\s*assets",
        r"equity\s*and\s*liabilities",
        r"non-current\s*assets",
        r"current\s*assets",
        r"shareholders['’]?\s*funds",
        r"share\s*capital"
    ]

    INCOME_STATEMENT_KEYWORDS = [
        r"statement\s*of\s*profit\s*and\s*loss",
        r"income\s*statement",
        r"statement\s*of\s*comprehensive\s*income",
        r"profit\s*&\s*loss",
        r"revenue\s*from\s*operations",
        r"cost\s*of\s*materials\s*consumed",
        r"employee\s*benefit\s*expenses",
        r"profit\s*before\s*tax",
        r"net\s*profit"
    ]

    CASH_FLOW_KEYWORDS = [
        r"cash\s*flow\s*statement",
        r"statement\s*of\s*cash\s*flows",
        r"cash\s*flows?\s*from\s*operating\s*activities",
        r"cash\s*flows?\s*from\s*investing\s*activities",
        r"cash\s*flows?\s*from\s*financing\s*activities",
        r"net\s*increase\s*in\s*cash",
        r"operating\s*cash\s*flow"
    ]

    NOTES_KEYWORDS = [
        r"notes\s*to\s*(the\s*)?financial\s*statements",
        r"significant\s*accounting\s*policies",
        r"contingent\s*liabilities",
        r"related\s*party\s*transactions",
        r"note\s*\d+"
    ]

    @classmethod
    def detect_statement_type(cls, text_or_lines: any) -> Optional[str]:
        """
        Takes raw string text, sheet name, or list of string lines/cells and returns:
        'balance_sheet' | 'income_statement' | 'cash_flow_statement' | 'notes' | None
        """
        if not text_or_lines:
            return None

        if isinstance(text_or_lines, list):
            sample_text = " ".join(str(x) for x in text_or_lines[:30]).lower()
        else:
            sample_text = str(text_or_lines).lower()

        scores = {
            "cash_flow_statement": 0,
            "balance_sheet": 0,
            "income_statement": 0,
            "notes": 0
        }

        # Check explicit titles first
        if "cash flow" in sample_text or "statement of cash flows" in sample_text:
            scores["cash_flow_statement"] += 5
        if "balance sheet" in sample_text or "statement of financial position" in sample_text:
            scores["balance_sheet"] += 5
        if "profit and loss" in sample_text or "income statement" in sample_text or "statement of profit" in sample_text:
            scores["income_statement"] += 5

        # Check keyword matches
        for pat in cls.CASH_FLOW_KEYWORDS:
            if re.search(pat, sample_text):
                scores["cash_flow_statement"] += 2

        for pat in cls.BALANCE_SHEET_KEYWORDS:
            if re.search(pat, sample_text):
                scores["balance_sheet"] += 2

        for pat in cls.INCOME_STATEMENT_KEYWORDS:
            if re.search(pat, sample_text):
                scores["income_statement"] += 2

        for pat in cls.NOTES_KEYWORDS:
            if re.search(pat, sample_text):
                scores["notes"] += 2

        best_statement = max(scores, key=scores.get)
        if scores[best_statement] > 0:
            return best_statement
        return None
