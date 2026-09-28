"""
3-Way Matching outcome models, exception types, and agent resolution actions.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    PERFECT_MATCH = "PERFECT_MATCH"
    EXCEPTION_RATE_VARIANCE = "EXCEPTION_RATE_VARIANCE"
    EXCEPTION_ROLE_MISMATCH = "EXCEPTION_ROLE_MISMATCH"
    EXCEPTION_MISSING_GR = "EXCEPTION_MISSING_GR"
    EXCEPTION_TAX_VARIANCE = "EXCEPTION_TAX_VARIANCE"
    EXCEPTION_PO_BALANCE_EXCEEDED = "EXCEPTION_PO_BALANCE_EXCEEDED"
    EXCEPTION_UNAPPROVED_EXPENSE = "EXCEPTION_UNAPPROVED_EXPENSE"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class ActionType(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"
    DRAFT_VENDOR_INQUIRY = "DRAFT_VENDOR_INQUIRY"
    REQUEST_INTERNAL_SIGN_OFF = "REQUEST_INTERNAL_SIGN_OFF"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"


class LineItemMatch(BaseModel):
    invoice_item_id: str
    po_line_num: Optional[int] = None
    matched_role_or_milestone: str
    invoiced_qty: float
    po_remaining_qty: Optional[float] = None
    invoiced_rate: float
    contract_max_rate: Optional[float] = None
    rate_variance: float = 0.0
    gr_approved: bool = False
    gr_receipt_id: Optional[str] = None
    status: MatchStatus
    details: str
    clause_citations: List[str] = Field(default_factory=list)


class ResolutionAction(BaseModel):
    action_type: ActionType
    title: str
    recipient: str = Field(description="Target recipient e.g. Vendor AP, Internal PM, or Senior AP Specialist")
    summary: str
    generated_communication: str = Field(description="Drafted email or workflow notification body")
    citations: List[str] = Field(default_factory=list, description="Contract or PO citations backing this decision")
    tolerance_applied: bool = False
    estimated_impact_usd: float = 0.0


class MatchingResult(BaseModel):
    invoice_id: str
    vendor_id: str
    po_number: str
    overall_status: MatchStatus
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in match/exception triage")
    total_invoiced_amount: float
    allowable_amount: float
    discrepancy_amount: float
    line_matches: List[LineItemMatch] = Field(default_factory=list)
    resolution_action: ResolutionAction
    audit_trail: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
