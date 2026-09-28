/**
 * Embedded IBM Financial Scenarios Data
 * Provides instant standalone offline execution for the interactive web terminal.
 */

const SCENARIOS = [
  {
    id: 1,
    code: "SCN-01",
    title: "Clean 3-Way Match (Milestone Deliverable)",
    subtitle: "Cloud Migration Phase 3 Cutover ($45,000.00)",
    category: "Accounts Payable",
    status: "PERFECT_MATCH",
    actionType: "AUTO_APPROVE",
    badgeColor: "success",
    confidence: "99.4%",
    invoiceId: "INV-2026-001",
    vendorName: "RedPillar Cloud Solutions LLC",
    vendorId: "VEND-IBM-8841",
    poNumber: "PO-45009812",
    amount: "$45,000.00",
    allowable: "$45,000.00",
    discrepancy: "$0.00",
    description: "Milestone MS-03 deliverable billed exactly per signed SOW schedule with corresponding PO commitment and verified SAP Goods/Services Receipt (SES).",
    lineItems: [
      {
        line: "01",
        desc: "Cloud Migration Phase 3 - DB Cutover & Hardening (MS-03)",
        qty: "1.0",
        unit: "MILESTONE",
        billedRate: "$45,000.00",
        contractMax: "$45,000.00",
        variance: "$0.00",
        grStatus: "APPROVED (GR-50001923)",
        status: "PERFECT_MATCH"
      }
    ],
    citations: [
      "SOW-IBM-2025-09 Milestone Schedule: MS-03 - Database Cutover & Hardening ($45,000.00)",
      "SAP S/4HANA PO-45009812 Line 10: Approved Delivery Receipt signed by Sarah Chen (IBM Delivery Director)"
    ],
    communication: `SYSTEM POSTING MEMORANDUM
Invoice: INV-2026-001 | Vendor: RedPillar Cloud Solutions LLC (VEND-IBM-8841)
PO: PO-45009812 | Amount: $45,000.00 USD
Status: VERIFIED 3-WAY MATCH. Ready for automated payment run on 2026-03-14.
AP Ledger Action: Cleared and scheduled for automated ACH disbursement.`,
    agentLogs: [
      "[09:30:01] NormalizerAgent: Ingested invoice INV-2026-001 from 'RedPillar Cloud Solutions LLC'.",
      "[09:30:02] ContractValidatorAgent (RAG): Retrieved SOW-IBM-2025-09. Milestone MS-03 matched with 100% confidence.",
      "[09:30:03] ERPAgent (SAP S/4HANA): Found open PO PO-45009812 Line 10. Verified Goods Receipt GR-50001923.",
      "[09:30:04] ResolutionAgent: Confidence score 0.99. No variance detected. Auto-posting clearance memo to AP ledger."
    ]
  },
  {
    id: 2,
    code: "SCN-02",
    title: "Semantic Role Mismatch (Resolved by RAG)",
    subtitle: "Lead Cloud DevOps Architect Consulting ($6,800.00)",
    category: "Contract Compliance",
    status: "PERFECT_MATCH",
    actionType: "AUTO_APPROVE",
    badgeColor: "success",
    confidence: "98.2%",
    invoiceId: "INV-2026-002",
    vendorName: "RedPillar Cloud Solutions LLC",
    vendorId: "VEND-IBM-8841",
    poNumber: "PO-45009812",
    amount: "$6,800.00",
    allowable: "$6,800.00",
    discrepancy: "$0.00",
    description: "Invoice uses informal role title 'Lead Cloud DevOps Architect' (40 hrs @ $170/hr). Traditional ERPs fail; RAG semantically aligns this with SOW contracted role 'Senior Infrastructure Consultant Tier 1' and confirms 3-way match.",
    lineItems: [
      {
        line: "01",
        desc: "Lead Cloud DevOps Architect sprint consulting (Sprint 12)",
        qty: "40.0",
        unit: "HOURS",
        billedRate: "$170.00/hr",
        contractMax: "$170.00/hr",
        variance: "$0.00",
        grStatus: "APPROVED (GR-50001924)",
        status: "PERFECT_MATCH"
      }
    ],
    citations: [
      "Schedule A Rate Card: 'Senior Infrastructure Consultant Tier 1' aliases include 'Lead Cloud DevOps Architect'",
      "SAP S/4HANA PO-45009812 Line 20: 80 hrs approved in GR-50001924 by David Ross (IBM Project Manager)"
    ],
    communication: `SYSTEM POSTING MEMORANDUM (SEMANTIC ALIGNMENT)
Invoice: INV-2026-002 | Vendor: RedPillar Cloud Solutions LLC
Role Grounding: 'Lead Cloud DevOps Architect' -> 'Senior Infrastructure Consultant Tier 1' (Confidence 0.98)
Billed Rate: $170.00/hr (Permissible under SOW Rate Schedule).
Status: 3-Way Match Verified. Scheduled for automated payment clearing.`,
    agentLogs: [
      "[09:30:01] NormalizerAgent: Normalized line LINE-01 role description 'Lead Cloud DevOps Architect'.",
      "[09:30:02] ContractValidatorAgent (RAG): Semantic embedding match mapped 'Lead Cloud DevOps Architect' to SOW role 'Senior Infrastructure Consultant Tier 1' (Score: 0.98).",
      "[09:30:03] ERPAgent: Querying PO Line 20 with canonical role 'Senior Infrastructure Consultant Tier 1'. Found 80 approved hours.",
      "[09:30:04] ResolutionAgent: Invoiced rate ($170/hr) matches SOW ceiling. Auto-approved without human clerk intervention."
    ]
  },
  {
    id: 3,
    code: "SCN-03",
    title: "Uncontracted Rate Bump Exception",
    subtitle: "Billed at $195/hr vs $170/hr SOW Cap ($1,250 Overcharge)",
    category: "Dispute Resolution",
    status: "EXCEPTION_RATE_VARIANCE",
    actionType: "DRAFT_VENDOR_INQUIRY",
    badgeColor: "danger",
    confidence: "95.0%",
    invoiceId: "INV-2026-003",
    vendorName: "RedPillar Cloud Solutions LLC",
    vendorId: "VEND-IBM-8841",
    poNumber: "PO-45009812",
    amount: "$9,750.00",
    allowable: "$8,500.00",
    discrepancy: "$1,250.00",
    description: "Vendor billed 50 hours at $195.00/hr instead of the agreed $170.00/hr rate cap. RAG flags Section 4.2 of the Master Agreement and autonomously synthesizes an audit-ready dispute letter requesting a $1,250 credit memo.",
    lineItems: [
      {
        line: "01",
        desc: "Senior Infrastructure Consultant Tier 1 - Cloud Architecture Advisory",
        qty: "50.0",
        unit: "HOURS",
        billedRate: "$195.00/hr",
        contractMax: "$170.00/hr",
        variance: "+$1,250.00",
        grStatus: "APPROVED (GR-50001924)",
        status: "EXCEPTION_RATE_VARIANCE"
      }
    ],
    citations: [
      "Master Services Agreement Section 4.2 (Rate Card Enforceability): Rates exceeding Schedule A are non-payable.",
      "Schedule A Rate Card: 'Senior Infrastructure Consultant Tier 1' cap is $170.00/hr."
    ],
    communication: `Subject: Formal Discrepancy Notice: Invoice INV-2026-003 (PO PO-45009812)

Dear RedPillar Cloud Solutions LLC Accounts Receivable Team,

IBM Accounts Payable has completed automated 3-way contract validation for invoice INV-2026-003. During review against governing agreement (PO PO-45009812 / SOW Rate Card), the following rate discrepancy was identified:

 - Line LINE-01 (Senior Infrastructure Consultant Tier 1): Invoiced Rate = $195.00/hr | Contract SOW Cap = $170.00/hr | Overcharge = $1,250.00

Total Discrepancy: $1,250.00 USD.

Pursuant to Schedule A (Rate Card) of our Master Agreement, billable rates are capped at the contracted maximum. Please issue a revised invoice for the allowable amount of $8,500.00 or provide a credit memo for $1,250.00.

Sincerely,
IBM Global Accounts Payable Automation`,
    agentLogs: [
      "[09:30:01] NormalizerAgent: Parsed line item: 50.0 hours @ $195.00/hr.",
      "[09:30:02] ContractValidatorAgent (RAG): SOW Rate Card look-up returned cap of $170.00/hr. Excess of $25.00/hr detected.",
      "[09:30:03] ContractValidatorAgent (RAG): Retrieved Section 4.2 clause on rate dispute penalties.",
      "[09:30:04] ResolutionAgent: Overcharge $1,250.00 exceeds $25 tolerance. Generated formal dispute email to vendor."
    ]
  },
  {
    id: 4,
    code: "SCN-04",
    title: "Missing Goods/Services Receipt (GR/SR)",
    subtitle: "Data Pipeline Consulting ($8,700.00 Awaiting PM Sign-Off)",
    category: "Procurement Workflow",
    status: "EXCEPTION_MISSING_GR",
    actionType: "REQUEST_INTERNAL_SIGN_OFF",
    badgeColor: "warning",
    confidence: "92.0%",
    invoiceId: "INV-2026-004",
    vendorName: "RedPillar Cloud Solutions LLC",
    vendorId: "VEND-IBM-8841",
    poNumber: "PO-45009812",
    amount: "$8,700.00",
    allowable: "$8,700.00",
    discrepancy: "$0.00 (Pending GR)",
    description: "Invoiced consulting hours comply with SOW rate cards ($145/hr x 60 hrs), but no delivery sign-off (Service Entry Sheet) has been logged in SAP S/4HANA. The agent automatically alerts the internal IBM Project Manager.",
    lineItems: [
      {
        line: "01",
        desc: "Data Integration Specialist Consulting (T&M) - Pipeline migration",
        qty: "60.0",
        unit: "HOURS",
        billedRate: "$145.00/hr",
        contractMax: "$145.00/hr",
        variance: "$0.00",
        grStatus: "MISSING IN SAP",
        status: "EXCEPTION_MISSING_GR"
      }
    ],
    citations: [
      "Master Agreement Section 5.1: Mandatory Goods/Services Receipt required prior to payment release.",
      "SAP S/4HANA PO-45009812 Line 30: Remaining balance $14,500.00 (GR count: 0)."
    ],
    communication: `Subject: ACTION REQUIRED: Delivery Receipt Missing for Vendor Invoice INV-2026-004

Hello David Ross (IBM Global Procurement),

Vendor RedPillar Cloud Solutions LLC has submitted invoice INV-2026-004 for $8,700.00 against PO PO-45009812.

Our automated 3-way matching system verified that the billed line items comply with contracted SOW rate cards, but NO Goods/Services Receipt (GR/SR - SES) has been recorded in SAP S/4HANA by the project team.

Please confirm delivery in SAP or reply to this notice to release payment.

IBM AP Operations`,
    agentLogs: [
      "[09:30:01] NormalizerAgent: Verified line items and rates ($145/hr).",
      "[09:30:02] ContractValidatorAgent (RAG): Rates verified against Data Integration Specialist rate card.",
      "[09:30:03] ERPAgent: SAP S/4HANA query returned PO Line 30. Zero Goods Receipts found.",
      "[09:30:04] ResolutionAgent: Triggered internal notification to Buyer David Ross to confirm delivery."
    ]
  },
  {
    id: 5,
    code: "SCN-05",
    title: "Minor Tax Rounding Tolerance",
    subtitle: "Cloud Phase 4 Milestone ($8.50 Regional Tax Rounding)",
    category: "Automated Policy",
    status: "EXCEPTION_TAX_VARIANCE",
    actionType: "AUTO_APPROVE",
    badgeColor: "success",
    confidence: "95.0%",
    invoiceId: "INV-2026-005",
    vendorName: "RedPillar Cloud Solutions LLC",
    vendorId: "VEND-IBM-8841",
    poNumber: "PO-45009812",
    amount: "$48,608.50",
    allowable: "$48,608.50",
    discrepancy: "$8.50 (Absorbed)",
    description: "An $8.50 rounding difference between state tax rate calculation and vendor invoicing. Because it falls within IBM's $25 administrative tolerance policy (Section 7.3), the system auto-approves payment and posts an adjustment memo to the audit log.",
    lineItems: [
      {
        line: "01",
        desc: "Cloud Migration Phase 4 Deliverable (MS-04)",
        qty: "1.0",
        unit: "MILESTONE",
        billedRate: "$45,000.00",
        contractMax: "$45,000.00",
        variance: "$0.00",
        grStatus: "APPROVED (GR-50001925)",
        status: "PERFECT_MATCH"
      }
    ],
    citations: [
      "Section 7.3 (Tax and Minor Rounding Tolerance): Variances under $25.00 automatically absorbed.",
      "SAP S/4HANA PO-45009812 Line 40: Goods Receipt GR-50001925 approved by Sarah Chen."
    ],
    communication: `AUTOMATED TOLERANCE CLEARANCE MEMO
Invoice: INV-2026-005 | Vendor: RedPillar Cloud Solutions LLC
PO: PO-45009812 | Billed Total: $48,608.50
Calculated Subtotal: $45,000.00 | Tax Claimed: $3,600.00
Variance: $8.50 (Tax/Rounding adjustment applied pursuant to IBM AP Policy §3.1).
Status: Auto-cleared and scheduled for payment disbursement.`,
    agentLogs: [
      "[09:30:01] NormalizerAgent: Parsed milestone deliverable MS-04 and tax line item.",
      "[09:30:02] ContractValidatorAgent (RAG): Milestone MS-04 validated ($45,000.00).",
      "[09:30:03] ERPAgent: Approved Goods Receipt GR-50001925 verified in SAP.",
      "[09:30:04] ResolutionAgent: Evaluated tax discrepancy of $8.50 <= $25.00 tolerance. Applied Section 7.3 automated clearance."
    ]
  }
];

const ASCII_IBM_PC = `
 ____________________________________________________________________
|  ________________________________________________________________  |
| |                                                                | |
| |  IBM Personal Computer (R) DOS Version 1.10                    | |
| |  (C)Copyright IBM Corp 1981, 2026                              | |
| |                                                                | |
| |  A> FINANCIAL_RUNTIME.EXE --ORCHESTRATOR=AGENTIC_AI            | |
| |  >> CONNECTED TO SAP S/4HANA (BAPI_INVOICE_CREATE)             | |
| |  >> RAG INDEX: 1,420 CLAUSES / 48 SOW RATE CARDS LOADED        | |
| |  >> SYSTEM READY FOR INVOICE EXCEPTION TRIAGE                  | |
| |                                                                | |
| |  _                                                             | |
| |________________________________________________________________| |
|                                                      [ POWER ] O   |
|____________________________________________________________________|
     \\__________________________________________________________/
    ==============================================================
    | [=====] [=====] [=====] [=====] [=====] [=====] [=====]    |
    | [=====] [=====] [=====] [=====] [=====] [=====] [=====]    |
    ==============================================================
`;
