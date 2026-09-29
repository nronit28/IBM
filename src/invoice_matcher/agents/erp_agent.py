"""
ERP Action Agent: Interfaces with SAP S/4HANA connector for PO balances and GR/SR sign-offs.
"""

from typing import Dict, List, Any, Optional
from ..models.invoice import Invoice
from ..models.matching import MatchStatus
from ..erp_service.sap_mock import SAPConnector


class ERPAgent:
    """Agent that performs ERP checks and 3-way matching against PO and Goods/Services Receipts."""

    def __init__(self, erp_connector: SAPConnector):
        self.erp = erp_connector

    def check_erp_alignment(
        self,
        invoice: Invoice,
        resolved_roles: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Validates PO balance and confirms Goods/Services Receipt (GR/SR) status in SAP.
        Uses RAG-resolved role when matching against ERP PO lines.
        """
        logs = [f"ERPAgent: Querying SAP S/4HANA for Purchase Order {invoice.po_number}."]
        po = self.erp.get_purchase_order(invoice.po_number)

        if not po:
            return {
                "po_found": False,
                "error": f"Purchase Order {invoice.po_number} does not exist in ERP.",
                "line_erp_status": {},
                "logs": logs + [f"ERPAgent: CRITICAL: PO {invoice.po_number} not found."]
            }

        logs.append(f"ERPAgent: Found PO {po.po_number} (Buyer: {po.buyer_name}, Total: ${po.total_value:,.2f}, Status: {po.status}).")

        line_erp_status: Dict[str, Dict[str, Any]] = {}

        for item in invoice.line_items:
            # Use RAG-resolved canonical role if available, falling back to item role
            effective_role = (resolved_roles.get(item.item_id) if resolved_roles else None) or item.role_title

            po_match = self.erp.match_po_line(
                po_number=invoice.po_number,
                item_desc=item.description,
                milestone_code=item.milestone_code,
                role_title=effective_role
            )

            status_entry: Dict[str, Any] = {
                "po_line_num": None,
                "po_remaining_qty": 0.0,
                "po_remaining_amount": 0.0,
                "gr_found": False,
                "gr_receipt_id": None,
                "gr_approved": False,
                "status": MatchStatus.PERFECT_MATCH,
                "erp_details": ""
            }

            if not po_match:
                status_entry["status"] = MatchStatus.MANUAL_REVIEW_REQUIRED
                status_entry["erp_details"] = f"No matching line found on PO {invoice.po_number}."
                logs.append(f"ERPAgent: Line {item.item_id} has no matching PO line.")
                line_erp_status[item.item_id] = status_entry
                continue

            po_line, score = po_match
            status_entry["po_line_num"] = po_line.line_num
            status_entry["po_remaining_qty"] = po_line.remaining_qty
            status_entry["po_remaining_amount"] = po_line.remaining_amount

            # If this invoice was already cleared in ERP, consider its own cleared amount available
            already_cleared = self.erp.posted_invoices.get(invoice.invoice_id)
            effective_remaining = po_line.remaining_amount
            if already_cleared and already_cleared.get("po_number") == invoice.po_number and already_cleared.get("line_num") == po_line.line_num:
                effective_remaining += already_cleared.get("amount", 0.0)

            # 1. Check PO remaining funds
            if item.total_amount > effective_remaining:
                status_entry["status"] = MatchStatus.EXCEPTION_PO_BALANCE_EXCEEDED
                status_entry["erp_details"] = (
                    f"Line amount ${item.total_amount:,.2f} exceeds remaining PO balance of "
                    f"${effective_remaining:,.2f} (Line {po_line.line_num})."
                )
                logs.append(f"ERPAgent: Line {item.item_id} exceeds PO balance on line {po_line.line_num}.")
                line_erp_status[item.item_id] = status_entry
                continue

            # 2. Check Goods/Services Receipt (GR/SR)
            receipts = self.erp.get_receipts(
                po_number=invoice.po_number,
                po_line_num=po_line.line_num,
                milestone_code=item.milestone_code
            )

            approved_receipt = next((r for r in receipts if r.approval_status == "APPROVED"), None)

            if approved_receipt:
                status_entry["gr_found"] = True
                status_entry["gr_receipt_id"] = approved_receipt.receipt_id
                status_entry["gr_approved"] = True
                status_entry["erp_details"] = (
                    f"3-Way Match verified against SAP Goods Receipt {approved_receipt.receipt_id} "
                    f"(Signed off by {approved_receipt.signed_off_by} on {approved_receipt.receipt_date})."
                )
                logs.append(f"ERPAgent: 3-Way Match confirmed for line {item.item_id} (GR: {approved_receipt.receipt_id}).")
            else:
                status_entry["status"] = MatchStatus.EXCEPTION_MISSING_GR
                status_entry["erp_details"] = (
                    f"MISSING GOODS/SERVICES RECEIPT: Work was invoiced but no approved receipt record exists "
                    f"in SAP for PO {invoice.po_number} Line {po_line.line_num}."
                )
                logs.append(f"ERPAgent: Exception on line {item.item_id}: Missing Goods/Services Receipt in SAP.")

            line_erp_status[item.item_id] = status_entry

        return {
            "po_found": True,
            "po_buyer": po.buyer_name,
            "po_status": po.status,
            "line_erp_status": line_erp_status,
            "logs": logs
        }
