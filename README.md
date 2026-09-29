# IBM // FIN_OS (R) — Autonomous Invoice Exception Handling & 3-Way Matching

An enterprise-grade, multi-agent financial runtime for automated invoice exception handling, contract grounding via RAG, and autonomous 3-way matching (Invoice vs. PO vs. Goods/Services Receipt vs. Master Services Agreement).

---

## 🚀 Key Capabilities

- **Autonomous 3-Way Matching**: Cross-correlates Invoices, Purchase Orders (POs), and Goods/Services Receipts (GRs) with real-time discrepancy detection.
- **RAG Contract Grounding**: Retrieves exact contractual terms, volume discounts, maximum allowable rates, and SLA clauses from Master Services Agreements (MSAs).
- **Multi-Agent Architecture**:
  - `NormalizerAgent`: Standardizes raw incoming invoices, handles OCR line-item mapping, and reconciles line items with PO lines.
  - `ValidatorAgent`: Vector-similarity contract clause lookup and rate/tolerance verification.
  - `ERPAgent`: SAP S/4HANA BAPI simulation for PO validation, goods receipts clearance, and ledger hold management.
  - `ResolutionAgent`: Determines automated remediation (straight-through payment, line-item price adjust, deduction debit memo, or human clerk escalation).
  - `APOrchestrator`: Coordinates the full exception resolution lifecycle and generates audit dossiers.
- **Retro-Futuristic Frontend**: Interactive Nothing-inspired web dashboard for real-time scenario simulation, telemetry, and terminal audits.

---

## 📂 Project Structure

```
├── frontend/                # Interactive web dashboard & live terminal
│   ├── assets/              # Static media assets
│   ├── css/style.css        # Retro-futuristic dark mode styles
│   ├── js/                  # App logic & scenario definitions
│   └── index.html           # Main UI interface
├── src/
│   └── invoice_matcher/     # Core Python agent package
│       ├── agents/          # Multi-agent orchestrators & specialists
│       ├── demo_data/       # Enterprise scenario datasets (10 test cases)
│       ├── erp_service/     # SAP S/4HANA mock service
│       ├── models/          # Pydantic data schemas (Invoice, PO, Contract, Match)
│       ├── rag/             # Vector indexing and clause retrieval
│       ├── main.py          # CLI runner
│       └── server.py        # Local HTTP server for the frontend
├── tests/                   # End-to-end and unit test suites
└── README.md
```

---

## ⚡ Quickstart

### 1. Run the CLI Simulation

Run all 10 AP edge-case scenarios through the autonomous agent pipeline:

```bash
python -m src.invoice_matcher.main --all
```

Or run a specific scenario (e.g., rate discrepancy resolution):

```bash
python -m src.invoice_matcher.main --scenario S03
```

### 2. Frontend Build & Web Dashboard

Install dependencies and build the production bundle:

```bash
npm install
npm run build
```

Start the local server (auto-detects and serves the optimized `dist/` bundle):

```bash
python -m src.invoice_matcher.server
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

For hot-reloading frontend development:

```bash
npm run dev
```

### 3. Run the Test Suite

```bash
python -m unittest discover tests
```

---

## 🧪 Scenarios Covered

1. **S01 — Perfect Clean Match**: 100% matched rates, PO, and goods receipt approved (Straight-Through Processing).
2. **S02 — Unrecorded Overtime**: Overtime billed without pre-authorization rider (Hold & Dispute).
3. **S03 — Rate Variance / MSA Discrepancy**: Billed rate exceeds contract cap; autonomous deduction memo issued.
4. **S04 — Unapproved Goods Receipt**: Invoice arrived prior to warehouse receipt verification (Auto-deferred).
5. **S05 — Quantity Overrun**: Quantity exceeds authorized purchase order ceiling.
6. **S06 — Volume Discount Omission**: Vendor failed to apply tiered rebate; system calculates correct deduction.
7. **S07 — Duplicate Billing**: Multiple invoices referencing identical deliverables and dates.
8. **S08 — Currency & Exchange Variance**: Cross-border foreign currency fluctuation beyond contractual tolerance.
9. **S09 — Milestone Dependency Failure**: Phase 2 billed prior to Phase 1 sign-off.
10. **S10 — Expired MSA**: Invoiced work delivered after contract expiration without extension addendum.

---

## 🛡️ License

Internal IBM & Academic Use.
