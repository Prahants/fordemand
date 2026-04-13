"""
models.py - SQLAlchemy ORM Models

Defines the database tables for the inventory and demand forecasting system:
- Product: catalog of products
- Inventory: current stock levels and reorder thresholds
- Sales: historical sales records
- Forecast: Prophet model predictions
- Alert: low-stock alerts
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from backend.db.database import Base


class Product(Base):
    """Product catalog table."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)

    # Relationships
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    sales = relationship("Sales", back_populates="product")
    forecasts = relationship("Forecast", back_populates="product")
    alerts = relationship("Alert", back_populates="product")


class Inventory(Base):
    """
    Inventory table tracking current stock levels.
    Each product has one inventory record with stock count and reorder threshold.
    """
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    stock = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=10)
    last_updated = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    product = relationship("Product", back_populates="inventory")


class Sales(Base):
    """
    Sales table recording daily sales per product.
    Used as input data for Prophet forecasting.
    """
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    date = Column(Date, nullable=False)
    quantity_sold = Column(Integer, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="sales")


class Forecast(Base):
    """
    Forecast table storing Prophet model predictions.
    Each record is one day's predicted demand for a product.
    """
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    predicted_value = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="forecasts")


class Alert(Base):
    """
    Alert table for low-stock notifications.
    Generated when current stock falls below the calculated reorder point.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    product = relationship("Product", back_populates="alerts")
