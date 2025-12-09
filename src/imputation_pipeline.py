import pandas as pd
import numpy as np

# 1. Load dataset and drop GUID
df = pd.read_csv("dataset_cleaned_final.csv")
df = df.drop(columns=["GUID"], errors="ignore")

# 2. Rename columns for easier access
df = df.rename(columns=lambda x: x.replace("Descriptive Properties - ", "").strip())

# 3. Split category string into Python lists
df["CategoryList"] = df["Categories"].fillna("").apply(lambda x: [c.strip() for c in x.split(";") if c.strip()])

# 4. Extract all unique categories in the dataset
all_categories = sorted({cat for lst in df["CategoryList"] for cat in lst})

print("Collected", len(all_categories), "unique categories")

# 5. Identify numeric columns for imputation
non_feature_cols = ["Material Name", "Categories", "CategoryList"]
feature_cols = [c for c in df.columns if c not in non_feature_cols]

# Convert values to float, ignoring non-numeric strings
for col in feature_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# 6. Build category → average value lookup tables
category_stats = {
    cat: {
        col: df.loc[df["CategoryList"].apply(lambda lst: cat in lst), col].mean()
        for col in feature_cols
    }
    for cat in all_categories
}

print("Built category average tables")


# 7. Weight assignment function
def get_weights(n):
    if n == 1:
        return [1.0]
    if n == 2:
        return [0.75, 0.25]
    if n == 3:
        return [0.6, 0.3, 0.1]
    # For 4+ categories, use geometric weighting
    base = np.array([0.5**i for i in range(n)])
    return (base / base.sum()).tolist()


# 8. Weighted imputation logic
def impute_row(row):
    categories = row["CategoryList"]
    if not categories:
        return row

    weights = get_weights(len(categories))

    for col in feature_cols:
        if not pd.isna(row[col]):
            continue

        weighted_values = []
        weighted_weights = []

        for cat, w in zip(categories, weights):
            avg_val = category_stats.get(cat, {}).get(col, np.nan)
            if not pd.isna(avg_val):
                weighted_values.append(avg_val * w)
                weighted_weights.append(w)

        if weighted_values:
            row[col] = sum(weighted_values) / sum(weighted_weights)

    return row


# 9. Apply imputation
df_imputed = df.apply(impute_row, axis=1)

print("Imputation complete")

# 10. Save final dataset
df_imputed.to_csv("dataset_final_imputed.csv", index=False)
print("Saved dataset_final_imputed.csv")