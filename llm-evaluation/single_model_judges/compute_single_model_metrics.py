#!/usr/bin/env python3
"""Compare DeepSeek, Qwen, Gemini, and GPT-5 one-shot scores on all dimensions."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_DIR = Path(__file__).resolve().parent
SCORES_DIR = EXPERIMENT_DIR / "outputs" / "single_model_scores"
METRIC_SCRIPT = ROOT / "shared" / "metric_utils.py"
DIMENSIONS = ("identification", "reason", "impact", "solution")
MODELS = (
    ("DeepSeek-V3.2", "deepseek_v3_2_score"),
    ("Qwen3-Max", "qwen3_max_score"),
    ("Gemini-2.5-Pro", "gemini_2_5_pro_score"),
    ("GPT-5", "gpt5_score"),
)


def load_metric_module():
    spec = importlib.util.spec_from_file_location("metric_functions", METRIC_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {METRIC_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    metric_module = load_metric_module()
    rows: list[dict[str, object]] = []
    for dimension in DIMENSIONS:
        human = pd.read_excel(ROOT / "datasets" / dimension / "human_scores.xlsx", usecols=["ID", dimension])
        scores = pd.read_excel(SCORES_DIR / f"{dimension}_single_model_scores.xlsx")
        merged = human.merge(scores, on="ID", validate="one_to_one")
        expected = pd.to_numeric(merged[dimension], errors="raise").astype(int)
        for model, column in MODELS:
            predicted = pd.to_numeric(merged[column], errors="raise").astype(int)
            metrics = metric_module.compute_metrics(expected, predicted)
            rows.append(
                {
                    "dimension": dimension,
                    "model": model,
                    "n": len(merged),
                    "exact_match": metrics["ExactMatch"],
                    "quadratic_weighted_kappa": metrics["KappaQuadratic"],
                    "spearman_rho": metrics["SpearmanRho"],
                    "gwet_ac2": metrics["GwetAC2"],
                }
            )
    result = pd.DataFrame(rows)
    output = EXPERIMENT_DIR / "outputs" / "four_model_single_shot_metrics.xlsx"
    result.to_excel(output, index=False)
    print(result.to_string(index=False))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
