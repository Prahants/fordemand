"""
main.py - FastAPI Application Entry Point

Initializes the database, registers all API routers, and provides
a data seeding endpoint to populate the DB from the CSV file.
"""

import os
import csv
from datetime import date
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.db.database import engine, Base, get_db
from backend.db.models import Product, Sales, Inventory
from backend.routes import products, inventory, sales, forecast, alerts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


# ─── FastAPI App ──────────────────────────────────────────────────
app = FastAPI(
    title="Smart Inventory & Demand Forecasting System",
    description="Track inventory, forecast demand with Prophet, and manage alerts.",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware (allow Streamlit frontend) ───────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register API Routers ────────────────────────────────────────
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(forecast.router)
app.include_router(alerts.router)


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Smart Inventory & Demand Forecasting System",
        "docs": "/docs",
    }


@app.post("/seed", tags=["Setup"])
def seed_data(db: Session = Depends(get_db)):
    """
    Seed the database with sample products and sales data from CSV.

    This endpoint:
    1. Creates products P101, P102, P103 if they don't exist
    2. Loads sales data from data/sales_data.csv
    3. Creates initial inventory records with default stock levels

    Returns:
        Summary of seeded data counts
    """
    # ─── Step 1: Create Products ──────────────────────────────────
    product_map = {
        "P101": {"name": "Widget Alpha", "category": "Electronics"},
        "P102": {"name": "Widget Beta", "category": "Electronics"},
        "P103": {"name": "Widget Gamma", "category": "Accessories"},
    }

    created_products = {}
    for code, info in product_map.items():
        # Check if product already exists by name
        existing = db.query(Product).filter(Product.name == info["name"]).first()
        if not existing:
            product = Product(name=info["name"], category=info["category"])
            db.add(product)
            db.commit()
            db.refresh(product)
            created_products[code] = product.id
        else:
            created_products[code] = existing.id

    # ─── Step 2: Load Sales Data from CSV ─────────────────────────
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sales_data.csv")
    csv_path = os.path.abspath(csv_path)

    sales_count = 0
    if os.path.exists(csv_path):
        # Clear existing sales data to avoid duplicates on re-seed
        db.query(Sales).delete()
        db.commit()

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                product_code = row["product_id"]
                if product_code in created_products:
                    sale = Sales(
                        product_id=created_products[product_code],
                        date=date.fromisoformat(row["date"]),
                        quantity_sold=int(row["quantity_sold"]),
                    )
                    db.add(sale)
                    sales_count += 1

        db.commit()

    # ─── Step 3: Create Initial Inventory ─────────────────────────
    inventory_defaults = {
        "P101": 50,
        "P102": 30,
        "P103": 15,
    }

    for code, stock in inventory_defaults.items():
        product_id = created_products[code]
        existing_inv = (
            db.query(Inventory).filter(Inventory.product_id == product_id).first()
        )
        if not existing_inv:
            inv = Inventory(
                product_id=product_id,
                stock=stock,
                reorder_threshold=10,
            )
            db.add(inv)

    db.commit()

    return {
        "message": "Database seeded successfully",
        "products_created": len(created_products),
        "sales_records_loaded": sales_count,
        "product_id_map": created_products,
    }
