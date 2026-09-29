"""
Unit tests for Gemini AI Reasoning Engine.
"""

import unittest
from src.invoice_matcher.agents.gemini_reasoner import GeminiAPReasoner


class TestGeminiAPReasoner(unittest.TestCase):

    def setUp(self):
        self.reasoner = GeminiAPReasoner()

    def test_reasoning_perfect_match(self):
        analysis = self.reasoner.analyze_invoice_matching(
            invoice_data={
                "invoice_id": "INV-2026-001",
                "vendor_name": "RedPillar Cloud Solutions LLC",
                "vendor_id": "VEND-IBM-8841",
                "total_amount": 45000.0,
                "po_number": "PO-45009812"
            },
            contract_data={"contract_id": "SOW-IBM-2025-09"},
            erp_data={"po_number": "PO-45009812"},
            preliminary_match={"overall_status": "PERFECT_MATCH", "discrepancy_amount": 0.0}
        )

        self.assertEqual(analysis["model_used"], "gemini-2.5-flash")
        self.assertEqual(analysis["recommended_action"], "AUTO_APPROVE")
        self.assertGreaterEqual(len(analysis["chain_of_thought"]), 4)
        self.assertEqual(analysis["confidence_score"], 1.0)

    def test_reasoning_rate_variance(self):
        analysis = self.reasoner.analyze_invoice_matching(
            invoice_data={
                "invoice_id": "INV-2026-003",
                "vendor_name": "RedPillar Cloud Solutions LLC",
                "vendor_id": "VEND-IBM-8841",
                "total_amount": 9750.0,
                "po_number": "PO-45009812"
            },
            contract_data={"contract_id": "SOW-IBM-2025-09"},
            erp_data={"po_number": "PO-45009812"},
            preliminary_match={"overall_status": "EXCEPTION_RATE_VARIANCE", "discrepancy_amount": 1250.0}
        )

        self.assertEqual(analysis["recommended_action"], "DISPUTE_VENDOR")
        self.assertIn("Section 4.2", analysis["contract_citations"][0])
        self.assertIn("FORMAL DISCREPANCY NOTICE", analysis["dispute_memo"])


if __name__ == "__main__":
    unittest.main()
