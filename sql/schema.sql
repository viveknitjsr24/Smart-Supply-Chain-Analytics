-- ============================================================
-- schema.sql
-- Phase 8 - SQL Data Model
-- A simple star schema: one fact table (sales) + dimension tables
-- (products, warehouses) + one derived table (inventory snapshot).
-- ============================================================

CREATE TABLE dim_products (
    Product_ID      VARCHAR(10) PRIMARY KEY,
    Product_Name    VARCHAR(100),
    Category        VARCHAR(50),
    Supplier        VARCHAR(50),
    Unit_Price      DECIMAL(10,2),
    Lead_Time_Days  INT
);

CREATE TABLE dim_warehouses (
    Warehouse_ID              VARCHAR(20) PRIMARY KEY,
    Region                    VARCHAR(50),
    Warehouse_Capacity_Units  INT
);

CREATE TABLE fact_sales (
    Order_ID            INT,
    Sale_Date            DATE,
    Product_ID           VARCHAR(10),
    Warehouse_ID          VARCHAR(20),
    Sales_Quantity        INT,
    Unit_Price            DECIMAL(10,2),
    Discount_Percent      DECIMAL(5,2),
    Promotion_Applied     VARCHAR(3),
    Revenue               DECIMAL(12,2),
    PRIMARY KEY (Order_ID, Product_ID),
    FOREIGN KEY (Product_ID) REFERENCES dim_products(Product_ID),
    FOREIGN KEY (Warehouse_ID) REFERENCES dim_warehouses(Warehouse_ID)
);

-- Inventory snapshot: one row per SKU, refreshed periodically from the WMS.
-- Populated here from the Phase 6 inventory_optimization.csv output.
CREATE TABLE inventory_snapshot (
    Product_ID          VARCHAR(10) PRIMARY KEY,
    Current_Inventory    INT,
    Reorder_Point         INT,
    Safety_Stock          INT,
    EOQ                   INT,
    ABC_Class             CHAR(1),
    Inventory_Health      VARCHAR(40),
    FOREIGN KEY (Product_ID) REFERENCES dim_products(Product_ID)
);
