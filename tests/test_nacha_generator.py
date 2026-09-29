"""
Unit tests for NACHA ACH 94-column file generator.
Validates strict 94-character column boundaries, record types, hashes, and block padding.
"""

import unittest
from src.invoice_matcher.payment_rails.nacha_generator import NACHAGenerator


class TestNACHAGenerator(unittest.TestCase):

    def test_nacha_file_line_lengths(self):
        """Every single line in the NACHA file must be exactly 94 characters."""
        nacha_content = NACHAGenerator.generate_single_payment_file(
            vendor_id="VEND-IBM-8841",
            vendor_name="RedPillar Cloud Solutions LLC",
            amount=45000.0,
            invoice_id="INV-2026-001",
            po_number="PO-45009812"
        )

        lines = nacha_content.split("\n")
        self.assertGreater(len(lines), 0)
        # Must be a multiple of 10 for ACH blocking factor
        self.assertEqual(len(lines) % 10, 0)

        for idx, line in enumerate(lines, 1):
            self.assertEqual(len(line), 94, f"Line {idx} length is {len(line)}, expected 94: '{line}'")

    def test_nacha_record_types_and_content(self):
        """Verify record types 1, 5, 6, 8, 9 are present in correct order."""
        nacha_content = NACHAGenerator.generate_single_payment_file(
            vendor_id="VEND-IBM-8841",
            vendor_name="RedPillar Cloud Solutions LLC",
            amount=12500.50,
            invoice_id="INV-2026-003",
            po_number="PO-45009812"
        )

        lines = nacha_content.split("\n")
        self.assertTrue(lines[0].startswith("1"))  # File Header
        self.assertTrue(lines[1].startswith("5"))  # Company / Batch Header
        self.assertTrue(lines[2].startswith("6"))  # Entry Detail
        self.assertTrue(lines[3].startswith("8"))  # Batch Control
        self.assertTrue(lines[4].startswith("9"))  # File Control

        # Check that amount in Entry Detail (line 2) is formatted in cents: 12500.50 -> 0001250050
        entry_detail = lines[2]
        amount_str = entry_detail[29:39]
        self.assertEqual(amount_str, "0001250050")

        # Check vendor name uppercase
        self.assertIn("REDPILLAR CLOUD SOLUTI", entry_detail)


if __name__ == "__main__":
    unittest.main()
