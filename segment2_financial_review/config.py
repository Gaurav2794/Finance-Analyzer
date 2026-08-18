"""
Centralized Configuration for Financial Review Engine.

Contains all configuration-driven thresholds, tolerances, and scoring parameters.
No hardcoded thresholds throughout the codebase.
"""

from decimal import Decimal
from typing import Dict


# Fluctuation percentage thresholds by metric (% YoY change trigger)
DEFAULT_FLUCTUATION_THRESHOLDS: Dict[str, float] = {
    "revenue": 20.0,
    "expense": 20.0,
    "cogs": 20.0,
    "gross_profit": 20.0,
    "operating_profit": 20.0,
    "net_profit": 20.0,
    "assets": 15.0,
    "liabilities": 20.0,
    "equity": 20.0,
    "cash": 30.0,
    "debt": 25.0,
    "other_income": 25.0,
    "gross_margin": 5.0,        # in percentage points (pp)
    "operating_margin": 5.0,    # in percentage points (pp)
    "net_margin": 5.0,          # in percentage points (pp)
}

# Fluctuation severity multiplier (e.g. >= 2.0x threshold -> HIGH severity)
HIGH_SEVERITY_MULTIPLIER: float = 2.0

# Unusual Gain Analysis Thresholds
DEFAULT_DIVERGENCE_THRESHOLD_PP: float = 8.0   # Percentage points divergence
DEFAULT_OTHER_INCOME_GROWTH_THRESHOLD: float = 30.0  # % growth in other income
DEFAULT_OTHER_INCOME_TO_REVENUE_THRESHOLD: float = 10.0  # % of revenue

# Core Arithmetic Tolerances
DEFAULT_TOLERANCE: Decimal = Decimal("0.01")
DEFAULT_WARNING_TOLERANCE: Decimal = Decimal("0.05")
