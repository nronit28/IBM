"""
ISO 20022 pain.001.001.09 XML Message Builder.
Customer Credit Transfer Initiation message for international & cross-border treasury settlements.
"""

import uuid
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, Any, Optional


class ISO20022Builder:
    """Builds valid ISO 20022 pain.001.001.09 XML credit transfer initiation documents."""

    NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"

    @classmethod
    def generate_pain001_xml(
        cls,
        invoice_id: str,
        vendor_id: str,
        vendor_name: str,
        amount: float,
        po_number: str,
        currency: str = "USD",
        vendor_iban_or_account: str = "US89BOFA000123456789",
        vendor_bic: str = "BOFAUS3NXXX",
        debtor_bic: str = "CHASUS33XXX",
        execution_date: Optional[datetime] = None
    ) -> str:
        """
        Generates an ISO 20022 pain.001.001.09 Customer Credit Transfer Initiation XML.
        """
        now = datetime.utcnow()
        exec_dt = execution_date or now
        msg_id = f"IBM-TXN-{now.strftime('%Y%m%d%H%M%S')}-{invoice_id}"
        pmt_inf_id = f"PMTINF-{invoice_id}"
        e2e_id = f"E2E-{invoice_id}-{po_number}"
        uetr = str(uuid.uuid4())

        # Root element
        root = ET.Element("Document", xmlns=cls.NAMESPACE)
        cstmr_init = ET.SubElement(root, "CstmrCdtTrfInitn")

        # --- 1. Group Header (GrpHdr) ---
        grp_hdr = ET.SubElement(cstmr_init, "GrpHdr")
        ET.SubElement(grp_hdr, "MsgId").text = msg_id
        ET.SubElement(grp_hdr, "CreDtTm").text = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        ET.SubElement(grp_hdr, "NbOfTxs").text = "1"
        ET.SubElement(grp_hdr, "CtrlSum").text = f"{amount:.2f}"
        
        initg_pty = ET.SubElement(grp_hdr, "InitgPty")
        ET.SubElement(initg_pty, "Nm").text = "IBM CORPORATION TREASURY DISBURSEMENT"

        # --- 2. Payment Information (PmtInf) ---
        pmt_inf = ET.SubElement(cstmr_init, "PmtInf")
        ET.SubElement(pmt_inf, "PmtInfId").text = pmt_inf_id
        ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"  # Credit Transfer
        ET.SubElement(pmt_inf, "BtchBookg").text = "false"
        ET.SubElement(pmt_inf, "NbOfTxs").text = "1"
        ET.SubElement(pmt_inf, "CtrlSum").text = f"{amount:.2f}"

        pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
        svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
        ET.SubElement(svc_lvl, "Cd").text = "SEPA" if currency == "EUR" else "URGP"

        ET.SubElement(pmt_inf, "ReqdExctnDt").text = exec_dt.strftime("%Y-%m-%d")

        # Debtor (IBM)
        dbtr = ET.SubElement(pmt_inf, "Dbtr")
        ET.SubElement(dbtr, "Nm").text = "INTERNATIONAL BUSINESS MACHINES CORP"
        
        dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
        dbtr_acct_id = ET.SubElement(dbtr_acct, "Id")
        dbtr_othr = ET.SubElement(dbtr_acct_id, "Othr")
        ET.SubElement(dbtr_othr, "Id").text = "IBM-GLOBAL-TREASURY-01928"

        dbtr_agt = ET.SubElement(pmt_inf, "DbtrAgt")
        dbtr_fin_instn = ET.SubElement(dbtr_agt, "FinInstnId")
        ET.SubElement(dbtr_fin_instn, "BICFI").text = debtor_bic

        # --- 3. Credit Transfer Transaction Information (CdtTrfTxInf) ---
        cdt_trf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
        
        pmt_id = ET.SubElement(cdt_trf, "PmtId")
        ET.SubElement(pmt_id, "EndToEndId").text = e2e_id
        ET.SubElement(pmt_id, "UETR").text = uetr

        amt = ET.SubElement(cdt_trf, "Amt")
        instd_amt = ET.SubElement(amt, "InstdAmt", Ccy=currency)
        instd_amt.text = f"{amount:.2f}"

        # Creditor Agent (Vendor Bank)
        cdtr_agt = ET.SubElement(cdt_trf, "CdtrAgt")
        cdtr_fin_instn = ET.SubElement(cdtr_agt, "FinInstnId")
        ET.SubElement(cdtr_fin_instn, "BICFI").text = vendor_bic

        # Creditor (Vendor)
        cdtr = ET.SubElement(cdt_trf, "Cdtr")
        ET.SubElement(cdtr, "Nm").text = vendor_name.upper()

        cdtr_acct = ET.SubElement(cdt_trf, "CdtrAcct")
        cdtr_acct_id = ET.SubElement(cdtr_acct, "Id")
        if vendor_iban_or_account.startswith("US") or len(vendor_iban_or_account) >= 15:
            ET.SubElement(cdtr_acct_id, "IBAN").text = vendor_iban_or_account
        else:
            cdtr_othr = ET.SubElement(cdtr_acct_id, "Othr")
            ET.SubElement(cdtr_othr, "Id").text = vendor_iban_or_account

        # Remittance Information
        rmt_inf = ET.SubElement(cdt_trf, "RmtInf")
        ET.SubElement(rmt_inf, "Ustrd").text = f"INV:{invoice_id} | PO:{po_number} | VENDOR:{vendor_id}"

        # Pretty print XML string
        raw_xml = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(raw_xml)
        return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
