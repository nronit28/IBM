"""
SQLite Persistence Layer for IBM AP 3-Way Matching and Payment Processing.
Provides ACID-compliant storage for Invoices, POs, Receipts, Disbursements, and Audit Trails.
"""

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


DB_PATH = Path(__file__).resolve().parent / "ap_finance.db"


class APDatabaseService:
    """Manages transactional database operations for the AP matching and payment pipeline."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initializes tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Invoices Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    invoice_id TEXT PRIMARY KEY,
                    vendor_id TEXT NOT NULL,
                    vendor_name TEXT NOT NULL,
                    po_number TEXT NOT NULL,
                    invoice_date TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    tax_amount REAL NOT NULL DEFAULT 0.0,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    status TEXT NOT NULL DEFAULT 'RECEIVED',
                    confidence_score REAL DEFAULT 0.0,
                    raw_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Purchase Orders Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    po_number TEXT PRIMARY KEY,
                    vendor_id TEXT NOT NULL,
                    vendor_name TEXT NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    total_committed REAL NOT NULL,
                    remaining_balance REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'OPEN'
                )
            """)

            # PO Line Items Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS po_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_number TEXT NOT NULL,
                    line_num INTEGER NOT NULL,
                    role_title TEXT,
                    description TEXT NOT NULL,
                    hourly_rate REAL NOT NULL,
                    committed_qty REAL NOT NULL,
                    invoiced_qty REAL NOT NULL DEFAULT 0.0,
                    invoiced_amount REAL NOT NULL DEFAULT 0.0,
                    milestone_code TEXT,
                    FOREIGN KEY (po_number) REFERENCES purchase_orders (po_number),
                    UNIQUE (po_number, line_num)
                )
            """)

            # Goods / Services Receipts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goods_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    po_number TEXT NOT NULL,
                    po_line_num INTEGER,
                    milestone_code TEXT,
                    delivered_qty REAL NOT NULL,
                    approved_by TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'APPROVED',
                    received_date TEXT NOT NULL
                )
            """)

            # Disbursements / Payments Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disbursements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_ref TEXT UNIQUE NOT NULL,
                    invoice_id TEXT NOT NULL,
                    vendor_id TEXT NOT NULL,
                    vendor_name TEXT NOT NULL,
                    po_number TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    rail TEXT NOT NULL, -- 'ACH' or 'ISO20022'
                    status TEXT NOT NULL, -- 'CLEARED', 'PENDING_APPROVAL', 'FAILED'
                    idempotency_key TEXT UNIQUE NOT NULL,
                    trace_number TEXT NOT NULL,
                    nacha_payload TEXT,
                    iso20022_xml TEXT,
                    dual_custody_required INTEGER NOT NULL DEFAULT 0,
                    authorized_by TEXT,
                    disbursed_at TEXT NOT NULL,
                    FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id)
                )
            """)

            # Disputes Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disputes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id TEXT NOT NULL,
                    vendor_id TEXT NOT NULL,
                    discrepancy_amount REAL NOT NULL,
                    reason TEXT NOT NULL,
                    memo TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'DISPATCHED',
                    dispatched_at TEXT NOT NULL
                )
            """)

            # Audit Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    details TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)

            conn.commit()

    # --- INVOICE OPERATIONS ---

    def upsert_invoice(self, invoice_data: Dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_id, vendor_id, vendor_name, po_number, invoice_date,
                    total_amount, tax_amount, currency, status, confidence_score,
                    raw_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(invoice_id) DO UPDATE SET
                    status=excluded.status,
                    confidence_score=excluded.confidence_score,
                    updated_at=excluded.updated_at
            """, (
                invoice_data["invoice_id"],
                invoice_data["vendor_id"],
                invoice_data["vendor_name"],
                invoice_data["po_number"],
                invoice_data.get("invoice_date", now[:10]),
                invoice_data["total_amount"],
                invoice_data.get("tax_amount", 0.0),
                invoice_data.get("currency", "USD"),
                invoice_data.get("status", "RECEIVED"),
                invoice_data.get("confidence_score", 0.0),
                json.dumps(invoice_data),
                now,
                now
            ))
            conn.commit()

    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_invoices(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices ORDER BY invoice_id ASC")
            return [dict(row) for row in cursor.fetchall()]

    def update_invoice_status(self, invoice_id: str, status: str, confidence_score: Optional[float] = None) -> None:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if confidence_score is not None:
                cursor.execute("""
                    UPDATE invoices SET status = ?, confidence_score = ?, updated_at = ? WHERE invoice_id = ?
                """, (status, confidence_score, now, invoice_id))
            else:
                cursor.execute("""
                    UPDATE invoices SET status = ?, updated_at = ? WHERE invoice_id = ?
                """, (status, now, invoice_id))
            conn.commit()

    # --- PURCHASE ORDER OPERATIONS ---

    def upsert_po(self, po_data: Dict[str, Any]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO purchase_orders (
                    po_number, vendor_id, vendor_name, currency, total_committed, remaining_balance, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(po_number) DO UPDATE SET
                    remaining_balance=excluded.remaining_balance,
                    status=excluded.status
            """, (
                po_data["po_number"],
                po_data["vendor_id"],
                po_data["vendor_name"],
                po_data.get("currency", "USD"),
                po_data["total_committed"],
                po_data["remaining_balance"],
                po_data.get("status", "OPEN")
            ))

            for line in po_data.get("lines", []):
                cursor.execute("""
                    INSERT INTO po_lines (
                        po_number, line_num, role_title, description, hourly_rate, committed_qty, invoiced_qty, invoiced_amount, milestone_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(po_number, line_num) DO UPDATE SET
                        invoiced_qty=excluded.invoiced_qty,
                        invoiced_amount=excluded.invoiced_amount
                """, (
                    po_data["po_number"],
                    line["line_num"],
                    line.get("role_title"),
                    line["description"],
                    line["hourly_rate"],
                    line["committed_qty"],
                    line.get("invoiced_qty", 0.0),
                    line.get("invoiced_amount", 0.0),
                    line.get("milestone_code")
                ))
            conn.commit()

    def get_po(self, po_number: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM purchase_orders WHERE po_number = ?", (po_number,))
            po_row = cursor.fetchone()
            if not po_row:
                return None
            po = dict(po_row)
            cursor.execute("SELECT * FROM po_lines WHERE po_number = ? ORDER BY line_num ASC", (po_number,))
            po["lines"] = [dict(r) for r in cursor.fetchall()]
            return po

    def deduct_po_balance(self, po_number: str, line_num: int, invoiced_qty: float, invoiced_amount: float) -> bool:
        """Deducts remaining committed balance and records cleared invoice amount on a PO line."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT remaining_balance FROM purchase_orders WHERE po_number = ?", (po_number,))
            po = cursor.fetchone()
            if not po:
                return False

            new_balance = max(0.0, po["remaining_balance"] - invoiced_amount)
            cursor.execute("""
                UPDATE purchase_orders SET remaining_balance = ? WHERE po_number = ?
            """, (new_balance, po_number))

            cursor.execute("""
                UPDATE po_lines
                SET invoiced_qty = invoiced_qty + ?, invoiced_amount = invoiced_amount + ?
                WHERE po_number = ? AND line_num = ?
            """, (invoiced_qty, invoiced_amount, po_number, line_num))

            conn.commit()
            return True

    # --- GOODS RECEIPTS OPERATIONS ---

    def add_receipt(self, receipt_data: Dict[str, Any]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO goods_receipts (
                    receipt_id, po_number, po_line_num, milestone_code, delivered_qty, approved_by, status, received_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                receipt_data["receipt_id"],
                receipt_data["po_number"],
                receipt_data.get("po_line_num"),
                receipt_data.get("milestone_code"),
                receipt_data["delivered_qty"],
                receipt_data["approved_by"],
                receipt_data.get("status", "APPROVED"),
                receipt_data.get("received_date", datetime.utcnow().strftime("%Y-%m-%d"))
            ))
            conn.commit()

    def get_receipts_by_po(self, po_number: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM goods_receipts WHERE po_number = ?", (po_number,))
            return [dict(r) for r in cursor.fetchall()]

    # --- DISBURSEMENTS OPERATIONS ---

    def get_disbursement_by_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM disbursements WHERE idempotency_key = ?", (idempotency_key,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_disbursement_by_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM disbursements WHERE invoice_id = ? ORDER BY id DESC LIMIT 1", (invoice_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def record_disbursement(self, data: Dict[str, Any]) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO disbursements (
                    payment_ref, invoice_id, vendor_id, vendor_name, po_number,
                    amount, currency, rail, status, idempotency_key, trace_number,
                    nacha_payload, iso20022_xml, dual_custody_required, authorized_by, disbursed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                    payment_ref=excluded.payment_ref,
                    status=excluded.status,
                    authorized_by=excluded.authorized_by,
                    nacha_payload=excluded.nacha_payload,
                    iso20022_xml=excluded.iso20022_xml,
                    disbursed_at=excluded.disbursed_at
            """, (
                data["payment_ref"],
                data["invoice_id"],
                data["vendor_id"],
                data["vendor_name"],
                data["po_number"],
                data["amount"],
                data.get("currency", "USD"),
                data["rail"],
                data["status"],
                data["idempotency_key"],
                data["trace_number"],
                data.get("nacha_payload"),
                data.get("iso20022_xml"),
                1 if data.get("dual_custody_required") else 0,
                data.get("authorized_by"),
                data.get("disbursed_at", datetime.utcnow().isoformat())
            ))
            payment_id = cursor.lastrowid
            return payment_id

    # --- DISPUTES OPERATIONS ---

    def record_dispute(self, invoice_id: str, vendor_id: str, discrepancy_amount: float, reason: str, memo: str) -> int:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO disputes (invoice_id, vendor_id, discrepancy_amount, reason, memo, status, dispatched_at)
                VALUES (?, ?, ?, ?, ?, 'DISPATCHED', ?)
            """, (invoice_id, vendor_id, discrepancy_amount, reason, memo, now))
            dispute_id = cursor.lastrowid

            cursor.execute("""
                UPDATE invoices SET status = 'DISPUTE_DISPATCHED', updated_at = ? WHERE invoice_id = ?
            """, (now, invoice_id))

            conn.commit()
            return dispute_id

    # --- AUDIT LOGS ---

    def log_audit(self, entity_id: str, event_type: str, agent_name: str, details: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (entity_id, event_type, agent_name, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (entity_id, event_type, agent_name, details, now))
            conn.commit()

    def get_audit_trail(self, entity_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM audit_logs WHERE entity_id = ? ORDER BY id ASC
            """, (entity_id,))
            return [dict(r) for r in cursor.fetchall()]

    def seed_demo_environment(self, erp_connector: Any, invoices: List[Any]) -> None:
        """Seeds SQLite database from the SAP mock and demo invoices."""
        for po_num, po in erp_connector.purchase_orders.items():
            po_data = {
                "po_number": po.po_number,
                "vendor_id": po.vendor_id,
                "vendor_name": "RedPillar Cloud Solutions LLC",
                "currency": po.currency,
                "total_committed": po.total_value,
                "remaining_balance": po.total_value,
                "status": po.status,
                "lines": [
                    {
                        "line_num": l.line_num,
                        "role_title": l.role_title,
                        "description": l.description,
                        "hourly_rate": l.unit_price,
                        "committed_qty": l.ordered_qty,
                        "invoiced_qty": l.invoiced_qty,
                        "invoiced_amount": l.invoiced_amount,
                        "milestone_code": l.milestone_code
                    }
                    for l in po.line_items
                ]
            }
            self.upsert_po(po_data)

        for po_num, receipts in erp_connector.receipts_by_po.items():
            for r in receipts:
                self.add_receipt({
                    "receipt_id": r.receipt_id,
                    "po_number": r.po_number,
                    "po_line_num": r.po_line_num,
                    "milestone_code": r.milestone_code,
                    "delivered_qty": r.received_qty,
                    "approved_by": r.signed_off_by,
                    "status": r.approval_status,
                    "received_date": r.receipt_date.isoformat()
                })

        for inv in invoices:
            self.upsert_invoice({
                "invoice_id": inv.invoice_id,
                "vendor_id": inv.vendor_id,
                "vendor_name": inv.vendor_name,
                "po_number": inv.po_number,
                "invoice_date": inv.invoice_date.isoformat(),
                "total_amount": inv.total_amount,
                "tax_amount": inv.tax_amount,
                "currency": inv.currency,
                "status": "RECEIVED",
                "confidence_score": 0.0
            })

