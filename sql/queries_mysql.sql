-- ============================================================
-- queries.sql
-- Phase 8 - Beginner-friendly business SQL queries
-- Tested against SQLite; syntax is close to standard ANSI SQL,
-- so only minor date-function tweaks are needed for MySQL/Postgres.
-- ============================================================

-- 1. MONTHLY SALES
-- What it answers: total revenue and units sold by calendar month.
-- Used for: the Monthly Sales Trend chart and finance reporting.
SELECT
    DATE_FORMAT(Sale_Date, '%Y-%m') AS Sales_Month,
    SUM(Sales_Quantity)          AS Total_Units,
    ROUND(SUM(Revenue), 2)       AS Total_Revenue
FROM fact_sales
GROUP BY Sales_Month
ORDER BY Sales_Month;


-- 2. PRODUCT DEMAND
-- What it answers: total historical demand (units) per product,
-- the base input for reorder and forecasting decisions.
SELECT
    p.Product_ID,
    p.Product_Name,
    p.Category,
    SUM(f.Sales_Quantity) AS Total_Demand_Units
FROM fact_sales f
JOIN dim_products p ON f.Product_ID = p.Product_ID
GROUP BY p.Product_ID, p.Product_Name, p.Category
ORDER BY Total_Demand_Units DESC;


-- 3. WAREHOUSE-WISE SALES
-- What it answers: which warehouse/region is moving the most product,
-- used to plan staffing and capacity per site.
SELECT
    w.Warehouse_ID,
    w.Region,
    SUM(f.Sales_Quantity)   AS Total_Units,
    ROUND(SUM(f.Revenue),2) AS Total_Revenue
FROM fact_sales f
JOIN dim_warehouses w ON f.Warehouse_ID = w.Warehouse_ID
GROUP BY w.Warehouse_ID, w.Region
ORDER BY Total_Revenue DESC;


-- 4. CURRENT INVENTORY
-- What it answers: a live look at what's on hand for every SKU right now.
SELECT
    i.Product_ID,
    p.Product_Name,
    i.Current_Inventory,
    i.Reorder_Point,
    i.ABC_Class
FROM inventory_snapshot i
JOIN dim_products p ON i.Product_ID = p.Product_ID
ORDER BY i.Current_Inventory DESC;


-- 5. LOW STOCK PRODUCTS (below Reorder Point)
-- What it answers: which SKUs are at risk of a stockout right now.
SELECT
    i.Product_ID,
    p.Product_Name,
    i.Current_Inventory,
    i.Reorder_Point,
    (i.Reorder_Point - i.Current_Inventory) AS Units_Short
FROM inventory_snapshot i
JOIN dim_products p ON i.Product_ID = p.Product_ID
WHERE i.Current_Inventory < i.Reorder_Point
ORDER BY Units_Short DESC;


-- 6. OVERSTOCKED PRODUCTS
-- What it answers: which SKUs are tying up excess capital/space.
SELECT
    i.Product_ID,
    p.Product_Name,
    i.Current_Inventory,
    i.Reorder_Point,
    i.Inventory_Health
FROM inventory_snapshot i
JOIN dim_products p ON i.Product_ID = p.Product_ID
WHERE i.Inventory_Health = 'Overstock'
ORDER BY i.Current_Inventory DESC;


-- 7. REORDER ALERTS
-- What it answers: an actionable daily list for the purchasing team -
-- exactly how many units to order per flagged SKU (rounded to the EOQ).
SELECT
    i.Product_ID,
    p.Product_Name,
    p.Supplier,
    i.Current_Inventory,
    i.Reorder_Point,
    i.EOQ AS Suggested_Order_Qty
FROM inventory_snapshot i
JOIN dim_products p ON i.Product_ID = p.Product_ID
WHERE i.Current_Inventory < i.Reorder_Point;


-- 8. ABC PRODUCTS
-- What it answers: how many SKUs (and how much revenue) fall in each
-- ABC class, to prioritize forecasting/replenishment effort.
SELECT
    i.ABC_Class,
    COUNT(*)                         AS Num_SKUs,
    ROUND(SUM(f_rev.Total_Revenue),2) AS Class_Revenue
FROM inventory_snapshot i
JOIN (
    SELECT Product_ID, SUM(Revenue) AS Total_Revenue
    FROM fact_sales
    GROUP BY Product_ID
) f_rev ON i.Product_ID = f_rev.Product_ID
GROUP BY i.ABC_Class
ORDER BY i.ABC_Class;


-- 9. INVENTORY TURNOVER
-- What it answers: how efficiently each SKU's inventory is being sold
-- through (higher = better capital efficiency).
SELECT
    p.Product_ID,
    p.Product_Name,
    ROUND(SUM(f.Sales_Quantity) * 1.0 / NULLIF(i.Current_Inventory, 0), 2) AS Inventory_Turnover
FROM fact_sales f
JOIN dim_products p ON f.Product_ID = p.Product_ID
JOIN inventory_snapshot i ON f.Product_ID = i.Product_ID
GROUP BY p.Product_ID, p.Product_Name, i.Current_Inventory
ORDER BY Inventory_Turnover DESC;


-- 10. TOP SELLING PRODUCTS
-- What it answers: the top 10 SKUs by revenue - useful for exec reporting
-- and for confirming ABC-A candidates.
SELECT
    p.Product_ID,
    p.Product_Name,
    p.Category,
    SUM(f.Sales_Quantity)   AS Units_Sold,
    ROUND(SUM(f.Revenue),2) AS Total_Revenue
FROM fact_sales f
JOIN dim_products p ON f.Product_ID = p.Product_ID
GROUP BY p.Product_ID, p.Product_Name, p.Category
ORDER BY Total_Revenue DESC
LIMIT 10;
