import re

INPUT = "comprehensive_matweb_data.csv"
OUTPUT = "dataset_stage1_reconstructed.csv"

EXPECTED_COLS = 67

def split_csv_row(row):
    parts = []
    current = []
    inside_quotes = False

    for c in row:
        if c == '"':
            inside_quotes = not inside_quotes
            current.append(c)
        elif c == ',' and not inside_quotes:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(c)

    # append last part
    parts.append("".join(current).strip())
    return parts

with open(INPUT, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

header = lines[0].strip()
fixed_rows = [header]

buffer = ""

for raw in lines[1:]:
    raw = raw.rstrip("\n")

    # accumulate
    buffer = raw if buffer == "" else (buffer + " " + raw)

    parts = split_csv_row(buffer)

    # if fewer columns than expected → continue accumulating
    if len(parts) < EXPECTED_COLS:
        continue

    # if more columns → truncate
    if len(parts) > EXPECTED_COLS:
        parts = parts[:EXPECTED_COLS]

    fixed_rows.append(",".join(parts))
    buffer = ""

# write output
with open(OUTPUT, "w", encoding="utf-8") as f:
    for row in fixed_rows:
        f.write(row + "\n")

print("Structural reconstruction finished.")