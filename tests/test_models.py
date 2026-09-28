"""
Unit tests for data models and schema validation.
"""

import unittest
from datetime import date
from src.invoice_matcher.models.invoice import Invoice, InvoiceLineItem
from src.invoice_matcher.models.contract import Contract, RateCardItem, MilestoneTerm, ContractClause
from src.invoice_matcher.models.erp import PurchaseOrder, POLineItem, GoodsServicesReceipt
from src.invoice_matcher.models.matching import MatchStatus, ActionType


class TestModels(unittest.TestCase):

    def test_invoice_line_item(self):
        item = InvoiceLineItem(
            item_id="L1",
            description="Consulting Services",
            quantity=10.0,
            unit_price=150.0,
            total_amount=1500.0
        )
        self.assertEqual(item.item_id, "L1")
        self.assertEqual(item.total_amount, 1500.0)

    def test_po_line_item_remaining(self):
        po_line = POLineItem(
            line_num=10,
            description="Cloud Migration",
            ordered_qty=100.0,
            unit_price=100.0,
            total_committed=10000.0,
            invoiced_qty=40.0,
            invoiced_amount=4000.0
        )
        self.assertEqual(po_line.remaining_qty, 60.0)
        self.assertEqual(po_line.remaining_amount, 6000.0)


if __name__ == "__main__":
    unittest.main()
