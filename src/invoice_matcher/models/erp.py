"""
ERP (SAP S/4HANA style) transactional models: Purchase Orders and Goods/Services Receipts.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date


class POLineItem(BaseModel):
    line_num: int = Field(description="PO Line item number e.g. 10, 20")
    description: str = Field(description="Description of committed good or service")
    milestone_code: Optional[str] = Field(default=None)
    role_title: Optional[str] = Field(default=None)
    ordered_qty: float
    unit: str = Field(default="HOURS")
    unit_price: float
    total_committed: float
    invoiced_qty: float = Field(default=0.0)
    invoiced_amount: float = Field(default=0.0)

    @property
    def remaining_qty(self) -> float:
        return max(0.0, self.ordered_qty - self.invoiced_qty)

    @property
    def remaining_amount(self) -> float:
        return max(0.0, self.total_committed - self.invoiced_amount)


class PurchaseOrder(BaseModel):
    po_number: str = Field(description="PO identifier e.g. PO-45009812")
    vendor_id: str
    buyer_name: str = Field(default="IBM Global Procurement")
    cost_center: str = Field(default="CC-US-FIN-4401")
    creation_date: date
    status: str = Field(default="OPEN", description="OPEN, PARTIALLY_INVOICED, CLOSED, BLOCKED")
    total_value: float
    currency: str = Field(default="USD")
    line_items: List[POLineItem] = Field(default_factory=list)


class GoodsServicesReceipt(BaseModel):
    receipt_id: str = Field(description="SAP Material/Service Document ID e.g. GR-50001923")
    po_number: str
    po_line_num: int
    milestone_code: Optional[str] = None
    received_qty: float
    received_amount: float
    receipt_date: date
    signed_off_by: str = Field(description="Delivery Lead or PM who confirmed receipt")
    approval_status: str = Field(default="APPROVED", description="APPROVED, PENDING, REJECTED")
    comments: Optional[str] = None
