# Phase 12 Evidence — Active Learning & Feedback Retraining

- **Date:** 2026-10-11T03:27:41.109203+00:00
- **Language:** python
- **Model Architecture:** logistic_regression
- **Feedback Windows Added to TRAIN:** 4
- **Validation Set Leakage:** 0 (Feedback isolated strictly to TRAIN)

## Performance Comparison (Before vs After Feedback)

| Evaluation Split | Metric | Before Feedback | After Feedback | Delta |
|---|---|---|---|---|
| Validation Split | Macro F1 | 0.7249 | 0.7257 | +0.0009 |
| Validation Split | Precision | 0.6976 | 0.6978 | +0.0002 |
| Validation Split | Recall | 0.8194 | 0.8194 | +0.0000 |
| External Benchmark | Macro F1 | 0.7241 | 0.5741 | -0.1500 |
| External Benchmark | Precision | 0.6176 | 0.6176 | +0.0000 |
| External Benchmark | Recall | 0.8750 | 0.8750 | +0.0000 |

## Safety Decision: REFUSED

> [!WARNING]
> External set macro F1 degraded from 0.7241 to 0.5741. Incorporating user false-positive hard negatives caused model overfitting or generalizability regression. Per Phase 12 safety policy, SecureLex REFUSES to deploy this artifact into production.
