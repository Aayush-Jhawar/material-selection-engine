import pandas as pd

INPUT = "materials_env_enriched.csv"
OUTPUT = "materials_final_with_price.csv"

df = pd.read_csv(INPUT)

PRICE_TABLE = {
    "Aluminum": 250,
    "Steel": 80,
    "Stainless Steel": 220,
    "Copper": 850,
    "Brass": 550,
    "Titanium": 2700,
    "Carbon Fiber": 2500,
    "ABS": 180,
    "PLA": 170,
    "Nylon": 260,
    "Polycarbonate": 280,
    "Polyethylene": 70,
    "PVC": 90,
    "Glass": 40,
    "Wood": 50,
    "Ceramic": 200,
    "Oxide": 200,
    "Nitride": 350,
    "Phosphide/Pnictide": 500,
    "Other Engineering Material": 300
}

# 1. Define weights based on number of categories
def get_weights(n):
    if n == 1:
        return [1.0]
    if n == 2:
        return [0.75, 0.25]
    if n == 3:
        return [0.6, 0.3, 0.1]
    # for 4+ categories
    extra = max(0, n - 3)
    leftover = 0.05
    base = [0.6, 0.3, 0.1]
    remaining_weight = leftover / extra if extra > 0 else 0
    return base + [remaining_weight] * extra

# 2. Compute price for each material using category weighting
def compute_price(cat_string):
    if pd.isna(cat_string):
        return None

    cats = [c.strip() for c in cat_string.split(";") if c.strip()]
    weights = get_weights(len(cats))

    price_values = []
    for cat, w in zip(cats, weights):
        matched = None
        for key in PRICE_TABLE.keys():
            if key.lower() in cat.lower():
                matched = PRICE_TABLE[key]
                break

        if matched is None:
            matched = PRICE_TABLE.get("Other Engineering Material", 300)

        price_values.append(w * matched)

    return sum(price_values)

# 3. Apply price computation
df["Cost_INR_per_kg"] = df["Categories"].apply(compute_price)

# 4. Derived metrics
if "Elastic Modulus" in df.columns:
    df["Cost_per_Stiffness"] = df["Cost_INR_per_kg"] / df["Elastic Modulus"]

if "UTS" in df.columns:
    df["Cost_per_Strength"] = df["Cost_INR_per_kg"] / df["UTS"]

if "CO2_kg_per_kg" in df.columns:
    df["Cost_per_CO2"] = df["Cost_INR_per_kg"] / df["CO2_kg_per_kg"]

# 5. Save final dataset
df.to_csv(OUTPUT, index=False)
print("Price enrichment complete →", OUTPUT)