import pandas as pd
import re

INPUT = "dataset_stage3_cleaned.csv"     # your latest file
OUTPUT = "dataset_cleaned_final.csv"

df = pd.read_csv(INPUT, dtype=str, keep_default_na=False)

# Columns that must NOT be stripped
IGNORE_COLS = ["GUID", "Material Name", "Categories"]

# regex to detect numbers
number_regex = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")

# patterns to delete completely
trash_patterns = [
    r"\bMetric\b",
    r"\bEnglish\b",
    r"\bClass\b",
    r"\bISO\b",
    r"\bDIN\b",
    r"\bHGB\b",
    r"\b<=\s*\d+",
    r"@Temperature [^,]*",
    r"@Strain [^,]*",
    r"@Wavelength [^,]*",
    r"@Frequency [^,]*",
    r"@Treatment[^,]*",
    r"@Thickness[^,]*",
    r"@Time[^,]*",
    r"@[A-Za-z ]*",
]

trash_regex = re.compile("|".join(trash_patterns), re.IGNORECASE)


def clean_cell(x):
    if not isinstance(x, str):
        return ""

    # ignore id/name fields
    if x in IGNORE_COLS:
        return x

    original = x.strip()

    # remove trash patterns
    cleaned = trash_regex.sub("", original)

    # extract numeric parts only
    nums = number_regex.findall(cleaned)

    if not nums:
        return ""

    # If multiple numbers, join with comma
    return ",".join(nums)


# apply to all columns except the first three
for col in df.columns:
    if col not in IGNORE_COLS:
        df[col] = df[col].apply(clean_cell)

df.to_csv(OUTPUT, index=False)
print("Final cleaning complete → dataset_cleaned_final.csv")