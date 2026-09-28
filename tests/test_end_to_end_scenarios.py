"""
End-to-End integration tests for all 5 IBM AP 3-Way Matching scenarios.
"""

import unittest
from src.invoice_matcher.demo_data.dataset import build_demo_environment
from src.invoice_matcher.agents.supervisor import APOrchestrator
from src.invoice_matcher.models.matching import MatchStatus, ActionType


class TestEndToEndScenarios(unittest.TestCase):

    def setUp(self):
        self.retriever, self.erp, self.invoices = build_demo_environment()
        self.orchestrator = APOrchestrator(retriever=self.retriever, erp_connector=self.erp)

    def test_scenario_1_clean_3_way_match(self):
        """Clean 3-way match on milestone MS-03 should auto-approve."""
        inv = self.invoices[0]  # INV-2026-001
        result = self.orchestrator.process_invoice(inv)

        self.assertEqual(result.overall_status, MatchStatus.PERFECT_MATCH)
        self.assertEqual(result.resolution_action.action_type, ActionType.AUTO_APPROVE)
        self.assertIn("SYSTEM POSTING MEMORANDUM", result.resolution_action.generated_communication)
        self.assertEqual(result.discrepancy_amount, 0.0)

    def test_scenario_2_semantic_role_match(self):
        """Informal title 'Lead Cloud DevOps Architect' matches SOW rate card via RAG."""
        inv = self.invoices[1]  # INV-2026-002
        result = self.orchestrator.process_invoice(inv)

        self.assertEqual(result.overall_status, MatchStatus.PERFECT_MATCH)
        self.assertEqual(result.resolution_action.action_type, ActionType.AUTO_APPROVE)
        self.assertEqual(result.line_matches[0].matched_role_or_milestone, "Senior Infrastructure Consultant Tier 1")

    def test_scenario_3_rate_variance_dispute(self):
        """Billed rate $195 vs $170 cap triggers dispute letter citing Section 4.2."""
        inv = self.invoices[2]  # INV-2026-003
        result = self.orchestrator.process_invoice(inv)

        self.assertEqual(result.overall_status, MatchStatus.EXCEPTION_RATE_VARIANCE)
        self.assertEqual(result.resolution_action.action_type, ActionType.DRAFT_VENDOR_INQUIRY)
        self.assertEqual(result.discrepancy_amount, 1250.0)
        self.assertIn("Formal Discrepancy Notice", result.resolution_action.generated_communication)
        self.assertIn("$1,250.00", result.resolution_action.generated_communication)

    def test_scenario_4_missing_gr_receipt(self):
        """Valid rate but missing Goods/Services Receipt triggers internal PM sign-off request."""
        inv = self.invoices[3]  # INV-2026-004
        result = self.orchestrator.process_invoice(inv)

        self.assertEqual(result.overall_status, MatchStatus.EXCEPTION_MISSING_GR)
        self.assertEqual(result.resolution_action.action_type, ActionType.REQUEST_INTERNAL_SIGN_OFF)
        self.assertIn("ACTION REQUIRED: Delivery Receipt Missing", result.resolution_action.generated_communication)

    def test_scenario_5_tax_tolerance(self):
        """$8.50 rounding tax variance falls within $25 tolerance and auto-approves."""
        inv = self.invoices[4]  # INV-2026-005
        result = self.orchestrator.process_invoice(inv)

        self.assertEqual(result.overall_status, MatchStatus.EXCEPTION_TAX_VARIANCE)
        self.assertEqual(result.resolution_action.action_type, ActionType.AUTO_APPROVE)
        self.assertTrue(result.resolution_action.tolerance_applied)
        self.assertIn("AUTOMATED TOLERANCE CLEARANCE MEMO", result.resolution_action.generated_communication)


if __name__ == "__main__":
    unittest.main()
