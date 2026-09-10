# Smart Supply Chain Analytics: Demand Forecasting, Inventory & Warehouse Optimization

An end-to-end supply chain analytics project for an e-commerce company similar to **Flipkart** — built to answer the questions a real supply chain / business analyst team asks every week: what will we sell, what should we stock, and how should the warehouse be organized.

## Project Overview

Retail and e-commerce companies lose money two ways at once: **stockouts** (lost sales, unhappy customers) and **overstocking** (cash tied up in inventory that isn't moving). This project builds a lightweight, explainable analytics pipeline that:

1. Forecasts short-term demand
2. Converts that forecast into concrete inventory policies (how much to order, when)
3. Converts ABC/velocity data into warehouse slotting decisions
4. Surfaces everything through SQL queries and a Power BI dashboard

## Business Problem

The company has no formal replenishment policy — inventory is stocked on gut feel, some SKUs stock out while others sit unsold for months, and warehouse shelving isn't organized by how fast products actually move. This project quantifies the cost of that and proposes a data-driven alternative.

## Solution Summary

| Area | Approach |
|---|---|
| Forecasting | Moving Average, Exponential Smoothing, Random Forest — compared on MAE/MAPE |
| Inventory | EOQ, Safety Stock, Reorder Point, ABC Classification, Turnover, DOI |
| Warehouse | ABC/velocity-based slotting, shelf assignment, utilization, picking-efficiency modeling |
| Reporting | SQL (SQLite) + Power BI dashboard (Executive Summary, Forecast, Inventory, Warehouse pages) |

## Workflow

```
Raw transactional data (synthetic, Kaggle-style)
        │
        ▼
  Data Cleaning  ──►  EDA (9 charts)
        │
        ▼
 Demand Forecasting (MA / ES / Random Forest)
        │
        ▼
 Inventory Optimization (EOQ, Safety Stock, ROP, ABC)
        │
        ▼
 Warehouse Optimization (Slotting, Utilization, Picking Efficiency)
        │
        ▼
   SQL Tables  ──►  Power BI Dashboard  ──►  Business Recommendations
```

## Results (from this run of the pipeline)

- **Forecast accuracy:** 96.1% (3.87% MAPE) using Exponential Smoothing — the best of the three models tested
- **Inventory:** 35 of 40 SKUs (87.5%) sit in a healthy range; only 2 SKUs (5%) are below reorder point at the snapshot used
- **ABC concentration:** the top 13 SKUs (Class A) drive 68.8% of revenue — textbook Pareto distribution
- **Estimated holding-cost reduction:** ~43% vs. a naive flat-stock baseline, from moving to an EOQ + safety stock policy
- **Warehouse utilization:** 67–82% across the 3 warehouses (healthy, with headroom before the 85% capacity risk line)
- **Estimated picking-time reduction:** ~46% from ABC/velocity-based slotting vs. an unoptimized layout

All numbers above are generated live by the code in this repo (see `/data/processed` and the console output of each script) — nothing here is hard-coded.

## Project Structure

```
Smart-Supply-Chain-Analytics/
│
├── data/
│   ├── raw/                  # synthetic raw transactional data (+ dirty-data issues for cleaning practice)
│   └── processed/            # cleaned data + all analytical outputs (forecast, inventory, warehouse)
│
├── src/
│   ├── generate_data.py      # builds the synthetic Kaggle-style dataset
│   ├── data_cleaning.py      # Phase 3
│   ├── eda.py                # Phase 4
│   ├── forecasting.py        # Phase 5
│   ├── inventory.py          # Phase 6
│   └── warehouse.py          # Phase 7
│
├── sql/
│   ├── schema.sql                     # table definitions
│   ├── queries.sql                    # 10 business queries, explained
│   └── load_data_and_test_queries.py  # builds supply_chain.db and validates every query
│
├── dashboard/
│   ├── POWERBI_GUIDE.md       # page-by-page dashboard spec + DAX measures
│   └── powerbi_data/          # ready-to-import CSVs
│
├── images/                    # all 14 generated charts
├── README.md
├── requirements.txt
└── main.py                    # runs the entire pipeline end-to-end
```

## Installation & How to Run

```bash
git clone <your-repo-url>
cd Smart-Supply-Chain-Analytics
pip install -r requirements.txt
python main.py
```

This regenerates the synthetic dataset, cleans it, runs EDA, forecasts demand, computes inventory and warehouse optimization outputs, and builds/validates the SQL database — in about 15 seconds, fully reproducible via fixed random seeds.

To explore individual phases, run any script in `src/` directly, e.g. `python src/forecasting.py`.

To view the dashboard, open Power BI Desktop and follow `dashboard/POWERBI_GUIDE.md`.

## Dataset Note

This project uses a **synthetic dataset generated to match the structure of real Kaggle e-commerce/supply-chain datasets** (e.g., online retail transaction logs), with warehouse and inventory fields added since public datasets rarely include both sales and warehouse-level data together. See `src/generate_data.py` for exactly how it's constructed, and the Dataset Selection section below for real Kaggle datasets this mirrors.

**Recommended real-world Kaggle datasets covering similar ground:**
- "DataCo Smart Supply Chain for Big Data Analysis" — order/shipment-level data with product, region, and delivery fields
- "Online Retail II" (UCI/Kaggle) — transaction-level e-commerce sales
- "Store Item Demand Forecasting Challenge" — pure time-series demand data, good for the forecasting module specifically

## Future Improvements

- Replace the synthetic warehouse/inventory snapshot with a real WMS feed
- Add multi-step (multi-week) forecasting with confidence intervals
- Extend ABC analysis to a joint ABC-XYZ (velocity + variability) matrix
- Automate the reorder-alert query into a scheduled email/Slack notification
- Add a live Power BI connection (DirectQuery) instead of static CSV import

## Tech Stack

Python (Pandas, NumPy, Matplotlib, Scikit-learn) · SQL (SQLite) · Power BI · Git/GitHub
