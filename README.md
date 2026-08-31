# IRIS Replication Package

This repository contains the replication package for:

> What Constitutes a Good Security Code Review Comment?  
> A Multi-Dimensional Assessment Framework

IRIS evaluates security code review comments from four dimensions:
Identification, Reason, Impact, and Solution.

## Repository Structure

| Path | Content |
|---|---|
| `data/` | Literature and practitioner-source data used for triangulation. |
| `taxonomy/` | IRIS taxonomy files and taxonomy definitions. |
| `annotation/` | Human scoring files, scoring rubric, and score-distribution/correlation scripts. |
| `questionnaire/` | Practitioner survey questionnaire material. |
| `sampling_new_361/` | The 361-instance sample used for thematic analysis. |
| `llm-evaluation/datasets/` | Dimension-specific evaluation datasets and final human scores. |
| `llm-evaluation/prompts/` | Dimension-specific prompts used for LLM-based assessment. |
| `llm-evaluation/01_single_model_judges/` | One-shot results for GPT-5, Gemini-2.5-Pro, DeepSeek-V3.2, and Qwen3-Max. |
| `llm-evaluation/02_cross_model_median_expert/` | Cross-model median and Qwen3-Max expert-adjudication results. |
| `llm-evaluation/03_single_model_repeated/` | Single-model repeated results and aggregation-strategy analysis. |

## Reproducing Results

Install dependencies:

```bash
python -m pip install -r llm-evaluation/requirements.txt
```

Run the offline evaluation scripts:

```bash
python llm-evaluation/01_single_model_judges/compute_single_model_metrics.py
python llm-evaluation/02_cross_model_median_expert/evaluate_cross_model_strategies.py
python llm-evaluation/02_cross_model_median_expert/plot_single_model_performance.py
python llm-evaluation/03_single_model_repeated/evaluate_aggregation_strategies.py
```

The reported metrics are Exact Match, Quadratic Weighted Kappa, Spearman's rho,
and Gwet's AC2.

This package includes saved evaluation outputs only. It does not include API
keys, URLs, or scripts for calling external LLM services.

## License

This project is released under the MIT License. See `LICENSE` for details.
