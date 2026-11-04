import json
from pathlib import Path
import sys

sys.path.insert(0, "backend")
sys.path.insert(0, ".")

from app.combined_detector import detect_all

samples = [json.loads(line) for line in open('evaluation/data/test_samples.jsonl', encoding='utf-8') if line.strip()]

fps = []
fns = []

for i, sample in enumerate(samples):
    text = sample['text']
    gt = sample['entities']
    gt_tuples = [(g['entity_type'], g['start'], g['end'], g['text']) for g in gt]
    preds = detect_all(text)
    pred_tuples = [(p['entity_type'], p['start'], p['end'], p['text'], p['detectors']) for p in preds]

    matched_gt = set()
    matched_p = set()
    for p_idx, p in enumerate(pred_tuples):
        for g_idx, g in enumerate(gt_tuples):
            if g_idx not in matched_gt and (p[0], p[1], p[2]) == (g[0], g[1], g[2]):
                matched_gt.add(g_idx)
                matched_p.add(p_idx)
                break
    for p_idx, p in enumerate(pred_tuples):
        if p_idx not in matched_p:
            fps.append((i+1, text, p))
    for g_idx, g in enumerate(gt_tuples):
        if g_idx not in matched_gt:
            fns.append((i+1, text, g))

print(f"Total FPs: {len(fps)}")
for sample_no, text, p in fps:
    print(f"Sample {sample_no:02d}: FP [{p[0]}] '{p[3]}' ({p[1]}..{p[2]}) by {p[4]} | Text: '{text}'")

print(f"\nTotal FNs: {len(fns)}")
for sample_no, text, g in fns:
    print(f"Sample {sample_no:02d}: FN [{g[0]}] '{g[3]}' ({g[1]}..{g[2]}) | Text: '{text}'")

