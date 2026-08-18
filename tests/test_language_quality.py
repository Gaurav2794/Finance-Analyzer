"""
Unit tests for Language Quality / Spelling & Grammar Review Engine.
Tests all 5 required cases:
1. Correct financial text → PASSED
2. Intentional spelling errors → correctly detected
3. Intentional grammar issue → correctly detected
4. Financial terminology/proper nouns → not incorrectly flagged
5. Empty/missing text → NOT_AVAILABLE
"""

import unittest
from segment2_financial_review.checks.language_quality import LanguageQualityEngine, run


class TestLanguageQualityEngine(unittest.TestCase):

    def test_1_correct_financial_text_passed(self):
        """Case 1: Correct financial narrative and notes → PASSED, score=100.0."""
        data = {
            "metadata": {
                "company": {"name": "Infosys Limited"}
            },
            "extracted_notes_and_disclosures": [
                {
                    "note_number": "1",
                    "topic": "Significant Accounting Policies",
                    "text": (
                        "The financial statements have been prepared in accordance with Indian Accounting Standards "
                        "(Ind AS) notified under Section 133 of the Companies Act. Revenue is recognized upon transfer "
                        "of control of promised products or services to customers in an amount that reflects the "
                        "consideration which the company expects to receive in exchange for those products or services."
                    ),
                    "source": {"page": 12, "file": "annual_report.pdf"}
                }
            ]
        }
        res = LanguageQualityEngine.evaluate(data)
        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(res.spelling_errors_count, 0)
        self.assertEqual(res.grammar_issues_count, 0)
        self.assertEqual(res.reviewed_passages_count, 1)
        self.assertEqual(len(res.details), 0)

    def test_2_intentional_spelling_errors_detected(self):
        """Case 2: Intentional spelling errors → correctly detected with suggestion & source."""
        data = {
            "metadata": {
                "company": {"name": "Test Corp"}
            },
            "extracted_notes_and_disclosures": [
                {
                    "note_number": "4",
                    "topic": "Borrowings",
                    "text": "The company has non-current liabilites and exepenses due to routine maintanance.",
                    "source": {"page": 18, "file": "report.pdf"}
                }
            ]
        }
        res = LanguageQualityEngine.evaluate(data)
        self.assertIn(res.status, ["WARNING", "FAILED"])
        self.assertGreater(res.spelling_errors_count, 0)
        
        flagged_words = [d.text.lower() for d in res.details if d.type == "SPELLING"]
        self.assertIn("liabilites", flagged_words)
        self.assertIn("exepenses", flagged_words)
        self.assertIn("maintanance", flagged_words)

        # Check source evidence is attached
        for d in res.details:
            self.assertEqual(d.source.page, 18)
            self.assertEqual(d.source.file, "report.pdf")

    def test_3_intentional_grammar_issues_detected(self):
        """Case 3: Intentional grammar errors (doubled words & agreement) → correctly detected."""
        data = {
            "metadata": {
                "company": {"name": "Test Corp"}
            },
            "extracted_notes_and_disclosures": [
                {
                    "note_number": "7",
                    "topic": "Commitments",
                    "text": "In the the opinion of the management, total assets is sufficient. A audit was performed.",
                    "source": {"page": 22, "file": "report.pdf"}
                }
            ]
        }
        res = LanguageQualityEngine.evaluate(data)
        self.assertGreater(res.grammar_issues_count, 0)
        
        grammar_details = [d for d in res.details if d.type == "GRAMMAR"]
        grammar_texts = [d.text.lower() for d in grammar_details]
        
        # Should catch "the the", "assets is", and "a audit"
        self.assertTrue(any("the the" in t for t in grammar_texts))
        self.assertTrue(any("assets is" in t for t in grammar_texts))
        self.assertTrue(any("a audit" in t for t in grammar_texts))

    def test_4_financial_lexicon_and_proper_nouns_not_flagged(self):
        """Case 4: Financial abbreviations, Ind AS terms, Indian currency & proper nouns → not incorrectly flagged."""
        data = {
            "metadata": {
                "company": {"name": "Reliance Industries Limited"}
            },
            "extracted_notes_and_disclosures": [
                {
                    "note_number": "15",
                    "topic": "Financial Instruments",
                    "text": (
                        "EBITDA and PAT increased in FY2024. Long-term debentures are amortised under Ind AS 109. "
                        "The company holds ₹3,480 Crores in liquid funds and 50 Lakhs in debentures. "
                        "Reliance maintains adequate solvency and interest coverage ratios without impairment."
                    ),
                    "source": {"page": 30, "file": "reliance_report.pdf"}
                }
            ]
        }
        res = LanguageQualityEngine.evaluate(data)
        self.assertEqual(res.spelling_errors_count, 0)
        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.score, 100.0)

    def test_5_empty_missing_text_not_available(self):
        """Case 5: Empty/missing narrative text → returns NOT_AVAILABLE score=0.0."""
        data_no_notes = {
            "metadata": {
                "company": {"name": "Minimal Spreadsheet Corp"}
            },
            "extracted_notes_and_disclosures": []
        }
        res = LanguageQualityEngine.evaluate(data_no_notes)
        self.assertEqual(res.status, "NOT_AVAILABLE")
        self.assertEqual(res.score, 0.0)
        self.assertEqual(res.reviewed_passages_count, 0)
        self.assertEqual(len(res.details), 0)

        data_empty_strings = {
            "metadata": {
                "company": {"name": "Empty Notes Corp"}
            },
            "extracted_notes_and_disclosures": [
                {"note_number": "1", "text": "   "}
            ]
        }
        res_empty = LanguageQualityEngine.evaluate(data_empty_strings)
        self.assertEqual(res_empty.status, "NOT_AVAILABLE")
        self.assertEqual(res_empty.score, 0.0)


if __name__ == "__main__":
    unittest.main()
