"""
Invoice Normalizer Agent: Parses and normalizes incoming invoice line items.
"""

import re
from typing import List, Tuple
from ..models.invoice import Invoice, InvoiceLineItem


class NormalizerAgent:
    """Standardizes descriptions, role aliases, and formats from raw vendor invoices."""

    ROLE_PATTERNS = [
        r"(senior|lead|principal|staff|junior|mid)?\s*(cloud|devops|data|software|systems|security|infrastructure)?\s*(architect|engineer|consultant|developer|specialist)",
        r"(project\s*manager|scrum\s*master|delivery\s*lead|technical\s*writer)"
    ]

    MILESTONE_PATTERNS = [
        r"\b(MS-\d+|MILESTONE\s*\d+|PHASE\s*\d+|SPRINT\s*\d+)\b"
    ]

    def process(self, invoice: Invoice) -> Tuple[Invoice, List[str]]:
        """Cleans and annotates invoice line items."""
        logs = [f"NormalizerAgent: Ingested invoice {invoice.invoice_id} from '{invoice.vendor_name}'."]
        normalized_items: List[InvoiceLineItem] = []

        for item in invoice.line_items:
            desc = item.description.strip()
            detected_role = item.role_title
            detected_ms = item.milestone_code

            # Extract role if not explicitly set
            if not detected_role:
                for pattern in self.ROLE_PATTERNS:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        detected_role = match.group(0).strip().title()
                        break

            # Extract milestone code if present (and not a pure hourly T&M item with sprint notes)
            if not detected_ms:
                if item.unit.upper() not in ("HOURS", "HRS", "HOUR"):
                    for pattern in self.MILESTONE_PATTERNS:
                        match = re.search(pattern, desc, re.IGNORECASE)
                        if match:
                            detected_ms = match.group(0).upper().replace(" ", "-")
                            break
                else:
                    # For hourly items, only match if explicitly tagged as MS-xx
                    explicit_ms = re.search(r"\b(MS-\d+|MILESTONE\s*\d+)\b", desc, re.IGNORECASE)
                    if explicit_ms:
                        detected_ms = explicit_ms.group(0).upper().replace(" ", "-")

            # Check unit calculation
            computed_total = round(item.quantity * item.unit_price, 2)
            if abs(computed_total - item.total_amount) > 0.05:
                logs.append(
                    f"NormalizerAgent: Discrepancy detected in line {item.item_id}: "
                    f"qty ({item.quantity}) * rate ({item.unit_price}) = {computed_total} "
                    f"vs billed {item.total_amount}. Using billed total for audit."
                )

            normalized_items.append(
                InvoiceLineItem(
                    item_id=item.item_id,
                    description=desc,
                    role_title=detected_role,
                    quantity=item.quantity,
                    unit=item.unit.upper(),
                    unit_price=item.unit_price,
                    total_amount=item.total_amount,
                    milestone_code=detected_ms,
                    tax_amount=item.tax_amount
                )
            )

        invoice.line_items = normalized_items
        logs.append(f"NormalizerAgent: Successfully normalized {len(normalized_items)} line items.")
        return invoice, logs
