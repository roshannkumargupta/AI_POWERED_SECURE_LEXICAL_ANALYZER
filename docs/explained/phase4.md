# Phase 4 Explained: Leak-Free Token ML Pipeline, 45-Dim Features, Calibration & External Evaluation

---

## 1. Executive Summary & Plain-English Overview

In Phase 4, SecureLex IDE (`apsla`) integrates machine learning into its lexical and static analysis pipeline. While Phase 2 established deterministic syntax and AST rules alongside data-flow taint analysis, real-world code frequently presents ambiguous, obfuscated, or anomalous patterns that cannot be fully captured by rigid pattern-matching alone.

Phase 4 introduces a **token-level classification pipeline** operating over sliding 9-token context windows. The ML subsystem predicts three discrete security categories for every token in a source file:
- `SAFE` (label 0): Standard, non-threatening lexical construct.
- `SUSPICIOUS` (label 1): Token situated in an anomalous, high-entropy, or potentially sensitive syntactic position (e.g., dynamic attribute access, unverified network parameters).
- `MALICIOUS` (label 2): Token associated with high-risk exploit payloads, dangerous sink invocations, or deceptive Unicode homoglyphs.

---

## 2. Core Architecture & Scientific Innovations

### A. The 45-Dimensional Language-Agnostic Feature Vector (`ml/features.py`)
Rather than relying on brittle language-specific AST tokens or huge language models requiring GPUs, `apsla` extracts 45 continuous and normalized statistical, lexical, and structural features per token:

| Feature Index | Feature Name | Description & Security Rationale |
|:---:|:---|:---|
| **0–3** | `kind_id_norm`, `length_norm`, `is_numeric`, `is_keyword` | Lexical identity and token type normalized to $[0, 1]$. |
| **4–9** | `zero_width_count`, `bidi_count`, `confusable_count`, `non_ascii_ratio`, `mixed_script`, `tag_char_count` | Unicode defense metrics detecting Trojan Source attacks, homoglyph confusables, and hidden invisible characters. |
| **10–13** | `char_entropy`, `bigram_entropy`, `trigram_entropy`, `normalised_entropy` | Shannon entropy across character, bigram, and trigram distributions to detect encrypted or obfuscated tokens. |
| **14–18** | `digit_ratio`, `upper_ratio`, `punctuation_ratio`, `whitespace_ratio`, `max_repeated_char_run_norm` | Morphological character composition metrics detecting encoded identifiers, hash constants, or padding. |
| **19–22** | `recovery_changed`, `recovery_diff_ratio`, `recovered_is_dangerous_api`, `recovered_is_keyword` | Unicode recovery differential metrics measuring whether homoglyph replacement unmasked a hidden sensitive API. |
| **23–25** | `looks_base64`, `looks_hex`, `decoded_payload_has_danger_words` | Payload inspection metrics probing for base64/hex encoding and decoding sensitive payloads (`eval`, `sh`, `system`). |
| **26–30** | `dangerous_api_exact`, `dangerous_api_substring`, `sql_keyword`, `shell_pattern`, `fuzzy_dangerous` | Lexical pattern indicators matching dangerous standard library sinks and injection vocabulary. |
| **31–35** | `in_string`, `in_comment`, `is_call`, `is_member_access`, `nesting_depth_norm` | Syntactic context flags identifying if the token is inside a call invocation, attribute chain, string, or deep block. |
| **36–38** | `is_first_argument`, `enclosing_call_has_concatenation`, `enclosing_call_is_known_sink` | Enclosing call semantics capturing whether untrusted arguments or dynamic concatenations enter a sink. |
| **39–41** | `neighbour_danger_density`, `neighbour_string_density`, `neighbour_operator_density` | Surrounding 9-token contextual density metrics capturing the local lexical environment. |
| **42–44** | `is_identifier`, `is_string_literal`, `is_operator` | Fundamental syntactic token classifications. |

### B. Strict Feature Schema Integrity & "No Silent Fallback" Policy
To guarantee complete reproducibility and eliminate silent configuration drift:
- The exact tuple of 45 feature names is hashed with SHA-256 (`FEATURE_SCHEMA_HASH: 313113ff1b1c3eaaef410590101e19a00c1721aa822f0c90e1034f7d06cc5b90`).
- Model metadata files (`meta.json`) store this hash upon creation.
- At runtime, `MLInferenceEngine` validates that the runtime hash exactly matches the artifact hash.
- **No Silent Fallback Policy:** If weights are missing, corrupted, or if schema hashes diverge, ML mode is set to `"off"`. The analyzer never falls back to uninitialized weights or random predictions.

### C. Leak-Free Data Partitioning & The Senior Baseline Problem
In prior academic prototypes (including the senior baseline in `legacy/senior-part1`), tokens were collected across snippets and randomly shuffled before train/test splitting. This introduced severe **data leakage**: tokens originating from identical code snippets appeared simultaneously in training and test sets, artificially inflating test scores to an identical $0.9412$ precision, recall, and F1.

SecureLex IDE eliminates this flaw through:
1. **Group-Aware Splitting:** Partitioning datasets strictly by `(language, template_family, snippet_id)` into 70% train, 15% validation, and 15% test pools. No template structure is shared between splits.
2. **Window De-duplication:** Window text hashes in validation or test splits are excised from training sets to prevent identical syntactic sequences from leaking across boundaries.

### D. Model Evaluation & Selection
Four diverse architectures were evaluated on identical CPU constraints:
1. **Logistic Regression (L2 Balanced):** Fast linear baseline.
2. **HistGradientBoostingClassifier:** Non-linear decision tree ensemble with binned histograms.
3. **WindowedBiLSTM (PyTorch):** Deep sequence architecture ($45 \to 64 \to \text{BiLSTM}(64) \to \text{MLP} \to 3$).
4. **Random Forest (100 estimators, max depth 14):** Robust ensemble providing superior generalization on sparse morphological and statistical features.

Random Forest was selected as the default production architecture due to its high macro-F1, stable CPU inference latency, and memory footprint well under the 50 MB threshold.

### E. Post-Hoc Calibration & Decision Threshold Tuning (`ml/calibrate.py`)
Because benign code contains $>90\%$ `SAFE` tokens, raw model probabilities are prone to over-confidence:
- **Temperature Scaling ($T$):** Optimizes a scalar temperature $T$ using L-BFGS-B on validation cross-entropy to calibrate multi-class probability outputs.
- **Malicious Threshold ($\tau_{\text{malicious}}$):** Sweeps $\tau \in [0.2, 0.8]$ on validation data to maximize the F1-score for the minority `MALICIOUS` class without inundating developers with false positives.

### F. Feature-Group Occlusion Explainability (`ml/explain.py`)
To prevent black-box opacity, `apsla` provides feature-group occlusion:
$$\Delta P = P_{\text{baseline}}(\text{target\_class}) - P_{\text{occluded}}(\text{target\_class})$$
By systematically masking 10 functional feature groups (Unicode, entropy, statistical, recovery, payload, api_keyword, context, enclosing_call, neighbours, structure), the engine reports exactly which feature category contributed most to elevating a token's suspicion score.

### G. Hybrid Detection Fusion (`fusion.py`)
Phase 4 connects deterministic AST rules, taint reachability paths, and machine learning probabilities according to PROJECT_SPEC Section H:
1. **Window Probability:**
   $$ml\_p = \min\left(1.0, \max_{t \in \text{range}}(P(\text{MALICIOUS}) + 0.5 \times P(\text{SUSPICIOUS}))\right)$$
2. **Confidence Blending (when ML is ON):**
   $$\text{Confidence} = 0.7 \times \text{rule\_conf} + 0.3 \times ml\_p$$
3. **Taint Confirmation Boost:**
   $$\text{Confidence} \leftarrow \min(1.0, \text{Confidence} + 0.15), \quad \text{Severity} \leftarrow \min(\text{CRITICAL}, \text{Severity} + 1)$$
4. **Noisy Rule Suppression:** Rules triggering without taint confirmation whose $ml\_p < 0.15$ are demoted by 1 severity tier (`"downgraded: model sees this as usual code"`).
5. **ML-Only Anomaly Rule (`APS-ALL-ML-001`):** High-confidence ML detections without matching rules generate anomaly findings (capped at 10 per file).

---

## 3. Concept Glossary

- **Sliding Context Window ($win=9$):** An asymmetric sliding window centered on token $i$ with 4 preceding and 4 succeeding tokens, providing local syntactic context.
- **Shannon Entropy:** A statistical metric of information content: $H(X) = -\sum p(x) \log_2 p(x)$. High character entropy indicates compressed or encrypted payloads.
- **Group-Aware Splitting:** Splitting data based on source document IDs rather than individual data points, preventing data leakage between evaluation partitions.
- **Temperature Scaling ($T$):** Dividing model logits by scalar $T$ before softmax to adjust confidence without altering rank ordering.
- **Malicious Decision Threshold ($\tau$):** A tuned decision boundary for class 2 that balances precision and recall on severely imbalanced datasets.
- **Feature Occlusion Importance:** An explainability technique that zeros out feature subsets to observe the resulting decrease in class probability.
- **Score Fusion:** The mathematical synthesis of deterministic AST rules, taint flow analysis, and statistical ML probabilities into a single confidence rating.

---

## 4. Viva Voce Q&A (Machine Learning & Static Code Analysis)

### Q1: Why is token-level random train/test splitting strictly forbidden in code security ML, and how does group-aware splitting prevent data leakage?
**Answer:**  
In source code, tokens are not independent and identically distributed (i.i.d.) variables; they are deeply contextual and derived from overarching syntactic templates and variable naming conventions. If tokens are split randomly across train and test sets, tokens from the same function or snippet appear in both partitions. The model will memorize snippet-specific identifiers (e.g., a specific database handle or variable name) and achieve artificially inflated test scores ($>94\%$) that fail completely on unseen real-world code.  
Group-aware splitting partitions data strictly at the `(language, template_family, snippet_id)` level. All tokens belonging to a given code snippet or template family reside entirely within train, validation, or test. This ensures that the model is evaluated on genuine syntactic and lexical generalization.

### Q2: Why does SecureLex IDE compute Shannon entropy at character, bigram, and trigram levels for lexical tokens?
**Answer:**  
Standard character entropy alone is insufficient to distinguish legitimate long identifier names from obfuscated strings. For example, a repeating hex string like `"abababababab"` has very low character entropy, while natural text with varied letters can have moderate entropy.  
By computing n-gram entropy across bigrams and trigrams alongside normalized character entropy, the model measures sequential transition predictability. Random base64 payloads, high-entropy cryptographic keys, and shellcode buffers exhibit uniformly high entropy across all three n-gram tiers, whereas natural identifiers and code syntax exhibit steep drops in higher-order n-gram entropy due to phonetic and grammatical structure.

### Q3: What is the "No Silent Fallback" policy and why is it essential for dependable security tools?
**Answer:**  
In conventional machine learning deployments, if a model weight file is missing or a feature vector dimension mismatches, systems often fall back silently—either by padding features with zeros or predicting uniform random probabilities. In a security analysis tool, silent fallbacks are hazardous: developers relying on automated security audits would receive non-deterministic or invalid confidence scores without any indication of system failure.  
SecureLex IDE enforces strict feature schema hashing (`FEATURE_SCHEMA_HASH`). If weights are missing, corrupted, or if the 45-feature schema differs by even a single entry, ML mode is explicitly set to `"off"`. This state is declared in every API response, surfaced in the CLI, and visually badged in the UI, ensuring full transparency.

### Q4: Why is post-hoc temperature scaling and decision threshold tuning ($\tau$) necessary for token security classification?
**Answer:**  
Modern supervised classifiers (such as neural networks and deep decision forests) are notoriously uncalibrated: their predicted softmax probabilities reflect decision boundary distances rather than true empirical probabilities of error. Furthermore, code security datasets are heavily skewed: $>90\%$ of tokens in real code are benign (`SAFE`). Standard argmax classification ($P > 0.5$) would either suffer from severe recall deficiency or catastrophic false positive rates.  
Post-hoc temperature scaling optimizes a scalar $T$ on validation cross-entropy to align predicted probabilities with actual empirical likelihoods. Tuning $\tau_{\text{malicious}}$ on validation data allows the engine to maximize the minority class F1-score without shifting the underlying model weights.

### Q5: How does feature-group occlusion explainability work, and why is it preferred over black-box token attribution?
**Answer:**  
Black-box attribution methods (such as integrated gradients or permutation on individual feature dimensions) often produce noisy, difficult-to-interpret weights across 405 window dimensions ($9 \times 45$). A developer reviewing an alert does not benefit from knowing that "dimension 17 had weight 0.04."  
Feature-group occlusion groups related features into 10 semantic buckets (e.g., `unicode`, `payload`, `entropy`, `enclosing_call`). By zeroing out an entire group across all 9 timesteps in the window and measuring the resulting probability drop $\Delta P = P_{\text{baseline}} - P_{\text{occluded}}$, the system explains the prediction in intuitive, developer-actionable terms: for instance, demonstrating that high `entropy` and `payload` encoding were the primary factors elevating suspicion.
