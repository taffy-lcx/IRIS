#!/usr/bin/env python3
"""Evaluate Qwen3-Max adjudication and same-base median on all dimensions."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_DIR = Path(__file__).resolve().parent
RUN_DIR = EXPERIMENT_DIR / "outputs" / "runs" / "deepseek_gemini_gpt5_qwen3expert_t0"
METRIC_SCRIPT = ROOT / "shared" / "metric_utils.py"
DIMENSIONS = ("identification", "reason", "impact", "solution")


def load_metric_module():
    spec = importlib.util.spec_from_file_location("metric_functions", METRIC_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {METRIC_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metric_row(dimension: str, strategy: str, expected: pd.Series, observed: pd.Series, metric_module) -> dict[str, object]:
    metrics = metric_module.compute_metrics(expected, observed)
    return {
        "dimension": dimension,
        "strategy": strategy,
        "n": len(expected),
        "exact_match": metrics["ExactMatch"],
        "quadratic_weighted_kappa": metrics["KappaQuadratic"],
        "spearman_rho": metrics["SpearmanRho"],
        "gwet_ac2": metrics["GwetAC2"],
    }


def main() -> None:
    metric_module = load_metric_module()
    metrics: list[dict[str, object]] = []
    predictions: list[pd.DataFrame] = []
    for dimension in DIMENSIONS:
        result = pd.read_excel(RUN_DIR / dimension / f"deepseek-gemini-gpt5_{dimension}.xlsx")
        human = pd.read_excel(ROOT / "datasets" / dimension / "human_scores.xlsx", usecols=["ID", dimension])
        merged = human.merge(result, on="ID", validate="one_to_one")
        expected = pd.to_numeric(merged[dimension], errors="raise").astype(int)
        expert = pd.to_numeric(merged["final_score"], errors="raise").astype(int)
        base = merged[["normal_score_1", "normal_score_2", "normal_score_3"]].apply(
            pd.to_numeric, errors="raise"
        )
        median = pd.Series(np.median(base.to_numpy(dtype=int), axis=1).astype(int), index=merged.index)
        metrics.append(metric_row(dimension, "qwen3_expert", expected, expert, metric_module))
        metrics.append(metric_row(dimension, "median_no_expert", expected, median, metric_module))
        predictions.append(
            pd.DataFrame(
                {
                    "dimension": dimension,
                    "ID": merged["ID"],
                    "human_score": expected,
                    "qwen3_expert": expert,
                    "median_no_expert": median,
                    "same_prediction": expert.eq(median),
                    "decision_method": merged["decision_method"],
                }
            )
        )
    metric_df = pd.DataFrame(metrics)
    prediction_df = pd.concat(predictions, ignore_index=True)
    output = RUN_DIR / "metrics.xlsx"
    with pd.ExcelWriter(output) as writer:
        metric_df.to_excel(writer, sheet_name="metrics", index=False)
        prediction_df.to_excel(writer, sheet_name="predictions", index=False)
    print(metric_df.to_string(index=False))
    print("agreement", prediction_df.groupby("dimension")["same_prediction"].mean().to_dict())
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
