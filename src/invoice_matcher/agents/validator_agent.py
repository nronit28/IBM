"""
Contract Validator Agent: Uses RAG to validate invoice line items against SOWs, rate cards, and clauses.
"""

from typing import Dict, List, Any, Optional
from ..models.invoice import Invoice, InvoiceLineItem
from ..models.matching import MatchStatus
from ..rag.contract_retriever import ContractRetriever


class ContractValidatorAgent:
    """Agent that performs semantic contract validation using RAG."""

    def __init__(self, retriever: ContractRetriever):
        self.retriever = retriever

    def validate_invoice(self, invoice: Invoice) -> Dict[str, Any]:
        """
        Validates invoice against vendor contracts and SOWs.
        Returns validation details per line item and relevant clause citations.
        """
        logs = [f"ContractValidatorAgent: Validating invoice {invoice.invoice_id} against contract base for vendor {invoice.vendor_id}."]
        line_validations: Dict[str, Dict[str, Any]] = {}
        contract_citations: List[str] = []

        # Find vendor contract general clauses
        general_clauses = self.retriever.search_clauses(
            query="invoicing payment terms discount tax tolerance",
            vendor_id=invoice.vendor_id,
            top_k=2
        )
        for chunk, score in general_clauses:
            contract_citations.append(f"{chunk.section} ({chunk.title}): \"{chunk.content}\"")

        for item in invoice.line_items:
            item_val: Dict[str, Any] = {
                "matched_role_or_milestone": "Unmatched",
                "max_allowable_rate": None,
                "rate_variance": 0.0,
                "status": MatchStatus.PERFECT_MATCH,
                "details": "",
                "citations": []
            }

            # 1. Milestone Billing Validation (only if not an hourly rate item)
            if item.milestone_code and item.unit.upper() not in ("HOURS", "HRS", "HOUR"):
                ms_match = self.retriever.match_milestone(item.milestone_code, invoice.vendor_id)
                if ms_match:
                    ms, score = ms_match
                    item_val["matched_role_or_milestone"] = f"{ms.milestone_code} - {ms.title}"
                    item_val["max_allowable_rate"] = ms.contract_amount
                    if item.total_amount > ms.contract_amount:
                        item_val["status"] = MatchStatus.EXCEPTION_RATE_VARIANCE
                        item_val["rate_variance"] = item.total_amount - ms.contract_amount
                        item_val["details"] = (
                            f"Invoiced amount ${item.total_amount:,.2f} exceeds contracted milestone payout "
                            f"of ${ms.contract_amount:,.2f} by ${item_val['rate_variance']:,.2f}."
                        )
                    else:
                        item_val["details"] = f"Milestone matched SOW with confidence {score:.2f}."
                    
                    citation = f"Milestone Schedule ({ms.milestone_code}): Deliverables: {ms.deliverables}. Amount: ${ms.contract_amount:,.2f}"
                    item_val["citations"].append(citation)
                    logs.append(f"ContractValidatorAgent: Line {item.item_id} matched milestone {ms.milestone_code}.")
                else:
                    item_val["status"] = MatchStatus.EXCEPTION_ROLE_MISMATCH
                    item_val["details"] = f"Milestone {item.milestone_code} not found in vendor SOW."
                    logs.append(f"ContractValidatorAgent: Line {item.item_id} milestone {item.milestone_code} uncontracted.")

            # 2. Time & Materials Role Validation
            elif item.role_title or item.description:
                query_role = item.role_title or item.description
                rc_match = self.retriever.match_rate_card_role(query_role, invoice.vendor_id)

                if rc_match:
                    rc, score, explanation = rc_match
                    item_val["matched_role_or_milestone"] = rc.role_title
                    item_val["max_allowable_rate"] = rc.max_hourly_rate
                    item_val["details"] = explanation

                    citation = f"Schedule A Rate Card: '{rc.role_title}' maximum allowable rate is ${rc.max_hourly_rate}/hr."
                    item_val["citations"].append(citation)

                    # Check rate variance
                    if item.unit_price > rc.max_hourly_rate:
                        excess_per_unit = round(item.unit_price - rc.max_hourly_rate, 2)
                        total_excess = round(excess_per_unit * item.quantity, 2)
                        item_val["status"] = MatchStatus.EXCEPTION_RATE_VARIANCE
                        item_val["rate_variance"] = total_excess
                        item_val["details"] += (
                            f" RATE VARIANCE: Invoiced rate ${item.unit_price}/hr exceeds contracted maximum "
                            f"${rc.max_hourly_rate}/hr by ${excess_per_unit}/hr (Total excess: ${total_excess:,.2f})."
                        )
                        logs.append(f"ContractValidatorAgent: Rate variance flagged on line {item.item_id}: +${total_excess:,.2f}.")
                    else:
                        logs.append(f"ContractValidatorAgent: Line {item.item_id} rate ${item.unit_price}/hr within SOW cap (${rc.max_hourly_rate}/hr).")

                else:
                    # Look up if this might be an unapproved travel/expense line
                    clause_hits = self.retriever.search_clauses(query_role, vendor_id=invoice.vendor_id, top_k=1)
                    if clause_hits:
                        chunk, c_score = clause_hits[0]
                        item_val["matched_role_or_milestone"] = chunk.title
                        item_val["citations"].append(f"{chunk.section}: {chunk.content}")
                        item_val["details"] = f"Matched to clause: {chunk.title}"
                    else:
                        item_val["status"] = MatchStatus.EXCEPTION_ROLE_MISMATCH
                        item_val["details"] = f"Role or service '{query_role}' does not match any approved SOW rate card."
                        logs.append(f"ContractValidatorAgent: Unmatched role on line {item.item_id}: '{query_role}'.")

            line_validations[item.item_id] = item_val

        return {
            "line_validations": line_validations,
            "contract_citations": contract_citations,
            "logs": logs
        }
