"""
prophet_model.py - Prophet Demand Forecasting Model

Core ML module that:
1. Converts sales data into Prophet format (ds, y)
2. Trains a Prophet model on historical data
3. Generates 7-day demand forecasts
4. Falls back to moving average if data points < 5
"""

import pandas as pd
import numpy as np
from prophet import Prophet
import logging

# Suppress Prophet's verbose logging output
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


def forecast_demand(dataframe: pd.DataFrame, periods: int = 7) -> dict:
    """
    Forecast future demand using Prophet or moving average fallback.

    Args:
        dataframe: DataFrame with columns ['date', 'quantity_sold']
        periods: Number of future days to forecast (default: 7)

    Returns:
        dict with keys:
            - 'forecasts': DataFrame with predicted values
            - 'method': 'prophet' or 'moving_average'
            - 'model': fitted Prophet model (None if fallback used)
    """

    # ─── Step 1: Data Preprocessing ───────────────────────────────
    # Sort by date and fill missing dates with forward fill
    df = dataframe.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Create complete date range and fill gaps
    full_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
    df = df.set_index("date").reindex(full_range).rename_axis("date").reset_index()
    df["quantity_sold"] = df["quantity_sold"].ffill().fillna(0)

    # ─── Step 2: Fallback Logic ───────────────────────────────────
    # Use moving average if we have fewer than 5 data points
    if len(df) < 5:
        return _moving_average_fallback(df, periods)

    # ─── Step 3: Convert to Prophet Format ────────────────────────
    # Prophet requires columns named 'ds' (datestamp) and 'y' (value)
    prophet_df = df.rename(columns={"date": "ds", "quantity_sold": "y"})

    # ─── Step 4: Train Prophet Model ──────────────────────────────
    model = Prophet(
        daily_seasonality=True,
        yearly_seasonality=False,
        weekly_seasonality=True,
    )
    model.fit(prophet_df)

    # ─── Step 5: Create Future Dataframe ──────────────────────────
    future = model.make_future_dataframe(periods=periods)

    # ─── Step 6: Generate Predictions ─────────────────────────────
    forecast = model.predict(future)

    # Extract only the future predictions (last N periods)
    future_forecast = forecast.tail(periods)[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    future_forecast = future_forecast.rename(columns={"ds": "date", "yhat": "predicted_value"})

    # Ensure predictions are non-negative (can't sell negative quantities)
    future_forecast["predicted_value"] = future_forecast["predicted_value"].clip(lower=0)

    return {
        "forecasts": future_forecast,
        "method": "prophet",
        "model": model,
        "full_forecast": forecast,
    }


def _moving_average_fallback(df: pd.DataFrame, periods: int) -> dict:
    """
    Fallback forecasting method using simple moving average.
    Used when there are fewer than 5 data points (not enough for Prophet).

    Args:
        df: DataFrame with columns ['date', 'quantity_sold']
        periods: Number of future days to forecast

    Returns:
        dict with forecast results using moving average method
    """
    # Calculate the average of all available data points
    avg_demand = df["quantity_sold"].mean()

    # Generate future dates
    last_date = df["date"].max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods)

    future_forecast = pd.DataFrame({
        "date": future_dates,
        "predicted_value": [round(avg_demand, 2)] * periods,
        "yhat_lower": [round(avg_demand * 0.8, 2)] * periods,
        "yhat_upper": [round(avg_demand * 1.2, 2)] * periods,
    })

    return {
        "forecasts": future_forecast,
        "method": "moving_average",
        "model": None,
        "full_forecast": None,
    }


def evaluate_model(actual: pd.Series, predicted: pd.Series) -> dict:
    """
    Evaluate model performance by comparing actual vs predicted values.

    Metrics:
        - MAE (Mean Absolute Error): Average absolute difference
        - RMSE (Root Mean Squared Error): Penalizes larger errors

    Args:
        actual: Series of actual sales values
        predicted: Series of predicted values

    Returns:
        dict with 'mae' and 'rmse' values
    """
    # Align lengths (use the shorter one)
    min_len = min(len(actual), len(predicted))
    actual = actual.iloc[:min_len].values
    predicted = predicted.iloc[:min_len].values

    # MAE = mean(|actual - predicted|)
    mae = float(np.mean(np.abs(actual - predicted)))

    # RMSE = sqrt(mean((actual - predicted)^2))
    rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))

    return {"mae": round(mae, 4), "rmse": round(rmse, 4)}
