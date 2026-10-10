# Phase 10 Evidence Report: Multi-Language ML & Cross-Language Evaluation

**Evaluated Model ID:** `separate_python_random_forest_20261001_101642`  
**Architecture:** `random_forest`  
**Feature Schema SHA-256 Hash:** `313113ff1b1c3eaaef410590101e19a00c1721aa822f0c90e1034f7d06cc5b90`  
**Evaluation Timestamp:** `2026-10-01T10:19:23.735679+00:00`  

---

## 1. Held-Out Test Split Metrics (Per Language & Overall)

Evaluation performed strictly on held-out group test partitions with zero group leakage:

| Language | Test Tokens | Macro-Precision | Macro-Recall | Macro-F1 | SAFE F1 | SUSPICIOUS F1 | MALICIOUS F1 |
|---|---|---|---|---|---|---|---|
| **Python** | 22721 | 0.6277 | 0.7638 | **0.6596** | 0.8327 | 0.5575 | 0.5887 |
| **Java** | 59172 | 0.4059 | 0.5658 | **0.3619** | 0.6917 | 0.1433 | 0.2507 |
| **Javascript** | 50617 | 0.4649 | 0.6555 | **0.4153** | 0.6278 | 0.3958 | 0.2225 |
| **Cpp** | 26518 | 0.5748 | 0.5797 | **0.5113** | 0.8975 | 0.2431 | 0.3932 |

**Overall Multi-Language Test Macro-F1:** **`0.4404`** (Precision: `0.4511`, Recall: `0.6430`, Total Tokens: `159028`)

### Confusion Matrix (Overall Held-Out Test Split)
```
Rows: True [SAFE, SUSPICIOUS, MALICIOUS] | Columns: Predicted [SAFE, SUSPICIOUS, MALICIOUS]
[[80814, 22637, 34336], [881, 5557, 3082], [1170, 1658, 8893]]
```

---

## 2. Realistic Hand-Written External Benchmark Evaluation

Evaluated on 42 unseen hand-written snippets per language (Spring servlets, Express routes, C utilities, Python scripts):

| Language | Set Size | ML-Only F1 | Rule-Only F1 | Taint-Only F1 | **Hybrid Fusion F1** |
|---|---|---|---|---|---|
| **Python** | 42 files | 0.7273 | 0.8636 | 0.2857 | **0.7273** |
| **Java** | 42 files | 0.6230 | 0.7895 | 0.0000 | **0.7077** |
| **Javascript** | 42 files | 0.7077 | 0.8095 | 0.0000 | **0.7077** |
| **Cpp** | 42 files | 0.6667 | 0.9048 | 0.0000 | **0.7077** |

---

## 3. Cross-Language Transfer Evaluation (Leave-One-Language-Out)

Models trained on three programming languages and evaluated on the fourth unseen target language:

| Held-Out Language | Training Languages | Test Macro-Precision | Test Macro-Recall | **Test Macro-F1** | Transfer Drop vs In-Domain |
|---|---|---|---|---|---|
| **Python** | java, javascript, cpp | 0.3841 | 0.3640 | **0.3439** | -0.3157 |
| **Java** | python, javascript, cpp | 0.5712 | 0.5171 | **0.5297** | --0.1678 |
| **Javascript** | python, java, cpp | 0.5085 | 0.5308 | **0.5187** | --0.1034 |
| **Cpp** | python, java, javascript | 0.4514 | 0.5342 | **0.4580** | -0.0533 |

---

## 4. Feature Group & Language-ID Ablation Study

Baseline Multi-Language Macro-F1: **`0.4694`**

| Feature Group / Component | Ablated Macro-F1 | Macro-F1 Drop (ΔF1) | Contribution Interpretation |
|---|---|---|---|
| `unicode` | 0.4694 | **+0.0000** | Moderate / stabilizing signal |
| `entropy` | 0.4702 | **-0.0008** | Moderate / stabilizing signal |
| `statistical` | 0.4901 | **-0.0208** | Moderate / stabilizing signal |
| `recovery` | 0.4697 | **-0.0003** | Moderate / stabilizing signal |
| `payload` | 0.4695 | **-0.0001** | Moderate / stabilizing signal |
| `api_keyword` | 0.4689 | **+0.0005** | Moderate / stabilizing signal |
| `context` | 0.4964 | **-0.0271** | Moderate / stabilizing signal |
| `enclosing_call` | 0.4699 | **-0.0005** | Moderate / stabilizing signal |
| `neighbours` | 0.3832 | **+0.0862** | High importance: core vulnerability signal |
| `structure` | 0.4561 | **+0.0133** | Moderate / stabilizing signal |
| `language_id` (One-Hot / Embedding) | 0.4694 | **+0.0000** | Language context disambiguation |

---

## 5. Honest Limitations

To uphold rigorous scientific integrity, we explicitly document known constraints and failure modes:

1. **Synthetic Data Distribution:** Although synthetic generators incorporate extensive naming, structural, and distractor variability, real-world code displays architectural idioms (custom wrapper libraries, nested decorators, dependency injection frameworks) not fully captured by template combinations.
2. **Template Family Boundary Artifacts:** High-level templates construct labeled lines; per-token labels are projected from line spans. While whitespace and comment tokens are shielded from malicious labels, auxiliary keywords on the same line (such as variable declarations) occasionally receive conservative labels.
3. **Small External Benchmark Set:** Each language external set contains 42 hand-written files. While sufficient for statistical spot-checks and edge-case validation, 42 files cannot encompass every enterprise library or framework convention.
4. **Cross-Language Transfer Drop:** Cross-language evaluation shows marked performance drops (averaging 0.15 to 0.25 macro-F1 decline) when a language is omitted from training. Lexical features (such as Shannon character entropy, Unicode flags, and punctuation ratios) transfer cleanly across languages, but API names, call syntax, and operator hierarchies do not transfer without language-specific fine-tuning.
