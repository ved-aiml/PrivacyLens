# PrivacyLens — Presentation & Viva Preparation Guide

An NLP-based on-device system for detecting sensitive personal identifiable information (PII) and performing context-preserving text anonymization.

---

## 1. Problem Statement
With the widespread adoption of Large Language Models (LLMs) and cloud-based AI tools (e.g., ChatGPT, Claude, external APIs), users and organizations frequently paste sensitive text into remote services. Unintentional exposure of Personally Identifiable Information (PII) — such as names, phone numbers, government identification numbers (PAN, Aadhaar), financial identifiers (IFSC, UPI), and credentials (passwords, API keys) — leads to serious privacy violations, compliance penalties (under GDPR, DPDP Act 2023), and security vulnerabilities.

---

## 2. Project Objective
Build a lightweight, explainable, and fully local Natural Language Processing (NLP) system called **PrivacyLens** that:
1. Detects both structured and unstructured sensitive information in raw text.
2. Anonymizes detected entities using consistent, entity-specific placeholders (e.g., `[PERSON_1]`, `[EMAIL_1]`).
3. Preserves a local anonymization mapping on-device so sensitive data is never exposed to downstream external models or servers.
4. Operates 100% locally on CPU without relying on external APIs, cloud services, databases, or web servers.

---

## 3. Architecture & Approaches

PrivacyLens combines three complementary paradigms:

### A. Regular Expressions (Rule-Based Matching)
- **Why Regex?** Structured PII adheres to rigid, deterministic syntactical formats defined by standards and regulatory authorities (e.g., email RFC 5322, Indian PAN checksum format `[A-Z]{5}[0-9]{4}[A-Z]`, 12-digit Aadhaar, 11-character IFSC codes, IPv4 addresses, and UUIDs).
- **Strengths:** Blazing fast execution (~0.1 ms per sample), 100% precision on well-formed identifiers, deterministic behavior, and zero GPU/model memory requirements.
- **Role in Pipeline:** Serves as the primary detector for structured and numerical identifiers.

### B. spaCy Named Entity Recognition (Statistical / CNN-Based)
- **Why spaCy (`en_core_web_sm`)?** Natural language text contains unstructured entities (human names, organizations, locations) that do not follow fixed patterns and cannot be parsed with regular expressions.
- **Strengths:** Highly optimized transition-based statistical NER pipeline with fast inference (~6 ms per sample), low memory footprint (~15 MB), and multi-class token classification (PERSON, ORG, GPE/LOC, DATE, TIME, MONEY).
- **Role in Pipeline:** Provides rapid linguistic extraction of common proper nouns and entities.

### C. Transformer Named Entity Recognition (Contextual Attention-Based)
- **Why Transformers (`dslim/bert-base-NER`)?** Pretrained bidirectional transformer encoders (BERT) capture deep semantic and syntactic contextual relationships through self-attention mechanisms.
- **Strengths:** Resolves ambiguous polysemous words based on sentence context (e.g., distinguishing "Apple" as an organization versus a fruit; identifying "May" as a person's name versus a month).
- **Role in Pipeline:** High-capacity contextual model that catches complex and out-of-vocabulary person names, international organizations, and locations.

### D. Why Combine Them? (Presidio / AI4Privacy Hierarchy)
No single technique solves all privacy detection challenges:
- **Regex alone** fails completely on human names and organizations (Recall ~50.60%).
- **Pretrained NER models alone** fail on domain-specific identifiers (PAN, Aadhaar, IFSC, UPI) because standard language models were never trained on tax/banking codes.
- **Recognizer Hierarchy Conflict Resolution:** When Regex validates a structured token (e.g. Phone, PAN, Aadhaar), lower-confidence overlapping generic tags from statistical NER (e.g. marking digits as DATE) are suppressed.
- **Result:** Combining them boosts dataset Recall from ~50% to **98.80%** while maintaining **88.17% Precision** and an **F1-Score of 93.18%**!

---

## 4. Evaluation Methodology & Metrics

Evaluation uses **exact entity-level matching**: a prediction is considered correct if and only if:
1. The `entity_type` matches the ground truth.
2. The `start` character offset matches exactly.
3. The `end` character offset matches exactly.

### A. Confusion Counts
- **True Positive (TP):** A sensitive entity was correctly detected with the right type and exact boundaries.
- **False Positive (FP):** The detector flagged a span that is harmless or misclassified an entity type (e.g., marking a phone number as a date).
- **False Negative (FN):** A sensitive entity existed in the text but was completely missed by the detector.

### B. Precision ($P$)
Measures the reliability of detections: of all entities flagged, what percentage was actually correct?
$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$
- *Example:* If $\text{TP} = 80$ and $\text{FP} = 20$:
  $$\text{Precision} = \frac{80}{80 + 20} = 0.80 = 80\%$$

### C. Recall ($R$)
Measures the coverage of the system: of all true sensitive entities present, what percentage did we catch?
$$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
- *Example:* If $\text{TP} = 80$ and $\text{FN} = 20$:
  $$\text{Recall} = \frac{80}{80 + 20} = 0.80 = 80\%$$

### D. F1-Score
The harmonic mean of Precision and Recall, giving equal weight to both:
$$\text{F1} = \frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$
- *Example:* If $P = 0.88$ and $R = 0.98$:
  $$\text{F1} = \frac{2 \times 0.88 \times 0.98}{0.88 + 0.98} \approx 0.927 = 92.7\%$$

### E. F0.5-Score (Privacy-Centric Metric)
In privacy-preserving text sanitization, **false positives matter significantly**. Over-redacting ordinary words ruins the downstream readability, syntax, and utility of the text for language models or human reviewers. Therefore, we weight Precision more heavily than Recall ($\beta = 0.5$):
$$F_\beta = (1 + \beta^2) \times \frac{\text{Precision} \times \text{Recall}}{\beta^2 \times \text{Precision} + \text{Recall}}$$
Setting $\beta = 0.5 \implies 1 + \beta^2 = 1.25$ and $\beta^2 = 0.25$:
$$F_{0.5} = \frac{1.25 \times \text{Precision} \times \text{Recall}}{0.25 \times \text{Precision} + \text{Recall}}$$
- *Example:* If $P = 0.8817$ and $R = 0.9880$:
  $$F_{0.5} = \frac{1.25 \times (0.8817 \times 0.9880)}{0.25 \times 0.8817 + 0.9880} = \frac{1.0889}{0.2204 + 0.9880} = \frac{1.0889}{1.2084} \approx 0.9011 = 90.11\%$$

---

## 5. Actual Experimental Results (Benchmark on 48 Samples, 83 Entities)

### A. Overall Benchmark Comparison Table

| Engine | Precision | Recall | F1-Score | F0.5-Score | Avg Inference Time |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Regex Only** | **100.00%** | 50.60% | 67.20% | 83.67% | **0.13 ms** |
| **spaCy Only** | 76.00% | 45.78% | 57.14% | 67.14% | 6.51 ms |
| **Transformer Only** | 83.33% | 48.19% | 61.07% | 72.73% | 46.51 ms |
| **Combined Detector**| **88.17%** | **98.80%** | **93.18%** | **90.11%** | 62.76 ms |

*One-time model loading time (reported separately):*
- Regex: $0.04\text{ ms}$
- spaCy: $0.808\text{ s}$
- Transformer (BERT): $10.830\text{ s}$

### B. Confusion Counts Breakdown

| Engine | TP | FP | FN | Total Predictions | Ground Truth Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Regex** | 42 | 0 | 41 | 42 | 83 |
| **spaCy** | 38 | 12 | 45 | 50 | 83 |
| **Transformer** | 40 | 8 | 43 | 48 | 83 |
| **Combined** | **82** | 11 | **1** | 93 | 83 |

### C. Per-Entity Breakdown (Combined Engine)

| Entity Type | Precision | Recall | F1-Score | TP | FP | FN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `PERSON` | 93.75% | 93.75% | 93.75% | 15 | 1 | 1 |
| `LOCATION` | 94.12% | 100.00% | 96.97% | 16 | 1 | 0 |
| `EMAIL` | 100.00% | 100.00% | 100.00% | 4 | 0 | 0 |
| `PHONE` | 100.00% | 100.00% | 100.00% | 5 | 0 | 0 |
| `PAN` | 100.00% | 100.00% | 100.00% | 3 | 0 | 0 |
| `AADHAAR` | 100.00% | 100.00% | 100.00% | 4 | 0 | 0 |
| `IFSC_CODE` | 100.00% | 100.00% | 100.00% | 2 | 0 | 0 |
| `UPI_ID` | 100.00% | 100.00% | 100.00% | 3 | 0 | 0 |
| `PASSWORD` | 100.00% | 100.00% | 100.00% | 2 | 0 | 0 |
| `API_KEY` | 100.00% | 100.00% | 100.00% | 2 | 0 | 0 |
| `IP_ADDRESS` | 100.00% | 100.00% | 100.00% | 3 | 0 | 0 |
| `PINCODE` | 100.00% | 100.00% | 100.00% | 2 | 0 | 0 |
| `FINANCIAL_AMOUNT` | 100.00% | 100.00% | 100.00% | 3 | 0 | 0 |
| `ORGANIZATION` | 69.23% | 100.00% | 81.82% | 9 | 4 | 0 |
| `DATE` | 50.00% | 100.00% | 66.67% | 3 | 3 | 0 |

---

## 6. Real-World Datasets & Industry Standards
In industrial privacy engineering (e.g. Microsoft Presidio, Hugging Face PII auditing):
1. **`ai4privacy/pii-masking-300k`**: The leading open-source multilingual dataset for synthetic PII masking, demonstrating that hybrid rule+model pipelines achieve higher robustness than deep learning alone.
2. **Microsoft Presidio Benchmark**: Demonstrates that rule-based recognizers must take precedence over general statistical token classifiers for structured IDs to eliminate false positives.

---

## 7. Limitations of the System
1. **Uncommon / Regional Names:** Pretrained models trained primarily on Western datasets (CoNLL-2003 / OntoNotes) occasionally struggle with uncommon regional naming conventions unless fine-tuned.
2. **Context Ambiguity:** Nouns that can refer to entities or objects (e.g., "Apple", "May", "Amazon") require sufficient context; in terse inputs, NER models may misclassify them.
3. **General NER Scope:** Standard linguistic NER models are unaware of national tax IDs, bank codes, or cryptographic secrets without dedicated rule extensions.

---

## 8. Future Scope
1. **Direct Presidio Integration:** Compare PrivacyLens runtime with full Microsoft Presidio deployments.
2. **Extended Checksums:** Add Verhoeff algorithm for Aadhaar and Luhn algorithm for Credit Cards.
3. **Local Fine-Tuned SLMs:** Fine-tune small language models (e.g. Qwen-2.5-0.5B) directly on PII corpora like `ai4privacy`.
4. **Desktop / Browser Extension:** Real-time clipboard anonymizer for ChatGPT / Claude web interfaces.

---

## 9. Expected Viva / Exam Questions & Answers

### Q1: What is PII, and why is local detection necessary?
**Answer:** PII (Personally Identifiable Information) is any data that can identify an individual (e.g., name, phone number, government ID, email). Local detection is necessary because sending raw sensitive data to third-party cloud APIs to check for privacy defeats the purpose of privacy; processing must occur entirely on-device under a zero-trust model.

### Q2: Why can't we use Regex for everything?
**Answer:** Natural language entities (human names, organizations, locations) have unbounded vocabularies and do not follow deterministic character patterns. A regular expression cannot distinguish whether "Jordan" is a person's name, a country, or a brand without linguistic and contextual understanding.

### Q3: Why can't we use BERT for everything?
**Answer:** Pretrained BERT models are trained on general text corpora to predict linguistic tokens. They have no built-in knowledge of algorithmic identifiers such as 10-character alphanumeric PAN numbers, 12-digit Aadhaar formats, or bank IFSC codes. Additionally, Transformer inference is compute-heavy (~46 ms vs 0.1 ms for Regex).

### Q4: Explain the difference between Precision and Recall in this project.
**Answer:** Precision measures *detection accuracy* ($\frac{\text{TP}}{\text{TP}+\text{FP}}$): out of everything we redacted, how much was actually sensitive? Recall measures *protection completeness* ($\frac{\text{TP}}{\text{TP}+\text{FN}}$): out of all actual sensitive items present, how many did we catch?

### Q5: Why is the F0.5 score emphasized instead of standard F1?
**Answer:** In text anonymization, false positives unnecessarily replace harmless words, destroying the semantic readability of the text. $F_{0.5}$ weights Precision twice as heavily as Recall ($\beta = 0.5$), prioritizing clean, non-invasive redactions over aggressive over-sanitization.

### Q6: How does the system achieve 98.80% Recall and 88.17% Precision?
**Answer:** Through recognizer hierarchy and deduplication. Regex catches structured tokens with 100% precision. When Regex confirms a structured entity (like phone or PAN), any overlapping generic tag from spaCy (like DATE) is suppressed. spaCy and BERT catch names and locations. The union achieves near-complete coverage while filtering false positives.

### Q7: Why do we replace entities from right to left during anonymization?
**Answer:** Replacing strings changes the length of the text. If we replace from left to right, every substitution shifts the character indices for all subsequent entities. Processing from right to left (descending order of start offset) ensures that earlier offsets remain intact and valid.

### Q8: How does PrivacyLens guarantee consistent anonymization for repeated entities?
**Answer:** The anonymizer maintains a local hash table mapping `(entity_type, original_value)` to an assigned placeholder (e.g., `("PERSON", "Rahul Sharma") -> "[PERSON_1]"`). Every subsequent occurrence of that exact tuple reuses `[PERSON_1]`.

### Q9: What happens when two detectors detect overlapping text spans?
**Answer:** If they have the exact same start, end, and entity type, they are deduplicated and their detector names are merged (e.g., `detectors: ["spacy", "transformer"]`). If a validated Regex match collides with generic NER, Regex takes priority. Remaining ambiguous overlaps are preserved and flagged with `overlap_warning`.

### Q10: How does the system handle Transformer model download or import failures?
**Answer:** Through graceful degradation. The Transformer detector initializes within an exception-safe wrapper. If PyTorch or model weights are missing or offline, it sets `is_available = False`, logs a warning, and allows Regex and spaCy to function normally without crashing.

### Q11: What is token aggregation in Transformer NER?
**Answer:** BERT uses WordPiece subword tokenization (e.g., splitting "Rahul" into "Ra" and "##hul"). Token classification outputs predictions per subword. Aggregation groups contiguous subwords of the same entity class back into a single character-level text span matching the original input slice.

### Q12: Why does anonymization replace text from right to left?
**Answer:** When substituting spans with placeholders of differing lengths, replacing from left to right would shift all subsequent character positions and invalidate earlier calculated offsets. Processing spans in descending order of start offsets (right to left) guarantees that every earlier offset remains invariant.

### Q13: What is the computational complexity of the regex detector?
**Answer:** For precompiled regular expressions matching a text of length $N$, deterministic finite automata (DFA) execution runs in $O(N)$ linear time per pattern. Across $K$ patterns, the overall complexity is $O(K \times N)$, which explains the sub-millisecond execution time.

### Q14: How does exact entity-level matching differ from token-level matching?
**Answer:** In token-level matching, getting 2 out of 3 words of an organization correct yields partial credit. In exact entity-level matching, the entire boundary `[start..end]` and class label must match ground truth perfectly. This is a stricter, more academically rigorous benchmark standard.

### Q15: What ethical guidelines are followed in this project's evaluation?
**Answer:** All evaluation samples and demonstration text use exclusively synthetic dummy data (fictitious names, dummy Aadhaar numbers starting with 2..9, RFC 2606 example emails like `example.com`). Zero real personal information is collected, stored, or processed.
