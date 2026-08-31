from pathlib import Path

import pandas as pd
from scipy.stats import kendalltau, spearmanr


DIMENSIONS = ["identification", "reason", "impact", "solution"]
VALID_SCORES = {1, 2, 3, 4}
INPUT_FILE = "final_manual_score.xlsx"
OUTPUT_DIR = "dimension_correlations"
OUTPUT_FILE = "expert_score_dimension_correlations.xlsx"


def p_to_text(value: float) -> str:
    if pd.isna(value):
        return ""
    if value == 0:
        return "<1e-300"
    if value < 0.001:
        return f"{value:.2e}"
    return f"{value:.4f}"


def lower_triangle_frame(values: dict[tuple[str, str], object], diagonal: object = "-") -> pd.DataFrame:
    table = pd.DataFrame("", index=DIMENSIONS, columns=DIMENSIONS)
    for row_i, row_dim in enumerate(DIMENSIONS):
        for col_i, col_dim in enumerate(DIMENSIONS):
            if row_i == col_i:
                table.loc[row_dim, col_dim] = diagonal
            elif row_i > col_i:
                table.loc[row_dim, col_dim] = values[(row_dim, col_dim)]
    return table.reset_index(names="Dimension")


def main() -> None:
    workdir = Path(__file__).resolve().parent
    input_path = workdir / INPUT_FILE
    output_dir = workdir / OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / OUTPUT_FILE

    df = pd.read_excel(input_path)
    missing = [col for col in DIMENSIONS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing dimension score columns: {missing}")

    score_df = df[DIMENSIONS].copy()
    for col in DIMENSIONS:
        score_df[col] = pd.to_numeric(score_df[col], errors="coerce")
    valid_df = score_df[score_df.apply(lambda row: all(v in VALID_SCORES for v in row), axis=1)]

    pair_rows = []
    spearman_values = {}
    spearman_p_values = {}
    spearman_combined = {}
    kendall_values = {}
    kendall_p_values = {}

    for i, dim_a in enumerate(DIMENSIONS):
        for j, dim_b in enumerate(DIMENSIONS):
            if i <= j:
                continue
            pair = valid_df[[dim_a, dim_b]].dropna().astype(int)
            rho, spearman_p = spearmanr(pair[dim_a], pair[dim_b], nan_policy="omit")
            tau, kendall_p = kendalltau(pair[dim_a], pair[dim_b], nan_policy="omit")

            spearman_values[(dim_a, dim_b)] = round(float(rho), 4)
            spearman_p_values[(dim_a, dim_b)] = p_to_text(float(spearman_p))
            spearman_combined[(dim_a, dim_b)] = f"{rho:.4f} ({p_to_text(float(spearman_p))})"
            kendall_values[(dim_a, dim_b)] = round(float(tau), 4)
            kendall_p_values[(dim_a, dim_b)] = p_to_text(float(kendall_p))

            pair_rows.append(
                {
                    "Dimension A": dim_a,
                    "Dimension B": dim_b,
                    "N": len(pair),
                    "SpearmanRho": round(float(rho), 4),
                    "SpearmanPValue": float(spearman_p),
                    "SpearmanPValueText": p_to_text(float(spearman_p)),
                    "KendallTauB": round(float(tau), 4),
                    "KendallPValue": float(kendall_p),
                    "KendallPValueText": p_to_text(float(kendall_p)),
                }
            )

    spearman_table = lower_triangle_frame(spearman_values)
    spearman_p_table = lower_triangle_frame(spearman_p_values)
    spearman_combined_table = lower_triangle_frame(spearman_combined)
    kendall_table = lower_triangle_frame(kendall_values)
    kendall_p_table = lower_triangle_frame(kendall_p_values)
    pair_df = pd.DataFrame(pair_rows)

    with pd.ExcelWriter(output_path) as writer:
        spearman_combined_table.to_excel(writer, sheet_name="Spearman_Rho_P_Lower", index=False)
        spearman_table.to_excel(writer, sheet_name="Spearman_Rho_Lower", index=False)
        spearman_p_table.to_excel(writer, sheet_name="Spearman_P_Lower", index=False)
        kendall_table.to_excel(writer, sheet_name="Kendall_TauB_Lower", index=False)
        kendall_p_table.to_excel(writer, sheet_name="Kendall_P_Lower", index=False)
        pair_df.to_excel(writer, sheet_name="Pairwise_Long", index=False)

    print("Spearman rho with p-values, lower triangle:")
    print(spearman_combined_table.to_string(index=False))
    print("\nKendall tau-b, lower triangle:")
    print(kendall_table.to_string(index=False))
    print(f"\nN valid rows: {len(valid_df)}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
