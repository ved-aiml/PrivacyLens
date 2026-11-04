"""PrivacyLens Evaluation Benchmark Script.

Evaluates four detection engines:
1. Regex only
2. spaCy NER only
3. Transformer NER only (dslim/bert-base-NER)
4. Combined detector

Metrics calculated:
- True Positives (TP), False Positives (FP), False Negatives (FN)
- Precision: TP / (TP + FP)
- Recall: TP / (TP + FN)
- F1-score: 2 * P * R / (P + R)
- F0.5-score: 1.25 * P * R / (0.25 * P + R)  [Weights Precision more heavily than Recall]
- Processing latency: Total time, average time per sample, average time per 100 words
- Model loading time (reported separately)
- Per-entity breakdowns for PERSON, ORGANIZATION, LOCATION, EMAIL, PHONE, PAN, AADHAAR, etc.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project modules are importable
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

from app.detector import detect_pii
from app.ner_detector import NERDetector
from app.transformer_detector import TransformerDetector
from app.combined_detector import detect_all


def compute_metrics(tp: int, fp: int, fn: int) -> dict[str, float]:
    """Compute Precision, Recall, F1, and F0.5 scores safely avoiding division by zero."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    if precision + recall > 0:
        f1 = (2 * precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    # F0.5 score: beta = 0.5 -> (1 + 0.25) * (P * R) / (0.25 * P + R)
    denom_f05 = (0.25 * precision) + recall
    if denom_f05 > 0:
        f05 = (1.25 * precision * recall) / denom_f05
    else:
        f05 = 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "f05": f05,
    }


def evaluate_dataset(
    predict_fn: Any,
    samples: list[dict[str, Any]],
    engine_name: str,
) -> dict[str, Any]:
    """Run predictions over dataset, compute timing and exact entity-level metrics."""
    total_words = 0
    inference_times = []

    # Global counts
    tp_global = 0
    fp_global = 0
    fn_global = 0

    # Per-entity type tracking: {entity_type: {"tp": int, "fp": int, "fn": int}}
    entity_counts: dict[str, dict[str, int]] = {}

    def get_ent_bucket(e_type: str) -> dict[str, int]:
        if e_type not in entity_counts:
            entity_counts[e_type] = {"tp": 0, "fp": 0, "fn": 0}
        return entity_counts[e_type]

    for sample in samples:
        text = sample["text"]
        gt_entities = sample.get("entities", [])
        words = len(text.split())
        total_words += max(1, words)

        # Measure sample inference time
        t_start = time.perf_counter()
        try:
            preds = predict_fn(text)
        except Exception as e:
            preds = []
        t_elapsed = time.perf_counter() - t_start
        inference_times.append(t_elapsed)

        # Canonicalize ground truth entities as tuples: (entity_type, start, end)
        gt_tuples = [(g["entity_type"], g["start"], g["end"]) for g in gt_entities]
        pred_tuples = [(p["entity_type"], p["start"], p["end"]) for p in preds]

        # Exact entity-level matching (one-to-one)
        matched_gt_indices = set()
        matched_pred_indices = set()

        for p_idx, p in enumerate(pred_tuples):
            for g_idx, g in enumerate(gt_tuples):
                if g_idx not in matched_gt_indices and p == g:
                    matched_gt_indices.add(g_idx)
                    matched_pred_indices.add(p_idx)
                    tp_global += 1
                    get_ent_bucket(p[0])["tp"] += 1
                    break

        # False positives: predictions that did not match any ground truth
        for p_idx, p in enumerate(pred_tuples):
            if p_idx not in matched_pred_indices:
                fp_global += 1
                get_ent_bucket(p[0])["fp"] += 1

        # False negatives: ground truth entities that were never predicted
        for g_idx, g in enumerate(gt_tuples):
            if g_idx not in matched_gt_indices:
                fn_global += 1
                get_ent_bucket(g[0])["fn"] += 1

    total_time = sum(inference_times)
    avg_time_ms = (total_time / len(samples) * 1000.0) if samples else 0.0
    time_per_100_words_ms = (total_time / (total_words / 100.0) * 1000.0) if total_words else 0.0

    global_metrics = compute_metrics(tp_global, fp_global, fn_global)

    # Compute per-entity metrics
    per_entity_metrics = {}
    for ent_type, counts in entity_counts.items():
        m = compute_metrics(counts["tp"], counts["fp"], counts["fn"])
        per_entity_metrics[ent_type] = {
            "tp": counts["tp"],
            "fp": counts["fp"],
            "fn": counts["fn"],
            "precision": m["precision"],
            "recall": m["recall"],
            "f1": m["f1"],
        }

    return {
        "engine": engine_name,
        "tp": tp_global,
        "fp": fp_global,
        "fn": fn_global,
        "precision": global_metrics["precision"],
        "recall": global_metrics["recall"],
        "f1": global_metrics["f1"],
        "f05": global_metrics["f05"],
        "total_time_s": total_time,
        "avg_time_ms": avg_time_ms,
        "time_per_100_words_ms": time_per_100_words_ms,
        "per_entity": per_entity_metrics,
    }


def run_benchmark():
    dataset_path = ROOT_DIR / "evaluation" / "data" / "test_samples.jsonl"
    if not dataset_path.exists():
        print(f"Dataset not found at {dataset_path}")
        return

    samples = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))

    total_gt = sum(len(s.get("entities", [])) for s in samples)
    print("=" * 80)
    print("PRIVACYLENS NLP BENCHMARK EVALUATION")
    print("=" * 80)
    print(f"Total Test Samples: {len(samples)}")
    print(f"Total Ground-Truth Sensitive Entities: {total_gt}")
    print("Matching Strategy: Exact Entity-Level Matching (entity_type, start, end)")
    print("-" * 80)

    # 1. Warm-up and measure loading times
    print("\n[Phase 1] Initializing and Loading Engines...")

    # Regex (no heavy load time)
    t0 = time.perf_counter()
    _ = detect_pii("Test warmup")
    regex_load_time_s = time.perf_counter() - t0

    # spaCy
    t0 = time.perf_counter()
    spacy_engine = NERDetector()
    _ = spacy_engine.detect_entities("Test warmup")
    spacy_load_time_s = time.perf_counter() - t0

    # Transformer
    t0 = time.perf_counter()
    tf_engine = TransformerDetector()
    if tf_engine.is_available:
        _ = tf_engine.detect_entities("Test warmup")
    tf_load_time_s = time.perf_counter() - t0

    print(f"  - Regex Detector Load Time:       {regex_load_time_s * 1000:.2f} ms")
    print(f"  - spaCy (en_core_web_sm) Load:     {spacy_load_time_s:.3f} s")
    if tf_engine.is_available:
        print(f"  - Transformer (bert-base-NER):   {tf_load_time_s:.3f} s")
    else:
        print("  - Transformer (bert-base-NER):   NOT AVAILABLE (Graceful Fallback)")

    # 2. Run evaluations
    print("\n[Phase 2] Running Inference and Scoring across configurations...")

    results = []

    # Config A: Regex Only
    print("  Evaluating [1/4] Regex Only...")
    results.append(evaluate_dataset(detect_pii, samples, "Regex"))

    # Config B: spaCy Only
    print("  Evaluating [2/4] spaCy Only...")
    results.append(evaluate_dataset(spacy_engine.detect_entities, samples, "spaCy"))

    # Config C: Transformer Only
    print("  Evaluating [3/4] Transformer Only...")
    if tf_engine.is_available:
        results.append(evaluate_dataset(tf_engine.detect_entities, samples, "Transformer"))
    else:
        results.append({
            "engine": "Transformer (N/A)",
            "tp": 0, "fp": 0, "fn": total_gt,
            "precision": 0.0, "recall": 0.0, "f1": 0.0, "f05": 0.0,
            "total_time_s": 0.0, "avg_time_ms": 0.0, "time_per_100_words_ms": 0.0,
            "per_entity": {},
        })

    # Config D: Combined Detector
    print("  Evaluating [4/4] Combined Detector...")
    results.append(evaluate_dataset(detect_all, samples, "Combined"))

    # 3. Overall Comparison Table
    print("\n" + "=" * 80)
    print("FINAL BENCHMARK COMPARISON TABLE")
    print("=" * 80)
    header = f"{'Engine':<16} | {'Precision':<9} | {'Recall':<9} | {'F1-Score':<9} | {'F0.5-Score':<10} | {'Avg Time (ms)':<13}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['engine']:<16} | "
            f"{r['precision'] * 100:>8.2f}% | "
            f"{r['recall'] * 100:>8.2f}% | "
            f"{r['f1'] * 100:>8.2f}% | "
            f"{r['f05'] * 100:>9.2f}% | "
            f"{r['avg_time_ms']:>13.2f}"
        )
    print("=" * 80)

    # 4. Confusion Counts Table
    print("\n" + "=" * 80)
    print("CONFUSION COUNTS BREAKDOWN (TP, FP, FN)")
    print("=" * 80)
    counts_header = f"{'Engine':<16} | {'TP':<6} | {'FP':<6} | {'FN':<6} | {'Total Preds':<11} | {'Ground Truth':<12}"
    print(counts_header)
    print("-" * len(counts_header))
    for r in results:
        total_preds = r["tp"] + r["fp"]
        print(
            f"{r['engine']:<16} | "
            f"{r['tp']:<6} | "
            f"{r['fp']:<6} | "
            f"{r['fn']:<6} | "
            f"{total_preds:<11} | "
            f"{total_gt:<12}"
        )
    print("=" * 80)

    # 5. Per-Entity Evaluation Table (Combined Engine)
    print("\n" + "=" * 80)
    print("PER-ENTITY EVALUATION (Combined Engine Breakdown)")
    print("=" * 80)
    ent_header = f"{'Entity Type':<20} | {'Precision':<9} | {'Recall':<9} | {'F1-Score':<9} | {'TP':<5} | {'FP':<5} | {'FN':<5}"
    print(ent_header)
    print("-" * len(ent_header))

    combined_res = results[-1]
    major_entities = [
        "PERSON",
        "ORGANIZATION",
        "LOCATION",
        "EMAIL",
        "PHONE",
        "PAN",
        "AADHAAR",
        "IFSC_CODE",
        "UPI_ID",
        "PASSWORD",
        "API_KEY",
        "IP_ADDRESS",
        "PINCODE",
        "DATE",
        "FINANCIAL_AMOUNT",
    ]

    for ent in major_entities:
        data = combined_res["per_entity"].get(ent)
        if data:
            print(
                f"{ent:<20} | "
                f"{data['precision'] * 100:>8.2f}% | "
                f"{data['recall'] * 100:>8.2f}% | "
                f"{data['f1'] * 100:>8.2f}% | "
                f"{data['tp']:<5} | "
                f"{data['fp']:<5} | "
                f"{data['fn']:<5}"
            )
        else:
            # Check other engines if combined had no entries
            print(f"{ent:<20} | {'N/A':>9} | {'N/A':>9} | {'N/A':>9} | {'0':<5} | {'0':<5} | {'0':<5}")

    print("=" * 80)

    # 6. Academic Analysis & Discussion
    print("\n" + "=" * 80)
    print("ACADEMIC INSIGHTS & METHODOLOGY EXPLANATION")
    print("=" * 80)
    print("""
1. Structured Identifiers vs. Linguistic Entities:
   - Regex excels on structured tokens (EMAIL, PHONE, PAN, AADHAAR, IFSC, IP, UPI)
     because they adhere to strict deterministic syntaxes and checksums.
   - spaCy and Transformer NER excel on unstructured named entities (PERSON,
     ORGANIZATION, LOCATION) that require syntactic context and word embeddings.

2. F0.5-Score Justification in Privacy Engineering:
   - In privacy-preserving text anonymization, False Positives (over-redacting
     ordinary words) degrade downstream readability and NLP utility.
   - F0.5 weights Precision twice as heavily as Recall (beta = 0.5), prioritizing
     accurate non-invasive redactions over aggressive over-anonymization.

3. Combined Engine Behavior:
   - The Combined Engine maximizes Recall by pooling complementary detectors.
   - However, combining multiple independent models can also accumulate False
     Positives from each sub-engine, making F0.5 and precision crucial monitors.
""")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()

