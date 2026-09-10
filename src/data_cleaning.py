"""
data_cleaning.py
-----------------
Phase 3 - Data Cleaning

Fixes the realistic data issues injected into the raw dataset:
1. Missing values
2. Duplicate rows
3. Wrong data types
4. Invalid values (negative quantities)
5. Outliers
6. Inconsistent text / date formatting
7. Final validation checks

Input:  data/raw/supply_chain_raw.csv
Output: data/processed/supply_chain_clean.csv
"""

import numpy as np
import pandas as pd

RAW_PATH = "data/raw/supply_chain_raw.csv"
CLEAN_PATH = "data/processed/supply_chain_clean.csv"

df = pd.read_csv(RAW_PATH)
print(f"Raw rows loaded: {len(df)}")
log = {}

# ------------------------------------------------------------------
# 1. Standardize text columns (casing, whitespace)
# ------------------------------------------------------------------
df["Category"] = df["Category"].str.strip().str.title()
df["Region"] = df["Region"].str.strip().str.title()
df["Product_ID"] = df["Product_ID"].str.strip()

# ------------------------------------------------------------------
# 2. Fix inconsistent date formats, then convert to datetime
# ------------------------------------------------------------------
# Some dates come as "DD/MM/YYYY" instead of "YYYY-MM-DD"
def parse_date(value):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return pd.to_datetime(value, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.NaT

df["Date"] = df["Date"].apply(parse_date)
log["unparseable_dates"] = int(df["Date"].isna().sum())
df = df.dropna(subset=["Date"])

# ------------------------------------------------------------------
# 3. Fix data type issues: Sales_Quantity has stray text/whitespace
# ------------------------------------------------------------------
df["Sales_Quantity"] = pd.to_numeric(
    df["Sales_Quantity"].astype(str).str.strip(), errors="coerce"
)
log["non_numeric_quantity_rows"] = int(df["Sales_Quantity"].isna().sum())

# ------------------------------------------------------------------
# 4. Handle invalid values: negative quantities are data-entry errors
#    (not the same as "returns" in this dataset, so we correct the sign)
# ------------------------------------------------------------------
log["negative_quantity_rows"] = int((df["Sales_Quantity"] < 0).sum())
df["Sales_Quantity"] = df["Sales_Quantity"].abs()

# ------------------------------------------------------------------
# 5. Missing values
#    - Unit_Price: impute using the median price for that Product_ID
#    - Region: derive from Warehouse_ID (deterministic mapping)
#    - Discount_Percent: assume no discount if missing (business rule)
#    - Lead_Time_Days: impute using the median lead time for that Supplier
# ------------------------------------------------------------------
log["missing_before"] = df.isna().sum().to_dict()

df["Unit_Price"] = df.groupby("Product_ID")["Unit_Price"].transform(
    lambda s: s.fillna(s.median())
)

wh_to_region = {"WH_NORTH": "North", "WH_SOUTH": "South", "WH_WEST": "West"}
df["Region"] = df["Region"].fillna(df["Warehouse_ID"].map(wh_to_region))

df["Discount_Percent"] = df["Discount_Percent"].fillna(0)

df["Lead_Time_Days"] = df.groupby("Supplier")["Lead_Time_Days"].transform(
    lambda s: s.fillna(s.median())
)

# Drop any still-missing rows on truly critical fields (should be ~0 rows)
critical_cols = ["Product_ID", "Sales_Quantity", "Unit_Price", "Date"]
before_drop = len(df)
df = df.dropna(subset=critical_cols)
log["rows_dropped_missing_critical"] = before_drop - len(df)

# ------------------------------------------------------------------
# 6. Remove duplicate transactions
# ------------------------------------------------------------------
before_dupes = len(df)
df = df.drop_duplicates(subset=["Order_ID", "Product_ID", "Date"])
log["duplicate_rows_removed"] = before_dupes - len(df)

# ------------------------------------------------------------------
# 7. Outlier detection & treatment (IQR method) on Sales_Quantity,
#    applied per Category so a "large" order isn't unfairly flagged
#    for a low-volume category like Electronics
# ------------------------------------------------------------------
def cap_outliers_iqr(group, col, k=1.5):
    q1, q3 = group[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - k * iqr, q3 + k * iqr
    return group[col].clip(lower=max(lower, 0), upper=upper)

outlier_count_before = 0
for cat, group in df.groupby("Category"):
    q1, q3 = group["Sales_Quantity"].quantile([0.25, 0.75])
    iqr = q3 - q1
    upper = q3 + 1.5 * iqr
    outlier_count_before += int((group["Sales_Quantity"] > upper).sum())

df["Sales_Quantity"] = df.groupby("Category", group_keys=False).apply(
    lambda g: cap_outliers_iqr(g, "Sales_Quantity")
)
log["outliers_capped"] = outlier_count_before

# ------------------------------------------------------------------
# 8. Recompute Revenue after all corrections (source of truth)
# ------------------------------------------------------------------
df["Revenue"] = (df["Unit_Price"] * df["Sales_Quantity"] *
                  (1 - df["Discount_Percent"] / 100)).round(2)

# ------------------------------------------------------------------
# 9. Data validation checks
# ------------------------------------------------------------------
assert df["Sales_Quantity"].min() >= 0, "Negative quantities still present!"
assert df["Unit_Price"].min() > 0, "Non-positive prices present!"
assert df["Date"].isna().sum() == 0, "Null dates present!"
assert df.duplicated(subset=["Order_ID", "Product_ID", "Date"]).sum() == 0, "Duplicates remain!"

df["Sales_Quantity"] = df["Sales_Quantity"].round().astype(int)
df = df.sort_values("Date").reset_index(drop=True)

df.to_csv(CLEAN_PATH, index=False)

print("\n===== DATA CLEANING SUMMARY =====")
for k, v in log.items():
    print(f"{k}: {v}")
print(f"\nFinal clean rows: {len(df)}")
print(f"Saved cleaned dataset to {CLEAN_PATH}")
