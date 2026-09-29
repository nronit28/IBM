"""
Unit tests for Synthetic Data Generator and Ingestion/Upload Pipeline.
"""

import unittest
from datetime import date
from src.invoice_matcher.demo_data.synthetic_generator import SyntheticDataGenerator, SCENARIO_SPECS
from src.invoice_matcher.demo_data.dataset import build_demo_environment
from src.invoice_matcher.agents.supervisor import APOrchestrator
from src.invoice_matcher.models.matching import MatchStatus, ActionType


class TestSyntheticDataAndUpload(unittest.TestCase):

    def setUp(self):
        self.retriever, self.erp, _ = build_demo_environment()
        self.orchestrator = APOrchestrator(retriever=self.retriever, erp_connector=self.erp)

    def test_get_scenario_specs(self):
        specs = SyntheticDataGenerator.get_specs()
        self.assertEqual(len(specs), 10)
        codes = [s["code"] for s in specs]
        self.assertIn("SYN-01", codes)
        self.assertIn("SYN-03", codes)
        self.assertIn("SYN-06", codes)

    def test_generate_clean_milestone(self):
        inv = SyntheticDataGenerator.generate_scenario("SYN_CLEAN_MILESTONE", invoice_index=101)
        self.assertEqual(inv.invoice_id, "INV-SYN-101")
        self.assertEqual(inv.total_amount, 45000.0)
        self.assertEqual(len(inv.line_items), 1)

        result = self.orchestrator.process_invoice(inv)
        self.assertEqual(result.overall_status, MatchStatus.PERFECT_MATCH)
        self.assertEqual(result.resolution_action.action_type, ActionType.AUTO_APPROVE)

    def test_generate_rate_overcharge(self):
        inv = SyntheticDataGenerator.generate_scenario("SYN_RATE_OVERCHARGE", invoice_index=103)
        self.assertEqual(inv.line_items[0].unit_price, 195.0)

        result = self.orchestrator.process_invoice(inv)
        self.assertEqual(result.overall_status, MatchStatus.EXCEPTION_RATE_VARIANCE)
        self.assertEqual(result.discrepancy_amount, 1250.0)

    def test_generate_missing_gr(self):
        inv = SyntheticDataGenerator.generate_scenario("SYN_MISSING_GR", invoice_index=104)
        result = self.orchestrator.process_invoice(inv)
        self.assertEqual(result.overall_status, MatchStatus.EXCEPTION_MISSING_GR)
        self.assertEqual(result.resolution_action.action_type, ActionType.REQUEST_INTERNAL_SIGN_OFF)

    def test_generate_batch(self):
        batch = SyntheticDataGenerator.generate_batch(count=5)
        self.assertEqual(len(batch), 5)
        ids = [b.invoice_id for b in batch]
        self.assertEqual(len(set(ids)), 5)

    def test_csv_export_and_import(self):
        batch = SyntheticDataGenerator.generate_batch(count=3)
        csv_str = SyntheticDataGenerator.to_csv(batch)
        self.assertIn("invoice_id,vendor_id", csv_str)

        imported = SyntheticDataGenerator.from_csv(csv_str)
        self.assertEqual(len(imported), 3)
        self.assertEqual(imported[0].invoice_id, batch[0].invoice_id)
        self.assertEqual(imported[0].total_amount, batch[0].total_amount)

    def test_json_export_and_import(self):
        batch = SyntheticDataGenerator.generate_batch(count=3)
        json_str = SyntheticDataGenerator.to_json(batch)
        self.assertIn("INV-SYN-101", json_str)

        imported = SyntheticDataGenerator.from_json(json_str)
        self.assertEqual(len(imported), 3)
        self.assertEqual(imported[0].invoice_id, batch[0].invoice_id)


if __name__ == "__main__":
    unittest.main()
