"""
Invoice models for AP Ingestion and Line Item Matching.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date


class InvoiceLineItem(BaseModel):
    item_id: str = Field(description="Unique line item ID e.g. LINE-001")
    description: str = Field(description="Raw line item description from invoice")
    role_title: Optional[str] = Field(default=None, description="Extracted job role or consulting title if applicable")
    quantity: float = Field(default=1.0, description="Hours, units, or milestone fraction")
    unit: str = Field(default="HOURS", description="Unit of measure e.g. HOURS, MONTHS, MILESTONE")
    unit_price: float = Field(description="Billed rate or unit price")
    total_amount: float = Field(description="Line total before tax")
    milestone_code: Optional[str] = Field(default=None, description="Milestone code if milestone billing e.g. MS-03")
    tax_amount: float = Field(default=0.0, description="Tax applicable to this line item")


class Invoice(BaseModel):
    invoice_id: str = Field(description="Invoice number e.g. INV-2026-9812")
    vendor_id: str = Field(description="IBM Vendor ID e.g. VEND-IBM-8841")
    vendor_name: str = Field(description="Legal entity name of supplier")
    po_number: str = Field(description="Referenced Purchase Order number e.g. PO-45009812")
    invoice_date: date = Field(description="Date invoice was issued")
    due_date: date = Field(description="Payment due date")
    currency: str = Field(default="USD", description="Currency code (USD, EUR, GBP)")
    subtotal: float = Field(description="Invoice subtotal before tax")
    tax_amount: float = Field(default=0.0, description="Total tax claimed")
    total_amount: float = Field(description="Final invoice total")
    line_items: List[InvoiceLineItem] = Field(default_factory=list, description="List of invoiced line items")
    status: str = Field(default="RECEIVED", description="RECEIVED, VALIDATING, EXCEPTION, APPROVED, REJECTED")
    notes: Optional[str] = Field(default=None, description="Any vendor-provided notes or remittance remarks")
