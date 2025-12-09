import pandas as pd

INPUT = "dataset_stage2_metric_only.csv"
OUTPUT = "dataset_stage3_cleaned.csv"

df = pd.read_csv(INPUT, dtype=str, keep_default_na=False)

# 1. Drop all "(Comment)" columns
comment_cols = [c for c in df.columns if "(Comment)" in c]

# 2. Drop English columns
english_cols = [c for c in df.columns if "English" in c]

# 3. Drop Material Notes
notes_cols = ["Material Notes"]

# 4. Drop chemical/acid/alkali class text
useless_text = [
    "Descriptive Properties - Acid Class, SR",
    "Descriptive Properties - Alkali Class, AR",
    "Descriptive Properties - Color",
    "Descriptive Properties - Component Elements Properties",
    "Descriptive Properties - Other"
]

# combine remove list
drop_cols = set(comment_cols + english_cols + notes_cols + useless_text)

df = df.drop(columns=[c for c in drop_cols if c in df.columns])

# 5. Drop columns with >95% blank
blank_threshold = 0.95
for col in df.columns:
    blank_ratio = (df[col] == "").mean()
    if blank_ratio > blank_threshold:
        df = df.drop(columns=[col])

df.to_csv(OUTPUT, index=False)
print("✅ Stage 3 complete: cleaned dataset saved.")
