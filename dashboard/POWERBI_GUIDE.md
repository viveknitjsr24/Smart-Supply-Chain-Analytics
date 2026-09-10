# Power BI Dashboard Guide

Power BI (.pbix) is a desktop application, so it can't be generated as a text
file — instead, this folder gives you everything needed to build it in
Power BI Desktop in under 30 minutes: clean, ready-to-import CSVs, the exact
data model, DAX measures, and a page-by-page visual spec.

## 1. Import the data

Open Power BI Desktop → **Get Data → Text/CSV** → import all 7 files from
`dashboard/powerbi_data/`:

| File | Role |
|---|---|
| `fact_sales.csv` | Fact table — one row per transaction |
| `dim_products.csv` | Dimension — product/category/supplier master data |
| `dim_warehouses.csv` | Dimension — warehouse/region master data |
| `inventory_optimization.csv` | EOQ, safety stock, ROP, ABC class, health status per SKU |
| `warehouse_optimization.csv` | Zone, shelf number, movement class per SKU |
| `forecast_model_comparison.csv` | MAE/MAPE for the 3 forecasting models |
| `next_4_week_forecast.csv` | Forward-looking demand forecast |

## 2. Build the data model

In **Model view**, create these relationships (all one-to-many, single direction):

- `dim_products[Product_ID]` → `fact_sales[Product_ID]`
- `dim_warehouses[Warehouse_ID]` → `fact_sales[Warehouse_ID]`
- `dim_products[Product_ID]` → `inventory_optimization[Product_ID]`
- `dim_products[Product_ID]` → `warehouse_optimization[Product_ID]`

## 3. Key DAX measures

```DAX
Total Revenue = SUM(fact_sales[Revenue])
Total Units Sold = SUM(fact_sales[Sales_Quantity])

Forecast Accuracy % =
VAR BestMAPE = MIN(forecast_model_comparison[MAPE])
RETURN 1 - (BestMAPE / 100)

Avg Inventory Turnover = AVERAGE(inventory_optimization[Inventory_Turnover])

Stockout Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(inventory_optimization), inventory_optimization[Reorder_Alert] = TRUE),
    COUNTROWS(inventory_optimization)
)

Service Level % = 0.95   -- based on the Z=1.65 service level used for Safety Stock

Warehouse Utilization % =
DIVIDE(
    SUM(warehouse_optimization[Current_Inventory]),
    SUM(dim_warehouses[Warehouse_Capacity_Units])
)
```

## 4. Dashboard pages & visuals

### Page 1 — Executive Summary
- **KPI cards (top row):** Total Revenue, Total Units Sold, Forecast Accuracy %, Inventory Turnover, Warehouse Utilization %
- **Line chart:** Monthly Revenue Trend (`fact_sales[Sale_Date]` by month vs `Total Revenue`)
- **Pie chart:** Revenue by Category
- **Bar chart:** Revenue by Region
- **Slicers:** Date range, Category, Region
- *Communicates:* one-glance business health for leadership.

### Page 2 — Demand Forecast
- **KPI cards:** Forecast Accuracy % (best model), Best Model Name, Next Week Forecast
- **Line chart:** Actual weekly demand vs forecast for the test window
- **Bar chart:** Model Comparison (MAPE by model, from `forecast_model_comparison.csv`)
- **Table:** `next_4_week_forecast.csv` — the actionable forward forecast
- *Communicates:* how much to expect, and how much to trust the forecast.

### Page 3 — Inventory Health
- **KPI cards:** Stockout Rate %, # Overstocked SKUs, Avg Inventory Turnover, Avg Days of Inventory
- **Bar chart:** SKU count by `Inventory_Health` (Understock / Optimal / Overstock)
- **Table:** Reorder alert list (`Current_Inventory < Reorder_Point`), sortable
- **Pie chart:** Revenue share by ABC Class
- **Slicer:** ABC Class, Category
- *Communicates:* which SKUs need action today (buy more / stop overordering).

### Page 4 — Warehouse Performance
- **KPI cards:** Warehouse Utilization %, Picking Time Saved %, # Fast-Moving SKUs
- **Bar chart:** Utilization % by Warehouse (with an 85% capacity reference line)
- **Bar chart:** SKU count by Movement Class (Fast/Medium/Slow)
- **Table:** Zone & shelf assignment per SKU
- *Communicates:* whether warehouses are balanced and whether slotting is working.

## 5. Design notes
- Use a consistent 3-4 color palette (blue = primary metric, orange = attention/alert, green = positive/optimal, red = risk).
- Keep KPI cards at the top of every page so a viewer can assess status in 5 seconds before drilling into charts.
- Add a Date slicer synced across pages (Edit Interactions) so all four pages respond to the same time filter.
