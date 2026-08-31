import pandas as pd
from sklearn.metrics import cohen_kappa_score
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

batch_files = [
    ("batch_1", BASE_DIR / "batch_1.xlsx"),
    ("batch_2", BASE_DIR / "batch_2.xlsx"),
    ("batch_3", BASE_DIR / "batch_3.xlsx"),
]

dimension_candidates = [
    ("Identification_human_1", "Identification_human_2"),
    ("Reason_human_1", "Reason_human_2"),
    ("Impact_human_1", "Impact_human_2"),
    ("Solution_human_1", "Solution_human_2"),
]

for batch_name, file_path in batch_files:
    df = pd.read_excel(file_path).dropna(how="all").copy()
    rater1_all = []
    rater2_all = []

    for col1, col2 in dimension_candidates:
        sub = df[[col1, col2]].dropna()
        rater1_all.extend(sub[col1].astype(int).tolist())
        rater2_all.extend(sub[col2].astype(int).tolist())

    kappa = cohen_kappa_score(rater1_all, rater2_all, weights="quadratic")
    print(f"{batch_name}: Quadratic Weighted Cohen's Kappa = {kappa:.4f}")
