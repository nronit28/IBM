"""
Integration tests for Financial Runtime REST API endpoints.
"""

import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from http.server import HTTPServer
from src.invoice_matcher.server import FinancialAppHandler


def make_request(path: str, method: str = "GET", payload: dict = None):
    url = f"http://localhost:8080{path}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content)
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"error": content}


class TestAPIEndpoints(unittest.TestCase):
    _server_thread = None
    _httpd = None

    @classmethod
    def setUpClass(cls):
        try:
            with urllib.request.urlopen("http://localhost:8080/api/status", timeout=1) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass

        try:
            cls._httpd = HTTPServer(("", 8080), FinancialAppHandler)
            cls._server_thread = threading.Thread(target=cls._httpd.serve_forever, daemon=True)
            cls._server_thread.start()
            time.sleep(0.5)
        except Exception as e:
            raise unittest.SkipTest(f"Cannot start local test server: {e}")

    @classmethod
    def tearDownClass(cls):
        if cls._httpd:
            cls._httpd.shutdown()
            cls._httpd.server_close()

    def test_api_status(self):
        status_code, body = make_request("/api/status")
        self.assertEqual(status_code, 200)
        self.assertEqual(body["system"], "IBM // FIN_OS (R)")
        self.assertIn("ACH_NACHA_94COL", body["rails"])
        self.assertIn("ISO20022_PAIN001_09", body["rails"])

    def test_api_invoices_list(self):
        status_code, body = make_request("/api/invoices")
        self.assertEqual(status_code, 200)
        self.assertIn("invoices", body)
        self.assertGreaterEqual(len(body["invoices"]), 5)

    def test_api_match_invoice(self):
        status_code, body = make_request("/api/match", method="POST", payload={"invoice_id": "INV-2026-001"})
        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["matching_result"]["overall_status"], "PERFECT_MATCH")

    def test_api_dispute_action(self):
        status_code, body = make_request("/api/action/dispute", method="POST", payload={
            "invoice_id": "INV-2026-002",
            "reason": "Contractual Rate Variance of +$25.00/hr",
            "memo": "Please reissue invoice reflecting SOW rate of $170.00/hr."
        })
        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["status"], "DISPUTE_DISPATCHED")

    def test_api_goods_receipt_action(self):
        status_code, body = make_request("/api/action/approve-receipt", method="POST", payload={
            "invoice_id": "INV-2026-004",
            "po_number": "PO-45009812",
            "po_line_num": 30,
            "delivered_qty": 60.0,
            "approved_by": "David Ross (IBM Project Manager)"
        })
        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["new_match_status"], "PERFECT_MATCH")


if __name__ == "__main__":
    unittest.main()
