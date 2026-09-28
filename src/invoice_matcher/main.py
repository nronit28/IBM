"""
Main CLI entrypoint for Autonomous Invoice Exception Handling & 3-Way Matching.
"""

import sys
import argparse
from typing import List
from .demo_data.dataset import build_demo_environment
from .agents.supervisor import APOrchestrator
from .models.matching import MatchingResult


def format_matching_result(result: MatchingResult) -> str:
    """Pretty prints the 3-way matching outcome and generated action."""
    action = result.resolution_action
    sep = "=" * 80
    subsep = "-" * 80

    output = []
    output.append(sep)
    output.append(f"  IBM ACCOUNTS PAYABLE: AUTONOMOUS 3-WAY MATCHING DOSSIER")
    output.append(f"  Invoice: {result.invoice_id} | Vendor: {result.vendor_id} | PO: {result.po_number}")
    output.append(f"  Overall Status: {result.overall_status.value} | Confidence: {result.confidence_score * 100:.1f}%")
    output.append(f"  Total Invoiced: ${result.total_invoiced_amount:,.2f} | Allowable: ${result.allowable_amount:,.2f} | Discrepancy: ${result.discrepancy_amount:,.2f}")
    output.append(sep)

    output.append("\n[LINE ITEM MATCHING & CONTRACT GROUNDING]")
    for item in result.line_matches:
        output.append(f" Line ID: {item.invoice_item_id} (PO Line: {item.po_line_num or 'N/A'})")
        output.append(f"  - Matched Contract Term: {item.matched_role_or_milestone}")
        output.append(f"  - Invoiced Rate: ${item.invoiced_rate:,.2f} | Contract Max: ${item.contract_max_rate or 0:,.2f} | Variance: ${item.rate_variance:,.2f}")
        output.append(f"  - Goods/Services Receipt: {'APPROVED (' + (item.gr_receipt_id or '') + ')' if item.gr_approved else 'MISSING / PENDING'}")
        output.append(f"  - Status: {item.status.value}")
        output.append(f"  - Details: {item.details}")
        if item.clause_citations:
            output.append(f"  - Citations: {item.clause_citations[0]}")
        output.append("")

    output.append(subsep)
    output.append(f"[AGENT RESOLUTION: {action.action_type.value}]")
    output.append(f" Title: {action.title}")
    output.append(f" Recipient: {action.recipient}")
    output.append(f" Summary: {action.summary}")
    output.append(f" Tolerance Applied: {'YES ($' + str(action.estimated_impact_usd) + ')' if action.tolerance_applied else 'NO'}")
    output.append(subsep)

    output.append("\n[AUTONOMOUS COMMUNICATION / POSTING MEMO DRAFT]:")
    indented_comm = "\n".join("  > " + line for line in action.generated_communication.split("\n"))
    output.append(indented_comm)

    output.append("\n[SUPERVISOR AUDIT TRAIL]:")
    for step in result.audit_trail:
        output.append(f"  * {step}")

    output.append(sep)
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="IBM AP Autonomous Invoice Exception Matcher")
    parser.add_argument("--all", action="store_true", help="Run all 5 test scenarios")
    parser.add_argument("--scenario", type=int, choices=[1, 2, 3, 4, 5], default=None, help="Run specific scenario (1-5)")

    args = parser.parse_args()

    retriever, erp, invoices = build_demo_environment()
    orchestrator = APOrchestrator(retriever=retriever, erp_connector=erp)

    if args.scenario:
        selected_invoices = [invoices[args.scenario - 1]]
    else:
        # Default run all
        selected_invoices = invoices

    print(f"\nProcessing {len(selected_invoices)} invoice(s) through Agentic 3-Way Matching Engine...\n")

    for idx, inv in enumerate(selected_invoices, 1):
        result = orchestrator.process_invoice(inv)
        print(format_matching_result(result))
        print("\n")


if __name__ == "__main__":
    main()
