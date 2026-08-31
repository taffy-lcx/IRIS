# Cross-Model Median and Expert Strategies

This directory contains the cross-model setting reported in RQ3.2. The three
base judgments come from DeepSeek-V3.2, Gemini-2.5-Pro, and GPT-5. The final
score is produced by either:

- median aggregation over the three base scores, or
- Qwen3-Max expert adjudication when base scores disagree.

The saved run is under:

`outputs/runs/deepseek_gemini_gpt5_qwen3expert_t0/`

Run:

```bash
python evaluate_cross_model_strategies.py
```

to recompute `metrics.xlsx` from the saved results. The metrics are Exact Match, Quadratic
Weighted Kappa, Spearman's rho, and Gwet's AC2.
