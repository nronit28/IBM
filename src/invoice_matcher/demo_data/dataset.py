"""
Demo Dataset generator for realistic IBM Accounts Payable 3-way matching scenarios.
"""

from datetime import date
from typing import Tuple, List
from ..models.invoice import Invoice, InvoiceLineItem
from ..models.contract import Contract, ContractClause, RateCardItem, MilestoneTerm
from ..models.erp import PurchaseOrder, POLineItem, GoodsServicesReceipt
from ..rag.document_indexer import ContractKnowledgeBase
from ..rag.contract_retriever import ContractRetriever
from ..erp_service.sap_mock import SAPConnector


def build_demo_environment() -> Tuple[ContractRetriever, SAPConnector, List[Invoice]]:
    """Initializes RAG Knowledge Base, SAP ERP Mock, and 5 Test Invoices."""

    # 1. Create Governing SOW & MSA Contract
    contract = Contract(
        contract_id="SOW-IBM-2025-09",
        contract_type="SOW",
        vendor_id="VEND-IBM-8841",
        title="IBM Cloud Transformation & Platform Engineering SOW",
        effective_date=date(2025, 1, 1),
        expiry_date=date(2027, 12, 31),
        currency="USD",
        payment_terms="Net 30",
        tax_tolerance_usd=25.0,
        rate_cards=[
            RateCardItem(
                role_title="Senior Infrastructure Consultant Tier 1",
                max_hourly_rate=170.0,
                currency="USD",
                experience_level="Senior",
                standard_aliases=[
                    "Lead Cloud DevOps Architect",
                    "Senior Cloud Engineer",
                    "Principal DevOps Lead",
                    "Infrastructure Consultant"
                ]
            ),
            RateCardItem(
                role_title="Data Integration Specialist",
                max_hourly_rate=145.0,
                currency="USD",
                experience_level="Mid-Senior",
                standard_aliases=[
                    "Senior ETL Developer",
                    "Data Pipeline Engineer",
                    "Analytics Platform Specialist"
                ]
            )
        ],
        milestones=[
            MilestoneTerm(
                milestone_code="MS-03",
                title="Cloud Migration Phase 3 - DB Cutover & Hardening",
                deliverables="Completion of multi-region PostgreSQL cutover and zero-downtime cluster certification.",
                contract_amount=45000.0,
                approval_required_by="IBM Delivery Director"
            ),
            MilestoneTerm(
                milestone_code="MS-04",
                title="Cloud Migration Phase 4 - Production Cutover Verification",
                deliverables="Production traffic verification and security sign-off.",
                contract_amount=45000.0,
                approval_required_by="IBM Delivery Director"
            )
        ],
        clauses=[
            ContractClause(
                clause_id="CLAUSE-4.2",
                section="Section 4.2 - Rate Card Enforceability",
                title="Strict Billable Rate Caps",
                text="Supplier shall invoice IBM only according to the contracted rates in Schedule A. Any invoiced rate exceeding the agreed rate cap without prior written change order is null and subject to dispute and automatic offset.",
                category="rates"
            ),
            ContractClause(
                clause_id="CLAUSE-5.1",
                section="Section 5.1 - Acceptance and 3-Way Match Verification",
                title="Mandatory Goods/Services Receipt",
                text="All vendor disbursements are conditional upon three-way matching against a valid Purchase Order and a formal Goods/Services Receipt (GR/SR) signed off in SAP by the authorized IBM Project Manager.",
                category="milestones"
            ),
            ContractClause(
                clause_id="CLAUSE-7.3",
                section="Section 7.3 - Tolerances and Administrative Adjustments",
                title="Tax and Minor Rounding Tolerance",
                text="Discrepancies of less than $25.00 resulting from state/regional sales tax rounding or currency calculation shall be absorbed under automated AP administrative tolerance without withholding payment.",
                category="taxes"
            )
        ]
    )

    # 2. Index into RAG Knowledge Base
    kb = ContractKnowledgeBase()
    kb.add_contract(contract)
    retriever = ContractRetriever(kb)

    # 3. Setup SAP ERP Connector
    erp = SAPConnector()

    po = PurchaseOrder(
        po_number="PO-45009812",
        vendor_id="VEND-IBM-8841",
        buyer_name="David Ross (IBM Global Procurement)",
        cost_center="CC-US-CLOUD-902",
        creation_date=date(2025, 1, 15),
        status="OPEN",
        total_value=175000.0,
        currency="USD",
        line_items=[
            POLineItem(
                line_num=10,
                description="Cloud Migration Phase 3 Milestone (MS-03)",
                milestone_code="MS-03",
                ordered_qty=1.0,
                unit="MILESTONE",
                unit_price=45000.0,
                total_committed=45000.0
            ),
            POLineItem(
                line_num=20,
                description="Senior Infrastructure Consulting Services (T&M)",
                role_title="Senior Infrastructure Consultant Tier 1",
                ordered_qty=500.0,
                unit="HOURS",
                unit_price=170.0,
                total_committed=85000.0
            ),
            POLineItem(
                line_num=30,
                description="Data Integration Specialist Consulting (T&M)",
                role_title="Data Integration Specialist",
                ordered_qty=100.0,
                unit="HOURS",
                unit_price=145.0,
                total_committed=14500.0
            ),
            POLineItem(
                line_num=40,
                description="Cloud Migration Phase 4 Deliverable (MS-04)",
                milestone_code="MS-04",
                ordered_qty=1.0,
                unit="MILESTONE",
                unit_price=45000.0,
                total_committed=45000.0
            )
        ]
    )
    erp.add_purchase_order(po)

    # Receipts for PO line 10 (MS-03)
    receipt_ms03 = GoodsServicesReceipt(
        receipt_id="GR-50001923",
        po_number="PO-45009812",
        po_line_num=10,
        milestone_code="MS-03",
        received_qty=1.0,
        received_amount=45000.0,
        receipt_date=date(2026, 2, 10),
        signed_off_by="Sarah Chen (IBM Delivery Director)",
        approval_status="APPROVED",
        comments="Phase 3 DB cutover completed successfully with zero SLA downtime."
    )
    erp.add_receipt(receipt_ms03)

    # Receipt for PO line 20 (Approved hours)
    receipt_hours = GoodsServicesReceipt(
        receipt_id="GR-50001924",
        po_number="PO-45009812",
        po_line_num=20,
        received_qty=300.0,
        received_amount=51000.0,
        receipt_date=date(2026, 2, 15),
        signed_off_by="David Ross (IBM Project Manager)",
        approval_status="APPROVED",
        comments="Consulting hours verified on sprint backlog."
    )
    erp.add_receipt(receipt_hours)

    # Receipt for PO line 40 (Approved MS-04)
    receipt_ms04 = GoodsServicesReceipt(
        receipt_id="GR-50001925",
        po_number="PO-45009812",
        po_line_num=40,
        milestone_code="MS-04",
        received_qty=1.0,
        received_amount=45000.0,
        receipt_date=date(2026, 2, 24),
        signed_off_by="Sarah Chen (IBM Delivery Director)",
        approval_status="APPROVED",
        comments="Phase 4 verified."
    )
    erp.add_receipt(receipt_ms04)

    # 4. Generate 5 Representative Invoices
    invoices = [
        # Scenario 1: Clean 3-Way Match (Milestone MS-03)
        Invoice(
            invoice_id="INV-2026-001",
            vendor_id="VEND-IBM-8841",
            vendor_name="RedPillar Cloud Solutions LLC",
            po_number="PO-45009812",
            invoice_date=date(2026, 2, 12),
            due_date=date(2026, 3, 14),
            currency="USD",
            subtotal=45000.0,
            tax_amount=0.0,
            total_amount=45000.0,
            line_items=[
                InvoiceLineItem(
                    item_id="LINE-01",
                    description="Cloud Migration Phase 3 - DB Cutover & Hardening (MS-03)",
                    milestone_code="MS-03",
                    quantity=1.0,
                    unit="MILESTONE",
                    unit_price=45000.0,
                    total_amount=45000.0
                )
            ],
            notes="Milestone MS-03 sign-off attached."
        ),

        # Scenario 2: Semantic Role Mismatch (Resolved by RAG)
        Invoice(
            invoice_id="INV-2026-002",
            vendor_id="VEND-IBM-8841",
            vendor_name="RedPillar Cloud Solutions LLC",
            po_number="PO-45009812",
            invoice_date=date(2026, 2, 18),
            due_date=date(2026, 3, 20),
            currency="USD",
            subtotal=6800.0,
            tax_amount=0.0,
            total_amount=6800.0,
            line_items=[
                InvoiceLineItem(
                    item_id="LINE-01",
                    description="Lead Cloud DevOps Architect sprint consulting (Sprint 12)",
                    role_title="Lead Cloud DevOps Architect",
                    quantity=40.0,
                    unit="HOURS",
                    unit_price=170.0,
                    total_amount=6800.0
                )
            ],
            notes="T&M timesheet approved."
        ),

        # Scenario 3: Uncontracted Rate Bump Exception
        Invoice(
            invoice_id="INV-2026-003",
            vendor_id="VEND-IBM-8841",
            vendor_name="RedPillar Cloud Solutions LLC",
            po_number="PO-45009812",
            invoice_date=date(2026, 2, 20),
            due_date=date(2026, 3, 22),
            currency="USD",
            subtotal=9750.0,
            tax_amount=0.0,
            total_amount=9750.0,
            line_items=[
                InvoiceLineItem(
                    item_id="LINE-01",
                    description="Senior Infrastructure Consultant Tier 1 - Cloud architecture advisory",
                    role_title="Senior Infrastructure Consultant Tier 1",
                    quantity=50.0,
                    unit="HOURS",
                    unit_price=195.0,  # Contract rate is $170/hr -> $25/hr overcharge = $1,250 overcharge!
                    total_amount=9750.0
                )
            ],
            notes="Adjusted rate applied per annual review."
        ),

        # Scenario 4: Missing Goods/Services Receipt (GR/SR)
        Invoice(
            invoice_id="INV-2026-004",
            vendor_id="VEND-IBM-8841",
            vendor_name="RedPillar Cloud Solutions LLC",
            po_number="PO-45009812",
            invoice_date=date(2026, 2, 22),
            due_date=date(2026, 3, 24),
            currency="USD",
            subtotal=8700.0,
            tax_amount=0.0,
            total_amount=8700.0,
            line_items=[
                InvoiceLineItem(
                    item_id="LINE-01",
                    description="Data Integration Specialist Consulting (T&M)",
                    role_title="Data Integration Specialist",
                    quantity=60.0,
                    unit="HOURS",
                    unit_price=145.0,  # Valid contracted rate, but no GR exists for line 30
                    total_amount=8700.0
                )
            ],
            notes="Awaiting delivery confirmation in SAP for line 30."
        ),

        # Scenario 5: Minor Tax Rounding Tolerance ($8.50 difference)
        Invoice(
            invoice_id="INV-2026-005",
            vendor_id="VEND-IBM-8841",
            vendor_name="RedPillar Cloud Solutions LLC",
            po_number="PO-45009812",
            invoice_date=date(2026, 2, 25),
            due_date=date(2026, 3, 27),
            currency="USD",
            subtotal=45000.0,
            tax_amount=3600.0,
            total_amount=48608.50,  # $8.50 rounding variance on MS-04
            line_items=[
                InvoiceLineItem(
                    item_id="LINE-01",
                    description="Cloud Migration Phase 4 Deliverable (MS-04)",
                    milestone_code="MS-04",
                    quantity=1.0,
                    unit="MILESTONE",
                    unit_price=45000.0,
                    total_amount=45000.0
                )
            ],
            notes="Regional jurisdiction tax calculation applied."
        ),
    ]

    return retriever, erp, invoices
