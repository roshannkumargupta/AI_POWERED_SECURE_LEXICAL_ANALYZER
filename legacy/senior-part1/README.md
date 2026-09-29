# AI-Powered Secure Lexical Analyzer

A hybrid rule-based and deep learning system for token-level security
analysis in Python source code.

## What it detects

- Unicode homoglyph attacks (Cyrillic/Greek lookalikes)
- Zero-width character injection
- exec/eval code injection
- SQL injection patterns in strings
- Shell command injection
- Base64 encoded payloads
- Taint flow (user input → dangerous sink)

## Architecture

- **Phase 1**: Unicode Recovery Engine (NFKC + confusable mapping)
- **Phase 2**: Regex tokeniser + token enrichment (entropy, unicode, context)
- **Phase 3**: 45-dimensional feature extraction
- **Phase 4**: BiLSTM sequence classifier (window=5)
- **Phase 5**: Rule engine + taint-lite tracking
- **Phase 6**: Hybrid decision fusion + explainability output

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Run

```bash
# Build dataset
python -m ML_model.build_dataset

# Train model
python -m ML_model.train_model

# Run pipeline on sample inputs
python -m ML_model.run_secure_engine --all-samples

# Start frontend
python -m uvicorn frontend.api:app --reload --port 8000
# Open http://localhost:8000
```

## Project Structure
