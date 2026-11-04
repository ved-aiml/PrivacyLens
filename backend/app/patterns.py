import re

PATTERNS = {
    # ---------------- EMAIL ----------------
    "EMAIL": re.compile(
        r"(?<![A-Za-z0-9._%+-])"
        r"[A-Za-z0-9_%+-]+"
        r"(?:\.[A-Za-z0-9_%+-]+)*"
        r"@"
        r"[A-Za-z0-9-]+"
        r"(?:\.[A-Za-z0-9-]+)*"
        r"\.[A-Za-z]{2,}"
        r"(?![A-Za-z0-9_-])"
    ),

    # ---------------- PHONE (INDIA) ----------------
    "PHONE": re.compile(
        r"(?<!\d)"
        r"(?:\+91[\s.-]?|91[\s.-]?|0)?"
        r"[6-9]\d{4}[\s.-]?\d{5}"
        r"(?!\d)"
    ),

    # ---------------- INDIAN PINCODE ----------------
    "PINCODE": re.compile(
        r"(?<!\d)"
        r"[1-9]\d{5}"
        r"(?!\d)"
    ),

    # ---------------- IPV4 ADDRESS ----------------
    "IP_ADDRESS": re.compile(
        r"(?<![\d.])"
        r"(?:\d{1,3}\.){3}\d{1,3}"
        r"(?![\d.])"
    ),

    # ---------------- PAN (PERMANENT ACCOUNT NUMBER) ----------------
    "PAN": re.compile(
        r"(?<![A-Za-z0-9])[A-Z]{5}[0-9]{4}[A-Z](?![A-Za-z0-9])",
        re.IGNORECASE,
    ),

    # ---------------- AADHAAR ----------------
    "AADHAAR": re.compile(
        r"(?<![A-Za-z0-9-])"
        r"(?:\d{4}[\s-]?\d{4}[\s-]?\d{4})"
        r"(?![A-Za-z0-9-])"
    ),

    # ---------------- IFSC CODE ----------------
    "IFSC_CODE": re.compile(
        r"(?<![A-Za-z0-9])[A-Z]{4}0[A-Z0-9]{6}(?![A-Za-z0-9])",
        re.IGNORECASE,
    ),

    # ---------------- UPI ID ----------------
    "UPI_ID": re.compile(
        r"(?<![A-Za-z0-9._%+-])[a-zA-Z0-9.\-_]{2,64}@"
        r"(?:okhdfcbank|okaxis|oksbi|okicici|paytm|upi|ybl|ibl|axl|apl|sbi|barodampay|postbank|idfcbank|federal|kotak)\b",
        re.IGNORECASE,
    ),

    # ---------------- GSTIN ----------------
    "GSTIN": re.compile(
        r"(?<![A-Za-z0-9])\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z](?![A-Za-z0-9])",
        re.IGNORECASE,
    ),

    # ---------------- VEHICLE NUMBER (INDIA) ----------------
    "VEHICLE_NUMBER": re.compile(
        r"(?<![A-Za-z0-9])[A-Z]{2}[ -]?[0-9]{1,2}[ -]?[A-Z]{1,3}[ -]?[0-9]{4}(?![A-Za-z0-9])",
        re.IGNORECASE,
    ),

    # ---------------- PASSPORT (INDIA) ----------------
    "PASSPORT": re.compile(
        r"(?<![A-Za-z0-9])[A-PR-WYa-pr-wy][1-9]\d{6}(?![A-Za-z0-9])"
    ),

    # ---------------- VOTER ID (EPIC) ----------------
    "VOTER_ID": re.compile(
        r"(?<![A-Za-z0-9])[A-Z]{3}[0-9]{7}(?![A-Za-z0-9])",
        re.IGNORECASE,
    ),

    # ---------------- DRIVING LICENCE (INDIA) ----------------
    "DL_NUMBER": re.compile(
        r"(?<![A-Za-z0-9])[A-Z]{2}[0-9]{2}[ -]?(?:19|20)\d{2}[0-9]{7}(?![A-Za-z0-9])|"
        r"(?<![A-Za-z0-9])[A-Z]{2}[ -]?[0-9]{13}(?![A-Za-z0-9])",
        re.IGNORECASE,
    ),

    # ---------------- RATION CARD ----------------
    "RATION_CARD": re.compile(
        r"(?<![A-Za-z0-9-])RC[-_]?[0-9]{10,12}(?![A-Za-z0-9-])"
    ),

    # ---------------- UUID ----------------
    "UUID": re.compile(
        r"(?<![A-Za-z0-9])[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}(?![A-Za-z0-9])"
    ),

    # ---------------- MAC ADDRESS ----------------
    "MAC_ADDRESS": re.compile(
        r"(?<![A-Za-z0-9])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![A-Za-z0-9])"
    ),

    # ---------------- ORDER ID ----------------
    "ORDER_ID": re.compile(
        r"(?<![A-Za-z0-9])(?:ORD|ORDER)[-_][0-9A-Za-z]{6,12}(?![A-Za-z0-9])",
        re.IGNORECASE,
    ),

    # ---------------- TRANSACTION ID ----------------
    "TRANSACTION_ID": re.compile(
        r"(?<![A-Za-z0-9])(?:TXN|TRX)[-_][0-9A-Za-z]{8,16}(?![A-Za-z0-9])",
        re.IGNORECASE,
    ),

    # ---------------- EMPLOYEE ID ----------------
    "EMPLOYEE_ID": re.compile(
        r"(?<![A-Za-z0-9])(?:EMP|EMPLOYEE)[-_][0-9A-Za-z]{4,8}(?![A-Za-z0-9])",
        re.IGNORECASE,
    ),

    # ---------------- FINANCIAL AMOUNT ----------------
    "FINANCIAL_AMOUNT": re.compile(
        r"(?<![A-Za-z0-9])(?:\$|₹|Rs\.?|€|£)\s*\d+(?:,\d+)*(?:\.\d+)?(?![A-Za-z0-9])|"
        r"(?<![A-Za-z0-9])\d+(?:,\d+)*(?:\.\d+)?\s*(?:dollars|euros|rupees|USD|INR|EUR)\b",
        re.IGNORECASE,
    ),

    # ---------------- DATE ----------------
    "DATE": re.compile(
        r"(?<![A-Za-z0-9])\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b|"
        r"(?<![A-Za-z0-9])(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        re.IGNORECASE,
    ),

    # ---------------- PASSWORD (IN CONTEXT) ----------------
    "PASSWORD": re.compile(
        r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*([^\s,;]+)"
    ),

    # ---------------- API KEY (IN CONTEXT OR TOKENS) ----------------
    "API_KEY": re.compile(
        r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*([A-Za-z0-9_\-]{16,})|"
        r"\b(sk_live_[0-9a-zA-Z]{24,32})\b|"
        r"\b(ghp_[0-9a-zA-Z]{36})\b"
    ),
}
