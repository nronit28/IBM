"""
Unit tests for RAG indexing and contract clause/role retrieval.
"""

import unittest
from datetime import date
from src.invoice_matcher.models.contract import Contract, RateCardItem, MilestoneTerm, ContractClause
from src.invoice_matcher.rag.document_indexer import ContractKnowledgeBase
from src.invoice_matcher.rag.contract_retriever import ContractRetriever


class TestRAGRetrieval(unittest.TestCase):

    def setUp(self):
        self.contract = Contract(
            contract_id="SOW-01",
            contract_type="SOW",
            vendor_id="VEND-01",
            title="DevOps SOW",
            effective_date=date(2025, 1, 1),
            expiry_date=date(2026, 12, 31),
            rate_cards=[
                RateCardItem(
                    role_title="Senior Infrastructure Consultant Tier 1",
                    max_hourly_rate=170.0,
                    standard_aliases=["Lead Cloud DevOps Architect", "Principal DevOps Lead"]
                )
            ],
            milestones=[
                MilestoneTerm(
                    milestone_code="MS-01",
                    title="Cluster Architecture Design",
                    deliverables="High level design document",
                    contract_amount=20000.0,
                    approval_required_by="IBM Architect"
                )
            ],
            clauses=[
                ContractClause(
                    clause_id="C-4.1",
                    section="Section 4.1",
                    title="Rate Cap",
                    text="Rates must not exceed agreed rate card.",
                    category="rates"
                )
            ]
        )
        self.kb = ContractKnowledgeBase()
        self.kb.add_contract(self.contract)
        self.retriever = ContractRetriever(self.kb)

    def test_semantic_role_alias_matching(self):
        # Query using alias
        match = self.retriever.match_rate_card_role("Lead Cloud DevOps Architect", "VEND-01")
        self.assertIsNotNone(match)
        rc, score, explanation = match
        self.assertEqual(rc.role_title, "Senior Infrastructure Consultant Tier 1")
        self.assertGreater(score, 0.8)
        self.assertEqual(rc.max_hourly_rate, 170.0)

    def test_clause_search(self):
        results = self.retriever.search_clauses("rate cap", vendor_id="VEND-01")
        self.assertGreater(len(results), 0)
        top_chunk, score = results[0]
        self.assertEqual(top_chunk.clause_id, "C-4.1")


if __name__ == "__main__":
    unittest.main()
