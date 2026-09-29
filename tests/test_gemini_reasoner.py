"""
Unit tests for Gemini AI Reasoning Engine.
"""

import os
import unittest
from src.invoice_matcher.agents.gemini_reasoner import GeminiAPReasoner


class TestGeminiAPReasoner(unittest.TestCase):

    def setUp(self):
        os.environ.pop("GEMINI_MODEL", None)
        self.reasoner = GeminiAPReasoner()

    def tearDown(self):
        os.environ.pop("GEMINI_MODEL", None)

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

        self.assertEqual(analysis["model_used"], "gemini-3.8-flash")
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

    def test_model_selection_and_switch(self):
        """Test dynamically changing the model to Gemini 3.8 Pro."""
        self.reasoner.set_model("gemini-3.8-pro")
        self.assertEqual(self.reasoner.model, "gemini-3.8-pro")

        analysis = self.reasoner.analyze_invoice_matching(
            invoice_data={"invoice_id": "INV-TEST-01"},
            contract_data={},
            erp_data={},
            preliminary_match={"overall_status": "PERFECT_MATCH"}
        )
        self.assertEqual(analysis["model_used"], "gemini-3.8-pro")
        self.assertIn("Gemini 3.8 Pro", analysis["engine"])

    def test_available_models(self):
        """Verify available models contain current generation models."""
        model_ids = [m["id"] for m in self.reasoner.AVAILABLE_MODELS]
        self.assertIn("gemini-3.8-flash", model_ids)
        self.assertIn("gemini-3.8-pro", model_ids)
        self.assertNotIn("gemini-2.5-flash", model_ids)


if __name__ == "__main__":
    unittest.main()
