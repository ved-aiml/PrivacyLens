from typing import Any


def anonymize_text(
    text: str, detections: list[dict[str, Any]]
) -> tuple[str, dict[str, str]]:
    """Anonymize sensitive entities in text by replacing them with entity-specific placeholders.

    - Processes replacements from right to left using exact offsets.
    - Repeated identical values for the same entity type receive consistent placeholders.
    - Returns (sanitized_text, mapping) where mapping maps placeholder -> original text.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not detections:
        return text, {}

    # Sort ascending by start offset to assign placeholders in reading order
    ordered_detections = sorted(detections, key=lambda d: (d["start"], d["end"]))

    entity_counters: dict[str, int] = {}
    value_to_placeholder: dict[tuple[str, str], str] = {}
    placeholder_to_value: dict[str, str] = {}

    # Assign consistent placeholders for repeated identical values
    annotated_detections: list[dict[str, Any]] = []
    for det in ordered_detections:
        entity_type = det["entity_type"]
        val = det["text"]
        key = (entity_type, val)

        if key not in value_to_placeholder:
            count = entity_counters.get(entity_type, 0) + 1
            entity_counters[entity_type] = count
            placeholder = f"[{entity_type}_{count}]"
            value_to_placeholder[key] = placeholder
            placeholder_to_value[placeholder] = val

        annotated_detections.append({
            "start": det["start"],
            "end": det["end"],
            "placeholder": value_to_placeholder[key],
            "text": val,
        })

    # Sort descending by start offset to perform replacements right-to-left
    # without invalidating earlier offsets
    annotated_detections.sort(key=lambda d: d["start"], reverse=True)

    sanitized = text
    last_processed_start = len(text) + 1

    for det in annotated_detections:
        start = det["start"]
        end = det["end"]

        # If a detection overlaps an already replaced region to its right, skip to avoid corruption
        if end > last_processed_start:
            continue

        sanitized = sanitized[:start] + det["placeholder"] + sanitized[end:]
        last_processed_start = start

    return sanitized, placeholder_to_value


def restore_text(sanitized_text: str, mapping: dict[str, str]) -> str:
    """Restore original sensitive text from sanitized text using the local mapping.

    Safe and local: no external calls or sensitive data logging.
    """
    if not isinstance(sanitized_text, str):
        raise TypeError("sanitized_text must be a string")
    if not isinstance(mapping, dict):
        raise TypeError("mapping must be a dictionary")

    restored = sanitized_text
    for placeholder, original_value in mapping.items():
        restored = restored.replace(placeholder, original_value)

    return restored

