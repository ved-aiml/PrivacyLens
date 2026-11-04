from typing import Any

from app.patterns import PATTERNS
from app.validators import (
    validate_ip,
    validate_phone,
    validate_pincode,
    validate_pan,
    validate_aadhaar_format,
    validate_ifsc,
    validate_upi,
    validate_gstin,
    validate_voter_id,
    validate_passport,
    validate_uuid,
    validate_mac,
)


VALIDATORS = {
    "IP_ADDRESS": validate_ip,
    "PHONE": validate_phone,
    "PINCODE": validate_pincode,
    "PAN": validate_pan,
    "AADHAAR": validate_aadhaar_format,
    "IFSC_CODE": validate_ifsc,
    "UPI_ID": validate_upi,
    "GSTIN": validate_gstin,
    "VOTER_ID": validate_voter_id,
    "PASSPORT": validate_passport,
    "UUID": validate_uuid,
    "MAC_ADDRESS": validate_mac,
}


def detect_pii(text: str) -> list[dict[str, Any]]:
    """Detect PII entities in text using regular expressions and domain validators.

    Returns a list of detections with entity_type, text, start, end, detector.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    detections: list[dict[str, Any]] = []

    for entity_type, pattern in PATTERNS.items():
        validator = VALIDATORS.get(entity_type)

        for match in pattern.finditer(text):
            # If the pattern has capturing groups, use the first non-empty group
            if match.lastindex and match.lastindex >= 1:
                value = None
                start = 0
                end = 0
                for group_idx in range(1, match.lastindex + 1):
                    if match.group(group_idx) is not None:
                        value = match.group(group_idx)
                        start = match.start(group_idx)
                        end = match.end(group_idx)
                        break
                if value is None:
                    value = match.group(0)
                    start = match.start(0)
                    end = match.end(0)
            else:
                value = match.group(0)
                start = match.start(0)
                end = match.end(0)

            # Clean trailing sentence punctuation from secrets/passwords (e.g. "password: abc.")
            if entity_type in ("PASSWORD", "API_KEY"):
                stripped = value.rstrip(".,;:!?")
                end = start + len(stripped)
                value = stripped

            # Apply additional validation if available.
            if validator and not validator(value):
                continue

            detections.append({
                "entity_type": entity_type,
                "text": value,
                "start": start,
                "end": end,
                "detector": "regex",
            })

    # Sort detections by start offset, then end offset
    detections.sort(key=lambda x: (x["start"], x["end"]))

    return detections
