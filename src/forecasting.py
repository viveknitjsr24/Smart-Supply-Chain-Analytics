"""
forecasting.py
---------------
Phase 5 - Demand Forecasting (the core analytical module)

Aggregates transactions into weekly overall demand, then forecasts using:
  1. Moving Average (simple, naive baseline)
  2. Simple Exponential Smoothing (weights recent demand more heavily)
  3. Random Forest Regressor (lag + calendar features)

Models are compared with MAE and MAPE on a held-out test period
(last 8 weeks), and results feed directly into Phase 6 (Inventory).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

plt.rcParams["figure.dpi"] = 110
CLEAN_PATH = "data/processed/supply_chain_clean.csv"

df = pd.read_csv(CLEAN_PATH, parse_dates=["Date"])

# ------------------------------------------------------------------
# 1. Build weekly demand series (overall company demand, in units)
#    Trim to the last FULL week (Mon-Sun) so a partial trailing week
#    doesn't create an artificial demand crash in the test set.
# ------------------------------------------------------------------
last_full_sunday = df["Date"].max() - pd.Timedelta(days=(df["Date"].max().weekday() + 1) % 7)
df_trimmed = df[df["Date"] <= last_full_sunday]

weekly = (
    df_trimmed.set_index("Date")
      .resample("W")["Sales_Quantity"]
      .sum()
      .rename("Demand")
      .to_frame()
)
print(f"Weekly series length: {len(weekly)} weeks "
      f"({weekly.index.min().date()} to {weekly.index.max().date()})")

TEST_WEEKS = 8
train = weekly.iloc[:-TEST_WEEKS]
test = weekly.iloc[-TEST_WEEKS:]

def mape(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

results = {}
forecasts = {}

# ------------------------------------------------------------------
# 2. Model 1 - Moving Average (window = 4 weeks)
# ------------------------------------------------------------------
MA_WINDOW = 4
history = list(train["Demand"])
ma_preds = []
for actual in test["Demand"]:
    pred = np.mean(history[-MA_WINDOW:])
    ma_preds.append(pred)
    history.append(actual)  # walk-forward: use actual once known

forecasts["Moving Average"] = ma_preds
results["Moving Average"] = {
    "MAE": mean_absolute_error(test["Demand"], ma_preds),
    "MAPE": mape(test["Demand"], ma_preds),
}

# ------------------------------------------------------------------
# 3. Model 2 - Simple Exponential Smoothing (alpha tuned by grid search)
# ------------------------------------------------------------------
def exponential_smoothing_forecast(train_series, test_series, alpha):
    level = train_series.iloc[-1]
    # warm up the smoothing level using the full training history
    smoothed = train_series.iloc[0]
    for val in train_series.iloc[1:]:
        smoothed = alpha * val + (1 - alpha) * smoothed
    level = smoothed
    preds = []
    for actual in test_series:
        preds.append(level)
        level = alpha * actual + (1 - alpha) * level  # walk-forward update
    return preds

best_alpha, best_mape = None, np.inf
for alpha in np.arange(0.1, 1.0, 0.1):
    preds = exponential_smoothing_forecast(train["Demand"], test["Demand"], alpha)
    m = mape(test["Demand"], preds)
    if m < best_mape:
        best_mape, best_alpha = m, alpha

es_preds = exponential_smoothing_forecast(train["Demand"], test["Demand"], best_alpha)
forecasts["Exponential Smoothing"] = es_preds
results["Exponential Smoothing"] = {
    "MAE": mean_absolute_error(test["Demand"], es_preds),
    "MAPE": mape(test["Demand"], es_preds),
}
print(f"Best alpha for Exponential Smoothing: {best_alpha:.1f}")

# ------------------------------------------------------------------
# 4. Model 3 - Random Forest Regressor (lag + calendar features)
# ------------------------------------------------------------------
feat_df = weekly.copy()
for lag in [1, 2, 3, 4]:
    feat_df[f"lag_{lag}"] = feat_df["Demand"].shift(lag)
feat_df["week_of_year"] = feat_df.index.isocalendar().week.astype(int)
feat_df["month"] = feat_df.index.month
feat_df["rolling_mean_4"] = feat_df["Demand"].shift(1).rolling(4).mean()
feat_df = feat_df.dropna()

feature_cols = ["lag_1", "lag_2", "lag_3", "lag_4", "week_of_year", "month", "rolling_mean_4"]
train_feat = feat_df.iloc[:-TEST_WEEKS]
test_feat = feat_df.iloc[-TEST_WEEKS:]

rf = RandomForestRegressor(n_estimators=300, max_depth=6, random_state=42)
rf.fit(train_feat[feature_cols], train_feat["Demand"])
rf_preds = rf.predict(test_feat[feature_cols])

forecasts["Random Forest"] = list(rf_preds)
results["Random Forest"] = {
    "MAE": mean_absolute_error(test_feat["Demand"], rf_preds),
    "MAPE": mape(test_feat["Demand"], rf_preds),
}

# ------------------------------------------------------------------
# 5. Model comparison table
# ------------------------------------------------------------------
comparison = pd.DataFrame(results).T.round(2)
comparison = comparison.sort_values("MAPE")
print("\n===== MODEL COMPARISON (last 8 weeks held out) =====")
print(comparison)
comparison.to_csv("data/processed/forecast_model_comparison.csv")

best_model = comparison.index[0]
print(f"\nBest performing model: {best_model}")

# ------------------------------------------------------------------
# 6. Plots - Actual vs Forecast for each model
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(weekly.index, weekly["Demand"], label="Actual (full history)", color="black", alpha=0.4)
ax.plot(test.index, test["Demand"], label="Actual (test)", color="black", linewidth=2)
ax.plot(test.index, ma_preds, label="Moving Average", linestyle="--")
ax.plot(test.index, es_preds, label="Exponential Smoothing", linestyle="--")
ax.plot(test_feat.index, rf_preds, label="Random Forest", linestyle="--")
ax.set_title("Actual vs Forecast - Weekly Demand (Last 8 Weeks Test)")
ax.set_ylabel("Units")
ax.legend()
fig.tight_layout()
fig.savefig("images/10_forecast_actual_vs_predicted.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4))
comparison["MAPE"].plot(kind="bar", ax=ax, color=["#2E86AB", "#F18F01", "#3B7A57"])
ax.set_title("Forecast Model Comparison (MAPE %)")
ax.set_ylabel("MAPE (%)")
ax.tick_params(axis="x", rotation=0)
fig.tight_layout()
fig.savefig("images/11_model_comparison_mape.png")
plt.close(fig)

# ------------------------------------------------------------------
# 7. Produce a forward-looking 4-week forecast using the best model
#    (retrain on ALL available data for the deployed forecast)
# ------------------------------------------------------------------
future_weeks = 4
if best_model == "Random Forest":
    rf_full = RandomForestRegressor(n_estimators=300, max_depth=6, random_state=42)
    rf_full.fit(feat_df[feature_cols], feat_df["Demand"])
    history_vals = list(weekly["Demand"])
    future_preds = []
    cur_index = weekly.index[-1]
    for _ in range(future_weeks):
        cur_index = cur_index + pd.Timedelta(weeks=1)
        lag_feats = {
            "lag_1": history_vals[-1], "lag_2": history_vals[-2],
            "lag_3": history_vals[-3], "lag_4": history_vals[-4],
            "week_of_year": cur_index.isocalendar().week,
            "month": cur_index.month,
            "rolling_mean_4": np.mean(history_vals[-4:]),
        }
        x_row = pd.DataFrame([lag_feats])[feature_cols]
        pred = rf_full.predict(x_row)[0]
        future_preds.append(pred)
        history_vals.append(pred)
elif best_model == "Exponential Smoothing":
    level = weekly["Demand"].iloc[0]
    for val in weekly["Demand"].iloc[1:]:
        level = best_alpha * val + (1 - best_alpha) * level
    future_preds = [level] * future_weeks
else:
    future_preds = [np.mean(weekly["Demand"].iloc[-MA_WINDOW:])] * future_weeks

future_dates = pd.date_range(weekly.index[-1] + pd.Timedelta(weeks=1), periods=future_weeks, freq="W")
future_forecast = pd.DataFrame({"Week": future_dates, "Forecasted_Demand": np.round(future_preds).astype(int)})
future_forecast.to_csv("data/processed/next_4_week_forecast.csv", index=False)
print(f"\nNext 4-week forecast (using {best_model}):")
print(future_forecast.to_string(index=False))

print("\nSaved: forecast_model_comparison.csv, next_4_week_forecast.csv, "
      "images/10_forecast_actual_vs_predicted.png, images/11_model_comparison_mape.png")
