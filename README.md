# PrivacyLens — NLP-Based Privacy Detection & Text Anonymization

**PrivacyLens** is a lightweight, explainable, and fully local Natural Language Processing (NLP) pipeline designed to detect sensitive Personally Identifiable Information (PII) in text and replace it with context-preserving placeholders.

---

## Key Highlights
- **100% Local & Offline:** No external APIs, no cloud servers, no databases, and no frontends or backends. Runs entirely on CPU.
- **Three Complementary Detection Engines:**
  1. **Regex-Based Detection:** High-speed deterministic extraction of structured identifiers (Email, Phone, PAN, Aadhaar, IFSC, UPI, IP, Passwords, API Keys, Financial Amounts).
  2. **spaCy NER (`en_core_web_sm`):** Fast statistical entity recognition for common proper nouns (Person, Organization, Location, Date, Time, Financial Amount).
  3. **Transformer NER (`dslim/bert-base-NER`):** Deep bidirectional contextual attention model for resolving ambiguous names, organizations, and locations with graceful offline fallback.
- **Combined Deduplication & Conflict Resolution:** Implements Microsoft Presidio recognizer hierarchy — validated structured tokens override generic NLP tags, removing duplicates and boosting F1 score to 93.18%.
- **Right-to-Left Anonymizer:** Replaces sensitive spans using exact character offsets from right to left, assigning consistent placeholders (e.g. `[PERSON_1]`) to repeated identical entities.
- **Local Anonymization Mapping:** Securely maps assigned placeholders to their original values locally without exposing raw text.
- **Rigorous Academic Evaluation:** Evaluated on 48 synthetic annotated samples (83 ground-truth entities) with exact entity-level matching, measuring Precision, Recall, F1, F0.5, and inference latencies.

---

## Project Structure

```
Privacy_lens/
├── app/                        # Application package (root accessible)
│   ├── detector.py             # Regex-based PII detector
│   ├── patterns.py             # Precompiled regular expressions
│   ├── validators.py           # Domain format & checksum validators
│   ├── ner_detector.py         # spaCy statistical NER detector
│   ├── transformer_detector.py # Hugging Face Transformer NER detector
│   ├── combined_detector.py    # Multi-engine consensus, conflict resolution & deduplication
│   └── anonymizer.py           # Right-to-left anonymization
├── backend/                    # Original backend directory (preserved)
│   ├── app/                    # Core source modules
│   ├── tests/                  # Test suite
│   ├── requirements.txt        # Dependency specification
│   └── venv/                   # Python virtual environment
├── demo.py                     # Interactive terminal demonstration script
├── evaluation/
│   ├── data/
│   │   └── test_samples.jsonl  # 48 verified synthetic benchmark samples
│   └── evaluate.py             # Academic benchmarking & metric reporting script
├── PRESENTATION_NOTES.md       # Comprehensive presentation guide & 15 viva Q&As
├── README.md                   # Project documentation
└── tests/
    └── test_detector.py        # 43 unit tests covering all components
```

---

## Installation & Setup

1. **Activate the Virtual Environment:**
   - **PowerShell (Windows):**
     ```powershell
     .\backend\venv\Scripts\Activate.ps1
     ```
   - **Command Prompt (Windows):**
     ```cmd
     backend\venv\Scripts\activate.bat
     ```
   - **Linux / macOS:**
     ```bash
     source backend/venv/bin/activate
     ```

2. **Install Dependencies (if setting up fresh environment):**
   ```bash
   pip install -r backend/requirements.txt
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   pip install transformers
   python -m spacy download en_core_web_sm
   ```

---

## Usage Commands

### 1. Run the Terminal Demo
Demonstrates detection across Regex, spaCy, Transformer, Combined engine, and anonymization on sample text:
```bash
python demo.py
```
*Optional custom input:*
```bash
python demo.py "My name is John Doe, email john@example.com, phone 9876543210."
```

### 2. Run the Benchmark Evaluation
Evaluates all four configurations on the verified 48-sample dataset with exact entity-level matching:
```bash
python evaluation/evaluate.py
```

### 3. Run the Unit Test Suite
Runs all 43 automated unit tests verifying regex patterns, validators, spaCy NER, Transformer NER, combined engine deduplication, and anonymization:
```bash
python -m pytest tests
```

---

## Actual Evaluation Benchmark Results

Evaluated on **48 manually annotated synthetic samples** containing **83 ground-truth sensitive entities** with exact entity-level matching `(entity_type, start_offset, end_offset)`:

| Engine | Precision | Recall | F1-Score | F0.5-Score | Avg Inference Time |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Regex Only** | **100.00%** | 50.60% | 67.20% | 83.67% | **0.13 ms** |
| **spaCy Only** | 76.00% | 45.78% | 57.14% | 67.14% | 6.51 ms |
| **Transformer Only** | 83.33% | 48.19% | 61.07% | 72.73% | 46.51 ms |
| **Combined Detector** | **88.17%** | **98.80%** | **93.18%** | **90.11%** | 62.76 ms |

*One-Time Engine Loading Times (reported separately):*
- Regex: `0.04 ms`
- spaCy (`en_core_web_sm`): `0.808 s`
- Transformer (`dslim/bert-base-NER`): `10.830 s`

### Confusion Counts (TP, FP, FN)

| Engine | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Total Predictions | Ground Truth |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Regex** | 42 | 0 | 41 | 42 | 83 |
| **spaCy** | 38 | 12 | 45 | 50 | 83 |
| **Transformer** | 40 | 8 | 43 | 48 | 83 |
| **Combined** | **82** | 11 | **1** | 93 | 83 |

---

## Supported PII Categories

| Detection Engine | Entity Categories |
| :--- | :--- |
| **Regex + Validators** | `EMAIL`, `PHONE`, `PINCODE`, `IP_ADDRESS`, `PAN`, `AADHAAR`, `IFSC_CODE`, `UPI_ID`, `GSTIN`, `VEHICLE_NUMBER`, `PASSPORT`, `VOTER_ID`, `DL_NUMBER`, `RATION_CARD`, `UUID`, `MAC_ADDRESS`, `ORDER_ID`, `TRANSACTION_ID`, `EMPLOYEE_ID`, `PASSWORD`, `API_KEY`, `FINANCIAL_AMOUNT`, `DATE` |
| **spaCy NER** | `PERSON`, `ORGANIZATION`, `LOCATION`, `DATE`, `TIME`, `FINANCIAL_AMOUNT`, `DEMOGRAPHIC_GROUP` |
| **Transformer NER** | `PERSON`, `ORGANIZATION`, `LOCATION`, `MISCELLANEOUS` |

---

## Presentation & Viva Preparation
Refer to [`PRESENTATION_NOTES.md`](file:///c:/Users/Ved%20sharma/Downloads/Privacy_lens/PRESENTATION_NOTES.md) for:
- Detailed breakdown of TP, FP, FN, Precision, Recall, F1, and F0.5 formulas with worked numeric examples.
- Academic discussion on why Regex excels on structured tokens while Transformers excel on contextual entities.
- Recognizer hierarchy conflict resolution (Presidio / AI4Privacy pattern).
- 15 frequently asked viva questions and concise answers.
