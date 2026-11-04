from typing import Any
import spacy

ENTITY_MAPPING = {
    "PERSON": "PERSON",
    "ORG": "ORGANIZATION",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "DATE": "DATE",
    "TIME": "TIME",
    "MONEY": "FINANCIAL_AMOUNT",
    "NORP": "DEMOGRAPHIC_GROUP",
}

# Standard tech/banking labels that statistical models mistakenly label as ORG or PERSON
TECH_LABELS_DENYLIST = {
    "KYC", "PAN", "IFSC", "UPI", "API", "JSON", "DL", "GST", "GSTIN", "OTP", "PIN",
    "EMAIL", "PHONE", "MOBILE", "CONTACT", "ADDRESS"
}


class NERDetector:
    _instance = None

    def __init__(self, model_name: str = "en_core_web_sm"):
        self.nlp = spacy.load(model_name)

    def detect_entities(self, text: str) -> list[dict[str, Any]]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        doc = self.nlp(text)
        detections: list[dict[str, Any]] = []

        for ent in doc.ents:
            entity_type = ENTITY_MAPPING.get(ent.label_)
            if entity_type is None:
                continue

            ent_text = ent.text.strip()

            # Filter out common acronyms/labels mistakenly classified as entities
            if ent_text.upper() in TECH_LABELS_DENYLIST:
                continue

            # Pure digit strings (phones, pincodes, account numbers) are not DATE entities
            if entity_type == "DATE" and ent_text.replace(" ", "").replace("-", "").isdigit():
                continue

            # Generic non-sensitive time/duration phrases (e.g. "regular business hours", "Monday to Friday")
            if entity_type in ("DATE", "TIME"):
                lower = ent_text.lower()
                if any(phrase in lower for phrase in ["business hours", "monday to friday", "autumn season"]):
                    continue

            detections.append({
                "entity_type": entity_type,
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "detector": "spacy",
            })

        detections.sort(key=lambda x: (x["start"], x["end"]))
        return detections
