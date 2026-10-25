# Phase 12 Evidence — Active Learning & Feedback Retraining

- **Date:** 2026-10-25T13:09:52.850503+00:00
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
| External Benchmark | Macro F1 | 0.0000 | -0.1500 | -0.1500 |
| External Benchmark | Precision | 0.0000 | 0.0000 | +0.0000 |
| External Benchmark | Recall | 0.0000 | 0.0000 | +0.0000 |

## Safety Decision: REFUSED

> [!WARNING]
> External set macro F1 degraded from 0.0000 to -0.1500. Incorporating user false-positive hard negatives caused model overfitting or generalizability regression. Per Phase 12 safety policy, SecureLex REFUSES to deploy this artifact into production.
