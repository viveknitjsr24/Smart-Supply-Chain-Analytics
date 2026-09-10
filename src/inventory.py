"""
inventory.py
------------
Phase 6 - Inventory Optimization

Uses historical demand (and the Phase 5 forecast) to compute, per SKU:
  - Average daily demand & demand std dev
  - EOQ (Economic Order Quantity)
  - Safety Stock
  - Reorder Point (ROP)
  - ABC Classification (revenue-based)
  - Inventory Turnover & Days of Inventory
  - Inventory Health Status (Understock / Optimal / Overstock)
  - Reorder Alerts

Output: data/processed/inventory_optimization.csv
"""

import numpy as np
import pandas as pd

CLEAN_PATH = "data/processed/supply_chain_clean.csv"
OUT_PATH = "data/processed/inventory_optimization.csv"

df = pd.read_csv(CLEAN_PATH, parse_dates=["Date"])

ORDERING_COST_PER_ORDER = 1000      # ₹ - cost to place & process one purchase order
HOLDING_COST_PCT_OF_PRICE = 0.10    # 10% of unit price per year to hold 1 unit in stock
SERVICE_Z = 1.65                    # Z-score for ~95% service level
NAIVE_BASELINE_DAYS = 21            # "no formal policy" baseline: flat 3 weeks of stock

# ------------------------------------------------------------------
# 1. Per-SKU demand statistics (daily grain, over the observed period)
# ------------------------------------------------------------------
n_days = (df["Date"].max() - df["Date"].min()).days + 1

sku = df.groupby(["Product_ID", "Product_Name", "Category", "Supplier"]).agg(
    Total_Units_Sold=("Sales_Quantity", "sum"),
    Total_Revenue=("Revenue", "sum"),
    Avg_Unit_Price=("Unit_Price", "mean"),
    Avg_Lead_Time_Days=("Lead_Time_Days", "mean"),
    Demand_Std_Daily_Proxy=("Sales_Quantity", "std"),
).reset_index()

sku["Avg_Daily_Demand"] = sku["Total_Units_Sold"] / n_days
sku["Demand_Std_Daily"] = sku["Demand_Std_Daily_Proxy"].fillna(0)
sku["Annual_Demand"] = sku["Avg_Daily_Demand"] * 365

# ------------------------------------------------------------------
# 2. EOQ = sqrt( (2 * Annual Demand * Ordering Cost) / Holding Cost per unit )
# ------------------------------------------------------------------
sku["Holding_Cost_Per_Unit"] = sku["Avg_Unit_Price"] * HOLDING_COST_PCT_OF_PRICE
sku["EOQ"] = np.sqrt(
    (2 * sku["Annual_Demand"] * ORDERING_COST_PER_ORDER) / sku["Holding_Cost_Per_Unit"]
).round().astype(int)

# ------------------------------------------------------------------
# 3. Safety Stock = Z * demand_std * sqrt(lead time in days)
# ------------------------------------------------------------------
sku["Safety_Stock"] = (
    SERVICE_Z * sku["Demand_Std_Daily"] * np.sqrt(sku["Avg_Lead_Time_Days"])
).round().astype(int)

# ------------------------------------------------------------------
# 4. Reorder Point = (Avg Daily Demand * Lead Time) + Safety Stock
# ------------------------------------------------------------------
sku["Reorder_Point"] = (
    sku["Avg_Daily_Demand"] * sku["Avg_Lead_Time_Days"] + sku["Safety_Stock"]
).round().astype(int)

# ------------------------------------------------------------------
# 5. ABC Classification (Pareto, by revenue contribution)
# ------------------------------------------------------------------
sku = sku.sort_values("Total_Revenue", ascending=False).reset_index(drop=True)
sku["Cumulative_Revenue_Pct"] = sku["Total_Revenue"].cumsum() / sku["Total_Revenue"].sum() * 100

def classify_abc(pct):
    if pct <= 70:
        return "A"
    elif pct <= 90:
        return "B"
    return "C"

sku["ABC_Class"] = sku["Cumulative_Revenue_Pct"].apply(classify_abc)

# ------------------------------------------------------------------
# 6. Simulated "current inventory on hand" snapshot
#    (in a real project this comes from the WMS; here we simulate a
#    realistic on-hand position so turnover/health-status math is real)
# ------------------------------------------------------------------
np.random.seed(3)
sku["Current_Inventory"] = (
    sku["Avg_Daily_Demand"] * np.random.uniform(8, 40, len(sku))
).round().astype(int)

# ------------------------------------------------------------------
# 7. Inventory Turnover & Days of Inventory (DOI)
#    Turnover = Annual Units Sold / Average Inventory
#    DOI = 365 / Turnover
# ------------------------------------------------------------------
sku["Inventory_Turnover"] = (sku["Annual_Demand"] / sku["Current_Inventory"].replace(0, np.nan)).round(2)
sku["Days_of_Inventory"] = (365 / sku["Inventory_Turnover"]).round(1)

# ------------------------------------------------------------------
# 8. Inventory Health Status
# ------------------------------------------------------------------
def health_status(row):
    if row["Current_Inventory"] < row["Reorder_Point"]:
        return "Understock - Reorder Needed"
    elif row["Current_Inventory"] > row["Reorder_Point"] + row["EOQ"] * 1.5:
        return "Overstock"
    return "Optimal"

sku["Inventory_Health"] = sku.apply(health_status, axis=1)
sku["Reorder_Alert"] = sku["Current_Inventory"] < sku["Reorder_Point"]

sku = sku.round(2)
sku.to_csv(OUT_PATH, index=False)

# ------------------------------------------------------------------
# 9. Sample calculation walkthrough (for README / interview explanation)
# ------------------------------------------------------------------
sample = sku.iloc[0]
print("===== SAMPLE EOQ / SAFETY STOCK / ROP CALCULATION =====")
print(f"SKU: {sample['Product_Name']} ({sample['Product_ID']})")
print(f"Annual Demand: {sample['Annual_Demand']:.0f} units")
print(f"Ordering Cost: Rs.{ORDERING_COST_PER_ORDER} | "
      f"Holding Cost/unit/year: Rs.{sample['Holding_Cost_Per_Unit']:.2f}")
print(f"EOQ = sqrt((2 x {sample['Annual_Demand']:.0f} x {ORDERING_COST_PER_ORDER}) / "
      f"{sample['Holding_Cost_Per_Unit']:.2f}) = {sample['EOQ']} units")
print(f"Safety Stock = {SERVICE_Z} x {sample['Demand_Std_Daily']:.2f} x "
      f"sqrt({sample['Avg_Lead_Time_Days']:.0f}) = {sample['Safety_Stock']} units")
print(f"Reorder Point = ({sample['Avg_Daily_Demand']:.2f} x {sample['Avg_Lead_Time_Days']:.0f}) "
      f"+ {sample['Safety_Stock']} = {sample['Reorder_Point']} units")

print("\n===== ABC CLASSIFICATION SUMMARY =====")
print(sku["ABC_Class"].value_counts())
print("\nRevenue share by class:")
print(sku.groupby("ABC_Class")["Total_Revenue"].sum() / sku["Total_Revenue"].sum() * 100)

print("\n===== INVENTORY HEALTH SUMMARY =====")
print(sku["Inventory_Health"].value_counts())

n_alerts = sku["Reorder_Alert"].sum()
print(f"\nReorder alerts triggered: {n_alerts} of {len(sku)} SKUs")

# Before vs after: naive "flat 3-week stock buffer, ignore demand variability"
# vs the EOQ+SafetyStock policy, compared on estimated annual holding cost
naive_inventory = sku["Avg_Daily_Demand"] * NAIVE_BASELINE_DAYS
optimized_inventory = (sku["EOQ"] / 2) + sku["Safety_Stock"]  # avg cycle stock + safety stock
naive_holding_cost = (naive_inventory * sku["Holding_Cost_Per_Unit"]).sum()
optimized_holding_cost = (optimized_inventory * sku["Holding_Cost_Per_Unit"]).sum()
reduction_pct = (1 - optimized_holding_cost / naive_holding_cost) * 100

print(f"\n===== BEFORE vs AFTER (Annual Holding Cost Estimate) =====")
print(f"Naive policy (flat {NAIVE_BASELINE_DAYS}-day stock, no formula): Rs.{naive_holding_cost:,.0f}")
print(f"EOQ + Safety Stock policy:                        Rs.{optimized_holding_cost:,.0f}")
print(f"Estimated holding cost reduction: {reduction_pct:.1f}%")

print(f"\nSaved detailed table to {OUT_PATH}")
