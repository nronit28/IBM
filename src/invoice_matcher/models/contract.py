"""
Contract and Statement of Work (SOW) domain models for RAG indexing and verification.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import date


class RateCardItem(BaseModel):
    role_title: str = Field(description="Contracted role title e.g. 'Senior Infrastructure Consultant Tier 1'")
    max_hourly_rate: float = Field(description="Maximum allowable hourly rate")
    currency: str = Field(default="USD")
    experience_level: str = Field(default="Senior", description="Junior, Mid, Senior, Principal")
    standard_aliases: List[str] = Field(default_factory=list, description="Common role aliases and variations")


class MilestoneTerm(BaseModel):
    milestone_code: str = Field(description="Milestone code e.g. MS-01, MS-02")
    title: str = Field(description="Milestone title")
    deliverables: str = Field(description="Required deliverables and acceptance criteria")
    contract_amount: float = Field(description="Fixed payout amount upon completion")
    approval_required_by: str = Field(description="Role responsible for sign-off e.g. 'IBM Delivery Partner'")


class ContractClause(BaseModel):
    clause_id: str = Field(description="Identifier e.g. CLAUSE-4.2")
    section: str = Field(description="Section heading or number")
    title: str = Field(description="Descriptive clause title")
    text: str = Field(description="Full contractual text")
    category: str = Field(description="rates, milestones, taxes, expenses, dispute_period, penalties")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Arbitrary tags for vector search")


class Contract(BaseModel):
    contract_id: str = Field(description="Contract or SOW ID e.g. SOW-IBM-2025-09")
    contract_type: str = Field(description="MSA, SOW, RATE_CARD, SLA")
    vendor_id: str = Field(description="IBM Vendor ID")
    title: str = Field(description="Agreement Title")
    effective_date: date
    expiry_date: date
    currency: str = Field(default="USD")
    payment_terms: str = Field(default="Net 30", description="Net 30, 2/10 Net 30, Net 60")
    rate_cards: List[RateCardItem] = Field(default_factory=list)
    milestones: List[MilestoneTerm] = Field(default_factory=list)
    clauses: List[ContractClause] = Field(default_factory=list)
    dispute_notice_days: int = Field(default=30, description="Allowed days to dispute billing")
    tax_tolerance_usd: float = Field(default=25.0, description="Allowable automated rounding variance")
