#!/usr/bin/env python3
"""Expert score distribution across the four IRIS dimensions.

The scores come from the final blind-review-confirmed human score workbooks in
`llm-evaluation/datasets/<dimension>/human_scores.xlsx`.

Styling matches the other paper figures: Times serif, a light gray ramp for the
ordinal score levels, no chart title (the caption carries it).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DIMENSIONS = ["identification", "reason", "impact", "solution"]
SCORES = [1, 2, 3, 4]

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = REPO_ROOT / "llm-evaluation" / "datasets"

# The score is ordinal, so lightness carries the order. Every palette below is
# monotone light-to-dark with an OKLCH lightness gap of at least 0.06 between
# neighbouring steps, which is what keeps two adjacent segments apart on paper.
# A thin dark outline separates the palest segment from the white page.
PALETTES = {
    # Full gray ramp: the safest in print, the widest separation.
    "gray": (
        {1: "0.93", 2: "0.80", 3: "0.62", 4: "0.44"},
        {1: "0.15", 2: "0.15", 3: "0.10", 4: "white"},
    ),
    # White -> gray -> light blue -> blue. The blue steps are darker than a
    # literal "very light blue" so that step 3 stays distinct from the gray.
    "blue": (
        {1: "#ffffff", 2: "#e4e4e4", 3: "#b3d2ee", 4: "#86b6ef"},
        {1: "0.15", 2: "0.15", 3: "0.15", 4: "0.15"},
    ),
    # Same, with a green top step instead of blue.
    "green": (
        {1: "#ffffff", 2: "#e4e4e4", 3: "#b3d2ee", 4: "#8ac38c"},
        {1: "0.15", 2: "0.15", 3: "0.15", 4: "0.15"},
    ),
}
DEFAULT_PALETTE = "blue"
SCORE_FACES, SCORE_TEXT = PALETTES[DEFAULT_PALETTE]
EDGE_COLOR = "0.20"
EDGE_WIDTH = 0.9
LEADER_COLOR = "0.45"

BAR_WIDTH = 0.58
INSIDE_LABEL_MIN = 22  # segments smaller than this are labelled beside the bar
Y_MAX = 440


def load_counts() -> tuple[pd.DataFrame, pd.DataFrame, int]:
    counts = pd.DataFrame(index=SCORES)
    totals = set()
    for dimension in DIMENSIONS:
        scores = pd.read_excel(DATASET_DIR / dimension / "human_scores.xlsx", usecols=[dimension])
        series = scores[dimension]
        counts[dimension] = series.value_counts().reindex(SCORES, fill_value=0).sort_index()
        totals.add(len(scores))
    if len(totals) != 1:
        raise RuntimeError(f"Dimensions have different record counts: {sorted(totals)}")
    total = totals.pop()
    percentages = (counts / total * 100).round(2)
    counts.index.name = "Score"
    percentages.index.name = "Score"
    return counts, percentages, total


def plot(counts: pd.DataFrame, total: int, output_dir: Path) -> list[Path]:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 22,
            "axes.labelsize": 26,
            "legend.fontsize": 21,
            "xtick.labelsize": 25,
            "ytick.labelsize": 21,
            "axes.linewidth": 1.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(13.0, 8.0))
    fig.subplots_adjust(left=0.098, right=0.985, bottom=0.085, top=0.985)

    x = np.arange(len(DIMENSIONS)) * 1.0
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="0.88", linewidth=0.7, linestyle=(0, (3, 3)), zorder=0)

    bottoms = np.zeros(len(DIMENSIONS))
    for score in SCORES:
        values = counts.loc[score, DIMENSIONS].to_numpy(dtype=float)
        bars = ax.bar(
            x,
            values,
            bottom=bottoms,
            width=BAR_WIDTH,
            label=f"Score {score}",
            facecolor=SCORE_FACES[score],
            edgecolor=EDGE_COLOR,
            linewidth=EDGE_WIDTH,
            zorder=3,
        )
        for bar, value, bottom in zip(bars, values, bottoms):
            middle = bottom + value / 2
            share = value / total * 100
            if value >= INSIDE_LABEL_MIN:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    middle,
                    f"{int(value)}\n({share:.1f}%)",
                    ha="center",
                    va="center",
                    fontsize=19,
                    linespacing=1.15,
                    color=SCORE_TEXT[score],
                    zorder=4,
                )
            else:
                # A thin segment cannot hold text, so the count sits outside it
                # with a hairline leader. A segment high in the stack is labelled
                # above the bar, where there is clear space; a low one is
                # labelled in the gap to its right.
                leader = {
                    "arrowstyle": "-",
                    "color": LEADER_COLOR,
                    "linewidth": 0.8,
                    "shrinkA": 0,
                    "shrinkB": 1,
                }
                label = f"{int(value)} ({share:.1f}%)"
                if middle > total / 2:
                    ax.annotate(
                        label,
                        xy=(bar.get_x() + bar.get_width() / 2, bottom + value),
                        xytext=(0, 13),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=18,
                        color="0.15",
                        zorder=4,
                        arrowprops=leader,
                    )
                else:
                    ax.annotate(
                        label,
                        xy=(bar.get_x() + bar.get_width(), middle),
                        xytext=(14, 0),
                        textcoords="offset points",
                        ha="left",
                        # Anchored by its bottom: a segment sitting on the
                        # baseline would otherwise push a centred label below
                        # the axis.
                        va="bottom",
                        fontsize=18,
                        color="0.15",
                        zorder=4,
                        arrowprops=leader,
                    )
        bottoms += values

    ax.set_ylabel("Number of comments", labelpad=12)
    ax.set_xticks(x)
    ax.set_xticklabels([dimension.capitalize() for dimension in DIMENSIONS])
    ax.set_xlim(x[0] - 0.62, x[-1] + 0.62)
    ax.set_ylim(0, Y_MAX)
    ticks = np.arange(0, 401, 100)
    ax.set_yticks(ticks)
    ax.set_yticklabels([str(tick) for tick in ticks])

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("0.25")
    ax.spines["left"].set_bounds(0, 400)
    ax.tick_params(axis="x", length=0, pad=9)
    ax.tick_params(axis="y", direction="out", length=4, width=1.0, color="0.25", pad=5)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        ncol=4,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.005),
        frameon=False,
        handlelength=1.8,
        handletextpad=0.6,
        columnspacing=2.0,
        borderaxespad=0.0,
    )

    pdf_path = output_dir / "score_distribution.pdf"
    png_path = output_dir / "score_distribution.png"
    fig.savefig(pdf_path, facecolor="white")
    fig.savefig(png_path, facecolor="white", dpi=200)
    plt.close(fig)
    return [pdf_path, png_path]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--palette",
        choices=sorted(PALETTES),
        default=DEFAULT_PALETTE,
        help=f"Colour ramp for the four score levels (default: {DEFAULT_PALETTE}).",
    )
    args = parser.parse_args()
    global SCORE_FACES, SCORE_TEXT
    SCORE_FACES, SCORE_TEXT = PALETTES[args.palette]

    output_dir = Path(__file__).resolve().parent / "score_distribution"
    output_dir.mkdir(exist_ok=True)

    counts, percentages, total = load_counts()
    # One workbook holds both tables; separate CSVs would only duplicate it.
    with pd.ExcelWriter(output_dir / "score_distribution.xlsx") as writer:
        counts.to_excel(writer, sheet_name="Counts")
        percentages.to_excel(writer, sheet_name="Percentages")

    for path in plot(counts, total, output_dir):
        print(f"Saved {path}")

    print(f"\nSource: {DATASET_DIR}/<dimension>/human_scores.xlsx")
    print("Counts:")
    print(counts.to_string())
    print("\nPercentages:")
    print(percentages.to_string())


if __name__ == "__main__":
    main()
