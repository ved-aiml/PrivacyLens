"""PrivacyLens Interactive Terminal Demo.

Demonstrates local PII detection and text anonymization using:
1. Regex-based detection
2. spaCy Named Entity Recognition
3. Transformer-based Named Entity Recognition (dslim/bert-base-NER)
4. Combined detection with deduplication
5. Safe local anonymization & placeholder restoration
"""

import sys
from pathlib import Path

# Ensure backend and root paths are available
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

from app.detector import detect_pii
from app.combined_detector import (
    detect_all,
    get_spacy_detector,
    get_transformer_detector,
)
from app.anonymizer import anonymize_text


DEFAULT_SAMPLE_TEXT = (
    "My name is Rahul Sharma. I study at Harvard University. "
    "My email is rahul@example.com. My phone is 9876543210. I live in New Delhi."
)


def format_detections(detections: list[dict]) -> str:
    if not detections:
        return "  [No entities detected]"
    lines = []
    for d in detections:
        det_label = d.get("detector") or ", ".join(d.get("detectors", []))
        flag = " [OVERLAP REVIEW]" if d.get("overlap_warning") else ""
        lines.append(
            f"  * [{d['entity_type']}] \"{d['text']}\" "
            f"(offsets {d['start']}..{d['end']}) via {det_label}{flag}"
        )
    return "\n".join(lines)


def run_demo(sample_text: str | None = None):
    text = sample_text or DEFAULT_SAMPLE_TEXT

    print("\n" + "=" * 80)
    print("                     PRIVACYLENS NLP DEMO")
    print("      Local PII Detection & Context-Preserving Anonymization")
    print("=" * 80)

    print("\n[1] INPUT TEXT:")
    print("-" * 80)
    print(f'"{text}"')
    print("-" * 80)

    # 1. Regex
    print("\n[2] REGEX-BASED DETECTION (Structured Identifiers):")
    regex_results = detect_pii(text)
    print(format_detections(regex_results))

    # 2. spaCy NER (reusing loaded singleton)
    print("\n[3] SPACY NER DETECTION (en_core_web_sm):")
    spacy_engine = get_spacy_detector()
    spacy_results = spacy_engine.detect_entities(text)
    print(format_detections(spacy_results))

    # 3. Transformer NER (reusing loaded singleton)
    print("\n[4] TRANSFORMER NER DETECTION (dslim/bert-base-NER):")
    tf_engine = get_transformer_detector()
    if tf_engine.is_available:
        tf_results = tf_engine.detect_entities(text)
        print(format_detections(tf_results))
    else:
        tf_results = []
        print("  [Transformer model not available - graceful fallback active]")

    # 4. Combined (reuses already computed results - zero duplicate execution)
    print("\n[5] COMBINED DETECTOR (Deduplicated & Complementary):")
    combined_results = detect_all(
        text,
        regex_matches=regex_results,
        spacy_matches=spacy_results,
        tf_matches=tf_results,
    )
    print(format_detections(combined_results))

    # 5. Anonymization
    print("\n[6] ANONYMIZED OUTPUT:")
    print("-" * 80)
    sanitized_text, mapping = anonymize_text(text, combined_results)
    print(f'"{sanitized_text}"')
    print("-" * 80)

    print("\n[7] LOCAL ANONYMIZATION MAPPING (Kept strictly on-device):")
    if mapping:
        for placeholder, original in mapping.items():
            print(f"  {placeholder:<18} -> \"{original}\"")
    else:
        print("  [No sensitive entities to map]")

    print("=" * 80 + "\n")


def interactive_loop():
    print("\n" + "=" * 80)
    print("                 PRIVACYLENS INTERACTIVE CONSOLE")
    print("=" * 80)
    print("Type or paste any text to test local privacy detection & anonymization.")
    print("Commands:")
    print("  - Type 'exit' or 'q' to quit.")
    print("  - Press [Enter] on an empty line to run the default sample.")
    print("=" * 80)

    while True:
        try:
            print("\nEnter your text below:")
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting PrivacyLens console.")
            break

        if user_input.lower() in ("exit", "quit", "q"):
            print("Exiting PrivacyLens console. Goodbye!")
            break

        if not user_input:
            print("[Using default sample text]")
            run_demo(DEFAULT_SAMPLE_TEXT)
        else:
            run_demo(user_input)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        custom_input = " ".join(sys.argv[1:]).strip()
        run_demo(custom_input)
    else:
        interactive_loop()
