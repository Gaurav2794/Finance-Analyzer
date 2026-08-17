"""
Generates multi-sheet sample Excel file with Balance Sheet, Profit & Loss, Cash Flow, and Disclosures.
"""

import pandas as pd
import os

os.makedirs("sample_data", exist_ok=True)

# 1. Balance Sheet
df_bs = pd.DataFrame([
    ["Particulars", "Note", "FY2024", "FY2023", "FY2022"],
    ["Property, Plant & Equipment", "4", "485.50", "440.20", "395.00"],
    ["Capital Work-in-Progress", "4", "35.80", "42.10", "28.40"],
    ["Goodwill on Consolidation", "5", "120.00", "120.00", "85.00"],
    ["Other Intangible Assets", "5", "65.40", "58.90", "44.30"],
    ["Right-of-Use Assets", "6", "145.20", "132.80", "110.50"],
    ["Non-Current Investments", "7", "180.60", "155.00", "130.20"],
    ["Total Non-Current Assets", "", "1155.40", "1054.00", "883.00"],
    ["Inventories", "11", "85.40", "74.20", "62.00"],
    ["Trade Receivables", "12", "620.50", "510.80", "435.20"],
    ["Cash & Cash Equivalents", "13", "310.20", "245.60", "185.40"],
    ["Other Bank Balances", "14", "95.00", "80.00", "65.00"],
    ["Current Investments", "15", "210.00", "175.50", "140.00"],
    ["Total Current Assets", "", "1535.60", "1260.50", "1026.00"],
    ["TOTAL ASSETS", "", "2691.00", "2314.50", "1909.00"],
    ["Equity Share Capital", "18", "120.00", "120.00", "120.00"],
    ["Other Equity", "19", "1545.30", "1312.10", "1062.80"],
    ["Total Equity", "", "1689.80", "1452.30", "1199.20"],
    ["Long-Term Borrowings", "20", "180.00", "210.00", "195.00"],
    ["Total Non-Current Liabilities", "", "371.20", "380.40", "335.30"],
    ["Short-Term Borrowings", "24", "95.00", "85.00", "72.00"],
    ["Trade Payables", "25", "315.80", "248.60", "194.20"],
    ["Other Current Liabilities", "28", "42.00", "9.40", "6.50"],
    ["Total Current Liabilities", "", "630.00", "481.80", "374.50"],
    ["TOTAL EQUITY AND LIABILITIES", "", "2691.00", "2314.50", "1909.00"]
])

# 2. Income Statement
df_is = pd.DataFrame([
    ["Particulars", "Note", "FY2024", "FY2023", "FY2022"],
    ["Revenue from Operations", "29", "3480.00", "2950.00", "2420.00"],
    ["Other Income", "30", "82.50", "65.40", "48.00"],
    ["Total Revenue", "", "3562.50", "3015.40", "2468.00"],
    ["Cost of Materials Consumed", "31", "320.40", "280.10", "235.00"],
    ["Employee Benefit Expenses", "32", "1820.00", "1540.00", "1280.00"],
    ["Finance Costs", "33", "42.50", "38.20", "32.00"],
    ["Depreciation & Amortisation Expense", "34", "118.60", "104.20", "89.50"],
    ["Other Expenses", "35", "612.00", "525.40", "435.50"],
    ["Total Expenses", "", "2913.50", "2487.90", "2072.00"],
    ["Operating Profit", "", "609.00", "500.30", "380.00"],
    ["Profit Before Tax", "", "649.00", "515.00", "396.00"],
    ["Tax Expense", "37", "154.45", "122.45", "94.80"],
    ["Profit for the Period", "", "494.55", "392.55", "301.20"]
])

# 3. Cash Flow
df_cf = pd.DataFrame([
    ["Particulars", "FY2024", "FY2023", "FY2022"],
    ["Operating Profit before Working Capital Changes", "778.80", "632.60", "499.80"],
    ["Net Cash Flows from Operating Activities", "577.55", "468.15", "368.00"],
    ["Purchase of Fixed Assets (CapEx)", "(190.20)", "(185.50)", "(155.00)"],
    ["Net Cash used in Investing Activities", "(224.70)", "(222.60)", "(183.30)"],
    ["Net Cash used in Financing Activities", "(288.25)", "(184.90)", "(143.70)"],
    ["Net Increase in Cash and Cash Equivalents", "64.60", "60.65", "41.00"],
    ["Cash and Cash Equivalents at Beginning of Year", "245.60", "184.95", "144.40"],
    ["Cash and Cash Equivalents at End of Year", "310.20", "245.60", "185.40"]
])

with pd.ExcelWriter("sample_data/sample_financials.xlsx", engine="openpyxl") as writer:
    df_bs.to_excel(writer, sheet_name="Balance Sheet", index=False, header=False)
    df_is.to_excel(writer, sheet_name="Profit & Loss", index=False, header=False)
    df_cf.to_excel(writer, sheet_name="Cash Flow Statement", index=False, header=False)

print("Generated sample_data/sample_financials.xlsx successfully!")
