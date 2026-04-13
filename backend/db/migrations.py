"""
migrations.py - Lightweight SQLite schema patching for dev.
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def _table_exists(conn, table_name: str) -> bool:
    result = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    ).fetchone()
    return result is not None


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def ensure_sqlite_schema(engine: Engine) -> None:
    """
    Adds newly introduced columns for existing SQLite DBs.
    Avoids crash on startup for local dev without Alembic.
    """
    with engine.begin() as conn:
        if _table_exists(conn, "products"):
            if not _column_exists(conn, "products", "sku"):
                conn.execute(text("ALTER TABLE products ADD COLUMN sku VARCHAR"))
            if not _column_exists(conn, "products", "supplier_id"):
                conn.execute(text("ALTER TABLE products ADD COLUMN supplier_id INTEGER"))

        if _table_exists(conn, "inventory"):
            if not _column_exists(conn, "inventory", "store_id"):
                conn.execute(text("ALTER TABLE inventory ADD COLUMN store_id INTEGER DEFAULT 1"))
            conn.execute(text("UPDATE inventory SET store_id = 1 WHERE store_id IS NULL"))

        if _table_exists(conn, "sales"):
            if not _column_exists(conn, "sales", "store_id"):
                conn.execute(text("ALTER TABLE sales ADD COLUMN store_id INTEGER DEFAULT 1"))
            if not _column_exists(conn, "sales", "promotion_flag"):
                conn.execute(text("ALTER TABLE sales ADD COLUMN promotion_flag BOOLEAN DEFAULT 0"))
            if not _column_exists(conn, "sales", "season_tag"):
                conn.execute(text("ALTER TABLE sales ADD COLUMN season_tag VARCHAR"))
            conn.execute(text("UPDATE sales SET store_id = 1 WHERE store_id IS NULL"))
            conn.execute(text("UPDATE sales SET promotion_flag = 0 WHERE promotion_flag IS NULL"))

        if _table_exists(conn, "alerts"):
            if not _column_exists(conn, "alerts", "store_id"):
                conn.execute(text("ALTER TABLE alerts ADD COLUMN store_id INTEGER DEFAULT 1"))
            if not _column_exists(conn, "alerts", "status"):
                conn.execute(text("ALTER TABLE alerts ADD COLUMN status VARCHAR DEFAULT 'open'"))
            conn.execute(text("UPDATE alerts SET store_id = 1 WHERE store_id IS NULL"))
            conn.execute(text("UPDATE alerts SET status = 'open' WHERE status IS NULL"))
