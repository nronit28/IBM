"""
Document Indexer for Contract and SOW Knowledge Base (RAG).
Chunks clauses, indexes rate cards, and creates searchable vectors/tokens.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import math
import re
from collections import Counter
from ..models.contract import Contract, ContractClause, RateCardItem, MilestoneTerm


@dataclass
class IndexedClause:
    chunk_id: str
    contract_id: str
    vendor_id: str
    clause_id: str
    section: str
    title: str
    content: str
    category: str
    tokens: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return [t.lower() for t in re.findall(r"\b[A-Za-z0-9_]{2,}\b", text)]


class ContractKnowledgeBase:
    """In-memory search index for contract clauses, SOW rate cards, and terms."""

    def __init__(self):
        self.indexed_clauses: List[IndexedClause] = []
        self.rate_cards_by_vendor: Dict[str, List[RateCardItem]] = {}
        self.milestones_by_vendor: Dict[str, List[MilestoneTerm]] = {}
        self.contracts: Dict[str, Contract] = {}
        self.doc_freq: Counter = Counter()
        self.total_docs: int = 0

    def add_contract(self, contract: Contract) -> None:
        """Index a contract, its clauses, rate cards, and milestones."""
        self.contracts[contract.contract_id] = contract

        # Index rate cards
        if contract.vendor_id not in self.rate_cards_by_vendor:
            self.rate_cards_by_vendor[contract.vendor_id] = []
        self.rate_cards_by_vendor[contract.vendor_id].extend(contract.rate_cards)

        # Index milestones
        if contract.vendor_id not in self.milestones_by_vendor:
            self.milestones_by_vendor[contract.vendor_id] = []
        self.milestones_by_vendor[contract.vendor_id].extend(contract.milestones)

        # Index discrete clauses
        for clause in contract.clauses:
            full_text = f"{clause.section} {clause.title}: {clause.text}"
            tokens = tokenize(full_text)
            chunk = IndexedClause(
                chunk_id=f"{contract.contract_id}-{clause.clause_id}",
                contract_id=contract.contract_id,
                vendor_id=contract.vendor_id,
                clause_id=clause.clause_id,
                section=clause.section,
                title=clause.title,
                content=clause.text,
                category=clause.category,
                tokens=tokens,
                metadata={
                    "vendor_id": contract.vendor_id,
                    "contract_type": contract.contract_type,
                    "tax_tolerance": contract.tax_tolerance_usd,
                    "payment_terms": contract.payment_terms,
                    **clause.metadata
                }
            )
            self.indexed_clauses.append(chunk)

            # Update document frequencies for BM25
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freq[token] += 1

        # Also index rate cards as searchable clauses
        for rc in contract.rate_cards:
            aliases_str = ", ".join(rc.standard_aliases)
            rc_text = (
                f"Rate Card Role: {rc.role_title} (Level: {rc.experience_level}). "
                f"Maximum allowable hourly rate: {rc.max_hourly_rate} {rc.currency}. "
                f"Recognized aliases and variations: {aliases_str}."
            )
            tokens = tokenize(rc_text)
            chunk = IndexedClause(
                chunk_id=f"{contract.contract_id}-RC-{rc.role_title.replace(' ', '_')}",
                contract_id=contract.contract_id,
                vendor_id=contract.vendor_id,
                clause_id=f"RATE-{rc.role_title}",
                section="Schedule A - Rate Cards",
                title=f"Rate Card: {rc.role_title}",
                content=rc_text,
                category="rates",
                tokens=tokens,
                metadata={"role_title": rc.role_title, "max_rate": rc.max_hourly_rate}
            )
            self.indexed_clauses.append(chunk)
            for token in set(tokens):
                self.doc_freq[token] += 1

        self.total_docs = len(self.indexed_clauses)
