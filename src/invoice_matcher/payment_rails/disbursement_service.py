"""
Payment Disbursement & Settlement Engine.
Enforces dual-custody approval thresholds, idempotency locks, NACHA/ISO20022 file generation,
and ERP ledger balance reconciliation.
"""

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from .nacha_generator import NACHAGenerator
from .iso20022_builder import ISO20022Builder
from ..database.db_service import APDatabaseService


class PaymentRail(str, Enum):
    ACH = "ACH"
    ISO20022 = "ISO20022"


class PaymentStatus(str, Enum):
    CLEARED = "CLEARED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class DisbursementService:
    """Manages transactional payment disbursements across ACH and ISO 20022 rails."""

    DUAL_CUSTODY_THRESHOLD_USD = 10000.0

    def __init__(self, db: Optional[APDatabaseService] = None):
        self.db = db or APDatabaseService()

    @classmethod
    def compute_idempotency_key(cls, vendor_id: str, invoice_id: str, po_number: str, amount: float) -> str:
        """Generates deterministic SHA-256 idempotency key to prevent double disbursements."""
        raw = f"{vendor_id}:{invoice_id}:{po_number}:{amount:.2f}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def disburse_payment(
        self,
        invoice_id: str,
        vendor_id: str,
        vendor_name: str,
        po_number: str,
        amount: float,
        rail: PaymentRail = PaymentRail.ACH,
        authorized_by: Optional[str] = None,
        force_override: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a payment disbursement with idempotency and dual-custody verification.
        """
        idempotency_key = self.compute_idempotency_key(vendor_id, invoice_id, po_number, amount)

        # 1. Check idempotency: Prevent duplicate disbursement
        existing = self.db.get_disbursement_by_idempotency(idempotency_key)
        if existing and existing["status"] == PaymentStatus.CLEARED.value:
            return {
                "success": True,
                "duplicate_suppressed": True,
                "payment_ref": existing["payment_ref"],
                "status": existing["status"],
                "message": f"Payment already cleared on {existing['disbursed_at']}. Replay suppressed.",
                "disbursement": existing
            }

        # 2. Dual-Custody Policy Check: Threshold >= $10,000
        requires_dual_custody = amount >= self.DUAL_CUSTODY_THRESHOLD_USD
        if requires_dual_custody and not authorized_by and not force_override:
            payment_ref = f"HOLD-{uuid.uuid4().hex[:8].upper()}"
            trace_number = f"12100035{uuid.uuid4().hex[:7]}"
            
            disbursement_data = {
                "payment_ref": payment_ref,
                "invoice_id": invoice_id,
                "vendor_id": vendor_id,
                "vendor_name": vendor_name,
                "po_number": po_number,
                "amount": amount,
                "currency": "USD",
                "rail": rail.value,
                "status": PaymentStatus.PENDING_APPROVAL.value,
                "idempotency_key": idempotency_key,
                "trace_number": trace_number,
                "nacha_payload": None,
                "iso20022_xml": None,
                "dual_custody_required": True,
                "authorized_by": None,
                "disbursed_at": datetime.utcnow().isoformat()
            }
            self.db.record_disbursement(disbursement_data)
            self.db.update_invoice_status(invoice_id, "PENDING_SECOND_APPROVAL")
            self.db.log_audit(
                entity_id=invoice_id,
                event_type="PAYMENT_HOLD_DUAL_CUSTODY",
                agent_name="DisbursementPolicyEngine",
                details=f"Payment of ${amount:,.2f} exceeds threshold (${self.DUAL_CUSTODY_THRESHOLD_USD:,.2f}). Requires second approval."
            )

            return {
                "success": False,
                "pending_approval": True,
                "payment_ref": payment_ref,
                "status": PaymentStatus.PENDING_APPROVAL.value,
                "message": f"Payment of ${amount:,.2f} held for dual-custody secondary authorization.",
                "disbursement": disbursement_data
            }

        # 3. Generate Banking Rails Payloads
        payment_ref = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        trace_number = f"12100035{uuid.uuid4().hex[:7]}"

        nacha_file = NACHAGenerator.generate_single_payment_file(
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            amount=amount,
            invoice_id=invoice_id,
            po_number=po_number
        )

        iso20022_xml = ISO20022Builder.generate_pain001_xml(
            invoice_id=invoice_id,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            amount=amount,
            po_number=po_number
        )

        disbursement_data = {
            "payment_ref": payment_ref,
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "po_number": po_number,
            "amount": amount,
            "currency": "USD",
            "rail": rail.value,
            "status": PaymentStatus.CLEARED.value,
            "idempotency_key": idempotency_key,
            "trace_number": trace_number,
            "nacha_payload": nacha_file,
            "iso20022_xml": iso20022_xml,
            "dual_custody_required": requires_dual_custody,
            "authorized_by": authorized_by or ("SYSTEM_AUTO" if not requires_dual_custody else "OVERRIDE_ADMIN"),
            "disbursed_at": datetime.utcnow().isoformat()
        }

        # 4. Record to Persistent Database & Ledger
        self.db.record_disbursement(disbursement_data)
        self.db.update_invoice_status(invoice_id, "PAID")
        
        # Deduct remaining balance from PO in DB (assume line 1 for single-line scenario or iterate)
        po = self.db.get_po(po_number)
        if po and po.get("lines"):
            target_line = po["lines"][0]
            self.db.deduct_po_balance(
                po_number=po_number,
                line_num=target_line["line_num"],
                invoiced_qty=target_line["committed_qty"],
                invoiced_amount=amount
            )

        self.db.log_audit(
            entity_id=invoice_id,
            event_type="DISBURSEMENT_CLEARED",
            agent_name="DisbursementService",
            details=f"Disbursed ${amount:,.2f} via {rail.value}. Ref: {payment_ref}. Trace: {trace_number}."
        )

        return {
            "success": True,
            "payment_ref": payment_ref,
            "trace_number": trace_number,
            "rail": rail.value,
            "status": PaymentStatus.CLEARED.value,
            "amount": amount,
            "nacha_payload": nacha_file,
            "iso20022_xml": iso20022_xml,
            "message": f"Successfully disbursed ${amount:,.2f} to {vendor_name} via {rail.value}.",
            "disbursement": disbursement_data
        }

    def authorize_high_value_payment(self, invoice_id: str, approver_name: str) -> Dict[str, Any]:
        """Secondary authorization for payments exceeding dual-custody threshold."""
        inv = self.db.get_invoice(invoice_id)
        if not inv:
            return {"success": False, "message": f"Invoice {invoice_id} not found."}

        return self.disburse_payment(
            invoice_id=inv["invoice_id"],
            vendor_id=inv["vendor_id"],
            vendor_name=inv["vendor_name"],
            po_number=inv["po_number"],
            amount=inv["total_amount"],
            authorized_by=approver_name,
            force_override=True
        )
