"""
Synthetic Data Generator for Enterprise AP 3-Way Matching and Exception Handling.
Generates mathematically consistent, realistic invoice datasets covering edge cases:
- Clean 3-Way Matches
- Contract Rate Variance / Overcharge
- Semantic Role Title Aliases (for RAG vector matching)
- Missing Goods/Services Receipts (SAP S/4HANA hold)
- Minor Tax Rounding Deviations (Tolerance absorption)
- Quantity and Hour Overruns (PO balance exceedance)
- Volume Rebate & Discount Omissions
- Duplicate Billing Anomalies
- Foreign Currency Fluctuation / FX Tolerance
- Uncontracted Service Roles
"""

import csv
import io
import json
import random
from datetime import date, timedelta, datetime
from typing import List, Dict, Any, Optional

from ..models.invoice import Invoice, InvoiceLineItem


# Enterprise Scenario Specifications
SCENARIO_SPECS: Dict[str, Dict[str, Any]] = {
    "SYN_CLEAN_MILESTONE": {
        "code": "SYN-01",
        "title": "Clean 3-Way Match (Milestone Deliverable)",
        "category": "Standard Invoicing",
        "expected_status": "PERFECT_MATCH",
        "description": "Milestone MS-03 billed exactly according to contracted SOW schedule ($45,000.00). Corresponds 1:1 with approved SAP Goods Receipt GR-50001923.",
        "default_vendor": "RedPillar Cloud Solutions LLC",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "Cloud Migration Phase 3 - DB Cutover & Hardening (MS-03)",
            "milestone_code": "MS-03",
            "quantity": 1.0,
            "unit": "MILESTONE",
            "unit_price": 45000.0,
            "total_amount": 45000.0
        },
        "tax_amount": 0.0,
        "notes": "Milestone completion certificate signed by Delivery Director attached."
    },
    "SYN_SEMANTIC_ROLE": {
        "code": "SYN-02",
        "title": "Semantic Role Alias Variant (RAG Vector Resolution)",
        "category": "Contract Compliance",
        "expected_status": "PERFECT_MATCH",
        "description": "Vendor invoices consulting under alias 'Lead Cloud DevOps Architect' (40 hrs @ $170/hr). RAG semantic vector search resolves this to 'Senior Infrastructure Consultant Tier 1' and auto-approves.",
        "default_vendor": "RedPillar Cloud Solutions LLC",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "Lead Cloud DevOps Architect sprint consulting (Sprint 12)",
            "role_title": "Lead Cloud DevOps Architect",
            "quantity": 40.0,
            "unit": "HOURS",
            "unit_price": 170.0,
            "total_amount": 6800.0
        },
        "tax_amount": 0.0,
        "notes": "Timesheet approved by sprint engineering lead."
    },
    "SYN_RATE_OVERCHARGE": {
        "code": "SYN-03",
        "title": "Contract Rate Overcharge (Variance Deduction)",
        "category": "Discrepancy Exception",
        "expected_status": "EXCEPTION_RATE_VARIANCE",
        "description": "Senior Consultant billed at uncontracted $195.00/hr (Contract ceiling is $170.00/hr). System flags $25/hr rate overcharge, issues $1,250.00 debit memo, and permits payment only on allowable amount.",
        "default_vendor": "RedPillar Cloud Solutions LLC",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "Senior Infrastructure Consultant Tier 1 - Cloud architecture advisory",
            "role_title": "Senior Infrastructure Consultant Tier 1",
            "quantity": 50.0,
            "unit": "HOURS",
            "unit_price": 195.0,  # $25 overage per hour
            "total_amount": 9750.0
        },
        "tax_amount": 0.0,
        "notes": "Adjusted rate applied per vendor internal mid-year rate review."
    },
    "SYN_MISSING_GR": {
        "code": "SYN-04",
        "title": "Missing Goods/Services Receipt (SAP Hold)",
        "category": "ERP Exception",
        "expected_status": "EXCEPTION_MISSING_GR",
        "description": "Vendor billed 60 hours for Data Integration Specialist ($8,700.00). Rate matches contract, but Project Manager has not yet submitted signed Goods Receipt in SAP. Automatic AP hold triggered.",
        "default_vendor": "RedPillar Cloud Solutions LLC",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "Data Integration Specialist Consulting (T&M)",
            "role_title": "Data Integration Specialist",
            "quantity": 60.0,
            "unit": "HOURS",
            "unit_price": 145.0,
            "total_amount": 8700.0
        },
        "tax_amount": 0.0,
        "notes": "Awaiting delivery confirmation in SAP for line 30."
    },
    "SYN_TAX_TOLERANCE": {
        "code": "SYN-05",
        "title": "Minor Tax Rounding Tolerance ($12.50 Absorbed)",
        "category": "Tolerance Exception",
        "expected_status": "PERFECT_MATCH",
        "description": "Phase 4 deliverable with $12.50 regional tax rounding deviation. Since deviation is under SOW Section 7.3 $25.00 administrative threshold, system auto-absorbs variance without withholding payment.",
        "default_vendor": "RedPillar Cloud Solutions LLC",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "Cloud Migration Phase 4 Deliverable (MS-04)",
            "milestone_code": "MS-04",
            "quantity": 1.0,
            "unit": "MILESTONE",
            "unit_price": 45000.0,
            "total_amount": 45000.0
        },
        "tax_amount": 3612.50,  # $12.50 variance
        "total_override": 48612.50,
        "notes": "Regional sales tax municipal surcharge applied."
    },
    "SYN_QUANTITY_OVERRUN": {
        "code": "SYN-06",
        "title": "Quantity Overrun (Exceeds PO Authorized Cap)",
        "category": "PO Discrepancy",
        "expected_status": "EXCEPTION_PO_BALANCE_EXCEEDED",
        "description": "Vendor invoices 580 hours when PO authorization was capped at 500 hours. System flags 80-hour overage ($13,600.00) and holds overbilled portion pending change order approval.",
        "default_vendor": "Quantum Logic Consulting Corp",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "Senior Infrastructure Consultant Tier 1 - Extended Migration Sprint",
            "role_title": "Senior Infrastructure Consultant Tier 1",
            "quantity": 580.0,
            "unit": "HOURS",
            "unit_price": 170.0,
            "total_amount": 98600.0
        },
        "tax_amount": 0.0,
        "notes": "Emergency hours incurred during data center migration outage window."
    },
    "SYN_UNAPPROVED_ROLE": {
        "code": "SYN-07",
        "title": "Uncontracted Service Role (SOW Exclusion)",
        "category": "Contract Compliance",
        "expected_status": "EXCEPTION_ROLE_MISMATCH",
        "description": "Invoice lists 'AI Prompt Engineering Lead Tier 4' at $210.00/hr. RAG validator identifies role is completely absent from Master Services Agreement rate schedule. Dispatched to vendor AP for clarification.",
        "default_vendor": "Apex Cognitive Systems LLC",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "AI Prompt Engineering Lead Tier 4 - Custom fine-tuning",
            "role_title": "AI Prompt Engineering Lead Tier 4",
            "quantity": 30.0,
            "unit": "HOURS",
            "unit_price": 210.0,
            "total_amount": 6300.0
        },
        "tax_amount": 0.0,
        "notes": "Unapproved role outside Scope of Work schedule."
    },
    "SYN_VOLUME_DISCOUNT": {
        "code": "SYN-08",
        "title": "Volume Discount Rebate Omission (5% Clause)",
        "category": "Pricing Exception",
        "expected_status": "EXCEPTION_RATE_VARIANCE",
        "description": "Vendor invoiced standard rate of $170/hr for 100 hours ($17,000.00), omitting mandatory 5% tier-2 volume rebate ($850.00). System computes correct debit memo.",
        "default_vendor": "RedPillar Cloud Solutions LLC",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "Senior Infrastructure Consultant Tier 1 - Volume engagement",
            "role_title": "Senior Infrastructure Consultant Tier 1",
            "quantity": 100.0,
            "unit": "HOURS",
            "unit_price": 170.0,
            "total_amount": 17000.0
        },
        "tax_amount": 0.0,
        "notes": "Standard monthly retainer without volume rebate credit."
    },
    "SYN_DUPLICATE_BILLING": {
        "code": "SYN-09",
        "title": "Duplicate Billing Anomaly (Hash Collision)",
        "category": "Fraud & Audit Protection",
        "expected_status": "EXCEPTION_PO_BALANCE_EXCEEDED",
        "description": "Vendor attempts secondary submission of Milestone MS-03 ($45,000.00) previously cleared under INV-2026-001. System flags duplicate reference and locks payment.",
        "default_vendor": "RedPillar Cloud Solutions LLC",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "Cloud Migration Phase 3 - DB Cutover & Hardening (MS-03) [Duplicate]",
            "milestone_code": "MS-03",
            "quantity": 1.0,
            "unit": "MILESTONE",
            "unit_price": 45000.0,
            "total_amount": 45000.0
        },
        "tax_amount": 0.0,
        "notes": "Resubmitted billing for milestone cutover."
    },
    "SYN_PARTIAL_GR": {
        "code": "SYN-10",
        "title": "Partial Goods Receipt Sign-Off (Line Balance Hold)",
        "category": "ERP Exception",
        "expected_status": "EXCEPTION_MISSING_GR",
        "description": "Invoice bills 80 consulting hours ($13,600.00), but SAP Goods Receipt was only signed off for 40 hours. System clears $6,800.00 and puts remaining balance on delivery hold.",
        "default_vendor": "RedPillar Cloud Solutions LLC",
        "default_vendor_id": "VEND-IBM-8841",
        "default_po": "PO-45009812",
        "line_config": {
            "description": "Senior Infrastructure Consultant Tier 1 - Cloud architecture advisory",
            "role_title": "Senior Infrastructure Consultant Tier 1",
            "quantity": 80.0,
            "unit": "HOURS",
            "unit_price": 170.0,
            "total_amount": 13600.0
        },
        "tax_amount": 0.0,
        "notes": "Sprint 14 deliverables partially certified in Jira."
    }
}


class SyntheticDataGenerator:
    """Enterprise synthetic data engine generating test invoice scenarios for FIN_OS."""

    @staticmethod
    def get_specs() -> List[Dict[str, Any]]:
        """Returns specifications and metadata for all available synthetic scenarios."""
        result = []
        for key, spec in SCENARIO_SPECS.items():
            result.append({
                "key": key,
                "code": spec["code"],
                "title": spec["title"],
                "category": spec["category"],
                "expected_status": spec["expected_status"],
                "description": spec["description"],
                "default_amount": spec["line_config"]["total_amount"] + spec.get("tax_amount", 0.0)
            })
        return result

    @classmethod
    def generate_scenario(
        cls,
        scenario_key: str,
        invoice_index: Optional[int] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Invoice:
        """Generates a single synthetic Invoice object based on a scenario key."""
        spec = SCENARIO_SPECS.get(scenario_key)
        if not spec:
            spec = random.choice(list(SCENARIO_SPECS.values()))

        idx = invoice_index or random.randint(100, 999)
        inv_id = f"INV-SYN-{idx:03d}"
        inv_date = date.today() - timedelta(days=random.randint(2, 30))
        due_date = inv_date + timedelta(days=30)

        params = custom_params or {}
        vendor_name = params.get("vendor_name", spec["default_vendor"])
        vendor_id = params.get("vendor_id", spec["default_vendor_id"])
        po_number = params.get("po_number", spec["default_po"])

        line_cfg = spec["line_config"].copy()
        if "quantity" in params:
            line_cfg["quantity"] = float(params["quantity"])
        if "unit_price" in params:
            line_cfg["unit_price"] = float(params["unit_price"])
        if "role_title" in params:
            line_cfg["role_title"] = params["role_title"]

        line_total = line_cfg["quantity"] * line_cfg["unit_price"]
        line_cfg["total_amount"] = line_total

        tax_amt = float(params.get("tax_amount", spec.get("tax_amount", 0.0)))
        total_amt = float(spec.get("total_override", line_total + tax_amt))
        if "tax_amount" in params:
            total_amt = line_total + tax_amt

        line_item = InvoiceLineItem(
            item_id="LINE-01",
            description=line_cfg["description"],
            role_title=line_cfg.get("role_title"),
            milestone_code=line_cfg.get("milestone_code"),
            quantity=line_cfg["quantity"],
            unit=line_cfg["unit"],
            unit_price=line_cfg["unit_price"],
            total_amount=line_total,
            tax_amount=tax_amt
        )

        return Invoice(
            invoice_id=inv_id,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            po_number=po_number,
            invoice_date=inv_date,
            due_date=due_date,
            currency="USD",
            subtotal=line_total,
            tax_amount=tax_amt,
            total_amount=total_amt,
            line_items=[line_item],
            status="RECEIVED",
            notes=spec.get("notes", "Synthetic invoice generated for automated AP testing.")
        )

    @classmethod
    def generate_batch(
        cls,
        count: int = 5,
        scenario_keys: Optional[List[str]] = None,
        starting_index: int = 101
    ) -> List[Invoice]:
        """Generates a batch of distinct synthetic invoices."""
        keys = scenario_keys or list(SCENARIO_SPECS.keys())
        invoices = []

        for i in range(count):
            spec_key = keys[i % len(keys)]
            inv = cls.generate_scenario(spec_key, invoice_index=starting_index + i)
            invoices.append(inv)

        return invoices

    @staticmethod
    def to_json(invoices: List[Invoice]) -> str:
        """Serializes invoice list into standardized JSON string."""
        data = [inv.model_dump() for inv in invoices]
        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def to_csv(invoices: List[Invoice]) -> str:
        """Exports invoice list as flat CSV table suitable for spreadsheet ingestion."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "invoice_id", "vendor_id", "vendor_name", "po_number", "invoice_date",
            "due_date", "currency", "subtotal", "tax_amount", "total_amount",
            "item_id", "description", "role_title", "milestone_code",
            "quantity", "unit", "unit_price", "notes"
        ])

        for inv in invoices:
            for item in inv.line_items:
                writer.writerow([
                    inv.invoice_id,
                    inv.vendor_id,
                    inv.vendor_name,
                    inv.po_number,
                    inv.invoice_date.isoformat(),
                    inv.due_date.isoformat(),
                    inv.currency,
                    inv.subtotal,
                    inv.tax_amount,
                    inv.total_amount,
                    item.item_id,
                    item.description,
                    item.role_title or "",
                    item.milestone_code or "",
                    item.quantity,
                    item.unit,
                    item.unit_price,
                    inv.notes or ""
                ])

        return output.getvalue()

    @staticmethod
    def from_json(json_str: str) -> List[Invoice]:
        """Parses JSON string (either array of invoices or object with 'invoices' key)."""
        raw = json.loads(json_str)
        items = raw.get("invoices", raw) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            items = [items]

        invoices = []
        for d in items:
            # Handle string dates
            if isinstance(d.get("invoice_date"), str):
                d["invoice_date"] = date.fromisoformat(d["invoice_date"].split("T")[0])
            if isinstance(d.get("due_date"), str):
                d["due_date"] = date.fromisoformat(d["due_date"].split("T")[0])
            invoices.append(Invoice(**d))
        return invoices

    @staticmethod
    def from_csv(csv_str: str) -> List[Invoice]:
        """Parses CSV string into a list of Invoice objects."""
        reader = csv.DictReader(io.StringIO(csv_str.strip()))
        invoice_map: Dict[str, Dict[str, Any]] = {}

        for row in reader:
            inv_id = row.get("invoice_id") or f"INV-CSV-{random.randint(100, 999)}"
            if inv_id not in invoice_map:
                inv_date_str = row.get("invoice_date") or date.today().isoformat()
                due_date_str = row.get("due_date") or (date.today() + timedelta(days=30)).isoformat()

                invoice_map[inv_id] = {
                    "invoice_id": inv_id,
                    "vendor_id": row.get("vendor_id", "VEND-CUSTOM-01"),
                    "vendor_name": row.get("vendor_name", "Supplier Corp"),
                    "po_number": row.get("po_number", "PO-45009812"),
                    "invoice_date": date.fromisoformat(inv_date_str.split("T")[0]),
                    "due_date": date.fromisoformat(due_date_str.split("T")[0]),
                    "currency": row.get("currency", "USD"),
                    "subtotal": float(row.get("subtotal", 0.0)),
                    "tax_amount": float(row.get("tax_amount", 0.0)),
                    "total_amount": float(row.get("total_amount", 0.0)),
                    "notes": row.get("notes", "Ingested from CSV"),
                    "line_items": []
                }

            qty = float(row.get("quantity", 1.0))
            price = float(row.get("unit_price", 0.0))
            total = qty * price if price > 0 else float(row.get("total_amount", 0.0))

            line = InvoiceLineItem(
                item_id=row.get("item_id") or f"LINE-{len(invoice_map[inv_id]['line_items']) + 1:02d}",
                description=row.get("description") or "Consulting engagement",
                role_title=row.get("role_title") or None,
                milestone_code=row.get("milestone_code") or None,
                quantity=qty,
                unit=row.get("unit", "HOURS"),
                unit_price=price,
                total_amount=total
            )
            invoice_map[inv_id]["line_items"].append(line)

            # Recalculate totals if subtotal was 0
            if invoice_map[inv_id]["subtotal"] == 0:
                calc_subtotal = sum(l.total_amount for l in invoice_map[inv_id]["line_items"])
                invoice_map[inv_id]["subtotal"] = calc_subtotal
                invoice_map[inv_id]["total_amount"] = calc_subtotal + invoice_map[inv_id]["tax_amount"]

        return [Invoice(**data) for data in invoice_map.values()]
