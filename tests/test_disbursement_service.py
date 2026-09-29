"""
Unit tests for Disbursement Service: Idempotency, Dual-Custody, and Ledger updates.
"""

import unittest
import tempfile
from pathlib import Path
from src.invoice_matcher.database.db_service import APDatabaseService
from src.invoice_matcher.payment_rails.disbursement_service import (
    DisbursementService,
    PaymentRail,
    PaymentStatus
)


class TestDisbursementService(unittest.TestCase):

    def test_disbursement_under_threshold(self):
        """Payments under $10,000 should clear automatically without dual custody."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = APDatabaseService(db_path=Path(tmpdir) / "test.db")
            service = DisbursementService(db=db)

            db.upsert_po({
                "po_number": "PO-TEST-1",
                "vendor_id": "VEND-1",
                "vendor_name": "Test Vendor",
                "total_committed": 20000.0,
                "remaining_balance": 20000.0,
                "lines": [{
                    "line_num": 1,
                    "description": "Services",
                    "hourly_rate": 100.0,
                    "committed_qty": 50.0
                }]
            })
            db.upsert_invoice({
                "invoice_id": "INV-SMALL-1",
                "vendor_id": "VEND-1",
                "vendor_name": "Test Vendor",
                "po_number": "PO-TEST-1",
                "total_amount": 5000.0
            })

            result = service.disburse_payment(
                invoice_id="INV-SMALL-1",
                vendor_id="VEND-1",
                vendor_name="Test Vendor",
                po_number="PO-TEST-1",
                amount=5000.0,
                rail=PaymentRail.ACH
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["status"], PaymentStatus.CLEARED.value)
            self.assertEqual(result["rail"], "ACH")
            self.assertTrue(result["payment_ref"].startswith("PAY-"))

            # PO balance should be deducted
            po = db.get_po("PO-TEST-1")
            self.assertEqual(po["remaining_balance"], 15000.0)

    def test_disbursement_over_threshold_dual_custody(self):
        """Payments >= $10,000 require secondary approval before clearing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = APDatabaseService(db_path=Path(tmpdir) / "test.db")
            service = DisbursementService(db=db)

            db.upsert_po({
                "po_number": "PO-TEST-2",
                "vendor_id": "VEND-2",
                "vendor_name": "Big Vendor",
                "total_committed": 100000.0,
                "remaining_balance": 100000.0,
                "lines": [{"line_num": 1, "description": "Consulting", "hourly_rate": 200.0, "committed_qty": 200.0}]
            })
            db.upsert_invoice({
                "invoice_id": "INV-LARGE-1",
                "vendor_id": "VEND-2",
                "vendor_name": "Big Vendor",
                "po_number": "PO-TEST-2",
                "total_amount": 45000.0
            })

            # Attempt disbursement without authorized_by
            hold_result = service.disburse_payment(
                invoice_id="INV-LARGE-1",
                vendor_id="VEND-2",
                vendor_name="Big Vendor",
                po_number="PO-TEST-2",
                amount=45000.0,
                rail=PaymentRail.ISO20022
            )

            self.assertFalse(hold_result["success"])
            self.assertEqual(hold_result["status"], PaymentStatus.PENDING_APPROVAL.value)
            self.assertTrue(hold_result["disbursement"]["dual_custody_required"])

            # Now approve with secondary signer
            auth_result = service.authorize_high_value_payment(
                invoice_id="INV-LARGE-1",
                approver_name="Maria Santos (VP Global Treasury)"
            )

            self.assertTrue(auth_result["success"])
            self.assertEqual(auth_result["status"], PaymentStatus.CLEARED.value)

            # Check idempotency: second identical attempt must be suppressed
            dup_result = service.disburse_payment(
                invoice_id="INV-LARGE-1",
                vendor_id="VEND-2",
                vendor_name="Big Vendor",
                po_number="PO-TEST-2",
                amount=45000.0
            )
            self.assertTrue(dup_result["duplicate_suppressed"])


if __name__ == "__main__":
    unittest.main()
