"""
Contract Retriever for RAG: Hybrid BM25 & Semantic Role Matching.
"""

from typing import List, Tuple, Optional, Dict
import math
from rapidfuzz import fuzz
from .document_indexer import ContractKnowledgeBase, IndexedClause, tokenize
from ..models.contract import RateCardItem, MilestoneTerm


class ContractRetriever:
    """Retrieves relevant contract clauses, rate cards, and milestones using hybrid search."""

    def __init__(self, knowledge_base: ContractKnowledgeBase):
        self.kb = knowledge_base

    def search_clauses(
        self,
        query: str,
        vendor_id: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 3
    ) -> List[Tuple[IndexedClause, float]]:
        """
        Hybrid BM25 and fuzzy search to find contract clauses.
        Returns list of (IndexedClause, score) sorted descending.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: List[Tuple[IndexedClause, float]] = []
        k1 = 1.5
        b = 0.75
        avg_doc_len = sum(len(c.tokens) for c in self.kb.indexed_clauses) / max(1, len(self.kb.indexed_clauses))

        for chunk in self.kb.indexed_clauses:
            if vendor_id and chunk.vendor_id != vendor_id:
                continue
            if category and chunk.category != category:
                continue

            # BM25 score
            bm25 = 0.0
            doc_len = len(chunk.tokens)
            doc_token_counts = {}
            for t in chunk.tokens:
                doc_token_counts[t] = doc_token_counts.get(t, 0) + 1

            for q in query_tokens:
                if q in doc_token_counts:
                    tf = doc_token_counts[q]
                    df = self.kb.doc_freq.get(q, 1)
                    idf = math.log(1.0 + (self.kb.total_docs - df + 0.5) / (df + 0.5))
                    numerator = tf * (k1 + 1.0)
                    denominator = tf + k1 * (1.0 - b + b * (doc_len / max(1.0, avg_doc_len)))
                    bm25 += idf * (numerator / max(1e-5, denominator))

            # Fuzzy token set similarity score (0 to 1)
            fuzzy_ratio = fuzz.token_set_ratio(query, f"{chunk.title} {chunk.content}") / 100.0

            # Combined hybrid score
            combined_score = bm25 + (fuzzy_ratio * 3.0)
            if combined_score > 0.1:
                scores.append((chunk, combined_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def match_rate_card_role(
        self,
        invoiced_role: str,
        vendor_id: str,
        min_confidence: float = 0.65
    ) -> Optional[Tuple[RateCardItem, float, str]]:
        """
        Semantically match an informal invoice role against the contracted SOW Rate Card.
        e.g., 'Lead Cloud DevOps Architect' -> 'Senior Infrastructure Consultant Tier 1'
        Returns: (RateCardItem, confidence_score, explanation) or None
        """
        rate_cards = self.kb.rate_cards_by_vendor.get(vendor_id, [])
        if not rate_cards:
            return None

        best_match: Optional[RateCardItem] = None
        best_score: float = 0.0
        best_explanation: str = ""

        clean_invoiced = invoiced_role.strip().lower()

        for rc in rate_cards:
            # 1. Direct match with role title
            score_title = fuzz.token_set_ratio(clean_invoiced, rc.role_title.lower()) / 100.0

            # 2. Check aliases
            alias_scores = [
                fuzz.token_set_ratio(clean_invoiced, alias.lower()) / 100.0
                for alias in rc.standard_aliases
            ]
            best_alias_score = max(alias_scores) if alias_scores else 0.0

            # 3. Partial ratio boost for keywords (e.g. Architect, Consultant, Engineer)
            partial = fuzz.partial_ratio(clean_invoiced, rc.role_title.lower()) / 100.0

            # Effective score
            effective_score = max(score_title, best_alias_score * 1.05, (score_title * 0.7 + partial * 0.3))
            effective_score = min(1.0, effective_score)

            if effective_score > best_score:
                best_score = effective_score
                best_match = rc
                matched_via = "title" if score_title >= best_alias_score else "contract alias"
                best_explanation = (
                    f"Matched '{invoiced_role}' to contracted SOW role '{rc.role_title}' "
                    f"via {matched_via} with confidence {best_score:.2f} (Max Rate: ${rc.max_hourly_rate}/hr)."
                )

        if best_match and best_score >= min_confidence:
            return best_match, best_score, best_explanation
        return None

    def match_milestone(
        self,
        milestone_query: str,
        vendor_id: str
    ) -> Optional[Tuple[MilestoneTerm, float]]:
        """Match invoice milestone code or description to SOW milestones."""
        milestones = self.kb.milestones_by_vendor.get(vendor_id, [])
        if not milestones:
            return None

        query_clean = milestone_query.strip().lower()
        for ms in milestones:
            if ms.milestone_code.lower() in query_clean:
                return ms, 1.0

        # Fuzzy match on title
        best_ms = None
        best_score = 0.0
        for ms in milestones:
            score = fuzz.token_set_ratio(query_clean, f"{ms.milestone_code} {ms.title}") / 100.0
            if score > best_score:
                best_score = score
                best_ms = ms

        if best_ms and best_score >= 0.70:
            return best_ms, best_score
        return None
