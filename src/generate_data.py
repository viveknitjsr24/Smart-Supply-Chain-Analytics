"""
generate_data.py
-----------------
Creates a realistic, Kaggle-style e-commerce supply chain dataset.

Why synthetic data?
Kaggle's "Online Retail" / "DataCo Smart Supply Chain" datasets have sales
transactions but usually lack warehouse/inventory fields. Here we simulate
an e-commerce company similar to Flipkart, at daily transaction grain,
across multiple categories, regions/warehouses and products - then
inject realistic "dirty data" problems so Phase 3 (Data Cleaning) has
real issues to fix.

Output: data/raw/supply_chain_raw.csv
"""

import numpy as np
import pandas as pd

np.random.seed(42)

# ---------------------------------------------------------------
# 1. Master data: products, categories, warehouses, suppliers
# ---------------------------------------------------------------
categories = ["Electronics", "Fashion", "Home & Kitchen", "Grocery"]

products = []
product_id = 1000
for cat in categories:
    n_products = 10  # 10 SKUs per category -> 40 SKUs total
    for i in range(n_products):
        products.append({
            "Product_ID": f"SKU{product_id}",
            "Product_Name": f"{cat.split()[0]}_Item_{i+1}",
            "Category": cat,
            "Unit_Price": round(np.random.uniform(150, 25000)
                                 if cat == "Electronics" else
                                 np.random.uniform(150, 3000), 2),
            "Supplier": np.random.choice(["Supplier_A", "Supplier_B", "Supplier_C", "Supplier_D"]),
            "Lead_Time_Days": int(np.random.choice([3, 5, 7, 10, 14])),
        })
        product_id += 1

products_df = pd.DataFrame(products)

warehouses = pd.DataFrame({
    "Warehouse_ID": ["WH_NORTH", "WH_SOUTH", "WH_WEST"],
    "Region": ["North", "South", "West"],
    # Sized so utilization comes out realistic (~65-85%) given the demand
    # volume this dataset generates - not arbitrarily large like a real DC.
    "Warehouse_Capacity_Units": [2800, 2300, 2600],
})

# ---------------------------------------------------------------
# 2. Generate daily transactions for 18 months
# ---------------------------------------------------------------
date_range = pd.date_range(start="2024-01-01", end="2025-06-30", freq="D")

rows = []
order_id = 500000

for date in date_range:
    # weekend / promo seasonality
    is_weekend = date.dayofweek >= 5
    month = date.month
    is_festive_month = month in [10, 11, 12]  # Diwali/holiday season boost

    for _, prod in products_df.iterrows():
        # not every product sells every day (sparsity is realistic)
        if np.random.rand() > 0.55:
            continue

        base_demand = {
            "Electronics": 4, "Fashion": 8, "Home & Kitchen": 6, "Grocery": 15
        }[prod["Category"]]

        seasonal_factor = 1.4 if is_festive_month else 1.0
        weekend_factor = 1.25 if is_weekend else 1.0
        trend_factor = 1 + (date - date_range[0]).days / 1500  # slow upward trend

        promo = np.random.rand() < 0.12  # 12% of records are promo days
        promo_factor = 1.6 if promo else 1.0

        noise = np.random.normal(1, 0.25)

        qty = max(0, int(base_demand * seasonal_factor * weekend_factor *
                          trend_factor * promo_factor * noise))
        if qty == 0:
            continue

        warehouse = warehouses.sample(1).iloc[0]
        discount_pct = np.random.choice([0, 5, 10, 15, 20], p=[0.55, 0.15, 0.15, 0.10, 0.05])

        rows.append({
            "Order_ID": order_id,
            "Date": date.strftime("%Y-%m-%d"),
            "Product_ID": prod["Product_ID"],
            "Product_Name": prod["Product_Name"],
            "Category": prod["Category"],
            "Warehouse_ID": warehouse["Warehouse_ID"],
            "Region": warehouse["Region"],
            "Sales_Quantity": qty,
            "Unit_Price": prod["Unit_Price"],
            "Discount_Percent": discount_pct,
            "Promotion_Applied": "Yes" if promo else "No",
            "Supplier": prod["Supplier"],
            "Lead_Time_Days": prod["Lead_Time_Days"],
        })
        order_id += 1

df = pd.DataFrame(rows)
df["Revenue"] = (df["Unit_Price"] * df["Sales_Quantity"] * (1 - df["Discount_Percent"] / 100)).round(2)

print(f"Base clean rows generated: {len(df)}")

# ---------------------------------------------------------------
# 3. Inject realistic data quality issues (for the cleaning phase)
# ---------------------------------------------------------------
df_dirty = df.copy()
n = len(df_dirty)

# a) Missing values in a few columns
for col, frac in [("Discount_Percent", 0.02), ("Unit_Price", 0.015),
                   ("Region", 0.01), ("Lead_Time_Days", 0.02)]:
    idx = np.random.choice(n, size=int(n * frac), replace=False)
    df_dirty.loc[idx, col] = np.nan

# b) Duplicate rows (simulate double-logged orders)
dupes = df_dirty.sample(frac=0.01, random_state=1)
df_dirty = pd.concat([df_dirty, dupes], ignore_index=True)

# Cast to object dtype up front so we can mix numbers/strings/NaN like real messy exports
df_dirty["Sales_Quantity"] = df_dirty["Sales_Quantity"].astype(object)
n2 = len(df_dirty)

# c) Wrong data types (quantity stored as text with stray spaces)
text_idx = np.random.choice(n2, size=int(n2 * 0.03), replace=False)
df_dirty.loc[text_idx, "Sales_Quantity"] = df_dirty.loc[text_idx, "Sales_Quantity"].astype(str) + " "

# d) Invalid / negative values (data entry errors, e.g. returns logged incorrectly)
neg_idx = np.random.choice(n2, size=int(n2 * 0.005), replace=False)
df_dirty.loc[neg_idx, "Sales_Quantity"] = -pd.to_numeric(
    df_dirty.loc[neg_idx, "Sales_Quantity"].astype(str).str.strip(), errors="coerce"
).fillna(1)

# e) Outliers (fat-finger quantity entries, e.g. 500 instead of 5)
out_idx = np.random.choice(n2, size=int(n2 * 0.003), replace=False)
df_dirty.loc[out_idx, "Sales_Quantity"] = (
    pd.to_numeric(df_dirty.loc[out_idx, "Sales_Quantity"].astype(str).str.strip(), errors="coerce").fillna(5) * 40
)

# f) Inconsistent category text casing / whitespace
cat_idx = np.random.choice(n2, size=int(n2 * 0.02), replace=False)
df_dirty.loc[cat_idx, "Category"] = df_dirty.loc[cat_idx, "Category"].str.lower() + "  "

# g) Inconsistent date formats for a small subset (still parseable)
date_idx = np.random.choice(n2, size=int(n2 * 0.01), replace=False)
df_dirty.loc[date_idx, "Date"] = pd.to_datetime(df_dirty.loc[date_idx, "Date"]).dt.strftime("%d/%m/%Y")

# Shuffle rows so dirty rows aren't clustered at the end
df_dirty = df_dirty.sample(frac=1, random_state=7).reset_index(drop=True)

df_dirty.to_csv("data/raw/supply_chain_raw.csv", index=False)
products_df.to_csv("data/raw/dim_products.csv", index=False)
warehouses.to_csv("data/raw/dim_warehouses.csv", index=False)

print(f"Final raw (dirty) dataset rows: {len(df_dirty)}")
print("Saved: data/raw/supply_chain_raw.csv, dim_products.csv, dim_warehouses.csv")
print("\nMissing value snapshot:\n", df_dirty.isna().sum())
