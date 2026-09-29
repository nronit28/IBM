"""
Autonomous Financial Runtime Server for IBM AP 3-Way Matching and Payment Processing.
Serves the retro-futuristic web app on http://localhost:8080 and provides REST endpoints
for multi-agent matching, payment disbursements (ACH & ISO 20022), and HITL actions.
"""

import os
import sys
import json
import urllib.parse
from datetime import datetime, date
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, Optional, List

from .demo_data.dataset import build_demo_environment
from .demo_data.synthetic_generator import SyntheticDataGenerator
from .agents.supervisor import APOrchestrator
from .agents.gemini_reasoner import GeminiAPReasoner
from .payment_rails.disbursement_service import DisbursementService, PaymentRail, PaymentStatus
from .database.db_service import APDatabaseService
from .models.erp import GoodsServicesReceipt
from .models.invoice import Invoice, InvoiceLineItem

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DIST_DIR = _PROJECT_ROOT / "dist"
FRONTEND_DIR = DIST_DIR if (DIST_DIR / "index.html").exists() else _PROJECT_ROOT / "frontend"
PORT = 8080


class FinancialRuntime:
    """Singleton runtime managing agents, ERP mock, persistent DB, settlement rails, and Gemini AI."""

    def __init__(self):
        self.retriever, self.erp, self.invoices = build_demo_environment()
        self.orchestrator = APOrchestrator(retriever=self.retriever, erp_connector=self.erp)
        self.gemini_reasoner = GeminiAPReasoner()
        self.db = APDatabaseService()
        self.disbursement_service = DisbursementService(db=self.db)

        # Seed database if not populated
        if not self.db.list_invoices():
            self.db.seed_demo_environment(self.erp, self.invoices)

        # Cache of matching results by invoice_id
        self.matching_results: Dict[str, Any] = {}
        # Pre-compute matches for demo dataset
        for inv in self.invoices:
            res = self.orchestrator.process_invoice(inv)
            self.matching_results[inv.invoice_id] = res

    def get_invoice_by_id(self, invoice_id: str):
        return next((inv for inv in self.invoices if inv.invoice_id == invoice_id), None)

    def ingest_invoices(self, new_invoices: List[Invoice]) -> List[Dict[str, Any]]:
        """Ingests, matches, and persists batch of new invoices into runtime and DB."""
        processed = []
        for inv in new_invoices:
            existing_idx = next((i for i, existing in enumerate(self.invoices) if existing.invoice_id == inv.invoice_id), None)
            if existing_idx is not None:
                self.invoices[existing_idx] = inv
            else:
                self.invoices.append(inv)

            # Execute 3-way match
            result = self.orchestrator.process_invoice(inv)
            self.matching_results[inv.invoice_id] = result

            # Upsert into SQLite
            self.db.upsert_invoice({
                "invoice_id": inv.invoice_id,
                "vendor_id": inv.vendor_id,
                "vendor_name": inv.vendor_name,
                "po_number": inv.po_number,
                "invoice_date": inv.invoice_date.isoformat(),
                "total_amount": inv.total_amount,
                "tax_amount": inv.tax_amount,
                "currency": inv.currency,
                "status": result.overall_status.value,
                "confidence_score": result.confidence_score
            })

            # Record audit event
            self.db.log_audit(
                entity_id=inv.invoice_id,
                event_type="INVOICE_INGESTED",
                agent_name="DataIngestionPipeline",
                details=f"Invoice {inv.invoice_id} ({inv.vendor_name}) ingested. Match Status: {result.overall_status.value}, Confidence: {result.confidence_score * 100:.1f}%"
            )

            processed.append({
                "invoice": inv.model_dump(),
                "matching_result": result.model_dump()
            })
        return processed


RUNTIME = FinancialRuntime()


class FinancialAppHandler(SimpleHTTPRequestHandler):
    """Serves frontend static assets and handles REST API requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def _send_text(self, status_code: int, content: str, content_type: str, filename: str):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Route /terminal to /terminal.html
        if path in ("/terminal", "/terminal/"):
            self.path = "/terminal.html"
            return super().do_GET()

        # GET /api/status
        if path == "/api/status":
            return self._send_json(200, {
                "system": "IBM // FIN_OS (R)",
                "status": "ONLINE",
                "agents": ["Normalizer", "ContractValidator_RAG", "ERPAction_SAP", "ResolutionAgent", "GeminiAPReasoner"],
                "rails": ["ACH_NACHA_94COL", "ISO20022_PAIN001_09"],
                "database": "SQLITE_ACID",
                "gemini_model": RUNTIME.gemini_reasoner.DEFAULT_MODEL,
                "gemini_live": RUNTIME.gemini_reasoner.is_live(),
                "version": "2.1.0"
            })

        # GET /api/invoices
        if path == "/api/invoices":
            invoices = []
            for inv in RUNTIME.invoices:
                res = RUNTIME.matching_results.get(inv.invoice_id)
                disb = RUNTIME.db.get_disbursement_by_invoice(inv.invoice_id)
                inv_db = RUNTIME.db.get_invoice(inv.invoice_id)
                invoices.append({
                    "invoice_id": inv.invoice_id,
                    "vendor_id": inv.vendor_id,
                    "vendor_name": inv.vendor_name,
                    "po_number": inv.po_number,
                    "total_amount": inv.total_amount,
                    "tax_amount": inv.tax_amount,
                    "match_status": res.overall_status.value if res else "UNKNOWN",
                    "confidence": f"{res.confidence_score * 100:.1f}%" if res else "0%",
                    "discrepancy": f"${res.discrepancy_amount:,.2f}" if res else "$0.00",
                    "allowable_amount": res.allowable_amount if res else inv.total_amount,
                    "action_type": res.resolution_action.action_type.value if res else "UNKNOWN",
                    "payment_status": disb["status"] if disb else "UNPAID",
                    "payment_ref": disb["payment_ref"] if disb else None,
                    "rail": disb["rail"] if disb else None,
                    "db_status": inv_db["status"] if inv_db else "RECEIVED"
                })
            return self._send_json(200, {"invoices": invoices})

        # GET /api/invoices/<id>
        if path.startswith("/api/invoices/"):
            inv_id = path.replace("/api/invoices/", "").strip()
            inv = RUNTIME.get_invoice_by_id(inv_id)
            if not inv:
                return self._send_json(404, {"error": f"Invoice {inv_id} not found."})

            res = RUNTIME.matching_results.get(inv_id)
            disb = RUNTIME.db.get_disbursement_by_invoice(inv_id)
            audit = RUNTIME.db.get_audit_trail(inv_id)
            po = RUNTIME.db.get_po(inv.po_number)

            return self._send_json(200, {
                "invoice": inv.model_dump(),
                "matching_result": res.model_dump() if res else None,
                "disbursement": disb,
                "purchase_order": po,
                "audit_trail": audit
            })

        # GET /api/payments/<invoice_id>/payload?format=ach|xml
        if path.startswith("/api/payments/") and "/payload" in path:
            parts = path.split("/")
            inv_id = parts[3]
            disb = RUNTIME.db.get_disbursement_by_invoice(inv_id)
            if not disb:
                return self._send_json(404, {"error": f"No disbursement record for invoice {inv_id}."})

            fmt = query.get("format", ["ach"])[0].lower()
            if fmt == "xml":
                xml_payload = disb.get("iso20022_xml") or ""
                return self._send_text(200, xml_payload, "application/xml", f"{inv_id}_iso20022.xml")
            else:
                ach_payload = disb.get("nacha_payload") or ""
                return self._send_text(200, ach_payload, "text/plain", f"{inv_id}_nacha.ach")

        # GET /api/data/synthetic-specs
        if path == "/api/data/synthetic-specs":
            specs = SyntheticDataGenerator.get_specs()
            return self._send_json(200, {"specs": specs})

        # GET /api/data/template?format=json|csv
        if path == "/api/data/template":
            fmt = query.get("format", ["json"])[0].lower()
            sample_batch = SyntheticDataGenerator.generate_batch(2, scenario_keys=["SYN_CLEAN_MILESTONE", "SYN_RATE_OVERCHARGE"])
            if fmt == "csv":
                csv_content = SyntheticDataGenerator.to_csv(sample_batch)
                return self._send_text(200, csv_content, "text/csv", "invoice_template.csv")
            else:
                json_content = SyntheticDataGenerator.to_json(sample_batch)
                return self._send_text(200, json_content, "application/json", "invoice_template.json")

        return super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            payload = json.loads(body)
        except Exception as e:
            return self._send_json(400, {"error": f"Invalid JSON payload: {str(e)}"})

        # POST /api/match
        if path == "/api/match":
            inv_id = payload.get("invoice_id")
            inv = RUNTIME.get_invoice_by_id(inv_id)
            if not inv:
                return self._send_json(404, {"error": f"Invoice {inv_id} not found."})

            result = RUNTIME.orchestrator.process_invoice(inv)
            RUNTIME.matching_results[inv_id] = result
            RUNTIME.db.update_invoice_status(inv_id, result.overall_status.value, result.confidence_score)

            # Generate Gemini AI Multi-Step Reasoning
            gemini_analysis = RUNTIME.gemini_reasoner.analyze_invoice_matching(
                invoice_data=inv.model_dump(),
                contract_data={"contract_id": "SOW-IBM-2025-09", "clauses": ["Section 4.2", "Section 5.1", "Section 7.3"]},
                erp_data={"po_number": inv.po_number, "status": "OPEN"},
                preliminary_match=result.model_dump()
            )

            return self._send_json(200, {
                "success": True,
                "invoice_id": inv_id,
                "matching_result": result.model_dump(),
                "gemini_analysis": gemini_analysis
            })

        # POST /api/pay
        if path == "/api/pay":
            inv_id = payload.get("invoice_id")
            rail_str = payload.get("rail", "ACH").upper()
            rail = PaymentRail.ISO20022 if rail_str == "ISO20022" else PaymentRail.ACH
            authorized_by = payload.get("authorized_by")
            force_override = payload.get("force_override", False)

            inv = RUNTIME.get_invoice_by_id(inv_id)
            if not inv:
                return self._send_json(404, {"error": f"Invoice {inv_id} not found."})

            res = RUNTIME.matching_results.get(inv_id)
            # Use allowable amount from match if available, else total
            pay_amount = res.allowable_amount if res else inv.total_amount

            disb_result = RUNTIME.disbursement_service.disburse_payment(
                invoice_id=inv.invoice_id,
                vendor_id=inv.vendor_id,
                vendor_name=inv.vendor_name,
                po_number=inv.po_number,
                amount=pay_amount,
                rail=rail,
                authorized_by=authorized_by,
                force_override=force_override
            )

            status_code = 200 if disb_result.get("success") else 422
            return self._send_json(status_code, disb_result)

        # POST /api/action/dispute
        if path == "/api/action/dispute":
            inv_id = payload.get("invoice_id")
            reason = payload.get("reason", "Contractual Rate Variance")
            memo = payload.get("memo", "")

            inv = RUNTIME.get_invoice_by_id(inv_id)
            if not inv:
                return self._send_json(404, {"error": f"Invoice {inv_id} not found."})

            res = RUNTIME.matching_results.get(inv_id)
            discrepancy = res.discrepancy_amount if res else 0.0

            dispute_id = RUNTIME.db.record_dispute(
                invoice_id=inv_id,
                vendor_id=inv.vendor_id,
                discrepancy_amount=discrepancy,
                reason=reason,
                memo=memo or (res.resolution_action.generated_communication if res else "")
            )

            RUNTIME.db.log_audit(
                entity_id=inv_id,
                event_type="DISPUTE_TRANSMITTED",
                agent_name="APDisputeHandler",
                details=f"Formal dispute memo dispatched to vendor {inv.vendor_id}. Discrepancy: ${discrepancy:,.2f}"
            )

            return self._send_json(200, {
                "success": True,
                "dispute_id": dispute_id,
                "invoice_id": inv_id,
                "status": "DISPUTE_DISPATCHED",
                "message": f"Dispute notice successfully dispatched to {inv.vendor_name} AP billing department."
            })

        # POST /api/action/approve-receipt (PM Goods Receipt Creation)
        if path == "/api/action/approve-receipt":
            inv_id = payload.get("invoice_id")
            po_number = payload.get("po_number", "PO-45009812")
            po_line_num = int(payload.get("po_line_num", 20))
            delivered_qty = float(payload.get("delivered_qty", 40.0))
            approved_by = payload.get("approved_by", "David Ross (IBM Project Manager)")

            inv = RUNTIME.get_invoice_by_id(inv_id)
            if not inv:
                return self._send_json(404, {"error": f"Invoice {inv_id} not found."})

            new_gr = GoodsServicesReceipt(
                receipt_id=f"GR-{datetime.utcnow().strftime('%M%S%f')[:8]}",
                po_number=po_number,
                po_line_num=po_line_num,
                received_qty=delivered_qty,
                received_amount=delivered_qty * 170.0,
                receipt_date=datetime.utcnow().date(),
                signed_off_by=approved_by,
                approval_status="APPROVED",
                comments="Late project manager sign-off approved via interactive console."
            )

            # Register in SAP mock and SQLite DB
            RUNTIME.erp.add_receipt(new_gr)
            RUNTIME.db.add_receipt({
                "receipt_id": new_gr.receipt_id,
                "po_number": po_number,
                "po_line_num": po_line_num,
                "delivered_qty": delivered_qty,
                "approved_by": approved_by,
                "status": "APPROVED",
                "received_date": new_gr.receipt_date.isoformat()
            })

            # Re-run matching on the invoice to transition from MISSING_GR to AUTO_APPROVE!
            result = RUNTIME.orchestrator.process_invoice(inv)
            RUNTIME.matching_results[inv_id] = result
            RUNTIME.db.update_invoice_status(inv_id, result.overall_status.value, result.confidence_score)

            RUNTIME.db.log_audit(
                entity_id=inv_id,
                event_type="GOODS_RECEIPT_APPROVED",
                agent_name="ProjectManagerHITL",
                details=f"Receipt {new_gr.receipt_id} recorded for line {po_line_num}. 3-Way Match re-evaluated."
            )

            return self._send_json(200, {
                "success": True,
                "receipt_id": new_gr.receipt_id,
                "new_match_status": result.overall_status.value,
                "matching_result": result.model_dump(),
                "message": f"Goods Receipt {new_gr.receipt_id} approved. Invoice {inv_id} re-matched and cleared for payment!"
            })

        # POST /api/settings/gemini-key
        if path == "/api/settings/gemini-key":
            api_key = payload.get("api_key", "").strip()
            if api_key:
                RUNTIME.gemini_reasoner.set_api_key(api_key)
                return self._send_json(200, {
                    "success": True,
                    "message": "Gemini API Key activated for live cloud reasoning.",
                    "live": RUNTIME.gemini_reasoner.is_live(),
                    "model": RUNTIME.gemini_reasoner.DEFAULT_MODEL
                })
            return self._send_json(400, {"error": "API key cannot be empty."})

        # POST /api/invoices/custom
        if path == "/api/invoices/custom":
            from .models.invoice import Invoice, InvoiceLineItem
            from datetime import date
            inv_id = f"INV-CUSTOM-{datetime.utcnow().strftime('%M%S')}"
            inv_amount = float(payload.get("total_amount", 8500.0))
            inv_rate = float(payload.get("unit_price", 170.0))
            inv_qty = float(payload.get("quantity", 50.0))
            vendor = payload.get("vendor_name", "Quantum Solutions Ltd")
            role = payload.get("role_title", "Senior Infrastructure Consultant Tier 1")

            inv_data = Invoice(
                invoice_id=inv_id,
                vendor_id=payload.get("vendor_id", "VEND-CUSTOM-99"),
                vendor_name=vendor,
                po_number=payload.get("po_number", "PO-45009812"),
                invoice_date=date.today(),
                due_date=date.today(),
                currency="USD",
                subtotal=inv_amount,
                tax_amount=float(payload.get("tax_amount", 0.0)),
                total_amount=inv_amount,
                line_items=[
                    InvoiceLineItem(
                        item_id="LINE-01",
                        description=f"{role} consulting engagement",
                        role_title=role,
                        quantity=inv_qty,
                        unit="HOURS",
                        unit_price=inv_rate,
                        total_amount=inv_amount
                    )
                ]
            )
            RUNTIME.invoices.append(inv_data)
            result = RUNTIME.orchestrator.process_invoice(inv_data)
            RUNTIME.matching_results[inv_id] = result
            RUNTIME.db.upsert_invoice({
                "invoice_id": inv_id,
                "vendor_id": inv_data.vendor_id,
                "vendor_name": inv_data.vendor_name,
                "po_number": inv_data.po_number,
                "invoice_date": inv_data.invoice_date.isoformat(),
                "total_amount": inv_data.total_amount,
                "tax_amount": inv_data.tax_amount,
                "currency": "USD",
                "status": result.overall_status.value,
                "confidence_score": result.confidence_score
            })
            gemini_analysis = RUNTIME.gemini_reasoner.analyze_invoice_matching(
                invoice_data=inv_data.model_dump(),
                contract_data={"contract_id": "SOW-IBM-2025-09", "clauses": ["Section 4.2", "Section 5.1", "Section 7.3"]},
                erp_data={"po_number": inv_data.po_number, "status": "OPEN"},
                preliminary_match=result.model_dump()
            )
            return self._send_json(200, {
                "success": True,
                "invoice": inv_data.model_dump(),
                "matching_result": result.model_dump(),
                "gemini_analysis": gemini_analysis
            })

        # POST /api/data/generate-synthetic
        if path == "/api/data/generate-synthetic":
            count = int(payload.get("count", 5))
            scenario_keys = payload.get("scenario_keys")
            batch = SyntheticDataGenerator.generate_batch(count=count, scenario_keys=scenario_keys)
            processed = RUNTIME.ingest_invoices(batch)
            return self._send_json(200, {
                "success": True,
                "message": f"Synthesized and verified {len(batch)} enterprise AP invoices.",
                "count": len(batch),
                "invoices": [p["invoice"] for p in processed],
                "results": [p["matching_result"] for p in processed]
            })

        # POST /api/data/upload
        if path == "/api/data/upload":
            raw_content = payload.get("content")
            new_invoices: List[Invoice] = []

            # 1. Direct array of invoice dicts
            if "invoices" in payload and isinstance(payload["invoices"], list):
                for item in payload["invoices"]:
                    if isinstance(item.get("invoice_date"), str):
                        item["invoice_date"] = date.fromisoformat(item["invoice_date"].split("T")[0])
                    if isinstance(item.get("due_date"), str):
                        item["due_date"] = date.fromisoformat(item["due_date"].split("T")[0])
                    new_invoices.append(Invoice(**item))

            # 2. CSV string in csv_data field
            elif isinstance(payload.get("csv_data"), str):
                new_invoices = SyntheticDataGenerator.from_csv(payload["csv_data"])

            # 3. Raw text content (JSON or CSV)
            elif isinstance(raw_content, str):
                trimmed = raw_content.strip()
                if trimmed.startswith("[") or trimmed.startswith("{"):
                    new_invoices = SyntheticDataGenerator.from_json(trimmed)
                else:
                    new_invoices = SyntheticDataGenerator.from_csv(trimmed)

            if not new_invoices:
                return self._send_json(400, {
                    "error": "No valid invoice records could be parsed. Provide valid JSON array or CSV text."
                })

            processed = RUNTIME.ingest_invoices(new_invoices)
            return self._send_json(200, {
                "success": True,
                "message": f"Successfully ingested and 3-way matched {len(new_invoices)} invoices.",
                "count": len(new_invoices),
                "invoices": [p["invoice"] for p in processed],
                "results": [p["matching_result"] for p in processed]
            })

        return self._send_json(404, {"error": f"Endpoint {path} not found."})


def run_server(port: Optional[int] = None):
    target_port = port
    if target_port is None:
        if len(sys.argv) > 1:
            for i, arg in enumerate(sys.argv[1:], start=1):
                if arg.isdigit():
                    target_port = int(arg)
                    break
                elif arg.startswith("--port="):
                    target_port = int(arg.split("=", 1)[1])
                    break
                elif arg in ("--port", "-p") and i < len(sys.argv) - 1 and sys.argv[i + 1].isdigit():
                    target_port = int(sys.argv[i + 1])
                    break
        if target_port is None:
            target_port = int(os.environ.get("PORT", PORT))

    print(f"\n========================================================")
    print(f"  IBM // FIN_OS (R) — AUTONOMOUS FINANCIAL RUNTIME v2.0")
    print(f"  Payment Rails: ACH NACHA (94-col) & ISO 20022 pain.001 XML")
    print(f"  Persistence: SQLite ACID-Compliant Database")
    print(f"  Frontend Directory: {FRONTEND_DIR}")
    print(f"  Local URL: http://localhost:{target_port}")
    print(f"========================================================\n")

    server_address = ("", target_port)
    httpd = HTTPServer(server_address, FinancialAppHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
