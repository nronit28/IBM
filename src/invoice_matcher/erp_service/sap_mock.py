"""
SAP S/4HANA ERP Mock Service for 3-Way Matching (PO, GR/SR, and Invoice Clearing).
"""

from typing import Dict, List, Optional, Tuple
from ..models.erp import PurchaseOrder, POLineItem, GoodsServicesReceipt
from rapidfuzz import fuzz


class SAPConnector:
    """Simulates SAP S/4HANA Procurement & AP Ledger APIs."""

    def __init__(self):
        self.purchase_orders: Dict[str, PurchaseOrder] = {}
        self.receipts_by_po: Dict[str, List[GoodsServicesReceipt]] = {}
        self.posted_invoices: Dict[str, Dict] = {}

    def add_purchase_order(self, po: PurchaseOrder) -> None:
        """Register a Purchase Order in the ERP."""
        self.purchase_orders[po.po_number] = po

    def add_receipt(self, receipt: GoodsServicesReceipt) -> None:
        """Register an approved Goods/Services Receipt (GR/SR - MIGO / SES in SAP)."""
        if receipt.po_number not in self.receipts_by_po:
            self.receipts_by_po[receipt.po_number] = []
        self.receipts_by_po[receipt.po_number].append(receipt)

    def get_purchase_order(self, po_number: str) -> Optional[PurchaseOrder]:
        """Fetch PO by ID."""
        return self.purchase_orders.get(po_number)

    def get_receipts(
        self,
        po_number: str,
        po_line_num: Optional[int] = None,
        milestone_code: Optional[str] = None
    ) -> List[GoodsServicesReceipt]:
        """Find approved receipts for a PO line or milestone."""
        receipts = self.receipts_by_po.get(po_number, [])
        filtered = []
        for r in receipts:
            if po_line_num is not None and r.po_line_num != po_line_num:
                continue
            if milestone_code is not None and r.milestone_code != milestone_code:
                continue
            filtered.append(r)
        return filtered

    def match_po_line(
        self,
        po_number: str,
        item_desc: str,
        milestone_code: Optional[str] = None,
        role_title: Optional[str] = None
    ) -> Optional[Tuple[POLineItem, float]]:
        """
        Find the corresponding PO line item using milestone code or description similarity.
        """
        po = self.get_purchase_order(po_number)
        if not po:
            return None

        # 1. Exact milestone code match
        if milestone_code:
            for line in po.line_items:
                if line.milestone_code and line.milestone_code.upper() == milestone_code.upper():
                    return line, 1.0

        # 2. Exact role title match
        if role_title:
            for line in po.line_items:
                if line.role_title and line.role_title.lower() == role_title.lower():
                    return line, 1.0

        # 3. Fuzzy search across line descriptions
        best_line = None
        best_score = 0.0
        for line in po.line_items:
            score = fuzz.token_set_ratio(item_desc.lower(), line.description.lower()) / 100.0
            if score > best_score:
                best_score = score
                best_line = line

        if best_line and best_score >= 0.65:
            return best_line, best_score
        return None

    def post_invoice_clearing(
        self,
        invoice_id: str,
        po_number: str,
        line_num: int,
        invoiced_qty: float,
        invoiced_amount: float
    ) -> bool:
        """
        Post invoice to AP ledger and deduct remaining balance from the PO line.
        """
        if invoice_id in self.posted_invoices:
            return True

        po = self.get_purchase_order(po_number)
        if not po:
            return False

        target_line = next((l for l in po.line_items if l.line_num == line_num), None)
        if not target_line:
            return False

        target_line.invoiced_qty += invoiced_qty
        target_line.invoiced_amount += invoiced_amount
        self.posted_invoices[invoice_id] = {
            "invoice_id": invoice_id,
            "po_number": po_number,
            "line_num": line_num,
            "amount": invoiced_amount,
            "cleared_at_erp": True
        }
        return True
