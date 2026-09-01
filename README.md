# IRIS: A Multi-Dimensional Framework for Security Code Review Comments

This repository contains the replication package for the study:

> **What Constitutes a Good Security Code Review Comment?**
>
> A Multi-Dimensional Assessment Framework

IRIS evaluates the quality of a security code review comment from four
complementary dimensions: **Identification**, **Reason**, **Impact**, and
**Solution**. The package includes the source data used in the study, the
taxonomy and scoring rubric, human annotations, prompts, saved LLM judgments,
and offline analysis scripts.

## IRIS Framework

| Dimension | Guiding question | Score progression |
|---|---|---|
| **Identification** | Does the comment identify a valid defect and localize it precisely? | Invalid or absent identification to precise code-level localization |
| **Reason** | Does the comment explain why the issue occurs? | No explicit reason to generalized causal reasoning |
| **Impact** | Does the comment describe what may happen if the issue is not fixed? | No explicit impact to security or system-level consequences |
| **Solution** | Does the comment provide actionable repair guidance? | No solution to a ready-to-use code-level fix |

Each dimension is rated independently on a four-point ordinal scale. Detailed
definitions and decision criteria are available in the
[scoring rubric](annotation/score_rubric.md). The recurring linguistic
realizations observed in review comments are documented in the
[taxonomy definition](taxonomy/taxonomy_definition.md).

## Research Artifacts

The repository follows the main stages of the study:

```text
Source collection
    -> 361-comment sample and thematic analysis
    -> IRIS taxonomy and four-level scoring rubric
    -> human annotation and agreement analysis
    -> LLM-based assessment experiments
```

| Path | Description |
|---|---|
| [`data/`](data/) | Literature-survey records and practitioner-source posts used for triangulation. |
| [`thematic_analysis/`](thematic_analysis/) | The 361-comment sample, the full comment collection, and staged thematic-analysis results. |
| [`taxonomy/`](taxonomy/) | The final taxonomy, intermediate manual coding workbooks, category definitions, and labeling decision order. |
| [`annotation/`](annotation/) | The IRIS scoring rubric, three manual-scoring batches, final human scores, and analysis scripts. |
| [`questionnaire/`](questionnaire/) | The practitioner questionnaire used in the study. |
| [`llm-evaluation/datasets/`](llm-evaluation/datasets/) | Evaluation instances and final human reference scores, organized by IRIS dimension. |
| [`llm-evaluation/prompts/`](llm-evaluation/prompts/) | Base-judge and expert-adjudicator prompts for each dimension. |
| [`llm-evaluation/01_single_model_judges/`](llm-evaluation/01_single_model_judges/) | One-shot judgments from four individual LLM judges, metrics, and comparison figures. |
| [`llm-evaluation/02_cross_model_median_expert/`](llm-evaluation/02_cross_model_median_expert/) | Cross-model median aggregation and Qwen3-Max expert adjudication results. |
| [`llm-evaluation/03_single_model_repeated/`](llm-evaluation/03_single_model_repeated/) | Three-run, same-model aggregation results and statistical comparisons. |

## Evaluation Data

The evaluation data are separated by dimension:

```text
llm-evaluation/datasets/
|-- identification/
|   |-- instances.xlsx
|   `-- human_scores.xlsx
|-- reason/
|-- impact/
`-- solution/
```

For each dimension, `instances.xlsx` contains the evaluation instances and
`human_scores.xlsx` contains the final human reference labels. The saved model
outputs retain instance identifiers so that predictions can be joined with the
human scores without relying on row order.

## LLM Evaluation Settings

The package contains three offline evaluation settings:

| Setting | Base judgments | Aggregation or adjudication | Main artifacts |
|---|---|---|---|
| **Single-model, one shot** | DeepSeek-V3.2, Gemini-2.5-Pro, GPT-5, and Qwen3-Max | Each model is evaluated independently | Per-dimension scores, explanations, summary metrics, and PDF figures |
| **Cross-model** | DeepSeek-V3.2, Gemini-2.5-Pro, and GPT-5 | Median aggregation or Qwen3-Max adjudication on disagreement | Resolved predictions and strategy metrics |
| **Single-model, repeated** | Three independent runs of DeepSeek-V3.2, Gemini-2.5-Pro, or GPT-5 | Median aggregation or Qwen3-Max adjudication on disagreement | Consolidated predictions, metrics, and significance tests |

Agreement with the human reference labels is reported using:

- Exact Match (EM)
- Quadratic Weighted Kappa (QWK)
- Spearman's rank correlation coefficient (rho)
- Gwet's AC2 with quadratic weights

The repeated-strategy analysis additionally uses the exact McNemar test for
Exact Match and paired bootstrap tests for QWK, Spearman's rho, and Gwet's AC2.

## Getting Started

Clone the repository and create an isolated Python environment:

```bash
git clone https://github.com/taffy-lcx/IRIS.git
cd IRIS

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r llm-evaluation/requirements.txt
```

The analysis code requires Python 3.9 or later. The main dependencies are
`pandas`, `openpyxl`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, and
`irrCAC`.

## Reproducing the Offline Analyses

Run commands from the repository root. The available analysis entry points
are:

```bash
# One-shot metrics for the four individual judges
python llm-evaluation/01_single_model_judges/compute_single_model_metrics.py

# Cross-model median and expert-adjudication metrics
python llm-evaluation/02_cross_model_median_expert/evaluate_cross_model_strategies.py

# Repeated single-model aggregation metrics and statistical tests
python llm-evaluation/03_single_model_repeated/evaluate_aggregation_strategies.py
```

The scripts read the saved workbooks under `llm-evaluation/` and write their
results back to the corresponding `outputs/` directories. Existing output
workbooks and figures are included so that the reported artifacts can be
inspected without rerunning the analyses.

> **Current release note:** the first two entry points import
> `llm-evaluation/shared/metric_utils.py`, which is not included in the current
> repository snapshot. Their saved metrics remain available, but those two
> scripts require the shared utility before they can be recomputed. The repeated
> single-model analysis is self-contained after installing the listed
> dependencies.

## Reproducibility Scope

This repository provides the data, prompts, human labels, saved model outputs,
and offline evaluation code used to inspect and analyze the study results. It
does **not** include API credentials, service URLs, or scripts for sending
requests to external LLM services. Consequently, the saved LLM generations can
be evaluated offline, while regenerating the model responses requires a
separate API setup.

All spreadsheets are provided in `.xlsx` format, and figures are provided as
`.pdf` files where applicable. Paths in the analysis scripts are resolved
relative to the repository, so the commands above do not depend on a specific
local installation directory.

## License

This project is released under the MIT License. See [`LICENSE`](LICENSE) for
details.
