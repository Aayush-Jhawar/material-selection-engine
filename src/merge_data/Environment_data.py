import pandas as pd
import numpy as np
import re
from pathlib import Path

INP = Path("dataset_final_imputed.csv")
OUT = Path("materials_env_enriched.csv")

# 1. LOAD
df = pd.read_csv(INP)
for bad in ["Unnamed: 0", "index"]:
    if bad in df.columns:
        df = df.drop(columns=[bad])

# 2. BASIC NORMALIZATION
# Ensure 'Material Name' exists
if "Material Name" not in df.columns:
    raise ValueError("Expected 'Material Name' column not found.")

# Make sure we have a Categories column; if not, create an empty one
if "Categories" not in df.columns:
    df["Categories"] = ""

# Clean up obvious non-numeric artifacts if any remain
def to_float_or_nan(x):
    try:
        return float(x)
    except Exception:
        return np.nan

def extract_first_number(s):
    if pd.isna(s):
        return np.nan
    s = str(s)
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
    return float(m.group(0)) if m else np.nan

for col in [
    "Density",
    "UTS", "Elastic Modulus", "Shear Modulus", "Poisson Ratio",
    "Thermal Conductivity", "Dielectric Constant", "Dielectric Loss Index",
    "CTE (Linear)", "Glass Transition Temperature", "Softening Point",
    "Working Point", "Annealing Point",
    "Refractive Index", "UV Transmittance",
    "Cost_USD_per_kg"
]:
    if col in df.columns:
        df[col] = df[col].apply(extract_first_number)

# 3. BUILD CATEGORY MAPPINGS
def canon_cat(token: str) -> str:
    t = token.strip().lower()
    if t in {"ferrous metal", "steel", "stainless steel", "aisi", "alloy steel", "carbon steel"}:
        return "Steel"
    if t in {"nonferrous metal", "aluminium", "aluminum"}:
        return "Aluminum"
    if t in {"oxide", "aluminum oxide", "alumina"}:
        return "Oxide"
    if t in {"glass"}:
        return "Glass"
    if t in {"ceramic", "refractory"}:
        return "Ceramic"
    if t in {"brass"}:
        return "Brass"
    if t in {"bronze"}:
        return "Bronze"
    if t in {"copper"}:
        return "Copper"
    if t in {"titanium"}:
        return "Titanium"
    if t in {"abs"}:
        return "ABS"
    if t in {"pla"}:
        return "PLA"
    if t in {"nylon", "pa6", "pa66"}:
        return "Nylon"
    if t in {"polycarbonate", "pc"}:
        return "Polycarbonate"
    if t in {"polyethylene", "pe", "hdpe", "ldpe"}:
        return "Polyethylene"
    if t in {"pvc"}:
        return "PVC"
    if t in {"carbon fiber", "cfrp"}:
        return "Carbon Fiber"
    if t in {"wood", "hardwood", "softwood"}:
        return "Wood"
    if t in {"semiconductor"}:
        return "Semiconductor"
    return token.strip().title()

# Environmental baselines (kg CO2 per kg, recyclability in %)
ENV = {
    # metals
    "Steel":            {"co2": 2.2,  "recycle": 86},
    "Stainless Steel":  {"co2": 6.2,  "recycle": 80},
    "Aluminum":         {"co2": 8.4,  "recycle": 95},
    "Copper":           {"co2": 4.0,  "recycle": 90},
    "Brass":            {"co2": 3.4,  "recycle": 85},
    "Bronze":           {"co2": 3.9,  "recycle": 80},
    "Titanium":         {"co2": 35.0, "recycle": 65},

    # polymers
    "ABS":              {"co2": 2.8,  "recycle": 50},
    "PLA":              {"co2": 1.9,  "recycle": 55},
    "Nylon":            {"co2": 6.5,  "recycle": 60},
    "Polycarbonate":    {"co2": 5.5,  "recycle": 40},
    "Polyethylene":     {"co2": 2.0,  "recycle": 30},
    "PVC":              {"co2": 2.7,  "recycle": 20},

    # composites / inorganic
    "Carbon Fiber":     {"co2": 29.0, "recycle": 75},
    "Glass":            {"co2": 1.4,  "recycle": 30},
    "Ceramic":          {"co2": 2.5,  "recycle": 5},   # generic technical ceramic
    "Oxide":            {"co2": 2.7,  "recycle": 5},   # oxide ceramic baseline

    # natural
    "Wood":             {"co2": 1.1,  "recycle": 95},

    # catch-alls
    "Semiconductor":    {"co2": 20.0, "recycle": 10},
    "Other":            {"co2": 5.0,  "recycle": 30},
}
DEFAULT_CO2 = 5.0
DEFAULT_REC = 30.0

# 4. WEIGHTS PER NUMBER OF CATEGORY TOKENS
def category_weights(n):
    if n <= 0:
        return []
    if n == 1:
        return [1.0]
    if n == 2:
        return [0.75, 0.25]
    if n == 3:
        return [0.6, 0.3, 0.1]
    base = [0.5, 0.25, 0.15, 0.10]
    if n <= 4:
        return base[:n]
    else:
        w = base + [0.0]*(n-4)
        return w

# 5. MAP CATEGORIES → CO2 / REC WITH WEIGHTS
def weighted_env_from_categories(cat_str: str):
    if pd.isna(cat_str) or not str(cat_str).strip():
        return DEFAULT_CO2, DEFAULT_REC

    raw_tokens = [t for t in str(cat_str).split(";") if t.strip()]
    tokens = [canon_cat(t) for t in raw_tokens]
    weights = category_weights(len(tokens))

    co2_vals, rec_vals, wts = [], [], []

    for t, w in zip(tokens, weights):
        env = ENV.get(t, ENV.get("Other"))
        if env is None:
            env = {"co2": DEFAULT_CO2, "recycle": DEFAULT_REC}
        co2_vals.append(env["co2"])
        rec_vals.append(env["recycle"])
        wts.append(w)

    if not wts or sum(wts) == 0:
        return DEFAULT_CO2, DEFAULT_REC

    sw = sum(wts)
    co2 = sum(v*w for v, w in zip(co2_vals, wts)) / sw
    rec = sum(v*w for v, w in zip(rec_vals, wts)) / sw
    return co2, rec

env = df["Categories"].apply(weighted_env_from_categories)
df["CO2_kg_per_kg"] = [x[0] for x in env]
df["Recyclability_pct"] = [x[1] for x in env]

# 6. DERIVED METRICS
def safe_div(a, b):
    try:
        a = float(a)
        b = float(b)
        if np.isnan(a) or np.isnan(b) or b == 0:
            return np.nan
        return a / b
    except Exception:
        return np.nan

# Compute derived metrics only if inputs exist
if "UTS" in df.columns and "Density" in df.columns:
    df["Strength_to_Weight"] = df.apply(lambda r: safe_div(r.get("UTS"), r.get("Density")), axis=1)

if "Elastic Modulus" in df.columns and "Density" in df.columns:
    df["Specific_Stiffness"] = df.apply(lambda r: safe_div(r.get("Elastic Modulus"), r.get("Density")), axis=1)

if "Elastic Modulus" in df.columns and "Cost_USD_per_kg" in df.columns:
    df["Stiffness_to_Cost"] = df.apply(lambda r: safe_div(r.get("Elastic Modulus"), r.get("Cost_USD_per_kg")), axis=1)

# Eco Index = (Strength_to_Weight * recyclability) / CO2
if "Strength_to_Weight" in df.columns:
    df["Eco_Index"] = (df["Strength_to_Weight"] * (df["Recyclability_pct"] / 100.0)) / df["CO2_kg_per_kg"]

# 7. SAVE
df.to_csv(OUT, index=False)
print(f"Wrote: {OUT}")

# 8. QUICK REPORT
have_cost = "Cost_USD_per_kg" in df.columns and df["Cost_USD_per_kg"].notna().sum()
print(f"Rows: {len(df)}")
print(f"Non-null CO2 entries: {df['CO2_kg_per_kg'].notna().sum()}")
print(f"Non-null Recyclability entries: {df['Recyclability_pct'].notna().sum()}")
if "Strength_to_Weight" in df.columns:
    print(f"Non-null Strength_to_Weight: {df['Strength_to_Weight'].notna().sum()}")
if "Specific_Stiffness" in df.columns:
    print(f"Non-null Specific_Stiffness: {df['Specific_Stiffness'].notna().sum()}")
if "Eco_Index" in df.columns:
    print(f"Non-null Eco_Index: {df['Eco_Index'].notna().sum()}")
if have_cost:
    print(f"Rows with Cost_USD_per_kg: {have_cost}")