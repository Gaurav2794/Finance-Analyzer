"""
Unit & Integration Tests for Segment 1 Document Processing Pipeline.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from segment1_document_processing.src.normalization.number_parser import NumberParser
from segment1_document_processing.src.normalization.label_mapper import LabelMapper
from segment1_document_processing.src.extraction.statement_detector import StatementDetector
from segment1_document_processing.src.pipeline import DocumentProcessingPipeline


class TestSegment1DocumentProcessing(unittest.TestCase):

    def test_number_parser(self):
        # Indian notation
        self.assertEqual(NumberParser.parse_financial_number("12,50,000"), 1250000.0)
        # Accounting bracket negative
        self.assertEqual(NumberParser.parse_financial_number("(5,000)"), -5000.0)
        self.assertEqual(NumberParser.parse_financial_number(" ( 185.50 ) "), -185.50)
        # Trailing minus
        self.assertEqual(NumberParser.parse_financial_number("250.00-"), -250.00)
        # Currency symbol
        self.assertEqual(NumberParser.parse_financial_number("₹ 3,480.00"), 3480.00)
        self.assertEqual(NumberParser.parse_financial_number("$1,200.50"), 1200.50)
        # Nil / dashes
        self.assertEqual(NumberParser.parse_financial_number("-"), 0.0)
        self.assertEqual(NumberParser.parse_financial_number("Nil"), 0.0)

    def test_label_mapper(self):
        # Balance Sheet line items
        key, _ = LabelMapper.map_label("Cash and Cash Equivalents", section="balance_sheet")
        self.assertEqual(key, "cash_and_cash_equivalents")

        key, _ = LabelMapper.map_label("Tangible Fixed Assets", section="balance_sheet")
        self.assertEqual(key, "property_plant_equipment")

        key, _ = LabelMapper.map_label("Sundry Debtors", section="balance_sheet")
        self.assertEqual(key, "trade_receivables")

        # Income Statement line items
        key, _ = LabelMapper.map_label("Revenue from Operations", section="income_statement")
        self.assertEqual(key, "revenue_from_operations")

        key, _ = LabelMapper.map_label("Cost of Goods Sold (COGS)", section="income_statement")
        self.assertEqual(key, "cost_of_materials_consumed")

    def test_statement_detector(self):
        self.assertEqual(StatementDetector.detect_statement_type("Consolidated Balance Sheet as of March 31"), "balance_sheet")
        self.assertEqual(StatementDetector.detect_statement_type("Statement of Profit and Loss for the year ended"), "income_statement")
        self.assertEqual(StatementDetector.detect_statement_type("Cash Flows from Operating Activities"), "cash_flow_statement")

    def test_csv_pipeline_run(self):
        csv_path = "sample_data/sample_balance_sheet.csv"
        self.assertTrue(os.path.exists(csv_path))
        
        result = DocumentProcessingPipeline.process_file_or_directory(csv_path, company_name="Apex Technologies")
        
        # Verify structure matches frozen contract
        self.assertIn("metadata", result)
        self.assertIn("team1_metrics", result)
        self.assertIn("balance_sheet", result)
        self.assertIn("document_quality", result["team1_metrics"])
        self.assertIn("extraction", result["team1_metrics"])
        self.assertIn("rag", result["team1_metrics"])
        
        bs = result["balance_sheet"]
        self.assertIn("property_plant_equipment", bs)
        self.assertIn("trade_receivables", bs)
        self.assertIn("cash_and_cash_equivalents", bs)
        
        # Check extracted multi-year values
        self.assertEqual(bs["property_plant_equipment"]["values"]["FY2024"], 485.50)
        self.assertEqual(bs["property_plant_equipment"]["values"]["FY2023"], 440.20)

    def test_excel_pipeline_run(self):
        excel_path = "sample_data/sample_financials.xlsx"
        if os.path.exists(excel_path):
            result = DocumentProcessingPipeline.process_file_or_directory(excel_path)
            self.assertIn("balance_sheet", result)
            self.assertIn("income_statement", result)
            self.assertIn("cash_flow_statement", result)
            self.assertEqual(result["team1_metrics"]["document_quality"]["data_quality_status"], "EXCELLENT")


if __name__ == "__main__":
    unittest.main()
