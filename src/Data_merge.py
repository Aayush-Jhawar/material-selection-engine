#!/usr/bin/env python3
# enrich_materials.py
import pandas as pd
import numpy as np
import os
import re

INPUT = "Data.csv"
OUTPUT = "materials_enriched.csv"

if not os.path.exists(INPUT):
    raise SystemExit(f"Input file not found: {INPUT} (put this script in same folder as your Data.csv)")

df = pd.read_csv(INPUT)

# Show initial info
print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
print("Columns:", df.columns.tolist())

# Columns we expect to coerce to numeric
numeric_cols = ["Su","Sy","A5","Bhn","E","G","mu","Ro","HV"]
for col in numeric_cols:
    if col in df.columns:
        # extract first numeric token and convert
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',','').str.extract(r'([+-]?[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)')[0], errors='coerce')

# Create normalized material name for mapping
if "Material" in df.columns:
    df["Material_clean"] = df["Material"].astype(str).str.strip().str.lower()
    # remove punctuation
    df["Material_clean"] = df["Material_clean"].apply(lambda s: re.sub(r'[^a-z0-9\s\-()]','', s))
else:
    df["Material_clean"] = ""

# Simple cost and CO2 lookup (extend this dictionary with more keys as needed)
cost_lookup = {
    "aluminum": 2.5, "aluminium": 2.5, "aluminum 6061": 2.5,
    "steel": 0.8, "stainless steel": 1.5, "aisi 1045": 0.9,
    "copper": 6.0, "brass": 4.0, "titanium": 10.0,
    "pla": 1.5, "abs": 1.8, "nylon": 3.0, "polyethylene": 1.2, "polycarbonate": 2.0,
    "wood": 0.5, "glass": 1.0, "carbon fiber": 20.0
}
co2_lookup = {
    "aluminum": 9.0, "aluminium":9.0, "aluminum 6061":9.0,
    "steel": 2.1, "stainless steel": 3.0, "aisi 1045": 2.1,
    "copper": 3.8, "brass": 4.5, "titanium": 11.0,
    "pla": 2.8, "abs": 3.2, "nylon": 6.0, "polyethylene": 2.0, "polycarbonate": 3.0,
    "wood": 0.4, "glass": 1.5, "carbon fiber": 25.0
}

def map_lookup(s, lookup):
    if not isinstance(s, str) or s.strip()=="":
        return np.nan
    s = s.lower()
    for k,v in lookup.items():
        if k in s:
            return v
    return np.nan

df['Cost_per_kg_est'] = df['Material_clean'].apply(lambda x: map_lookup(x, cost_lookup))
df['CO2_per_kg_est'] = df['Material_clean'].apply(lambda x: map_lookup(x, co2_lookup))

# Derived features (guard against division by zero / NaN)
df['Strength_to_Weight'] = df.apply(lambda r: (r['Su']/r['Ro']) if pd.notna(r.get('Su')) and pd.notna(r.get('Ro')) and r['Ro']!=0 else np.nan, axis=1)
df['Stiffness_to_Cost'] = df.apply(lambda r: (r['E']/r['Cost_per_kg_est']) if pd.notna(r.get('E')) and pd.notna(r.get('Cost_per_kg_est')) and r['Cost_per_kg_est']!=0 else np.nan, axis=1)
df['Eco_Index'] = df.apply(lambda r: ((1.0/r['CO2_per_kg_est'])*r['Strength_to_Weight']) if pd.notna(r.get('CO2_per_kg_est')) and pd.notna(r.get('Strength_to_Weight')) and r['CO2_per_kg_est']!=0 else np.nan, axis=1)

# Save enriched file
df.to_csv(OUTPUT, index=False)
print(f"Enriched dataset saved to {OUTPUT} (rows: {df.shape[0]}, cols: {df.shape[1]})")

# Print quick diagnostics
print("\nMissing value counts (top 10):")
print(df.isnull().sum().sort_values(ascending=False).head(20))
print("\nSample rows with filled estimates:")
print(df.loc[df['Cost_per_kg_est'].notnull(), ['Material','Cost_per_kg_est','CO2_per_kg_est']].head(10).to_string(index=False))