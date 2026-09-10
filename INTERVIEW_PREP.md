# Interview Preparation - 20 Questions & Answers

## Supply Chain Questions

**1. What are the main KPIs you tracked in this project, and why do they matter?**
Forecast accuracy (MAPE), inventory turnover, days of inventory, stockout rate, and warehouse utilization. Together they balance the two competing goals of supply chain: don't run out of stock, and don't tie up cash in stock that isn't moving. No single KPI captures both, which is why I tracked several side by side.
*Follow-up: which KPI would you prioritize if you could only pick one?* Stockout rate — a stockout is a lost sale and a damaged customer relationship today, while excess inventory is a slower, recoverable cost.

**2. Why did you choose weekly demand aggregation instead of daily?**
Daily data was too noisy (many SKU-days had zero sales) to forecast reliably, and daily granularity isn't actionable for replenishment decisions anyway — lead times are measured in days-to-weeks. Weekly aggregation smooths noise while staying granular enough to react to short-term shifts like a promotion.

**3. How would this project change for a perishable goods company (e.g., groceries) vs. electronics?**
Perishables need shorter forecast horizons, tighter safety stock (spoilage risk instead of just stockout risk), and FEFO (first-expired-first-out) warehouse logic instead of pure ABC/velocity slotting. Electronics can tolerate longer lead times but carries higher holding cost per unit, which is exactly why the EOQ formula pushed toward smaller, more frequent orders for high-value SKUs in this project.

**4. What's the difference between a push and a pull supply chain strategy, and which does this project support?**
Push produces based on forecasts and pushes inventory downstream; pull produces/replenishes based on actual demand signals. This project is a pull-oriented design — the reorder point and EOQ system only triggers replenishment when real depletion crosses a threshold, rather than pre-building large batches on a schedule.

**5. What business risk did you not model, and how would you address it in a real deployment?**
Supplier reliability / lead-time variability. I used an average lead time per supplier, but in reality lead times fluctuate, and that variability should feed directly into the safety stock formula (I'd extend it to account for both demand variability and lead-time variability, not just demand variability).

## Forecasting Questions

**6. Why did you avoid ARIMA, Prophet, or deep learning models?**
The project brief and the business context called for it: an entry-level analyst needs to explain their model to a non-technical stakeholder, and the marginal accuracy gain from more complex models rarely justifies the loss of interpretability for a 40-SKU, moderately-seasonal dataset. Simpler models here were only marginally worse (or comparable) to Random Forest, which validates that choice.

**7. Walk me through how Exponential Smoothing works.**
It forecasts the next period as a weighted average of the most recent actual value and the previous forecast, controlled by a smoothing parameter alpha (0-1). A higher alpha reacts faster to recent changes but is noisier; a lower alpha is smoother but slower to adapt. I grid-searched alpha (0.1 to 0.9) and selected the value that minimized MAPE on the holdout set.

**8. Why did Random Forest not dramatically outperform the simpler models?**
With only ~70 weekly data points and a fairly stable demand pattern, there isn't enough signal or data volume for a tree-based model to meaningfully out-learn a well-tuned smoothing method. This is a common real-world result — complex models need more data and more complex patterns to earn their keep.
*Follow-up: when WOULD you expect Random Forest to win?* When there are strong, nonlinear interactions between multiple features (promotions, pricing, holidays, weather) and enough historical data to learn them.

**9. What's the difference between MAE and MAPE, and why report both?**
MAE is the average absolute error in the original units (e.g., units of demand) — easy to interpret but not comparable across SKUs with different scales. MAPE expresses that same error as a percentage of actual demand, which makes it comparable across products or time periods of different magnitude. Reporting both gives an absolute and a relative view.

**10. How would you validate that your forecast is actually good enough for the business, not just statistically good?**
I'd tie the forecast MAPE to a business outcome: run a service-level simulation showing that at this forecast accuracy, safety stock set with a 95% service level actually achieves close to 95% real-world fill rate. A "good enough" forecast is one where the downstream inventory decisions perform, not just one with a low error metric in isolation.

## Inventory Questions

**11. Explain the EOQ formula in plain English.**
EOQ finds the order quantity that minimizes the total of two competing costs: ordering cost (which favors fewer, bigger orders) and holding cost (which favors more, smaller orders). The formula, sqrt((2 × annual demand × ordering cost) / holding cost per unit), is the mathematical balance point between those two.

**12. Why did high-value Electronics SKUs get smaller EOQ values than cheaper Grocery SKUs?**
Holding cost per unit is a percentage of unit price, so high-value items are expensive to hold in stock. EOQ responds by recommending smaller, more frequent orders for those items to minimize capital tied up, while cheaper, high-volume grocery items can be ordered in larger batches more cheaply.

**13. How is Safety Stock different from Reorder Point?**
Safety stock is a buffer quantity to protect against demand and lead-time uncertainty. Reorder Point is the inventory level that triggers a new order — calculated as expected demand during lead time PLUS that safety stock buffer. Safety stock is one ingredient of the reorder point calculation, not a separate trigger.

**14. Why use ABC classification instead of treating all SKUs the same?**
Because effort and attention are limited resources. In this dataset, the top 13 SKUs (Class A) drove roughly 69% of revenue — spending equal forecasting/monitoring effort on all 40 SKUs would misallocate that effort. ABC lets you concentrate tight reorder points and frequent review on the SKUs that matter most financially.

**15. What would you do differently if a SKU was flagged "Overstock" for six months straight?**
I'd investigate the root cause before just discounting it: is demand structurally declining (needs a lower reorder point and possibly a markdown/liquidation plan), or is it a one-time overorder (a process fix, like tightening approval on large purchase orders)? I wouldn't apply the same fix to both cases.

## Warehouse Questions

**16. Why place fast-moving SKUs closer to the dispatch area?**
Every pick trip has a fixed "walk time" cost. If a SKU is picked frequently, that walk time is paid over and over — so minimizing distance for high-frequency SKUs has an outsized impact on total labor hours, versus optimizing placement for a SKU that's picked rarely.

**17. How did you measure "picking efficiency" without real warehouse layout data?**
I modeled it directly: each warehouse zone was assigned an estimated pick time (based on distance from dispatch), then multiplied by pick frequency (units sold) to get total labor hours under the old vs. new layout. It's a simplification of real time-and-motion studies, but it captures the core mechanism warehouse slotting is meant to exploit.

**18. If Warehouse_West is at 82% utilization and growing, what would you recommend?**
I'd flag it against the 85% risk threshold and recommend either rebalancing some SKU allocation to a less-utilized warehouse (North was at 67%), or starting capacity-expansion planning now rather than after a stockout-by-space-constraint event occurs — utilization problems are much cheaper to solve proactively.

## SQL Questions

**19. Why use a fact/dimension (star schema) design instead of one big flat table?**
Normalization avoids repeating product and warehouse attributes on every single sales row, keeps updates to master data (like a price change) in one place, and makes joins explicit and readable. For a BI tool like Power BI, a star schema is also the standard, best-performing structure for building measures and relationships.
*Follow-up: what's a tradeoff of normalizing?* Every query needs a JOIN, which is slightly more complex to write and can be marginally slower than a single denormalized table, though negligible at this data scale.

**20. Walk me through your Reorder Alerts query and why it's useful.**
It joins the inventory snapshot to the product table and filters to rows where Current_Inventory is less than Reorder_Point, returning exactly the actionable columns a buyer needs: which SKU, which supplier, and the suggested order quantity from the EOQ column. It's designed to be dropped straight into a scheduled report or dashboard table without any further processing — the business user doesn't need to interpret raw numbers, just act on the list.

---

## Power BI Questions (bonus, asked in some interviews)

**How did you decide what to put in a KPI card vs. a chart?**
KPI cards are for the handful of numbers a stakeholder needs to know before anything else (accuracy, turnover, stockout rate) — single values, no context needed. Charts are for anything that needs a trend or a comparison to be meaningful, like revenue over time or utilization across warehouses.

**Why sync slicers across dashboard pages?**
So a user filtering to, say, the Electronics category on the Executive Summary page sees that same filter reflected on the Inventory Health and Warehouse Performance pages, instead of having to re-filter each page manually — it keeps the whole dashboard telling one consistent story.
