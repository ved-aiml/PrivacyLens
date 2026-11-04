import logging
import os
from typing import Any

# Suppress noisy symlink warnings on Windows
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

logger = logging.getLogger(__name__)

TRANSFORMER_ENTITY_MAPPING = {
    "PER": "PERSON",
    "ORG": "ORGANIZATION",
    "LOC": "LOCATION",
    "MISC": "MISCELLANEOUS",
}

TECH_LABELS_DENYLIST = {
    "KYC", "PAN", "IFSC", "UPI", "API", "JSON", "DL", "GST", "GSTIN", "OTP", "PIN",
    "EMAIL", "PHONE", "MOBILE", "CONTACT", "ADDRESS"
}


class TransformerDetector:
    """Transformer-based NER detector using Hugging Face token-classification pipeline."""

    _instance = None
    _pipeline = None
    _load_attempted = False
    _load_error = None

    def __init__(self, model_name: str = "dslim/bert-base-NER"):
        self.model_name = model_name
        self._ensure_loaded()

    def _ensure_loaded(self):
        if TransformerDetector._load_attempted:
            return

        TransformerDetector._load_attempted = True
        try:
            from transformers import pipeline

            # Load on CPU (device=-1)
            TransformerDetector._pipeline = pipeline(
                "token-classification",
                model=self.model_name,
                aggregation_strategy="simple",
                device=-1,
            )
        except Exception as e:
            TransformerDetector._pipeline = None
            TransformerDetector._load_error = str(e)
            logger.warning(
                f"Failed to load Transformer model '{self.model_name}': {e}. "
                "Regex and spaCy detectors will continue to work."
            )

    @property
    def is_available(self) -> bool:
        return TransformerDetector._pipeline is not None

    def detect_entities(self, text: str) -> list[dict[str, Any]]:
        """Extract named entities and character offsets using the Transformer pipeline."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        if not self.is_available or not text.strip():
            return []

        try:
            raw_entities = TransformerDetector._pipeline(text)
        except Exception as e:
            logger.warning(f"Error during Transformer inference: {e}")
            return []

        # Merge contiguous / subword tokens belonging to the same entity group
        merged_spans: list[dict[str, Any]] = []
        for ent in raw_entities:
            # Filter low confidence predictions to prevent noise
            score = float(ent.get("score", 1.0))
            if score < 0.80:
                continue

            label = ent.get("entity_group", ent.get("entity", ""))
            mapped_type = TRANSFORMER_ENTITY_MAPPING.get(label)
            if not mapped_type:
                continue

            start = int(ent["start"])
            end = int(ent["end"])

            if (
                merged_spans
                and merged_spans[-1]["entity_type"] == mapped_type
                and start <= merged_spans[-1]["end"] + 1
            ):
                # Extend the previous span to cover subwords / contiguous words
                merged_spans[-1]["end"] = max(merged_spans[-1]["end"], end)
            else:
                merged_spans.append({
                    "entity_type": mapped_type,
                    "start": start,
                    "end": end,
                })

        # Build clean final detection objects matching exact text slice
        detections: list[dict[str, Any]] = []
        for span in merged_spans:
            s = span["start"]
            e = span["end"]

            # Trim whitespace from offsets if any
            while s < e and text[s].isspace():
                s += 1
            while e > s and text[e - 1].isspace():
                e -= 1

            if s >= e:
                continue

            ent_text = text[s:e]

            # Filter single or 2-letter subword fragments (e.g. "PA", "IF", "DL", "A")
            if len(ent_text) <= 2 and ent_text.upper() not in {"US", "UK", "EU"}:
                continue

            # Filter common technical labels
            if ent_text.upper() in TECH_LABELS_DENYLIST:
                continue

            detections.append({
                "entity_type": span["entity_type"],
                "text": ent_text,
                "start": s,
                "end": e,
                "detector": "transformer",
            })

        detections.sort(key=lambda x: (x["start"], x["end"]))
        return detections
