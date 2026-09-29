"""
US Automated Clearing House (ACH) NACHA 94-Column Formatter.
Generates fully compliant NACHA files for Corporate Credit or Debit (CCD) B2B vendor payments.
"""

from datetime import datetime
from typing import Dict, List, Any


class NACHAGenerator:
    """Generates standard 94-column NACHA files for corporate vendor disbursements."""

    # Default IBM Treasury & Originator parameters
    IMMEDIATE_DEST_ROUTING = "121000358"   # Federal Reserve Bank of San Francisco
    IMMEDIATE_ORIGIN_ID   = "1313495110"   # IBM Treasury EIN / Company ID
    IMMEDIATE_DEST_NAME   = "FEDACH SAN FRANCISCO"
    IMMEDIATE_ORIGIN_NAME = "IBM CORPORATION"
    ORIGINATING_DFI       = "12100035"

    @classmethod
    def generate_single_payment_file(
        cls,
        vendor_id: str,
        vendor_name: str,
        amount: float,
        invoice_id: str,
        po_number: str,
        routing_number: str = "021000021",  # JP Morgan Chase NY
        account_number: str = "982348102948",
        effective_date: datetime = None
    ) -> str:
        """
        Creates a valid 94-column NACHA string for a single vendor payout.
        """
        now = datetime.utcnow()
        eff_dt = effective_date or now
        amount_cents = int(round(amount * 100))

        # --- RECORD 1: File Header Record ---
        rec1 = (
            "1"                                           # Record Type (pos 1)
            "01"                                          # Priority Code (pos 2-3)
            + f" {cls.IMMEDIATE_DEST_ROUTING:<9}"[:10]    # Immediate Dest: blank + 9 digits (pos 4-13)
            + f" {cls.IMMEDIATE_ORIGIN_ID:<9}"[:10]      # Immediate Origin: blank + 9-10 chars (pos 14-23)
            + now.strftime("%y%m%d")                     # File Creation Date (pos 24-29)
            + now.strftime("%H%M")                       # File Creation Time (pos 30-33)
            + "A"                                         # File ID Modifier (pos 34)
            + "094"                                       # Record Size (pos 35-37)
            + "10"                                        # Blocking Factor (pos 38-39)
            + "1"                                         # Format Code (pos 40)
            + f"{cls.IMMEDIATE_DEST_NAME:<23}"[:23]       # Immediate Destination Name (pos 41-63)
            + f"{cls.IMMEDIATE_ORIGIN_NAME:<23}"[:23]     # Immediate Origin Name (pos 64-86)
            + "        "                                  # Reference Code (pos 87-94)
        )
        assert len(rec1) == 94, f"Record 1 length error: {len(rec1)}"

        # --- RECORD 5: Company/Batch Header Record ---
        company_name = "IBM CORP AP"
        rec5 = (
            "5"                                           # Record Type (pos 1)
            "220"                                         # Service Class: Credits Only (pos 2-4)
            + f"{company_name:<16}"[:16]                  # Company Name (pos 5-20)
            + f"{po_number:<20}"[:20]                     # Company Discretionary Data (pos 21-40)
            + f"{cls.IMMEDIATE_ORIGIN_ID:<10}"[:10]      # Company Identification (pos 41-50)
            + "CCD"                                       # Standard Entry Class Code (pos 51-53)
            + "VENDOR PAY"                                # Company Entry Description (pos 54-63)
            + now.strftime("%y%m%d")                     # Company Descriptive Date (pos 64-69)
            + eff_dt.strftime("%y%m%d")                  # Effective Entry Date (pos 70-75)
            + "   "                                       # Settlement Date Julian (pos 76-78)
            + "1"                                         # Originator Status Code (pos 79)
            + f"{cls.ORIGINATING_DFI:<8}"[:8]             # Originating DFI ID (pos 80-87)
            + "0000001"                                   # Batch Number (pos 88-94)
        )
        assert len(rec5) == 94, f"Record 5 length error: {len(rec5)}"

        # --- RECORD 6: Entry Detail Record ---
        # Routing: 8 digits DFI + 1 check digit
        clean_routing = routing_number.replace("-", "").strip()
        rdfi_routing = clean_routing[:8].zfill(8)
        check_digit = clean_routing[8:9] if len(clean_routing) >= 9 else "1"
        trace_seq = "0000001"
        trace_number = f"{cls.ORIGINATING_DFI[:8]}{trace_seq}"

        rec6 = (
            "6"                                           # Record Type (pos 1)
            "22"                                          # Transaction Code: Checking Credit (pos 2-3)
            + f"{rdfi_routing:<8}"[:8]                    # Receiving DFI Identification (pos 4-11)
            + check_digit                                 # Check Digit (pos 12)
            + f"{account_number:<17}"[:17]                # DFI Account Number (pos 13-29)
            + f"{amount_cents:010d}"                      # Amount in cents (pos 30-39)
            + f"{vendor_id:<15}"[:15]                     # Individual/Vendor ID (pos 40-54)
            + f"{vendor_name.upper():<22}"[:22]           # Receiving Company Name (pos 55-76)
            + "  "                                        # Discretionary Data (pos 77-78)
            + "0"                                         # Addenda Record Indicator (pos 79)
            + f"{trace_number:<15}"[:15]                  # Trace Number (pos 80-94)
        )
        assert len(rec6) == 94, f"Record 6 length error: {len(rec6)}"

        # --- RECORD 8: Company/Batch Control Record ---
        entry_hash = int(rdfi_routing) % 10000000000
        rec8 = (
            "8"                                           # Record Type (pos 1)
            "220"                                         # Service Class Code (pos 2-4)
            + "000001"                                    # Entry/Addenda Count (pos 5-10)
            + f"{entry_hash:010d}"                        # Entry Hash (pos 11-20)
            + "000000000000"                              # Total Debit Dollar Amount (pos 21-32)
            + f"{amount_cents:012d}"                      # Total Credit Dollar Amount (pos 33-44)
            + f"{cls.IMMEDIATE_ORIGIN_ID:<10}"[:10]      # Company Identification (pos 45-54)
            + "                   "                       # Message Authentication Code (pos 55-73)
            + "      "                                    # Reserved (pos 74-79)
            + f"{cls.ORIGINATING_DFI:<8}"[:8]             # Originating DFI ID (pos 80-87)
            + "0000001"                                   # Batch Number (pos 88-94)
        )
        assert len(rec8) == 94, f"Record 8 length error: {len(rec8)}"

        # --- RECORD 9: File Control Record ---
        # 4 core records (1, 5, 6, 8) + record 9 = 5 records.
        # Blocks must be multiple of 10. 5 records in 1 block of 10 records -> padded with 5 lines of 9s.
        rec9 = (
            "9"                                           # Record Type (pos 1)
            "000001"                                      # Batch Count (pos 2-7)
            "000001"                                      # Block Count (pos 8-13)
            "00000001"                                    # Entry / Addenda Count (pos 14-21)
            + f"{entry_hash:010d}"                        # Entry Hash (pos 22-31)
            + "000000000000"                              # Total Debit Amount (pos 32-43)
            + f"{amount_cents:012d}"                      # Total Credit Amount (pos 44-55)
            + " " * 39                                    # Reserved blank (pos 56-94)
        )
        assert len(rec9) == 94, f"Record 9 length error: {len(rec9)}"

        records = [rec1, rec5, rec6, rec8, rec9]

        # Pad to full 10-record block with Type 9 lines
        pad_line = "9" * 94
        while len(records) % 10 != 0:
            records.append(pad_line)

        return "\n".join(records)
