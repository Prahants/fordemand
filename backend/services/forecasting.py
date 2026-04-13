"""
forecasting.py - Forecasting Service

Orchestrates the demand forecasting pipeline:
1. Fetches sales data from the database
2. Preprocesses data for Prophet
3. Runs the ML model (or fallback)
4. Calculates safety stock & reorder point
5. Stores forecast results in the database
6. Triggers alert checks
7. Returns comprehensive forecast results
"""

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from datetime import date

from backend.db.models import Sales, Forecast, Inventory, ForecastLog
from backend.services.inventory_service import (
    calculate_safety_stock,
    calculate_reorder_point,
    DEFAULT_LEAD_TIME,
    DEFAULT_Z_SCORE,
)
from backend.services.alert_service import check_and_create_alerts
from ml.prophet_model import forecast_demand, evaluate_model


def run_forecast_pipeline(
    db: Session,
    product_id: int,
    store_id: int = 1,
    lead_time: int = DEFAULT_LEAD_TIME,
    z_score: float = DEFAULT_Z_SCORE,
) -> dict:
    """
    Full forecasting pipeline for a given product.

    Steps:
        1. Fetch sales data from DB
        2. Sort by date and preprocess
        3. Convert to Prophet format
        4. Apply Prophet model (or moving average fallback)
        5. Forecast next 7 days
        6. Calculate safety stock and reorder point
        7. Evaluate model (MAE, RMSE) if enough data
        8. Store results in DB
        9. Check alerts
        10. Return forecast results

    Args:
        db: Database session
        product_id: Product ID to forecast
        lead_time: Replenishment lead time in days
        z_score: Service level Z-score

    Returns:
        dict with forecasts, metrics, and alert info
    """

    # ─── Step 1: Fetch Sales Data ────────────────────────────────
    sales_records = (
        db.query(Sales)
        .filter(Sales.product_id == product_id, Sales.store_id == store_id)
        .order_by(Sales.date)
        .all()
    )

    if not sales_records:
        return {"error": f"No sales data found for product {product_id}"}

    # ─── Step 2: Convert to DataFrame ────────────────────────────
    sales_data = pd.DataFrame([
        {"date": record.date, "quantity_sold": record.quantity_sold}
        for record in sales_records
    ])

    # ─── Step 3-5: Run Prophet Model ─────────────────────────────
    result = forecast_demand(sales_data, periods=7)

    forecasts_df = result["forecasts"]
    method = result["method"]

    # ─── Step 6: Calculate Business Metrics ───────────────────────
    # Standard deviation of historical daily demand
    std_dev = float(sales_data["quantity_sold"].std())

    # Average forecasted daily demand
    avg_forecast = float(forecasts_df["predicted_value"].mean())

    safety_stock = calculate_safety_stock(std_dev, lead_time, z_score)

    # Reorder Point = (avg_forecast * lead_time) + safety_stock
    reorder_point = calculate_reorder_point(avg_forecast, lead_time, safety_stock)

    # ─── Step 7: Model Evaluation (MAE / RMSE) ───────────────────
    mae, rmse = None, None
    if method == "prophet" and result["full_forecast"] is not None:
        full_forecast = result["full_forecast"]
        # Compare in-sample predictions with actual values
        historical_predictions = full_forecast.head(len(sales_data))
        if len(historical_predictions) > 0:
            metrics = evaluate_model(
                actual=sales_data["quantity_sold"].reset_index(drop=True),
                predicted=historical_predictions["yhat"].reset_index(drop=True),
            )
            mae = metrics["mae"]
            rmse = metrics["rmse"]

    # ─── Step 8: Store Forecast Results in DB ─────────────────────
    # Clear old forecasts for this product
    db.query(Forecast).filter(Forecast.product_id == product_id).delete()

    stored_forecasts = []
    for _, row in forecasts_df.iterrows():
        forecast_record = Forecast(
            product_id=product_id,
            predicted_value=round(float(row["predicted_value"]), 2),
            date=pd.Timestamp(row["date"]).date(),
        )
        db.add(forecast_record)
        stored_forecasts.append(forecast_record)

    db.commit()

    # Refresh to get IDs
    for f in stored_forecasts:
        db.refresh(f)

    # ─── Step 9: Check Alerts ─────────────────────────────────────
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id, Inventory.store_id == store_id)
        .first()
    )
    alert = None
    if inventory:
        # Update reorder threshold in inventory
        inventory.reorder_threshold = int(reorder_point)
        db.commit()

        alert = check_and_create_alerts(
            db, product_id, store_id, inventory.stock, reorder_point
        )

    # ─── Step 9.5: Store Forecast Logs (predicted vs actual variance) ───────
    for _, row in forecasts_df.iterrows():
        horizon_date = pd.Timestamp(row["date"]).date()
        actual_sale = (
            db.query(Sales)
            .filter(
                Sales.product_id == product_id,
                Sales.store_id == store_id,
                Sales.date == horizon_date,
            )
            .first()
        )
        actual_demand = float(actual_sale.quantity_sold) if actual_sale else None
        predicted_demand = round(float(row["predicted_value"]), 2)
        variance = (
            round(actual_demand - predicted_demand, 2)
            if actual_demand is not None
            else None
        )
        db.add(
            ForecastLog(
                product_id=product_id,
                store_id=store_id,
                horizon_date=horizon_date,
                predicted_demand=predicted_demand,
                actual_demand=actual_demand,
                variance=variance,
            )
        )
    db.commit()

    # ─── Step 10: Return Results ──────────────────────────────────
    return {
        "product_id": product_id,
        "store_id": store_id,
        "forecasts": [
            {
                "id": f.id,
                "product_id": f.product_id,
                "predicted_value": f.predicted_value,
                "date": f.date,
            }
            for f in stored_forecasts
        ],
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "mae": mae,
        "rmse": rmse,
        "method": method,
        "alert": {
            "id": alert.id,
            "message": alert.message,
        } if alert else None,
    }
