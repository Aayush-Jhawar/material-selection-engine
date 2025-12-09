import re
import pandas as pd

INPUT = "dataset_stage1_reconstructed.csv"
OUTPUT = "dataset_stage2_metric_only.csv"

# English-unit patterns
patterns = [
    r"\d+(\.\d+)?\s*psi\b",
    r"\d+(\.\d+)?\s*ksi\b",
    r"\d+(\.\d+)?\s*lb\/in",
    r"\d+(\.\d+)?\s*°F",
    r"\d+(\.\d+)?\s*BTU[^,]*",
    r"\d+(\.\d+)?\s*in\b",
    r"\d+(\.\d+)?\s*F\b",
    r"\d+(\.\d+)?\s*ohm-cm@Temperature [0-9]+ °F",
]

combined = re.compile("|".join(patterns), re.IGNORECASE)

df = pd.read_csv(INPUT, dtype=str, keep_default_na=False)

def clean_cell(x):
    if not isinstance(x, str):
        return x
    return combined.sub("", x).strip().strip(",")

for col in df.columns:
    df[col] = df[col].apply(clean_cell)

df.to_csv(OUTPUT, index=False)
print("English units removed.")