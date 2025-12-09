# 🧪 Materials-ML Decision Engine  
### A Data-Driven Material Selection System using Scraping → Cleaning → Category-Aware Imputation → PCA/KMeans → TOPSIS Scoring

---

## 📌 Project Overview
This repository contains an **end-to-end machine learning pipeline** developed as part of the DES646 Practical Project.  
Unlike typical datasets sourced from Kaggle or GitHub, this project builds a **fully custom dataset from scratch** using:

- ✔️ **Web scraping** (MatWeb) — 2,400+ materials  
- ✔️ **Manual & automated data cleaning for malformed CSVs**  
- ✔️ **Category-aware imputation** using weighted ontology  
- ✔️ **Integration of sustainability metrics** (CO₂ footprint)  
- ✔️ **Cost estimation** using marketplace scraping  
- ✔️ **Feature scaling, PCA, clustering, correlations**  
- ✔️ **TOPSIS-based multi-criteria decision scoring**  
- ✔️ **Final ranked material recommendations**

The system combines **engineering, economic and environmental factors** into a unified decision engine.

---

## 🗂 Pipeline Architecture

Scraping → Cleaning → Normalisation →
Category-Weighted Imputation →
CO₂ & Cost Integration → Scaling → PCA →
KMeans Clustering → TOPSIS Scoring →
Ranked Material Recommendations

---

## 📁 Repository Structure

materials-ml-decision-engine/

│

├── data/

│ ├── raw/ # Scraped raw CSVs

│ ├── cleaned/ # Cleaned CSVs

│ ├── processed # Final enriched datasets

│

├── analysis/

│ ├── ml_pipeline.ipynb

│ ├── analysis.ipynb

│

├── src/

│ ├── scraper.py

│ ├── data_cleaning/ # Codes for cleaning and imputation

│ ├── data_merging/ # Merge Cost and Environmental data

│

└── README.md

---

## 🔍 Key Features

### **1. Custom Web Scraper**
- Handles JavaScript-generated pages  
- Extracts full material property tables  
- Captures 32+ physical, mechanical, thermal and optical properties  

---

### **2. Intelligent Data Cleaning**
- Fixes misaligned rows  
- Removes malformed embedded commas  
- Filters out non-numeric fragments like `"4.6 @ Frequency"`  
- Normalises units  

---

### **3. Category-Aware Imputation (Novel Contribution)**
Each material belongs to multiple classes, e.g.:
Ceramic → Oxide → Aluminium Oxide

Weighted imputation:

- 1 category → 100% weight  
- 2 categories → 0.75 + 0.25  
- 3 categories → 0.6 + 0.3 + 0.1  

This preserves *engineering meaning* and avoids unrealistic averages.

---

### **4. ML Pipeline**
- RobustScaler → PCA  
- KMeans clustering  
- Correlation analysis  
- TOPSIS scoring (multi-criteria decision making)  

Scores integrate:

- Performance  
- Cost  
- Environmental footprint  

---

### **5. Outputs**
- Ranked material list  
- PCA visualisation  
- Cluster map  
- TOPSIS distribution  
- Correlation matrix  

---
