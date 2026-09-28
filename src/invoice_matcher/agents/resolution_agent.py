"""
Resolution Agent: Evaluates tolerances, triages exceptions, and autonomously drafts resolutions.
"""

from typing import Dict, List, Any
from ..models.invoice import Invoice
from ..models.matching import (
    MatchStatus,
    ActionType,
    LineItemMatch,
    ResolutionAction,
    MatchingResult,
)


class ResolutionAgent:
    """Agent that determines final matching outcome, applies tolerances, and drafts communications."""

    DEFAULT_TOLERANCE_USD = 25.0

    def resolve(
        self,
        invoice: Invoice,
        contract_validation: Dict[str, Any],
        erp_validation: Dict[str, Any]
    ) -> MatchingResult:
        """
        Combines contract and ERP findings to determine action and generate audit-ready output.
        """
        logs = ["ResolutionAgent: Evaluating composite 3-way matching findings."]
        line_matches: List[LineItemMatch] = []
        overall_status = MatchStatus.PERFECT_MATCH
        total_rate_variance = 0.0
        discrepancy_descriptions: List[str] = []
        all_citations: List[str] = list(contract_validation.get("contract_citations", []))

        line_val = contract_validation.get("line_validations", {})
        line_erp = erp_validation.get("line_erp_status", {})

        for item in invoice.line_items:
            c_val = line_val.get(item.item_id, {})
            e_val = line_erp.get(item.item_id, {})

            c_status = c_val.get("status", MatchStatus.PERFECT_MATCH)
            e_status = e_val.get("status", MatchStatus.PERFECT_MATCH)
            rate_var = c_val.get("rate_variance", 0.0)
            total_rate_variance += rate_var

            # Determine dominant line status
            if c_status == MatchStatus.EXCEPTION_RATE_VARIANCE:
                line_status = MatchStatus.EXCEPTION_RATE_VARIANCE
                discrepancy_descriptions.append(f"Line {item.item_id}: {c_val.get('details', '')}")
            elif c_status == MatchStatus.EXCEPTION_ROLE_MISMATCH:
                line_status = MatchStatus.EXCEPTION_ROLE_MISMATCH
                discrepancy_descriptions.append(f"Line {item.item_id}: {c_val.get('details', '')}")
            elif e_status == MatchStatus.EXCEPTION_MISSING_GR:
                line_status = MatchStatus.EXCEPTION_MISSING_GR
                discrepancy_descriptions.append(f"Line {item.item_id}: {e_val.get('erp_details', '')}")
            elif e_status == MatchStatus.EXCEPTION_PO_BALANCE_EXCEEDED:
                line_status = MatchStatus.EXCEPTION_PO_BALANCE_EXCEEDED
                discrepancy_descriptions.append(f"Line {item.item_id}: {e_val.get('erp_details', '')}")
            elif e_status != MatchStatus.PERFECT_MATCH:
                line_status = e_status
            else:
                line_status = MatchStatus.PERFECT_MATCH

            # Combine details
            combined_details = f"{c_val.get('details', '')} | {e_val.get('erp_details', '')}".strip(" |")
            line_citations = c_val.get("citations", [])
            all_citations.extend(line_citations)

            match_entry = LineItemMatch(
                invoice_item_id=item.item_id,
                po_line_num=e_val.get("po_line_num"),
                matched_role_or_milestone=c_val.get("matched_role_or_milestone", "N/A"),
                invoiced_qty=item.quantity,
                po_remaining_qty=e_val.get("po_remaining_qty"),
                invoiced_rate=item.unit_price,
                contract_max_rate=c_val.get("max_allowable_rate"),
                rate_variance=rate_var,
                gr_approved=e_val.get("gr_approved", False),
                gr_receipt_id=e_val.get("gr_receipt_id"),
                status=line_status,
                details=combined_details,
                clause_citations=line_citations
            )
            line_matches.append(match_entry)

        # Evaluate tax variance
        computed_subtotal = sum(i.total_amount for i in invoice.line_items)
        expected_total = computed_subtotal + invoice.tax_amount
        tax_or_rounding_diff = round(abs(invoice.total_amount - expected_total), 2)

        # Check dominant overall status
        status_priority = [
            MatchStatus.EXCEPTION_RATE_VARIANCE,
            MatchStatus.EXCEPTION_ROLE_MISMATCH,
            MatchStatus.EXCEPTION_MISSING_GR,
            MatchStatus.EXCEPTION_PO_BALANCE_EXCEEDED,
            MatchStatus.MANUAL_REVIEW_REQUIRED,
        ]

        found_exceptions = [m.status for m in line_matches if m.status != MatchStatus.PERFECT_MATCH]
        if found_exceptions:
            for p in status_priority:
                if p in found_exceptions:
                    overall_status = p
                    break
        elif tax_or_rounding_diff > 0:
            if tax_or_rounding_diff <= self.DEFAULT_TOLERANCE_USD:
                overall_status = MatchStatus.EXCEPTION_TAX_VARIANCE
            else:
                overall_status = MatchStatus.MANUAL_REVIEW_REQUIRED

        # Calculate confidence score
        if overall_status == MatchStatus.PERFECT_MATCH:
            confidence = 0.99
        elif overall_status in (MatchStatus.EXCEPTION_RATE_VARIANCE, MatchStatus.EXCEPTION_TAX_VARIANCE):
            confidence = 0.95
        elif overall_status == MatchStatus.EXCEPTION_MISSING_GR:
            confidence = 0.92
        else:
            confidence = 0.82

        # Generate Action and Communication Draft
        resolution_action = self._synthesize_action(
            invoice=invoice,
            status=overall_status,
            line_matches=line_matches,
            rate_variance=total_rate_variance,
            tax_diff=tax_or_rounding_diff,
            citations=all_citations,
            po_buyer=erp_validation.get("po_buyer", "IBM Procurement")
        )

        audit_trail = [
            f"Step 1: Normalizer parsed {len(invoice.line_items)} line items.",
            f"Step 2: RAG Contract Validator executed against vendor {invoice.vendor_id}.",
            f"Step 3: ERP SAP Connector evaluated PO {invoice.po_number} and GR receipts.",
            f"Step 4: Resolution Agent determined status: {overall_status.value} (Confidence: {confidence * 100:.1f}%).",
            f"Step 5: Generated Resolution Action: {resolution_action.action_type.value} -> '{resolution_action.title}'."
        ]

        return MatchingResult(
            invoice_id=invoice.invoice_id,
            vendor_id=invoice.vendor_id,
            po_number=invoice.po_number,
            overall_status=overall_status,
            confidence_score=confidence,
            total_invoiced_amount=invoice.total_amount,
            allowable_amount=max(0.0, invoice.total_amount - total_rate_variance),
            discrepancy_amount=total_rate_variance if total_rate_variance > 0 else tax_or_rounding_diff,
            line_matches=line_matches,
            resolution_action=resolution_action,
            audit_trail=audit_trail,
            metadata={"tax_diff": tax_or_rounding_diff}
        )

    def _synthesize_action(
        self,
        invoice: Invoice,
        status: MatchStatus,
        line_matches: List[LineItemMatch],
        rate_variance: float,
        tax_diff: float,
        citations: List[str],
        po_buyer: str
    ) -> ResolutionAction:
        """Constructs the specific action, email draft, or clearance memo."""

        if status == MatchStatus.PERFECT_MATCH:
            return ResolutionAction(
                action_type=ActionType.AUTO_APPROVE,
                title="Automated 3-Way Match Passed - Schedule Payment",
                recipient="SAP AP Ledger / Automated Disbursement",
                summary="Invoice completely matches contracted SOW terms, PO line allocation, and approved SAP Goods/Services Receipts.",
                generated_communication=(
                    f"SYSTEM POSTING MEMORANDUM\n"
                    f"Invoice: {invoice.invoice_id} | Vendor: {invoice.vendor_name} ({invoice.vendor_id})\n"
                    f"PO: {invoice.po_number} | Amount: ${invoice.total_amount:,.2f} {invoice.currency}\n"
                    f"Status: VERIFIED 3-WAY MATCH. Ready for automated payment run on {invoice.due_date}."
                ),
                citations=citations,
                tolerance_applied=False,
                estimated_impact_usd=0.0
            )

        if status == MatchStatus.EXCEPTION_TAX_VARIANCE:
            return ResolutionAction(
                action_type=ActionType.AUTO_APPROVE,
                title="Auto-Approve Under Tolerance Policy (Tax/Rounding Variance)",
                recipient="SAP AP Ledger & Financial Controller Audit Log",
                summary=f"Discrepancy of ${tax_diff:.2f} is within automated tolerance threshold (${self.DEFAULT_TOLERANCE_USD:.2f}).",
                generated_communication=(
                    f"AUTOMATED TOLERANCE CLEARANCE MEMO\n"
                    f"Invoice: {invoice.invoice_id} | Vendor: {invoice.vendor_name}\n"
                    f"PO: {invoice.po_number} | Billed Total: ${invoice.total_amount:,.2f}\n"
                    f"Variance: ${tax_diff:.2f} (Tax/Rounding adjustment applied pursuant to IBM AP Policy §3.1)."
                ),
                citations=citations,
                tolerance_applied=True,
                estimated_impact_usd=tax_diff
            )

        if status == MatchStatus.EXCEPTION_RATE_VARIANCE:
            # Build dispute email
            variance_lines_text = []
            for m in line_matches:
                if m.status == MatchStatus.EXCEPTION_RATE_VARIANCE:
                    variance_lines_text.append(
                        f" - Line {m.invoice_item_id} ({m.matched_role_or_milestone}): "
                        f"Invoiced Rate = ${m.invoiced_rate:.2f}/hr | Contract SOW Cap = ${m.contract_max_rate:.2f}/hr | "
                        f"Overcharge = ${m.rate_variance:,.2f}"
                    )
            lines_str = "\n".join(variance_lines_text)

            email_body = (
                f"Subject: Formal Discrepancy Notice: Invoice {invoice.invoice_id} (PO {invoice.po_number})\n\n"
                f"Dear {invoice.vendor_name} Accounts Receivable Team,\n\n"
                f"IBM Accounts Payable has completed automated 3-way contract validation for invoice {invoice.invoice_id}. "
                f"During review against governing agreement (PO {invoice.po_number} / SOW Rate Card), "
                f"the following rate discrepancy was identified:\n\n"
                f"{lines_str}\n\n"
                f"Total Discrepancy: ${rate_variance:,.2f} {invoice.currency}.\n\n"
                f"Pursuant to Schedule A (Rate Card) of our Master Agreement, billable rates are capped at the contracted maximum. "
                f"Please issue a revised invoice for the allowable amount of ${invoice.total_amount - rate_variance:,.2f} "
                f"or provide a credit memo for ${rate_variance:,.2f}.\n\n"
                f"Sincerely,\n"
                f"IBM Global Accounts Payable Automation"
            )

            return ResolutionAction(
                action_type=ActionType.DRAFT_VENDOR_INQUIRY,
                title="Draft Vendor Rate Discrepancy Notice",
                recipient=f"{invoice.vendor_name} Accounts Receivable",
                summary=f"Invoiced rate exceeds SOW maximum by ${rate_variance:,.2f}. Vendor inquiry drafted citing SOW Rate Card.",
                generated_communication=email_body,
                citations=citations,
                tolerance_applied=False,
                estimated_impact_usd=rate_variance
            )

        if status == MatchStatus.EXCEPTION_MISSING_GR:
            email_body = (
                f"Subject: ACTION REQUIRED: Delivery Receipt Missing for Vendor Invoice {invoice.invoice_id}\n\n"
                f"Hello {po_buyer},\n\n"
                f"Vendor {invoice.vendor_name} has submitted invoice {invoice.invoice_id} for ${invoice.total_amount:,.2f} "
                f"against PO {invoice.po_number}.\n\n"
                f"Our automated 3-way matching system verified that the billed line items comply with contracted SOW rate cards, "
                f"but NO Goods/Services Receipt (GR/SR - SES) has been recorded in SAP S/4HANA by the project team.\n\n"
                f"Please confirm delivery in SAP or reply to this notice to release payment.\n\n"
                f"IBM AP Operations"
            )

            return ResolutionAction(
                action_type=ActionType.REQUEST_INTERNAL_SIGN_OFF,
                title="Request Internal Delivery Sign-Off from Project Manager",
                recipient=po_buyer,
                summary="Contract terms valid, but awaiting Goods/Services Receipt in SAP from IBM Project Manager.",
                generated_communication=email_body,
                citations=citations,
                tolerance_applied=False,
                estimated_impact_usd=invoice.total_amount
            )

        # Default Escalation
        return ResolutionAction(
            action_type=ActionType.ESCALATE_TO_HUMAN,
            title="Escalate Complex Exception to Senior AP Specialist",
            recipient="IBM Senior AP Exceptions Team",
            summary=f"Unresolved discrepancy or uncontracted line item in invoice {invoice.invoice_id}.",
            generated_communication=(
                f"EXCEPTION DOSSIER FOR HUMAN AP REVIEW\n"
                f"Invoice: {invoice.invoice_id} | Amount: ${invoice.total_amount:,.2f}\n"
                f"Vendor: {invoice.vendor_name} | PO: {invoice.po_number}\n"
                f"Reasons: Multiple or high-variance exceptions detected."
            ),
            citations=citations,
            tolerance_applied=False,
            estimated_impact_usd=invoice.total_amount
        )
