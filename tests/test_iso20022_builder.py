"""
Unit tests for ISO 20022 pain.001.001.09 XML message builder.
"""

import unittest
import xml.etree.ElementTree as ET
from src.invoice_matcher.payment_rails.iso20022_builder import ISO20022Builder


class TestISO20022Builder(unittest.TestCase):

    def test_iso20022_valid_xml_structure(self):
        """Verify that generated XML is well-formed and adheres to pain.001 elements."""
        xml_content = ISO20022Builder.generate_pain001_xml(
            invoice_id="INV-2026-001",
            vendor_id="VEND-IBM-8841",
            vendor_name="RedPillar Cloud Solutions LLC",
            amount=45000.0,
            po_number="PO-45009812",
            currency="USD"
        )

        root = ET.fromstring(xml_content)
        self.assertTrue(root.tag.endswith("Document"))

        # Find CstmrCdtTrfInitn
        ns = {"p": ISO20022Builder.NAMESPACE}
        cstmr_init = root.find("p:CstmrCdtTrfInitn", ns)
        self.assertIsNotNone(cstmr_init)

        # Check GrpHdr
        grp_hdr = cstmr_init.find("p:GrpHdr", ns)
        self.assertIsNotNone(grp_hdr)
        msg_id = grp_hdr.find("p:MsgId", ns).text
        self.assertIn("INV-2026-001", msg_id)
        self.assertEqual(grp_hdr.find("p:CtrlSum", ns).text, "45000.00")

        # Check PmtInf & CdtTrfTxInf
        pmt_inf = cstmr_init.find("p:PmtInf", ns)
        self.assertIsNotNone(pmt_inf)
        self.assertEqual(pmt_inf.find("p:PmtMtd", ns).text, "TRF")

        cdt_trf = pmt_inf.find("p:CdtTrfTxInf", ns)
        self.assertIsNotNone(cdt_trf)

        instd_amt = cdt_trf.find("p:Amt/p:InstdAmt", ns)
        self.assertIsNotNone(instd_amt)
        self.assertEqual(instd_amt.text, "45000.00")
        self.assertEqual(instd_amt.attrib.get("Ccy"), "USD")

        # Verify Remittance contains invoice and PO
        rmt = cdt_trf.find("p:RmtInf/p:Ustrd", ns).text
        self.assertIn("INV-2026-001", rmt)
        self.assertIn("PO-45009812", rmt)


if __name__ == "__main__":
    unittest.main()
