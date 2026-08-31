#!/usr/bin/env python3
"""Statistical tests for the current aggregation table.

This script uses the final blind-review-confirmed ground truth and evaluates
the four paper metrics only:
  EM, quadratic weighted kappa, Spearman rho, Gwet AC2.

No absolute-error metric is included.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from irrCAC.raw import CAC as RawCAC
from irrCAC.weights import Weights
from scipy.stats import binomtest, spearmanr
from sklearn.metrics import cohen_kappa_score


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
DATASET_DIR = PROJECT_ROOT / "datasets"
SAME_BASE_DIR = ROOT / "outputs" / "three_repeat_strategies"
MIXED_BASE_DIR = (
    PROJECT_ROOT
    / "02_cross_model_median_expert"
    / "outputs"
    / "runs"
    / "deepseek_gemini_gpt5_qwen3expert_t0"
)
OUTPUT_DIR = ROOT / "outputs" / "current_aggregation_significance"
OUTPUT_XLSX = OUTPUT_DIR / "current_aggregation_significance_tests.xlsx"

DIMENSIONS = ["identification", "reason", "impact", "solution"]
N_BOOTSTRAP = 10000
RANDOM_SEED = 1327
SCORES = [1, 2, 3, 4]
Q = len(SCORES)
AC2_WEIGHTS = Weights(SCORES)["quadratic"]


@dataclass(frozen=True)
class Method:
    setting: str
    strategy: str

    @property
    def label(self) -> str:
        return f"{self.setting} | {self.strategy}"


METHODS = [
    Method("Cross-model", "Median"),
    Method("Cross-model", "Expert"),
    Method("DeepSeek-V3.2 x3", "Median"),
    Method("DeepSeek-V3.2 x3", "Expert"),
    Method("Gemini-2.5-Pro x3", "Median"),
    Method("Gemini-2.5-Pro x3", "Expert"),
    Method("GPT-5 x3", "Median"),
    Method("GPT-5 x3", "Expert"),
]


def p_to_text(value: float) -> str:
    if value < 0.001:
        return "<0.001"
    return f"{value:.4f}"


def load_human_reference(dimension: str) -> pd.DataFrame:
    return pd.read_excel(
        DATASET_DIR / dimension / "human_scores.xlsx",
        usecols=["ID", dimension],
    ).rename(columns={dimension: "human"})


def load_predictions(dimension: str) -> pd.DataFrame:
    human = load_human_reference(dimension)
    output = human.copy()

    mixed = pd.read_excel(
        MIXED_BASE_DIR / dimension / f"deepseek-gemini-gpt5_{dimension}.xlsx"
    )
    mixed = human.merge(mixed, on="ID", validate="one_to_one")
    mixed_score_cols = ["normal_score_1", "normal_score_2", "normal_score_3"]
    output["Cross-model | Median"] = mixed[mixed_score_cols].median(axis=1).astype(int)
    output["Cross-model | Expert"] = mixed["final_score"].astype(int)

    same_base_files = {
        "DeepSeek-V3.2 x3": ("deepseek", "deepseek"),
        "Gemini-2.5-Pro x3": ("gemini", "gemini"),
        "GPT-5 x3": ("gpt5", "gpt5"),
    }
    for setting, (folder, prefix) in same_base_files.items():
        result = pd.read_excel(SAME_BASE_DIR / folder / f"{prefix}_{dimension}.xlsx")
        result = human.merge(result, on="ID", validate="one_to_one")
        output[f"{setting} | Median"] = result["median_score"].astype(int)
        output[f"{setting} | Expert"] = result["expert_score"].astype(int)

    return output


def qwk(reference: np.ndarray, prediction: np.ndarray) -> float:
    return float(cohen_kappa_score(reference, prediction, weights="quadratic"))


def qwk_fast(reference: np.ndarray, prediction: np.ndarray) -> float:
    reference = reference.astype(int) - 1
    prediction = prediction.astype(int) - 1
    conf = np.bincount(4 * reference + prediction, minlength=16).reshape(4, 4)
    row = conf.sum(axis=1)
    col = conf.sum(axis=0)
    expected = np.outer(row, col) / conf.sum()
    dist = (np.arange(4)[:, None] - np.arange(4)[None, :]) ** 2
    numerator = float((dist * conf).sum())
    denominator = float((dist * expected).sum())
    return 1.0 if denominator == 0 else 1.0 - numerator / denominator


def spearman(reference: np.ndarray, prediction: np.ndarray) -> float:
    rho, _ = spearmanr(reference, prediction, nan_policy="omit")
    return float(rho)


def average_ranks_for_ordinal(values: np.ndarray) -> np.ndarray:
    counts = np.bincount(values.astype(int), minlength=5)[1:5].astype(float)
    starts = np.r_[0.0, np.cumsum(counts)[:-1]]
    avg_by_score = starts + (counts + 1.0) / 2.0
    return avg_by_score[values.astype(int) - 1]


def spearman_fast(reference: np.ndarray, prediction: np.ndarray) -> float:
    r_ref = average_ranks_for_ordinal(reference)
    r_pred = average_ranks_for_ordinal(prediction)
    ref_centered = r_ref - r_ref.mean()
    pred_centered = r_pred - r_pred.mean()
    denom = np.sqrt((ref_centered**2).sum() * (pred_centered**2).sum())
    return float("nan") if denom == 0 else float((ref_centered * pred_centered).sum() / denom)


def ac2(reference: np.ndarray, prediction: np.ndarray) -> float:
    ratings = pd.DataFrame(
        {
            "rater1": pd.Categorical(reference, categories=SCORES, ordered=True),
            "rater2": pd.Categorical(prediction, categories=SCORES, ordered=True),
        }
    ).astype(int)
    return float(RawCAC(ratings, weights="quadratic").gwet()["est"]["coefficient_value"])


def ac2_fast(reference: np.ndarray, prediction: np.ndarray) -> float:
    n = len(reference)
    agree = np.zeros((n, Q), dtype=float)
    for k, score in enumerate(SCORES):
        agree[:, k] = (reference == score).astype(float) + (prediction == score).astype(float)
    agree_w = agree @ AC2_WEIGHTS.T
    ri = agree.sum(axis=1)
    sum_q = (agree * (agree_w - 1)).sum(axis=1)
    valid = ri >= 2
    n2more = int(valid.sum())
    pa = float(np.sum(sum_q[valid] / (ri[valid] * (ri[valid] - 1))) / n2more)
    pi_vec = (agree / ri[:, None]).mean(axis=0)
    pe = float(AC2_WEIGHTS.sum() * np.sum(pi_vec * (1 - pi_vec)) / (Q * (Q - 1)))
    return float((pa - pe) / (1 - pe))


POINT_METRICS = {
    "ExactMatch": lambda ref, pred: float(np.mean(ref == pred)),
    "KappaQuadratic": qwk,
    "SpearmanRho": spearman,
    "GwetAC2": ac2,
}

BOOTSTRAP_METRICS = {
    "KappaQuadratic": qwk_fast,
    "SpearmanRho": spearman_fast,
    "GwetAC2": ac2_fast,
}


def mcnemar_exact(reference: np.ndarray, method: np.ndarray, baseline: np.ndarray) -> dict:
    method_correct = method == reference
    baseline_correct = baseline == reference
    method_only = int(np.sum(method_correct & ~baseline_correct))
    baseline_only = int(np.sum(~method_correct & baseline_correct))
    p_value = (
        1.0
        if method_only + baseline_only == 0
        else float(
            binomtest(
                min(method_only, baseline_only),
                method_only + baseline_only,
                p=0.5,
                alternative="two-sided",
            ).pvalue
        )
    )
    return {
        "MethodMetric": float(np.mean(method_correct)),
        "BaselineMetric": float(np.mean(baseline_correct)),
        "Difference": float(np.mean(method_correct) - np.mean(baseline_correct)),
        "PValue": p_value,
        "CI95Low": None,
        "CI95High": None,
        "MethodCorrectOnly": method_only,
        "BaselineCorrectOnly": baseline_only,
    }


def paired_bootstrap(
    reference: np.ndarray,
    method: np.ndarray,
    baseline: np.ndarray,
    metric_fn,
    rng: np.random.Generator,
) -> dict:
    n = len(reference)
    observed_method = metric_fn(reference, method)
    observed_baseline = metric_fn(reference, baseline)
    observed_diff = observed_method - observed_baseline
    diffs = np.empty(N_BOOTSTRAP, dtype=float)
    for i in range(N_BOOTSTRAP):
        sample_idx = rng.integers(0, n, size=n)
        diffs[i] = metric_fn(reference[sample_idx], method[sample_idx]) - metric_fn(
            reference[sample_idx], baseline[sample_idx]
        )
    p_two_sided = 2 * min(
        (np.sum(diffs <= 0) + 1) / (N_BOOTSTRAP + 1),
        (np.sum(diffs >= 0) + 1) / (N_BOOTSTRAP + 1),
    )
    return {
        "MethodMetric": observed_method,
        "BaselineMetric": observed_baseline,
        "Difference": observed_diff,
        "PValue": min(1.0, float(p_two_sided)),
        "CI95Low": float(np.nanpercentile(diffs, 2.5)),
        "CI95High": float(np.nanpercentile(diffs, 97.5)),
        "MethodCorrectOnly": None,
        "BaselineCorrectOnly": None,
    }


def comparison_pairs() -> list[tuple[str, Method, Method]]:
    cross_expert = Method("Cross-model", "Expert")
    pairs: list[tuple[str, Method, Method]] = []

    for baseline in METHODS:
        if baseline != cross_expert:
            pairs.append(("Cross-model Expert vs alternatives", cross_expert, baseline))

    for setting in [
        "Cross-model",
        "DeepSeek-V3.2 x3",
        "Gemini-2.5-Pro x3",
        "GPT-5 x3",
    ]:
        pairs.append(
            (
                "Expert vs Median within setting",
                Method(setting, "Expert"),
                Method(setting, "Median"),
            )
        )

    deduped = []
    seen = set()
    for comparison_type, method, baseline in pairs:
        key = (comparison_type, method, baseline)
        if key not in seen:
            seen.add(key)
            deduped.append((comparison_type, method, baseline))
    return deduped


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RANDOM_SEED)
    metric_rows = []
    test_rows = []
    spearman_p_rows = []

    for dimension in DIMENSIONS:
        df = load_predictions(dimension)
        reference = df["human"].to_numpy(dtype=int)

        for method in METHODS:
            prediction = df[method.label].to_numpy(dtype=int)
            point = {
                metric_name: metric_fn(reference, prediction)
                for metric_name, metric_fn in POINT_METRICS.items()
            }
            rho, rho_p = spearmanr(reference, prediction, nan_policy="omit")
            metric_rows.append(
                {
                    "Dimension": dimension,
                    "ModelSetting": method.setting,
                    "Strategy": method.strategy,
                    "N": len(reference),
                    **{name: round(value, 4) for name, value in point.items()},
                }
            )
            spearman_p_rows.append(
                {
                    "Dimension": dimension,
                    "ModelSetting": method.setting,
                    "Strategy": method.strategy,
                    "N": len(reference),
                    "SpearmanRho": float(rho),
                    "SpearmanPValue": float(rho_p),
                    "SpearmanPValueText": p_to_text(float(rho_p)),
                    "SignificantAt0.05": bool(rho_p < 0.05),
                }
            )

        for comparison_type, method, baseline in comparison_pairs():
            method_prediction = df[method.label].to_numpy(dtype=int)
            baseline_prediction = df[baseline.label].to_numpy(dtype=int)

            em = mcnemar_exact(reference, method_prediction, baseline_prediction)
            test_rows.append(
                {
                    "ComparisonType": comparison_type,
                    "Dimension": dimension,
                    "Method": method.label,
                    "Baseline": baseline.label,
                    "Metric": "ExactMatch",
                    "Test": "McNemar exact",
                    "N": len(reference),
                    **em,
                    "PValueText": p_to_text(em["PValue"]),
                    "SignificantAt0.05": bool(em["PValue"] < 0.05),
                }
            )

            for metric_name, metric_fn in BOOTSTRAP_METRICS.items():
                result = paired_bootstrap(
                    reference, method_prediction, baseline_prediction, metric_fn, rng
                )
                test_rows.append(
                    {
                        "ComparisonType": comparison_type,
                        "Dimension": dimension,
                        "Method": method.label,
                        "Baseline": baseline.label,
                        "Metric": metric_name,
                        "Test": f"Paired bootstrap ({N_BOOTSTRAP} resamples)",
                        "N": len(reference),
                        **result,
                        "PValueText": p_to_text(result["PValue"]),
                        "SignificantAt0.05": bool(result["PValue"] < 0.05),
                    }
                )

    metrics = pd.DataFrame(metric_rows)
    tests = pd.DataFrame(test_rows)
    spearman_ps = pd.DataFrame(spearman_p_rows)

    tests["Diff (p)"] = tests.apply(
        lambda row: f"{row['Difference']:.4f} ({row['PValueText']})", axis=1
    )
    compact = tests.pivot_table(
        index=["ComparisonType", "Dimension", "Method", "Baseline"],
        columns="Metric",
        values="Diff (p)",
        aggfunc="first",
    ).reset_index()
    compact = compact[
        [
            "ComparisonType",
            "Dimension",
            "Method",
            "Baseline",
            "ExactMatch",
            "KappaQuadratic",
            "SpearmanRho",
            "GwetAC2",
        ]
    ]

    tests_for_write = tests.copy()
    for col in ["MethodMetric", "BaselineMetric", "Difference", "CI95Low", "CI95High"]:
        tests_for_write[col] = tests_for_write[col].round(4)

    with pd.ExcelWriter(OUTPUT_XLSX) as writer:
        metrics.to_excel(writer, sheet_name="Four_Metrics", index=False)
        tests_for_write.to_excel(writer, sheet_name="All_Tests", index=False)
        compact.to_excel(writer, sheet_name="Compact_Diff_P", index=False)
        spearman_ps.to_excel(writer, sheet_name="Spearman_Association_P", index=False)
        for metric in [
            "ExactMatch",
            "KappaQuadratic",
            "SpearmanRho",
            "GwetAC2",
        ]:
            tests_for_write[tests_for_write["Metric"] == metric].to_excel(
                writer, sheet_name=metric[:31], index=False
            )

    print(f"Saved: {OUTPUT_XLSX}")
    print(f"Rows: metrics={len(metrics)}, tests={len(tests)}, compact={len(compact)}")
    print()
    print(compact.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
