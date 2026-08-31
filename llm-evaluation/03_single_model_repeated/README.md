# Single-Model Repeated Strategies

This directory contains the single-model repeated setting reported in RQ3.2.
For each base model, three independent runs are combined using:

- median aggregation over the three repeated scores, or
- Qwen3-Max expert adjudication when the three repeated scores disagree.

The base models are DeepSeek-V3.2, Gemini-2.5-Pro, and GPT-5. The consolidated
three-repeat scores and the resolved median/expert results are under
`outputs/three_repeat_strategies/`.

Run:

```bash
python evaluate_aggregation_strategies.py
```

to recompute the aggregation-strategy metrics and statistical tests from the
saved median/expert outputs. This directory does not include API-calling
generation scripts. The metrics are Exact Match, Quadratic Weighted Kappa,
Spearman's rho, and Gwet's AC2.
