#!/usr/bin/env python3
"""Compute the macro-average RQ3.2 effects and combined forest plot."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnchoredOffsetbox, HPacker, TextArea
from sklearn.metrics import cohen_kappa_score


HERE = Path(__file__).resolve().parent
EVAL_ROOT = HERE.parent
DATASET_DIR = EVAL_ROOT / "datasets"
REPEATED_DIR = (
    EVAL_ROOT / "03_single_model_repeated" / "outputs" / "three_repeat_strategies"
)
CROSS_DIR = (
    EVAL_ROOT
    / "02_cross_model_median_expert"
    / "outputs"
    / "runs"
    / "deepseek_gemini_gpt5_qwen3expert_t0"
)
FIGURE_DIR = HERE / "figures"

DIMENSIONS = ("identification", "reason", "impact", "solution")
DIMENSION_LABELS = {
    "identification": "Identification",
    "reason": "Reason",
    "impact": "Impact",
    "solution": "Solution",
}
MODELS = ("DeepSeek-V3.2", "Gemini-2.5-Pro", "GPT-5")
MODEL_FOLDERS = {
    "DeepSeek-V3.2": "deepseek",
    "Gemini-2.5-Pro": "gemini",
    "GPT-5": "gpt5",
}
EFFECT_LABELS = {
    "repeated": "Repeated",
    "diversity": "Diversity",
    "expert": "Expert",
}
SCORES = {1, 2, 3, 4}
SEED = 20260902
B_BOOT = 10_000
B_PERM = 10_000
ALPHA = 0.05


def read_indexed(path: Path) -> pd.DataFrame:
    frame = pd.read_excel(path)
    if "ID" not in frame.columns:
        raise ValueError(f"Missing ID column: {path}")
    frame["ID"] = pd.to_numeric(frame["ID"], errors="raise").astype(int)
    if frame["ID"].duplicated().any():
        raise ValueError(f"Duplicate IDs: {path}")
    return frame.set_index("ID").sort_index()


def score_array(series: pd.Series, label: str) -> np.ndarray:
    numeric = pd.to_numeric(series, errors="raise")
    if numeric.isna().any():
        raise ValueError(f"Missing scores: {label}")
    values = numeric.to_numpy(dtype=float)
    if not np.all(values == np.floor(values)):
        raise ValueError(f"Non-integer scores: {label}")
    result = values.astype(np.int8)
    invalid = sorted(set(result) - SCORES)
    if invalid:
        raise ValueError(f"Scores outside 1..4 in {label}: {invalid}")
    return result


def quadratic_kappa(reference: np.ndarray, prediction: np.ndarray) -> float:
    return float(
        cohen_kappa_score(
            reference,
            prediction,
            labels=sorted(SCORES),
            weights="quadratic",
        )
    )


def kappa_batch(reference: np.ndarray, prediction: np.ndarray) -> np.ndarray:
    """Compute quadratic kappa for each row of two equally shaped matrices."""
    if reference.ndim == 1:
        reference = np.broadcast_to(reference, prediction.shape)
    codes = 4 * (reference.astype(np.int16) - 1) + (
        prediction.astype(np.int16) - 1
    )
    counts = np.empty((codes.shape[0], 16), dtype=np.float64)
    for code in range(16):
        counts[:, code] = np.sum(codes == code, axis=1)

    observed = counts.reshape(-1, 4, 4)
    row_marginals = observed.sum(axis=2)
    column_marginals = observed.sum(axis=1)
    sample_sizes = observed.sum(axis=(1, 2))
    expected = (
        row_marginals[:, :, None]
        * column_marginals[:, None, :]
        / sample_sizes[:, None, None]
    )
    distance = (np.arange(4)[:, None] - np.arange(4)[None, :]) ** 2
    numerator = np.sum(observed * distance, axis=(1, 2))
    denominator = np.sum(expected * distance, axis=(1, 2))

    result = np.full(len(observed), np.nan, dtype=float)
    valid = denominator > 0
    result[valid] = 1.0 - numerator[valid] / denominator[valid]
    result[~valid & (numerator == 0)] = 1.0
    return result


def random_arrays(dimension: str, n: int) -> tuple[np.ndarray, np.ndarray]:
    dimension_index = DIMENSIONS.index(dimension)
    rng = np.random.default_rng(np.random.SeedSequence([SEED, dimension_index]))
    bootstrap_indices = rng.integers(
        0, n, size=(B_BOOT, n), dtype=np.int16
    )
    permutation_masks = rng.integers(
        0, 2, size=(B_PERM, n), dtype=np.int8
    ).astype(bool)
    return bootstrap_indices, permutation_masks


def bootstrap_kappa_delta(
    reference: np.ndarray,
    prediction_a: np.ndarray,
    prediction_b: np.ndarray,
    indices: np.ndarray,
) -> np.ndarray:
    reference_boot = reference[indices]
    return kappa_batch(reference_boot, prediction_a[indices]) - kappa_batch(
        reference_boot, prediction_b[indices]
    )


def permutation_kappa_delta(
    reference: np.ndarray,
    prediction_a: np.ndarray,
    prediction_b: np.ndarray,
    masks: np.ndarray,
) -> np.ndarray:
    permuted_a = np.where(masks, prediction_b, prediction_a)
    permuted_b = np.where(masks, prediction_a, prediction_b)
    return kappa_batch(reference, permuted_a) - kappa_batch(reference, permuted_b)


def load_inputs() -> dict[str, dict]:
    expected_ids = set(range(1, 362))
    all_data = {}

    for dimension in DIMENSIONS:
        human_frame = read_indexed(
            DATASET_DIR / dimension / "human_scores.xlsx"
        )
        if set(human_frame.index) != expected_ids:
            raise ValueError(f"Human IDs are not exactly 1..361: {dimension}")
        human = score_array(human_frame[dimension], f"{dimension} human")

        repeated = {}
        for model in MODELS:
            folder = MODEL_FOLDERS[model]
            frame = read_indexed(
                REPEATED_DIR / folder / f"{folder}_{dimension}.xlsx"
            )
            if set(frame.index) != expected_ids:
                raise ValueError(f"Repeated IDs do not align: {model}, {dimension}")

            candidates = np.column_stack(
                [
                    score_array(
                        frame[f"run_0{run}_score"],
                        f"{model} {dimension} run_0{run}",
                    )
                    for run in (1, 2, 3)
                ]
            )
            computed_median = np.median(candidates, axis=1).astype(np.int8)
            stored_median = score_array(
                frame["median_score"], f"{model} {dimension} median"
            )
            if not np.array_equal(computed_median, stored_median):
                raise ValueError(f"Stored Median is inconsistent: {model}, {dimension}")

            repeated[model] = {
                "Single": candidates[:, 0],
                "Median": computed_median,
                "Expert": score_array(
                    frame["expert_score"], f"{model} {dimension} expert"
                ),
            }

        cross_frame = read_indexed(
            CROSS_DIR
            / dimension
            / f"deepseek-gemini-gpt5_{dimension}.xlsx"
        )
        if set(cross_frame.index) != expected_ids:
            raise ValueError(f"Cross-model IDs do not align: {dimension}")
        cross_candidates = np.column_stack(
            [
                score_array(
                    cross_frame[f"normal_score_{candidate}"],
                    f"cross-model {dimension} candidate {candidate}",
                )
                for candidate in (1, 2, 3)
            ]
        )
        cross_median = np.median(cross_candidates, axis=1).astype(np.int8)
        if "median_score" in cross_frame.columns:
            stored_cross_median = score_array(
                cross_frame["median_score"],
                f"cross-model {dimension} median",
            )
            if not np.array_equal(cross_median, stored_cross_median):
                raise ValueError(
                    f"Stored cross-model Median is inconsistent: {dimension}"
                )
        cross = {
            "Median": cross_median,
            "Expert": score_array(
                cross_frame["final_score"], f"cross-model {dimension} expert"
            ),
        }

        all_data[dimension] = {
            "human": human,
            "repeated": repeated,
            "cross": cross,
        }

    return all_data


def effect_pairs(data: dict, effect: str) -> list[tuple[np.ndarray, np.ndarray]]:
    if effect == "repeated":
        return [
            (data["repeated"][model]["Median"], data["repeated"][model]["Single"])
            for model in MODELS
        ]
    if effect == "diversity":
        return [
            (data["cross"]["Median"], data["repeated"][model]["Median"])
            for model in MODELS
        ]
    if effect == "expert":
        pairs = [
            (data["repeated"][model]["Expert"], data["repeated"][model]["Median"])
            for model in MODELS
        ]
        pairs.append((data["cross"]["Expert"], data["cross"]["Median"]))
        return pairs
    raise ValueError(f"Unknown effect: {effect}")


def macro_effect(
    reference: np.ndarray,
    pairs: list[tuple[np.ndarray, np.ndarray]],
    bootstrap_indices: np.ndarray,
    permutation_masks: np.ndarray,
) -> dict[str, float]:
    observed_deltas = [
        quadratic_kappa(reference, prediction_a)
        - quadratic_kappa(reference, prediction_b)
        for prediction_a, prediction_b in pairs
    ]
    observed_macro = float(np.mean(observed_deltas))

    bootstrap_distribution = np.zeros(B_BOOT, dtype=float)
    permutation_distribution = np.zeros(B_PERM, dtype=float)
    for prediction_a, prediction_b in pairs:
        bootstrap_distribution += (
            bootstrap_kappa_delta(
                reference,
                prediction_a,
                prediction_b,
                bootstrap_indices,
            )
            / len(pairs)
        )
        permutation_distribution += (
            permutation_kappa_delta(
                reference,
                prediction_a,
                prediction_b,
                permutation_masks,
            )
            / len(pairs)
        )

    valid_bootstrap = bootstrap_distribution[
        np.isfinite(bootstrap_distribution)
    ]
    valid_permutation = permutation_distribution[
        np.isfinite(permutation_distribution)
    ]
    if len(valid_bootstrap) < 0.99 * B_BOOT:
        raise RuntimeError("More than 1% of macro bootstrap replicates are invalid")
    if len(valid_permutation) < 0.99 * B_PERM:
        raise RuntimeError("More than 1% of macro permutation replicates are invalid")

    ci_lower, ci_upper = np.percentile(valid_bootstrap, [2.5, 97.5])
    p_raw = (
        1
        + np.sum(np.abs(valid_permutation) >= abs(observed_macro))
    ) / (len(valid_permutation) + 1)
    return {
        "delta_kappa": observed_macro,
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "p_raw": float(p_raw),
    }


def compute_summary(all_data: dict[str, dict]) -> pd.DataFrame:
    rows = []
    random_cache = {
        dimension: random_arrays(
            dimension, len(all_data[dimension]["human"])
        )
        for dimension in DIMENSIONS
    }

    for effect in ("repeated", "diversity", "expert"):
        for dimension in DIMENSIONS:
            data = all_data[dimension]
            bootstrap_indices, permutation_masks = random_cache[dimension]
            result = macro_effect(
                data["human"],
                effect_pairs(data, effect),
                bootstrap_indices,
                permutation_masks,
            )
            rows.append(
                {
                    "effect": EFFECT_LABELS[effect],
                    "dimension": DIMENSION_LABELS[dimension],
                    **result,
                }
            )

    summary = pd.DataFrame(rows)
    summary["significant"] = summary["p_raw"] < ALPHA
    return summary[
        [
            "effect",
            "dimension",
            "delta_kappa",
            "ci_lower",
            "ci_upper",
            "p_raw",
            "significant",
        ]
    ]


def configure_plot_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 17,
            "axes.titlesize": 18,
            "axes.labelsize": 18,
            "xtick.labelsize": 17,
            "ytick.labelsize": 18,
            "mathtext.fontset": "custom",
            "mathtext.rm": "Times New Roman",
            "mathtext.it": "Times New Roman:italic",
            "mathtext.bf": "Times New Roman:bold",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.7,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def plot_combined(summary: pd.DataFrame) -> None:
    titles = {
        "Repeated": "Repeated-inference effect",
        "Diversity": "Model-diversity effect",
        "Expert": "Expert-adjudication effect",
    }
    subtitles = {
        "Repeated": "Repeated \N{MINUS SIGN} Single-run",
        "Diversity": "Cross-model \N{MINUS SIGN} Single-model repeated",
        "Expert": "Expert \N{MINUS SIGN} Median",
    }

    values = (
        summary["ci_lower"].tolist()
        + summary["ci_upper"].tolist()
        + summary["delta_kappa"].tolist()
        + [0.0]
    )
    low, high = min(values), max(values)
    left_padding = max(0.02, 0.08 * (high - low))
    right_padding = max(0.01, 0.04 * (high - low))
    x_limits = (low - left_padding, high + right_padding)

    configure_plot_style()
    fig, axes = plt.subplots(
        3,
        1,
        figsize=(8.0, 7.0),
        sharex=True,
        sharey=True,
    )
    fig.subplots_adjust(
        left=0.21,
        right=0.985,
        top=0.92,
        bottom=0.10,
        hspace=0.55,
    )
    dimensions_bottom_up = list(
        reversed([DIMENSION_LABELS[item] for item in DIMENSIONS])
    )

    for ax, effect in zip(axes, ("Repeated", "Diversity", "Expert")):
        frame = summary[summary["effect"] == effect].set_index("dimension")
        for y, dimension in enumerate(dimensions_bottom_up):
            row = frame.loc[dimension]
            delta = row["delta_kappa"]
            ax.errorbar(
                delta,
                y,
                xerr=[
                    [delta - row["ci_lower"]],
                    [row["ci_upper"] - delta],
                ],
                fmt="o",
                color="black",
                ecolor="0.3",
                elinewidth=1.2,
                capsize=2.5,
                markersize=5.0,
                markerfacecolor="black",
                markeredgecolor="black",
            )
        ax.axvline(
            0,
            color="0.35",
            linestyle=(0, (4, 2.5)),
            linewidth=1.0,
        )
        ax.set_yticks(range(4))
        ax.set_yticklabels([])
        for y, dimension in enumerate(dimensions_bottom_up):
            label = dimension
            if frame.loc[dimension, "significant"]:
                label += r"$^{*}$"
            ax.text(
                -0.24,
                y,
                label,
                transform=ax.get_yaxis_transform(),
                ha="left",
                va="center",
                fontsize=18,
                clip_on=False,
            )
        title_text = TextArea(
            titles[effect],
            textprops={
                "fontfamily": "Times New Roman",
                "fontsize": 18,
                "fontweight": "bold",
                "color": "black",
            },
        )
        subtitle_text = TextArea(
            subtitles[effect],
            textprops={
                "fontfamily": "Times New Roman",
                "fontsize": 17,
                "color": "0.25",
            },
        )
        header = HPacker(
            children=[title_text, subtitle_text],
            align="baseline",
            pad=0,
            sep=10,
        )
        ax.add_artist(
            AnchoredOffsetbox(
                loc="lower left",
                child=header,
                frameon=False,
                bbox_to_anchor=(0, 1.06),
                bbox_transform=ax.transAxes,
                borderpad=0,
                pad=0,
            )
        )
        ax.grid(axis="x", color="0.90", linewidth=0.5)
        ax.set_axisbelow(True)
        ax.set_xlim(*x_limits)
        ax.set_ylim(-0.30, 3.70)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)

    x_ticks = np.arange(-0.025, 0.126, 0.025)
    for ax in axes:
        ax.set_xticks(x_ticks)
        ax.tick_params(axis="x", labelbottom=True)

    fig.savefig(
        FIGURE_DIR / "xianzhuxing.pdf",
        bbox_inches="tight",
        pad_inches=0.03,
    )
    fig.savefig(
        FIGURE_DIR / "fig_rq32_effects_combined.png",
        dpi=400,
        bbox_inches="tight",
        pad_inches=0.03,
    )
    plt.close(fig)


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    all_data = load_inputs()
    summary = compute_summary(all_data)
    plot_combined(summary)

    print(f"Wrote macro-average RQ3.2 figures to {FIGURE_DIR}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
