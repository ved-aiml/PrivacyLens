from typing import Any

from app.patterns import PATTERNS
from app.validators import (
    validate_ip,
    validate_phone,
    validate_pincode,
)


VALIDATORS = {
    "IP_ADDRESS": validate_ip,
    "PHONE": validate_phone,
    "PINCODE": validate_pincode,
}


def detect_pii(text: str) -> list[dict[str, Any]]:

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    detections = []

    for entity_type, pattern in PATTERNS.items():

        validator = VALIDATORS.get(entity_type)

        for match in pattern.finditer(text):

            value = match.group()

            # Apply additional validation if available.
            if validator and not validator(value):
                continue

            detections.append({
                "entity_type": entity_type,
                "text": value,
                "start": match.start(),
                "end": match.end(),
                "detector": "regex",
            })

    detections.sort(
        key=lambda x: (x["start"], x["end"])
    )

    return detections