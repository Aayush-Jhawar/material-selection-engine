# 🌐 Materials Selection Engine  
_A complete end-to-end computational pipeline for engineering material selection using scraped data, environmental metrics, and multi-criteria decision making._

## 🔍 Project Overview
This project builds a fully automated material-selection decision engine by integrating:

- **Custom web-scraping** of 2,500+ materials from MatWeb  
- **Data cleaning + error correction** for noisy scraped CSVs  
- **Category-aware weighted imputation** for missing values  
- **Environmental impact integration** (CO₂ per kg, recyclability, embodied energy)  
- **Economic factors** (scraped cost values)  
- **ML and MCDM techniques**:  
  - PCA for dimensionality reduction  
  - TOPSIS for ranking  
  - Weighted scoring based on engineering relevance  

The final output is a **ranked list of materials** optimized for engineering, environmental, and cost constraints.

---

## 🚀 Features

### ✔ 1. Robust Scraping System  
- Playwright-based automated scraper  
- Extracts complete property tables for every material  
- Handles pagination, tokenized forms, and dynamic content

### ✔ 2. Intelligent Cleaning Pipeline  
- Removes corrupted rows, misaligned fields, and text-embedded units  
- Unit normalization (e.g., GPa → MPa, g/cc → kg/m³)  
- Parsed structured numeric values from complex formats

### ✔ 3. Weighted Category-Based Imputation  
Missing values are filled using proportional weights from all category levels:
- Main category weight = 0.6  
- Subcategory weight = 0.3  
- Additional categories weight = 0.1  

This ensures imputed values match material families realistically.

### ✔ 4. Multi-Criteria Decision Making  
- Robust scaling  
- PCA variance analysis  
- TOPSIS scoring  
- Final ranking table for all materials

---

## 📁 Repository Structure
See folder tree in the repository root.

---

## 📊 Outputs
- Ranked materials CSV  
- All intermediate cleaned datasets  
- PCA plots, correlation matrices, TOPSIS distributions  
- Technical paper and final report

---
