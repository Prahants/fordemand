"""
models.py - SQLAlchemy ORM Models

Defines the database tables for the inventory and demand forecasting system:
- Product: catalog of products
- Inventory: current stock levels and reorder thresholds
- Sales: historical sales records
- Forecast: Prophet model predictions
- Alert: low-stock alerts
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Date,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from backend.db.database import Base


class Product(Base):
    """Product catalog table."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    sku = Column(String, nullable=True, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Relationships
    inventory = relationship("Inventory", back_populates="product")
    sales = relationship("Sales", back_populates="product")
    forecasts = relationship("Forecast", back_populates="product")
    alerts = relationship("Alert", back_populates="product")
    supplier = relationship("Supplier", back_populates="products")


class Supplier(Base):
    """Supplier information for procurement and replenishment."""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    contact_email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    products = relationship("Product", back_populates="supplier")


class Store(Base):
    """Store or warehouse location."""
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    location = Column(String, nullable=True)
    store_type = Column(String, nullable=False, default="store")  # store/warehouse

    inventory = relationship("Inventory", back_populates="store")
    sales = relationship("Sales", back_populates="store")
    alerts = relationship("Alert", back_populates="store")


class User(Base):
    """Simple user model with role-based authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False, default="staff")  # admin/manager/staff


class Inventory(Base):
    """
    Inventory table tracking current stock levels.
    Each product has one inventory record with stock count and reorder threshold.
    """
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, default=1)
    stock = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=10)
    last_updated = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    product = relationship("Product", back_populates="inventory")
    store = relationship("Store", back_populates="inventory")

    __table_args__ = (
        UniqueConstraint("product_id", "store_id", name="uq_inventory_product_store"),
    )


class Sales(Base):
    """
    Sales table recording daily sales per product.
    Used as input data for Prophet forecasting.
    """
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    date = Column(Date, nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, default=1)
    quantity_sold = Column(Integer, nullable=False)
    promotion_flag = Column(Boolean, nullable=False, default=False)
    season_tag = Column(String, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="sales")
    store = relationship("Store", back_populates="sales")


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
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, default=1)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")  # open/ack/resolved
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    product = relationship("Product", back_populates="alerts")
    store = relationship("Store", back_populates="alerts")


class ForecastLog(Base):
    """
    Stores model-vs-actual comparisons for variance tracking.
    Each row captures one forecast horizon date for a product/store.
    """
    __tablename__ = "forecast_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, default=1)
    horizon_date = Column(Date, nullable=False)
    predicted_demand = Column(Float, nullable=False)
    actual_demand = Column(Float, nullable=True)
    variance = Column(Float, nullable=True)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
