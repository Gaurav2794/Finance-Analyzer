"""
Financial Label Mapping Engine.
Normalizes raw textual line items from PDFs/Excel/CSVs to standardized canonical keys
used in the Segment 1 -> Segment 2 JSON contract.
"""

import re
from typing import Optional, Tuple, Dict


class LabelMapper:
    # Standard label mappings for Balance Sheet
    BALANCE_SHEET_MAP: Dict[str, str] = {
        # Non-Current Assets
        "property, plant and equipment": "property_plant_equipment",
        "property plant and equipment": "property_plant_equipment",
        "property, plant & equipment": "property_plant_equipment",
        "property plant & equipment": "property_plant_equipment",
        "tangible fixed assets": "property_plant_equipment",
        "fixed assets": "property_plant_equipment",
        "tangible assets": "property_plant_equipment",
        "capital work-in-progress": "capital_work_in_progress",
        "capital work in progress": "capital_work_in_progress",
        "cwip": "capital_work_in_progress",
        "goodwill": "goodwill",
        "goodwill on consolidation": "goodwill",
        "other intangible assets": "intangible_assets",
        "intangible assets": "intangible_assets",
        "intangibles": "intangible_assets",
        "right-of-use assets": "right_of_use_assets",
        "right of use assets": "right_of_use_assets",
        "rou assets": "right_of_use_assets",
        "non-current investments": "investments_non_current",
        "non current investments": "investments_non_current",
        "investments in joint ventures": "investments_non_current",
        "other non-current financial assets": "other_financial_assets_non_current",
        "other non current financial assets": "other_financial_assets_non_current",
        "deferred tax assets (net)": "deferred_tax_assets_net",
        "deferred tax assets": "deferred_tax_assets_net",
        "other non-current assets": "other_non_current_assets",
        "other non current assets": "other_non_current_assets",
        "total non-current assets": "total_non_current_assets",
        "total non current assets": "total_non_current_assets",

        # Current Assets
        "inventories": "inventories",
        "inventory": "inventories",
        "stock in trade": "inventories",
        "trade receivables": "trade_receivables",
        "accounts receivable": "trade_receivables",
        "sundry debtors": "trade_receivables",
        "debtors": "trade_receivables",
        "cash and cash equivalents": "cash_and_cash_equivalents",
        "cash & cash equivalents": "cash_and_cash_equivalents",
        "cash and bank balances": "cash_and_cash_equivalents",
        "cash & bank": "cash_and_cash_equivalents",
        "bank balances other than cash": "bank_balances_other",
        "other bank balances": "bank_balances_other",
        "current investments": "current_investments",
        "short term investments": "current_investments",
        "other current financial assets": "other_current_financial_assets",
        "unbilled revenue": "other_current_financial_assets",
        "other current assets": "other_current_assets",
        "total current assets": "total_current_assets",
        "total assets": "total_assets",

        # Equity
        "equity share capital": "equity_share_capital",
        "share capital": "equity_share_capital",
        "common stock": "equity_share_capital",
        "other equity / retained earnings": "other_equity",
        "other equity": "other_equity",
        "reserves and surplus": "other_equity",
        "reserves & surplus": "other_equity",
        "retained earnings": "other_equity",
        "non-controlling interests": "non_controlling_interests",
        "minority interest": "non_controlling_interests",
        "total equity & liabilities": "total_equity_and_liabilities",
        "total equity and liabilities": "total_equity_and_liabilities",
        "total equity": "total_equity",

        # Non-Current Liabilities
        "long-term borrowings": "long_term_borrowings",
        "long term borrowings": "long_term_borrowings",
        "non-current borrowings": "long_term_borrowings",
        "term loans": "long_term_borrowings",
        "non-current lease liabilities": "lease_liabilities_non_current",
        "lease liabilities - non current": "lease_liabilities_non_current",
        "long-term provisions": "long_term_provisions",
        "long term provisions": "long_term_provisions",
        "deferred tax liabilities (net)": "deferred_tax_liabilities_net",
        "deferred tax liabilities": "deferred_tax_liabilities_net",
        "other non-current liabilities": "other_non_current_liabilities",
        "total non-current liabilities": "total_non_current_liabilities",

        # Current Liabilities
        "short-term borrowings": "short_term_borrowings",
        "short term borrowings": "short_term_borrowings",
        "current borrowings": "short_term_borrowings",
        "working capital loan": "short_term_borrowings",
        "current lease liabilities": "lease_liabilities_current",
        "lease liabilities - current": "lease_liabilities_current",
        "trade payables": "trade_payables",
        "accounts payable": "trade_payables",
        "sundry creditors": "trade_payables",
        "other current financial liabilities": "other_current_financial_liabilities",
        "short-term provisions": "short_term_provisions",
        "short term provisions": "short_term_provisions",
        "provisions": "short_term_provisions",
        "current tax liabilities (net)": "current_tax_liabilities_net",
        "provision for income tax": "current_tax_liabilities_net",
        "other current liabilities": "other_current_liabilities",
        "total current liabilities": "total_current_liabilities",
        "total liabilities": "total_liabilities",
        "balance sheet difference": "balance_sheet_difference",
    }

    # Standard label mappings for Income Statement
    INCOME_STATEMENT_MAP: Dict[str, str] = {
        "revenue from operations": "revenue_from_operations",
        "revenue from contracts with customers": "revenue_from_operations",
        "gross revenue": "revenue_from_operations",
        "revenue": "revenue_from_operations",
        "sales": "revenue_from_operations",
        "sales revenue": "revenue_from_operations",
        "turnover": "revenue_from_operations",
        "gross turnover": "revenue_from_operations",
        "other income": "other_income",
        "other operating income": "other_income",
        "total income": "total_income",
        "total revenue": "total_income",

        # Expenses
        "cost of materials / cost of sales": "cost_of_materials_consumed",
        "cost of materials consumed": "cost_of_materials_consumed",
        "cost of goods sold": "cost_of_materials_consumed",
        "cost of sales": "cost_of_materials_consumed",
        "cogs": "cost_of_materials_consumed",
        "raw materials consumed": "cost_of_materials_consumed",
        "employee benefit expenses": "employee_benefit_expenses",
        "employee benefits expense": "employee_benefit_expenses",
        "salaries and wages": "employee_benefit_expenses",
        "staff costs": "employee_benefit_expenses",
        "finance costs": "finance_costs",
        "finance cost": "finance_costs",
        "interest expense": "finance_costs",
        "interest and finance charges": "finance_costs",
        "depreciation and amortization expense": "depreciation_and_amortization",
        "depreciation and amortisation expense": "depreciation_and_amortization",
        "depreciation & amortisation": "depreciation_and_amortization",
        "depreciation and amortization": "depreciation_and_amortization",
        "depreciation": "depreciation_and_amortization",
        "total operating expenses": "total_operating_expenses",
        "other expenses": "other_operating_expenses",
        "other operating expenses": "other_operating_expenses",
        "operating expenses": "other_operating_expenses",
        "administrative expenses": "other_operating_expenses",
        "total expenses": "total_expenses",

        # Profit Lines
        "operating profit / ebit": "operating_profit",
        "operating profit": "operating_profit",
        "operating income": "operating_profit",
        "ebit": "operating_profit",
        "gross profit": "gross_profit",
        "profit before exceptional items and tax": "profit_before_tax",
        "profit before tax": "profit_before_tax",
        "profit before taxation": "profit_before_tax",
        "pbt": "profit_before_tax",
        "current tax": "current_tax",
        "deferred tax": "deferred_tax",
        "total tax expense": "total_tax_expense",
        "tax expense": "total_tax_expense",
        "profit for the period / net profit": "profit_for_the_period",
        "profit for the period": "profit_for_the_period",
        "profit for the year": "profit_for_the_period",
        "net profit": "profit_for_the_period",
        "net profit after tax": "profit_for_the_period",
        "pat": "profit_for_the_period",
        "net income": "profit_for_the_period",
        "exceptional gain": "exceptional_gain",
        "exceptional loss": "exceptional_loss",
        "basic earnings per share": "basic_eps",
        "basic eps": "basic_eps",
        "diluted earnings per share": "diluted_eps",
        "diluted eps": "diluted_eps"
    }

    # Standard label mappings for Cash Flow
    CASH_FLOW_MAP: Dict[str, str] = {
        "profit before tax": "profit_before_tax",
        "depreciation & amortisation": "depreciation_and_amortization",
        "depreciation and amortization": "depreciation_and_amortization",
        "working capital movement": "working_capital_adjustments",
        "working capital adjustments": "working_capital_adjustments",
        "interest paid": "interest_paid",
        "taxes paid": "taxes_paid",
        "operating profit before working capital changes": "operating_profit_before_working_capital_changes",
        "cash generated from operations": "cash_generated_from_operations",
        "net cash from operating activities": "net_cash_from_operating_activities",
        "net cash flows from operating activities": "net_cash_from_operating_activities",
        "cash flow from operating activities": "net_cash_from_operating_activities",
        "cfo": "net_cash_from_operating_activities",
        "operating cash flow": "net_cash_from_operating_activities",

        "net cash from investing activities": "net_cash_from_investing_activities",
        "net cash flows from investing activities": "net_cash_from_investing_activities",
        "net cash used in investing activities": "net_cash_from_investing_activities",
        "cash flow from investing activities": "net_cash_from_investing_activities",
        "cfi": "net_cash_from_investing_activities",
        "investing cash flow": "net_cash_from_investing_activities",
        "purchase of property, plant, equipment": "purchase_of_ppe_and_intangibles",
        "capital expenditure": "purchase_of_ppe_and_intangibles",
        "capex": "purchase_of_ppe_and_intangibles",
        "acquisition / investment activities": "purchase_of_investments",
        "asset disposal proceeds": "proceeds_from_sale_of_assets",

        "new borrowings": "proceeds_from_borrowings",
        "proceeds from borrowings": "proceeds_from_borrowings",
        "repayment of borrowings": "repayment_of_borrowings",
        "lease principal payments": "lease_principal_payments",
        "dividends paid": "dividends_paid",
        "net cash from financing activities": "net_cash_from_financing_activities",
        "net cash flows from financing activities": "net_cash_from_financing_activities",
        "net cash used in financing activities": "net_cash_from_financing_activities",
        "cash flow from financing activities": "net_cash_from_financing_activities",
        "cff": "net_cash_from_financing_activities",
        "financing cash flow": "net_cash_from_financing_activities",

        "net increase / (decrease) in cash and cash equivalents": "net_change_in_cash_and_cash_equivalents",
        "net increase in cash and cash equivalents": "net_change_in_cash_and_cash_equivalents",
        "net change in cash": "net_change_in_cash_and_cash_equivalents",
        "cash and cash equivalents at beginning of the year": "opening_cash_and_cash_equivalents",
        "cash and cash equivalents at the beginning of the year": "opening_cash_and_cash_equivalents",
        "opening cash balance": "opening_cash_and_cash_equivalents",
        "opening cash": "opening_cash_and_cash_equivalents",
        "cash and cash equivalents at end of the year": "closing_cash_and_cash_equivalents",
        "cash and cash equivalents at the end of the year": "closing_cash_and_cash_equivalents",
        "closing cash balance": "closing_cash_and_cash_equivalents",
        "closing cash": "closing_cash_and_cash_equivalents",
        "cash flow reconciliation difference": "cash_flow_reconciliation_difference",
    }

    @classmethod
    def clean_text(cls, raw_label: str) -> str:
        """Removes notes numbers, punctuation, excessive spaces, Roman numerals from label."""
        if not raw_label:
            return ""
        label = raw_label.lower().strip()
        # Remove footnote/note numbers like (1), [2], Note 5, 4(a)
        label = re.sub(r"\b(note\s*\d+[a-z]?|\(\d+\)|\[\d+\])", "", label)
        # Remove Roman numeral prefixes like I., II., (a), (b), 1., 2.
        label = re.sub(r"^\s*([ivxlcdm]+\.|\([a-z0-9]+\)|\d+\.)\s*", "", label)
        # Normalize whitespace and hyphens
        label = re.sub(r"[\s\t\n]+", " ", label)
        label = label.replace("–", "-").replace("—", "-").strip()
        return label

    @classmethod
    def map_label(cls, raw_label: str, section: Optional[str] = None) -> Tuple[Optional[str], str]:
        """
        Maps a raw label to (standard_key, cleaned_label).
        If section is provided ('balance_sheet', 'income_statement', 'cash_flow'), prioritizes that map.
        """
        cleaned = cls.clean_text(raw_label)
        if not cleaned:
            return None, cleaned

        if section == "balance_sheet":
            if cleaned in cls.BALANCE_SHEET_MAP:
                return cls.BALANCE_SHEET_MAP[cleaned], cleaned
        elif section == "income_statement":
            if cleaned in cls.INCOME_STATEMENT_MAP:
                return cls.INCOME_STATEMENT_MAP[cleaned], cleaned
        elif section == "cash_flow":
            if cleaned in cls.CASH_FLOW_MAP:
                return cls.CASH_FLOW_MAP[cleaned], cleaned

        # Fallback cross-search across all dictionaries (exact match first)
        for mapping in [cls.BALANCE_SHEET_MAP, cls.INCOME_STATEMENT_MAP, cls.CASH_FLOW_MAP]:
            if cleaned in mapping:
                return mapping[cleaned], cleaned

        # Fuzzy substring match - prioritize longer patterns first
        all_items = []
        for mapping in [cls.BALANCE_SHEET_MAP, cls.INCOME_STATEMENT_MAP, cls.CASH_FLOW_MAP]:
            all_items.extend(mapping.items())
        # Sort by length of pattern descending
        all_items.sort(key=lambda x: len(x[0]), reverse=True)

        for pattern, key in all_items:
            if len(pattern) > 5 and (pattern in cleaned or cleaned in pattern):
                return key, cleaned

        # Fallback: create safe snake_case key
        safe_key = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
        return safe_key or None, cleaned
