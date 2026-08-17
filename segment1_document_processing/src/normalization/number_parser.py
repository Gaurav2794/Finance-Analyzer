"""
Number and Currency Normalizer for Financial Documents.
Handles:
- Indian comma notation: 12,50,000
- US comma notation: 1,250,000
- Negative numbers in accounting brackets: (5,000) or ( 5,000.50 ) -> -5000.50
- Currency symbols: ₹, $, €, £, INR, USD
- Magnitude suffixes: Cr / Crore, L / Lakh, K / Thousand, M / Million, B / Billion
- Dash / Nil indicators: '-', '–', 'nil', 'N/A' -> 0.0 or None
"""

import re
from typing import Optional, Tuple


class NumberParser:
    # Regex patterns
    CURRENCY_SYMBOLS = r"[₹\$€£]|INR|USD|EUR|GBP|Rs\.?|Rs"
    BRACKET_NEGATIVE = re.compile(r"^\s*\(\s*([^()]+)\s*\)\s*$")
    TRAILING_NEGATIVE = re.compile(r"^\s*([0-9.,]+)\s*-\s*$")
    CLEAN_CHARS = re.compile(r"[₹\$€£]|INR|USD|EUR|GBP|Rs\.?|Rs|\s")

    SCALE_MULTIPLIERS = {
        "cr": 10000000.0,
        "crore": 10000000.0,
        "crores": 10000000.0,
        "l": 100000.0,
        "lac": 100000.0,
        "lakh": 100000.0,
        "lakhs": 100000.0,
        "k": 1000.0,
        "thousand": 1000.0,
        "thousands": 1000.0,
        "m": 1000000.0,
        "mn": 1000000.0,
        "million": 1000000.0,
        "millions": 1000000.0,
        "b": 1000000000.0,
        "bn": 1000000000.0,
        "billion": 1000000000.0,
        "billions": 1000000000.0,
    }

    @classmethod
    def parse_financial_number(cls, raw_val: any, default_scale_multiplier: float = 1.0) -> Optional[float]:
        """
        Parses a raw string or numeric value into a standard float.
        """
        if raw_val is None:
            return None

        if isinstance(raw_val, (int, float)):
            if str(raw_val) == "nan":
                return None
            return float(raw_val)

        text = str(raw_val).strip()
        if not text:
            return None

        # Check for nil/dash/na
        if text in ["-", "–", "—", "nil", "Nil", "NIL", "N/A", "n/a", "NA", "None", "null"]:
            return 0.0

        is_negative = False

        # Check for bracket notation: (123.45)
        bracket_match = cls.BRACKET_NEGATIVE.match(text)
        if bracket_match:
            is_negative = True
            text = bracket_match.group(1).strip()

        # Check for trailing minus: 123.45-
        trailing_match = cls.TRAILING_NEGATIVE.match(text)
        if trailing_match:
            is_negative = True
            text = trailing_match.group(1).strip()

        # Check for leading minus
        if text.startswith("-"):
            is_negative = True
            text = text[1:].strip()

        # Check for inline unit scales like '12.5 Cr' or '150 K'
        unit_multiplier = 1.0
        text_lower = text.lower()
        for unit_name, multiplier in cls.SCALE_MULTIPLIERS.items():
            pattern = rf"\b{unit_name}\b"
            if re.search(pattern, text_lower):
                unit_multiplier = multiplier
                text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
                break

        # Remove currency symbols and non-numeric separators except . and ,
        text = cls.CLEAN_CHARS.sub("", text)

        # Remove commas (handles both Indian 12,50,000 and US 1,250,000)
        text = text.replace(",", "")

        # Remove % if percentage
        text = text.replace("%", "").strip()

        try:
            val = float(text)
            if is_negative:
                val = -val
            
            # Apply inline unit multiplier if found, else default
            if unit_multiplier != 1.0:
                val = val * (unit_multiplier / default_scale_multiplier)

            return round(val, 4)
        except ValueError:
            return None

    @classmethod
    def detect_currency_and_scale(cls, text: str) -> Tuple[str, str, float]:
        """
        Detects currency and magnitude scale from document headers or text.
        Returns (currency, scale_label, multiplier).
        """
        text_lower = text.lower()
        
        currency = "INR"
        if "usd" in text_lower or "$" in text:
            currency = "USD"
        elif "eur" in text_lower or "€" in text:
            currency = "EUR"
        elif "gbp" in text_lower or "£" in text:
            currency = "GBP"
        elif "inr" in text_lower or "₹" in text or "rs" in text_lower or "rupees" in text_lower:
            currency = "INR"

        scale = "Absolute"
        multiplier = 1.0

        if "crore" in text_lower or "cr." in text_lower or "in crores" in text_lower or "₹ in cr" in text_lower:
            scale = "Crores"
            multiplier = 10000000.0
        elif "lakh" in text_lower or "lacs" in text_lower or "in lakhs" in text_lower or "₹ in lakh" in text_lower:
            scale = "Lakhs"
            multiplier = 100000.0
        elif "million" in text_lower or "in millions" in text_lower or "mn" in text_lower:
            scale = "Millions"
            multiplier = 1000000.0
        elif "thousand" in text_lower or "in thousands" in text_lower or "'000" in text_lower:
            scale = "Thousands"
            multiplier = 1000.0
        elif "billion" in text_lower or "in billions" in text_lower or "bn" in text_lower:
            scale = "Billions"
            multiplier = 1000000000.0

        return currency, scale, multiplier
