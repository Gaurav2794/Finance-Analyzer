"""
Unit tests for segment2_financial_review/analytics/related_disclosure.py.

Coverage:
- Calculation of related parties count, transactions count, disclosed value, total value, difference, consistency %
- Sub-item transaction summation and mismatch detection
- Missing disclosure note handling (NOT_AVAILABLE status)
- Real and sample financial datasets compatibility
"""

import json
import os
import sys
import unittest
from decimal import Decimal

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from segment2_financial_review.analytics import related_disclosure as rd


def _build_mock_rp_data(
    disclosed_value="63.80",
    total_val=None,
    transactions=None,
    party_count=4,
    tx_count=12,
    has_note=True,
):
    notes = []
    if has_note:
        note_dict = {
            "note_number": "Note 40",
            "topic": "Related Party Disclosures",
            "disclosed_value": disclosed_value,
            "related_party_count": party_count,
            "transaction_count": tx_count,
            "source": {"file": "report.pdf", "page": 77},
        }
        if total_val is not None:
            note_dict["total_transaction_value"] = total_val
        if transactions is not None:
            note_dict["transactions"] = transactions
        notes.append(note_dict)

    return {
        "metadata": {
            "document_id": "DOC-TEST-RP",
            "periods": [{"period_key": "FY2024", "is_audited": True}],
        },
        "balance_sheet": {},
        "income_statement": {},
        "cash_flow_statement": {},
        "extracted_notes_and_disclosures": notes,
    }


class TestRelatedDisclosure(unittest.TestCase):

    def test_01_consistent_related_party_disclosure(self):
        """Test perfectly consistent related party disclosure."""
        data = _build_mock_rp_data(disclosed_value="63.80")
        res = rd.run(data)

        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(res.number_of_related_parties, 4)
        self.assertEqual(res.number_of_related_transactions, 12)
        self.assertEqual(res.disclosed_related_party_value, Decimal("63.80"))
        self.assertEqual(res.total_related_party_value, Decimal("63.80"))
        self.assertEqual(res.disclosure_difference, Decimal("0.00"))
        self.assertEqual(res.disclosure_consistency_pct, 100.0)
        self.assertEqual(res.note_reference, "Note 40")
        self.assertIsNotNone(res.note_source)

    def test_02_sub_transaction_sum_mismatch(self):
        """Test mismatch when sum of sub-transactions differs from disclosed total."""
        # Sub-transactions: 19.70 + 44.10 + 10.00 = 73.80 vs disclosed 63.80 (diff = 10.00 Cr)
        txs = [
            {"description": "KMP", "amount": "19.70"},
            {"description": "Associate", "amount": "44.10"},
            {"description": "Other", "amount": "10.00"},
        ]
        data = _build_mock_rp_data(disclosed_value="63.80", transactions=txs)
        res = rd.run(data)

        self.assertEqual(res.status, "WARNING")
        self.assertEqual(res.score, 75.0)
        self.assertEqual(res.total_related_party_value, Decimal("73.80"))
        self.assertEqual(res.disclosed_related_party_value, Decimal("63.80"))
        self.assertEqual(res.disclosure_difference, Decimal("10.00"))
        self.assertEqual(res.undisclosed_mismatched_value, Decimal("10.00"))
        # 63.80 / 73.80 * 100 = 86.45%
        self.assertEqual(res.disclosure_consistency_pct, 86.45)
        self.assertTrue(any("MISMATCH" in issue for issue in res.issues))

    def test_03_missing_related_party_note(self):
        """Test missing disclosure note gracefully returns NOT_AVAILABLE."""
        data = _build_mock_rp_data(has_note=False)
        res = rd.run(data)

        self.assertEqual(res.status, "NOT_AVAILABLE")
        self.assertIsNone(res.total_related_party_value)
        self.assertIsNone(res.disclosed_related_party_value)
        self.assertTrue(any("NOT_AVAILABLE" in issue for issue in res.issues))

    def test_04_sample_and_real_dataset_compatibility(self):
        """Run against sample_financial_data.json and real output."""
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = rd.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "NOT_AVAILABLE"])
            self.assertEqual(res.number_of_related_parties, 4)
            self.assertEqual(res.disclosed_related_party_value, Decimal("63.80"))

        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = rd.run(data)
            # Real output has 0 disclosure notes, so it should cleanly return NOT_AVAILABLE
            self.assertEqual(res.status, "NOT_AVAILABLE")


if __name__ == "__main__":
    unittest.main()
