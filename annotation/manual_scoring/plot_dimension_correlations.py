from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


DIMENSIONS = ["identification", "reason", "impact", "solution"]
LABELS = ["Identification", "Reason", "Impact", "Solution"]
VALID_SCORES = {1, 2, 3, 4}
INPUT_FILE = "final_manual_score.xlsx"
OUTPUT_DIR = "dimension_correlations"


def p_to_text(value: float) -> str:
    if value < 0.001:
        return "p<0.001"
    return f"p={value:.3f}"


def main() -> None:
    workdir = Path(__file__).resolve().parent
    output_dir = workdir / OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)

    df = pd.read_excel(workdir / INPUT_FILE)
    score_df = df[DIMENSIONS].copy()
    for col in DIMENSIONS:
        score_df[col] = pd.to_numeric(score_df[col], errors="coerce")
    score_df = score_df[score_df.apply(lambda row: all(v in VALID_SCORES for v in row), axis=1)]

    n = len(DIMENSIONS)
    rho_matrix = np.full((n, n), np.nan)
    p_matrix = np.full((n, n), np.nan)

    for i, dim_i in enumerate(DIMENSIONS):
        for j, dim_j in enumerate(DIMENSIONS):
            if i == j:
                continue
            pair = score_df[[dim_i, dim_j]].dropna().astype(int)
            rho, p_value = spearmanr(pair[dim_i], pair[dim_j], nan_policy="omit")
            rho_matrix[i, j] = rho
            p_matrix[i, j] = p_value

    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.spines.bottom": False,
            "xtick.color": "#222222",
            "ytick.color": "#222222",
        }
    )

    cmap = plt.get_cmap("RdBu_r").copy()
    cmap.set_bad(color="white")
    fig, ax = plt.subplots(figsize=(6.4, 5.4), dpi=220)
    im = ax.imshow(np.ma.masked_invalid(rho_matrix), cmap=cmap, vmin=-1.0, vmax=1.0)

    ax.set_title("Pairwise Spearman Correlations among IRIS Dimensions", fontsize=13, pad=14)
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(LABELS, rotation=35, ha="right")
    ax.set_yticklabels(LABELS)
    ax.tick_params(length=0)
    ax.tick_params(axis="x", bottom=False, labelbottom=False, top=True, labeltop=True)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            else:
                rho = rho_matrix[i, j]
                p_value = p_matrix[i, j]
                text_color = "white" if abs(rho) >= 0.35 else "#222222"
                ax.text(
                    j,
                    i,
                    f"{rho:.3f}\n{p_to_text(p_value)}",
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=9,
                )

    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(n - 0.5, -0.5)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Spearman's rho", rotation=90)
    cbar.outline.set_visible(False)

    fig.tight_layout()

    output_png = output_dir / "expert_score_dimension_spearman_heatmap.png"
    output_pdf = output_dir / "expert_score_dimension_spearman_heatmap.pdf"
    fig.savefig(output_png, bbox_inches="tight")
    fig.savefig(output_pdf, bbox_inches="tight")
    plt.close(fig)

    print(f"N valid rows: {len(score_df)}")
    print(f"Saved plot: {output_png}")
    print(f"Saved plot: {output_pdf}")


if __name__ == "__main__":
    main()
