# Single-Model Judges

This directory contains the one-shot evaluation results for four individual
LLM judges reported in RQ3.1:

- DeepSeek-V3.2
- Gemini-2.5-Pro
- GPT-5
- Qwen3-Max

`outputs/single_model_scores/` contains the cleaned saved scores and
explanations. Each dimension workbook contains only these four models.

`outputs/four_model_single_shot_metrics.xlsx` summarizes their agreement with
the final human labels using the four paper metrics: Exact Match, Quadratic
Weighted Kappa, Spearman's rho, and Gwet's AC2.

Run:

```bash
python compute_single_model_metrics.py
```

to recompute the summary from the saved outputs and
`llm-evaluation/datasets/*/human_scores.xlsx`.
