"""
Local Web Server for IBM Financial Solutions Frontend.
Serves the Nothing-inspired retro-futuristic web app on http://localhost:8080
"""

import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Paths
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
PORT = 8080


class FinancialAppHandler(SimpleHTTPRequestHandler):
    """Serves frontend static assets and provides API hooks to the agent pipeline."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            status_data = {
                "system": "IBM // FIN_OS (R)",
                "status": "ONLINE",
                "agents": ["Normalizer", "ContractValidator_RAG", "ERPAction_SAP", "ResolutionAgent"],
                "version": "1.10.0"
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        return super().do_GET()


def run_server():
    print(f"\n========================================================")
    print(f"  IBM // FIN_OS (R) — AUTONOMOUS FINANCIAL RUNTIME")
    print(f"  Frontend Directory: {FRONTEND_DIR}")
    print(f"  Local URL: http://localhost:{PORT}")
    print(f"========================================================\n")

    server_address = ("", PORT)
    httpd = HTTPServer(server_address, FinancialAppHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
