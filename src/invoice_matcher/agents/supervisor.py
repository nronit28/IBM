"""
Supervisor / AP Orchestrator: Coordinates subagents through the 3-way matching lifecycle.
"""

from typing import Dict, Any, List
from ..models.invoice import Invoice
from ..models.matching import MatchingResult, ActionType
from .normalizer_agent import NormalizerAgent
from .validator_agent import ContractValidatorAgent
from .erp_agent import ERPAgent
from .resolution_agent import ResolutionAgent
from ..rag.contract_retriever import ContractRetriever
from ..erp_service.sap_mock import SAPConnector


class APOrchestrator:
    """Supervisor agent coordinating the full 3-way matching and exception resolution pipeline."""

    def __init__(self, retriever: ContractRetriever, erp_connector: SAPConnector):
        self.retriever = retriever
        self.erp = erp_connector

        # Initialize subagents
        self.normalizer = NormalizerAgent()
        self.validator = ContractValidatorAgent(retriever=self.retriever)
        self.erp_agent = ERPAgent(erp_connector=self.erp)
        self.resolution_agent = ResolutionAgent()

    def process_invoice(self, raw_invoice: Invoice) -> MatchingResult:
        """
        Executes multi-agent 3-way matching workflow on a single invoice.
        """
        # Step 1: Ingestion & Normalization
        norm_invoice, norm_logs = self.normalizer.process(raw_invoice)

        # Step 2: Contract Validation via RAG
        contract_validation = self.validator.validate_invoice(norm_invoice)

        # Extract RAG-resolved roles for downstream ERP line matching
        resolved_roles = {}
        for item_id, v in contract_validation.get("line_validations", {}).items():
            matched = v.get("matched_role_or_milestone")
            if matched and matched != "Unmatched":
                resolved_roles[item_id] = matched

        # Step 3: ERP 3-Way Match Verification (PO & GR/SR) using resolved canonical roles
        erp_validation = self.erp_agent.check_erp_alignment(norm_invoice, resolved_roles=resolved_roles)

        # Step 4: Resolution & Discrepancy Triage
        result = self.resolution_agent.resolve(
            invoice=norm_invoice,
            contract_validation=contract_validation,
            erp_validation=erp_validation
        )

        # If Auto-Approved, trigger ERP ledger posting
        if result.resolution_action.action_type == ActionType.AUTO_APPROVE:
            for item in norm_invoice.line_items:
                line_match = next((m for m in result.line_matches if m.invoice_item_id == item.item_id), None)
                if line_match and line_match.po_line_num:
                    self.erp.post_invoice_clearing(
                        invoice_id=norm_invoice.invoice_id,
                        po_number=norm_invoice.po_number,
                        line_num=line_match.po_line_num,
                        invoiced_qty=item.quantity,
                        invoiced_amount=item.total_amount
                    )

        return result
