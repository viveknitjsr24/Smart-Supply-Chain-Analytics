# Resume Content

## Project Summary (2-3 lines)

Built an end-to-end supply chain analytics pipeline for a simulated e-commerce business, combining demand forecasting, inventory optimization, and warehouse slotting to cut estimated holding costs by ~43% and picking time by ~46%. Delivered results through SQL and an interactive Power BI dashboard.

## Resume Bullet Points (ATS-friendly, measurable)

- Engineered an end-to-end supply chain analytics pipeline in Python (Pandas, NumPy, Scikit-learn) covering data cleaning, EDA, demand forecasting, and inventory/warehouse optimization for a 40-SKU, 3-warehouse e-commerce dataset.
- Built and compared three demand forecasting models (Moving Average, Exponential Smoothing, Random Forest), achieving **96.1% forecast accuracy (3.87% MAPE)** and selecting the best model via MAE/MAPE benchmarking.
- Designed a data-driven inventory policy (EOQ, Safety Stock, Reorder Point, ABC Classification) that reduced estimated annual holding costs by **~43%** versus a naive fixed-stock baseline, while cutting stockout risk to 5% of SKUs.
- Implemented ABC/velocity-based warehouse slotting logic that reduced estimated picking time by **~46%**, and built 10 production-style SQL queries plus a 4-page Power BI dashboard to surface KPIs (forecast accuracy, turnover, stockout rate, warehouse utilization) for business stakeholders.

## Key Technical Skills Demonstrated

- **Languages/Tools:** Python, SQL (SQLite), Power BI, Git/GitHub, VS Code
- **Libraries:** Pandas, NumPy, Matplotlib, Scikit-learn (Random Forest)
- **Techniques:** Data cleaning & validation, exploratory data analysis, time-series demand forecasting, EOQ/safety-stock modeling, ABC (Pareto) analysis, warehouse slotting logic, KPI dashboard design
- **Domain knowledge:** Inventory planning, warehouse operations, supply chain KPIs (forecast accuracy, inventory turnover, days of inventory, stockout rate, warehouse utilization)

## Interview Elevator Pitch (60-90 seconds)

"I built an end-to-end supply chain analytics project modeled on an e-commerce business like Flipkart, because I wanted to show the full loop from raw data to a business decision — not just a forecasting model in isolation.

I started with 18 months of transaction data across 40 SKUs and 3 warehouses, cleaned it — handling missing values, duplicates, and outliers — and ran EDA to understand seasonality, category mix, and promotion impact. For forecasting, I deliberately kept it simple: Moving Average and Exponential Smoothing as baselines, and a Random Forest with lag features as a slightly more sophisticated option. I compared them with MAE and MAPE rather than jumping to something like ARIMA or a neural network, because in a real inventory-planning context, a simple, explainable 96% accurate model that a supply chain manager can trust beats a marginally better black box.

The forecast then feeds directly into inventory decisions — I calculated EOQ, safety stock, and reorder points per SKU, and used ABC classification to prioritize which products deserve the tightest monitoring. That policy cut estimated holding costs by about 43% compared to a flat, one-size-fits-all stocking rule.

Finally, I used that same ABC and velocity data to redesign warehouse slotting — putting fast movers closer to dispatch — which reduced modeled picking time by around 46%. I wrapped it all in SQL queries for ad hoc business questions and a Power BI dashboard so the results are usable by someone non-technical, not just visible in a notebook."

