from typing import Any

from app.detector import detect_pii
from app.ner_detector import NERDetector
from app.transformer_detector import TransformerDetector

# Lazy singletons for detectors
_spacy_detector: NERDetector | None = None
_transformer_detector: TransformerDetector | None = None

# High-confidence structured categories from Regex
STRUCTURED_PII_TYPES = {
    "EMAIL", "PHONE", "PINCODE", "IP_ADDRESS", "PAN", "AADHAAR",
    "IFSC_CODE", "UPI_ID", "GSTIN", "PASSPORT", "VOTER_ID", "DL_NUMBER",
    "UUID", "MAC_ADDRESS", "ORDER_ID", "TRANSACTION_ID", "EMPLOYEE_ID",
    "PASSWORD", "API_KEY", "FINANCIAL_AMOUNT"
}


def get_spacy_detector() -> NERDetector:
    global _spacy_detector
    if _spacy_detector is None:
        _spacy_detector = NERDetector()
    return _spacy_detector


def get_transformer_detector() -> TransformerDetector:
    global _transformer_detector
    if _transformer_detector is None:
        _transformer_detector = TransformerDetector()
    return _transformer_detector


def detect_all(
    text: str,
    regex_matches: list[dict[str, Any]] | None = None,
    spacy_matches: list[dict[str, Any]] | None = None,
    tf_matches: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Run or receive Regex, spaCy, and Transformer detector results, combine them,

    apply priority conflict resolution, merge exact duplicates, and flag partial overlaps.

    Accepts pre-computed matches (e.g. from demo steps) to avoid duplicate model execution.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    # 1. Regex detection (run only if not provided)
    if regex_matches is None:
        try:
            regex_matches = detect_pii(text)
        except Exception:
            regex_matches = []

    # 2. spaCy NER detection (run only if not provided)
    if spacy_matches is None:
        try:
            spacy_det = get_spacy_detector()
            spacy_matches = spacy_det.detect_entities(text)
        except Exception:
            spacy_matches = []

    # 3. Transformer NER detection (run only if not provided)
    if tf_matches is None:
        try:
            tf_det = get_transformer_detector()
            if tf_det.is_available:
                tf_matches = tf_det.detect_entities(text)
            else:
                tf_matches = []
        except Exception:
            tf_matches = []

    # Suppress generic statistical/NLP spans that collide with validated structured Regex tokens
    # (e.g. spaCy classifying a 10-digit phone number as DATE, or IFSC code as ORGANIZATION)
    filtered_spacy: list[dict[str, Any]] = []
    for s_det in spacy_matches:
        s_start, s_end = s_det["start"], s_det["end"]
        collides = False
        for r_det in regex_matches:
            if r_det["entity_type"] in STRUCTURED_PII_TYPES:
                r_start, r_end = r_det["start"], r_det["end"]
                # Overlap check
                if s_start < r_end and r_start < s_end:
                    collides = True
                    break
        if not collides:
            filtered_spacy.append(s_det)

    filtered_tf: list[dict[str, Any]] = []
    for t_det in tf_matches:
        t_start, t_end = t_det["start"], t_det["end"]
        collides = False
        for r_det in regex_matches:
            if r_det["entity_type"] in STRUCTURED_PII_TYPES:
                r_start, r_end = r_det["start"], r_det["end"]
                if t_start < r_end and r_start < t_end:
                    collides = True
                    break
        if not collides:
            filtered_tf.append(t_det)

    all_detections: list[dict[str, Any]] = []
    all_detections.extend(regex_matches)
    all_detections.extend(filtered_spacy)
    all_detections.extend(filtered_tf)

    # Merge exact duplicate detections: same (start, end, entity_type)
    merged_map: dict[tuple[int, int, str], dict[str, Any]] = {}

    for det in all_detections:
        key = (det["start"], det["end"], det["entity_type"])
        detector_name = det.get("detector", "unknown")

        if key not in merged_map:
            merged_map[key] = {
                "entity_type": det["entity_type"],
                "text": det["text"],
                "start": det["start"],
                "end": det["end"],
                "detectors": [detector_name],
            }
        else:
            if detector_name not in merged_map[key]["detectors"]:
                merged_map[key]["detectors"].append(detector_name)
                merged_map[key]["detectors"].sort()

    combined: list[dict[str, Any]] = list(merged_map.values())
    combined.sort(key=lambda x: (x["start"], x["end"]))

    # Detect and flag partial overlaps for review
    for i in range(len(combined)):
        for j in range(i + 1, len(combined)):
            det_a = combined[i]
            det_b = combined[j]
            # Overlap condition: start_a < end_b and start_b < end_a
            if det_a["start"] < det_b["end"] and det_b["start"] < det_a["end"]:
                det_a["overlap_warning"] = True
                det_b["overlap_warning"] = True

    return combined
