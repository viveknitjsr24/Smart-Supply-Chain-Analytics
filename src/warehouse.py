"""
warehouse.py
------------
Phase 7 - Warehouse Optimization (rule-based, no machine learning)

Uses the ABC classification + demand data from Phase 6 to:
  1. Assign warehouse slotting zones & shelf numbers (fast movers near dispatch)
  2. Identify fast-moving vs slow-moving SKUs
  3. Estimate warehouse utilization vs capacity
  4. Estimate picking efficiency (distance/time saved by good slotting)

Output: data/processed/warehouse_optimization.csv
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.dpi"] = 110

INVENTORY_PATH = "data/processed/inventory_optimization.csv"
CLEAN_PATH = "data/processed/supply_chain_clean.csv"
WAREHOUSE_DIM_PATH = "data/raw/dim_warehouses.csv"

inv = pd.read_csv(INVENTORY_PATH)
df = pd.read_csv(CLEAN_PATH, parse_dates=["Date"])
warehouses = pd.read_csv(WAREHOUSE_DIM_PATH)

# ------------------------------------------------------------------
# 1. Fast / Slow moving classification based on units sold per day
#    (velocity, independent of price - complements the revenue-based ABC)
# ------------------------------------------------------------------
inv["Velocity_Rank_Pct"] = inv["Avg_Daily_Demand"].rank(pct=True)

def movement_class(pct):
    if pct >= 0.66:
        return "Fast-Moving"
    elif pct >= 0.33:
        return "Medium-Moving"
    return "Slow-Moving"

inv["Movement_Class"] = inv["Velocity_Rank_Pct"].apply(movement_class)

# ------------------------------------------------------------------
# 2. Warehouse Slotting - assign each SKU to a Zone & Shelf Number
#    Rule: ABC class + movement speed together decide proximity to
#    the dispatch/packing area. Zone A = closest to dispatch (aisle 1),
#    Zone C = farthest (aisle 3).
# ------------------------------------------------------------------
def assign_zone(row):
    if row["ABC_Class"] == "A" or row["Movement_Class"] == "Fast-Moving":
        return "Zone 1 - Near Dispatch"
    elif row["ABC_Class"] == "B" or row["Movement_Class"] == "Medium-Moving":
        return "Zone 2 - Mid Aisle"
    return "Zone 3 - Back of Warehouse"

inv["Warehouse_Zone"] = inv.apply(assign_zone, axis=1)

zone_shelf_start = {"Zone 1 - Near Dispatch": 1, "Zone 2 - Mid Aisle": 101, "Zone 3 - Back of Warehouse": 201}
inv = inv.sort_values(["Warehouse_Zone", "Avg_Daily_Demand"], ascending=[True, False]).reset_index(drop=True)
inv["Shelf_Number"] = inv.groupby("Warehouse_Zone").cumcount() + 1
inv["Shelf_Number"] = inv.apply(lambda r: zone_shelf_start[r["Warehouse_Zone"]] + r["Shelf_Number"] - 1, axis=1)

# ------------------------------------------------------------------
# 3. Warehouse Utilization - compare current inventory (space proxy)
#    against each warehouse's capacity. We approximate each SKU's
#    footprint as 1 unit = 1 "capacity unit" and split current
#    inventory across warehouses by each SKU's regional sales mix.
# ------------------------------------------------------------------
wh_share = (
    df.groupby(["Product_ID", "Warehouse_ID"])["Sales_Quantity"].sum()
      .reset_index(name="Units")
)
wh_share["Warehouse_Share"] = wh_share.groupby("Product_ID")["Units"].transform(lambda s: s / s.sum())

inv_wh = wh_share.merge(inv[["Product_ID", "Current_Inventory", "ABC_Class", "Movement_Class"]], on="Product_ID")
inv_wh["Inventory_In_Warehouse"] = (inv_wh["Current_Inventory"] * inv_wh["Warehouse_Share"]).round().astype(int)

wh_util = inv_wh.groupby("Warehouse_ID")["Inventory_In_Warehouse"].sum().reset_index()
wh_util = wh_util.merge(warehouses, on="Warehouse_ID")
wh_util["Utilization_Pct"] = (wh_util["Inventory_In_Warehouse"] / wh_util["Warehouse_Capacity_Units"] * 100).round(1)

# ------------------------------------------------------------------
# 4. Picking Efficiency Analysis
#    Simple, explainable model: each "aisle hop" away from dispatch
#    adds fixed picking seconds. Compare total picking time under
#    the OLD naive layout (alphabetical/random shelving) vs the NEW
#    ABC-based slotting, weighted by pick frequency (units sold).
# ------------------------------------------------------------------
SECONDS_PER_ZONE_HOP = {"Zone 1 - Near Dispatch": 20, "Zone 2 - Mid Aisle": 45, "Zone 3 - Back of Warehouse": 75}
inv["Pick_Time_Sec_New_Layout"] = inv["Warehouse_Zone"].map(SECONDS_PER_ZONE_HOP)

# Naive layout = shelved in Product_ID order, ignoring velocity (common in unoptimized warehouses)
naive_order = inv.sort_values("Product_ID").reset_index(drop=True)
n = len(naive_order)
zones_cycle = (["Zone 1 - Near Dispatch"] * (n // 3) +
               ["Zone 2 - Mid Aisle"] * (n // 3) +
               ["Zone 3 - Back of Warehouse"] * (n - 2 * (n // 3)))
naive_order["Naive_Zone"] = zones_cycle
naive_order["Pick_Time_Sec_Naive_Layout"] = naive_order["Naive_Zone"].map(SECONDS_PER_ZONE_HOP)
inv = inv.merge(naive_order[["Product_ID", "Pick_Time_Sec_Naive_Layout"]], on="Product_ID")

inv["Total_Picks_Estimate"] = inv["Total_Units_Sold"]  # proxy: 1 pick per unit sold
inv["Total_Pick_Time_New_Hrs"] = (inv["Total_Picks_Estimate"] * inv["Pick_Time_Sec_New_Layout"]) / 3600
inv["Total_Pick_Time_Naive_Hrs"] = (inv["Total_Picks_Estimate"] * inv["Pick_Time_Sec_Naive_Layout"]) / 3600

total_new_hrs = inv["Total_Pick_Time_New_Hrs"].sum()
total_naive_hrs = inv["Total_Pick_Time_Naive_Hrs"].sum()
time_saved_pct = (1 - total_new_hrs / total_naive_hrs) * 100

inv.to_csv("data/processed/warehouse_optimization.csv", index=False)

# ------------------------------------------------------------------
# 5. Visualizations
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 4))
inv["Movement_Class"].value_counts().reindex(
    ["Fast-Moving", "Medium-Moving", "Slow-Moving"]
).plot(kind="bar", ax=ax, color=["#2E86AB", "#F18F01", "#C1666B"])
ax.set_title("SKU Count by Movement Class")
ax.set_ylabel("Number of SKUs")
ax.tick_params(axis="x", rotation=20)
fig.tight_layout()
fig.savefig("images/12_movement_class_distribution.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(wh_util["Warehouse_ID"], wh_util["Utilization_Pct"], color="#3B7A57")
ax.axhline(85, color="red", linestyle="--", label="85% capacity warning line")
ax.set_title("Warehouse Utilization (%)")
ax.set_ylabel("Utilization %")
ax.legend()
fig.tight_layout()
fig.savefig("images/13_warehouse_utilization.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["Naive Layout", "ABC-Optimized Layout"], [total_naive_hrs, total_new_hrs],
       color=["#C1666B", "#2E86AB"])
ax.set_title("Total Estimated Picking Time (18-month period)")
ax.set_ylabel("Hours")
fig.tight_layout()
fig.savefig("images/14_picking_efficiency.png")
plt.close(fig)

# ------------------------------------------------------------------
# 6. Console summary
# ------------------------------------------------------------------
print("===== MOVEMENT CLASSIFICATION =====")
print(inv["Movement_Class"].value_counts())

print("\n===== WAREHOUSE ZONE ASSIGNMENT (sample) =====")
print(inv[["Product_ID", "Product_Name", "ABC_Class", "Movement_Class",
           "Warehouse_Zone", "Shelf_Number"]].head(8).to_string(index=False))

print("\n===== WAREHOUSE UTILIZATION =====")
print(wh_util[["Warehouse_ID", "Region", "Inventory_In_Warehouse",
               "Warehouse_Capacity_Units", "Utilization_Pct"]].to_string(index=False))

print("\n===== PICKING EFFICIENCY =====")
print(f"Naive layout total pick time:  {total_naive_hrs:,.0f} hours")
print(f"ABC-optimized layout pick time: {total_new_hrs:,.0f} hours")
print(f"Estimated picking time saved:   {time_saved_pct:.1f}%")

print("\nSaved: data/processed/warehouse_optimization.csv, "
      "images/12-14 warehouse charts")
