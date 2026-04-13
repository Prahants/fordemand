"""
streamlit_app.py - Smart Inventory & Demand Forecasting Dashboard

A multi-page Streamlit dashboard that connects to the FastAPI backend
to display inventory data, sales history, demand forecasts, and alerts.

Pages:
    1. Dashboard  - Overview with key metrics and charts
    2. Products   - Product catalog management
    3. Inventory  - Stock levels and reorder thresholds
    4. Sales Entry - Add new sales records
    5. Forecast   - Prophet demand forecasting with visualizations
    6. Alerts     - Low-stock alert management
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
import io
import json
import qrcode  # pyright: ignore[reportMissingModuleSource]
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import cv2
import av
import threading
import time

# ─── Configuration ────────────────────────────────────────────────
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Smart Inventory & Demand Forecasting",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS for Premium Look ──────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Metric card styling */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #a0a0b8;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }

    /* Header styling */
    h1, h2, h3 {
        font-weight: 700;
    }

    /* Success/error message styling */
    .stAlert {
        border-radius: 10px;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }

    /* ─── Alert Card Styles ──────────────────────────────── */
    .alert-card {
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .alert-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    }
    .alert-card.critical {
        background: linear-gradient(135deg, #2d1215 0%, #3b1520 100%);
        border: 1px solid rgba(239,68,68,0.35);
    }
    .alert-card.warning {
        background: linear-gradient(135deg, #2d2512 0%, #3b3015 100%);
        border: 1px solid rgba(245,158,11,0.35);
    }
    .alert-card.resolved {
        background: linear-gradient(135deg, #122d1a 0%, #153b20 100%);
        border: 1px solid rgba(34,197,94,0.3);
        opacity: 0.7;
    }

    .alert-severity {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .severity-critical {
        background: rgba(239,68,68,0.2);
        color: #f87171;
        border: 1px solid rgba(239,68,68,0.3);
    }
    .severity-warning {
        background: rgba(245,158,11,0.2);
        color: #fbbf24;
        border: 1px solid rgba(245,158,11,0.3);
    }
    .severity-resolved {
        background: rgba(34,197,94,0.2);
        color: #4ade80;
        border: 1px solid rgba(34,197,94,0.3);
    }

    .alert-product-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f0f0f5;
        margin: 8px 0 4px 0;
    }
    .alert-store {
        font-size: 0.8rem;
        color: #8888a8;
        margin-bottom: 14px;
    }

    .alert-stats {
        display: flex;
        gap: 24px;
        margin: 12px 0;
    }
    .alert-stat {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .alert-stat-label {
        font-size: 0.7rem;
        color: #8888a8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .alert-stat-value {
        font-size: 1.15rem;
        font-weight: 700;
    }
    .stat-stock { color: #f87171; }
    .stat-reorder { color: #fbbf24; }
    .stat-deficit { color: #fb923c; }

    .alert-timestamp {
        font-size: 0.75rem;
        color: #6b6b88;
        margin-top: 10px;
    }

    /* Summary pill cards */
    .summary-pill {
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
    }
    .pill-critical {
        background: linear-gradient(135deg, #2d1215 0%, #3b1520 100%);
        border: 1px solid rgba(239,68,68,0.3);
    }
    .pill-warning {
        background: linear-gradient(135deg, #2d2512 0%, #3b3015 100%);
        border: 1px solid rgba(245,158,11,0.3);
    }
    .pill-resolved {
        background: linear-gradient(135deg, #122d1a 0%, #153b20 100%);
        border: 1px solid rgba(34,197,94,0.3);
    }
    .pill-total {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .pill-number {
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .pill-label {
        font-size: 0.78rem;
        color: #8888a8;
        margin-top: 4px;
    }

    /* ─── Dashboard alert mini-cards ──────────────────────── */
    .dash-alert {
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .dash-alert.critical {
        background: linear-gradient(135deg, #2d1215 0%, #3b1520 100%);
        border-left: 4px solid #ef4444;
    }
    .dash-alert.warning {
        background: linear-gradient(135deg, #2d2512 0%, #3b3015 100%);
        border-left: 4px solid #f59e0b;
    }
    .dash-alert-icon { font-size: 1.4rem; }
    .dash-alert-text {
        font-size: 0.88rem;
        color: #e0e0e5;
        line-height: 1.4;
    }
    .dash-alert-text strong { color: #fff; }

    /* ─── Styled Error Toast ─────────────────────────────── */
    .error-toast {
        border-radius: 14px;
        padding: 28px 32px;
        margin: 16px 0;
        background: linear-gradient(135deg, #1a1020 0%, #2a1428 50%, #1a1020 100%);
        border: 1px solid rgba(168, 85, 247, 0.25);
        box-shadow: 0 0 30px rgba(168, 85, 247, 0.08), 0 4px 24px rgba(0,0,0,0.4);
        position: relative;
        overflow: hidden;
    }
    .error-toast::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #a855f7, #ec4899, #a855f7);
    }
    .error-toast-icon {
        font-size: 2.2rem;
        margin-bottom: 10px;
    }
    .error-toast-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #e8d5f5;
        margin-bottom: 8px;
    }
    .error-toast-msg {
        font-size: 0.9rem;
        color: #b0a0c0;
        line-height: 1.6;
    }
    .error-toast-hint {
        margin-top: 16px;
        padding: 12px 16px;
        border-radius: 10px;
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.15);
        font-size: 0.85rem;
        color: #a5b4fc;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ────────────────────────────────────────

def _auth_headers() -> dict:
    role = st.session_state.get("active_role", "staff")
    return {"X-Role": role}

ROLE_PAGES = {
    "admin": ["Dashboard", "Products", "Inventory", "Sales Entry", "Forecast", "QR Generator", "Alerts"],
    "manager": ["Dashboard", "Products", "Inventory", "Sales Entry", "Forecast", "QR Generator", "Alerts"],
    "staff": ["Dashboard", "Inventory", "Sales Entry", "Forecast", "QR Generator", "Alerts"],
}


class QRScanner(VideoProcessorBase):
    """WebRTC video processor for live QR detection."""

    def __init__(self) -> None:
        self.detector = cv2.QRCodeDetector()
        self.last_data = None
        self._lock = threading.Lock()

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        data, bbox, _ = self.detector.detectAndDecode(img)

        if not data:
            decoded_multi, decoded_info, points_multi, _ = self.detector.detectAndDecodeMulti(img)
            if decoded_multi and decoded_info:
                data = next((val for val in decoded_info if val), None)
                bbox = points_multi if points_multi is not None else bbox

        if data:
            with self._lock:
                self.last_data = data
            if bbox is not None:
                pts = bbox.astype(int).reshape(-1, 2)
                for i in range(len(pts)):
                    cv2.line(
                        img,
                        tuple(pts[i]),
                        tuple(pts[(i + 1) % len(pts)]),
                        (0, 255, 0),
                        2,
                    )

                cv2.putText(
                    img,
                    data,
                    (pts[0][0], pts[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def get_last_data(self):
        with self._lock:
            return self.last_data


def _extract_error_detail(response) -> str:
    """Pull the human-readable detail from a FastAPI error response."""
    try:
        body = response.json()
        if isinstance(body, dict) and "detail" in body:
            return body["detail"]
    except Exception:
        pass
    return response.text or "Unknown error"


def _show_error_toast(title: str, message: str, hint: str | None = None):
    """Render a styled error card instead of a raw st.error."""
    hint_html = ""
    if hint:
        hint_html = f'<div class="error-toast-hint">💡 {hint}</div>'
    st.markdown(
        f'<div class="error-toast">'
        f'  <div class="error-toast-icon">⚠️</div>'
        f'  <div class="error-toast-title">{title}</div>'
        f'  <div class="error-toast-msg">{message}</div>'
        f'  {hint_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _show_connection_error():
    _show_error_toast(
        "Connection Failed",
        "Unable to reach the backend server. Please make sure the FastAPI server is running.",
        "Run <code>uvicorn backend.main:app --reload</code> in your terminal to start the server.",
    )


def api_get(endpoint: str):
    """Make a GET request to the backend API."""
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        _show_connection_error()
        return None
    except requests.exceptions.HTTPError as e:
        detail = _extract_error_detail(e.response)
        _show_error_toast("Request Failed", detail)
        return None


def api_post(endpoint: str, data: dict):
    """Make a POST request to the backend API."""
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", json=data, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        _show_connection_error()
        return None
    except requests.exceptions.HTTPError as e:
        detail = _extract_error_detail(e.response)
        _show_error_toast("Request Failed", detail)
        return None


def create_plotly_theme():
    """Return a consistent dark theme layout for Plotly charts."""
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#e0e0e0"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )


import re

def _parse_alert_message(msg: str) -> dict:
    """Extract structured fields from an alert message string."""
    info: dict = {"product": "Unknown", "store": "Unknown", "stock": None, "reorder": None, "raw": msg}
    m = re.search(r"'([^']+)'\s+at\s+'([^']+)'", msg)
    if m:
        info["product"] = m.group(1)
        info["store"] = m.group(2)
    stock_m = re.search(r"has\s+(\d+)\s+units?", msg)
    if stock_m:
        info["stock"] = int(stock_m.group(1))
    reorder_m = re.search(r"[Rr]eorder\s+point\s+is\s+(\d+)", msg)
    if reorder_m:
        info["reorder"] = int(reorder_m.group(1))
    return info


def _severity(stock, reorder) -> str:
    if stock is None or reorder is None:
        return "warning"
    ratio = stock / reorder if reorder > 0 else 1.0
    return "critical" if ratio < 0.5 else "warning"


# ─── Sidebar Navigation ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📦 Inventory System")
    st.markdown("---")
    if "active_role" not in st.session_state:
        st.session_state.active_role = "manager"
    st.session_state.active_role = st.selectbox(
        "Role",
        options=["admin", "manager", "staff"],
        index=["admin", "manager", "staff"].index(st.session_state.active_role),
    )

    stores = api_get("/master/stores") or [{"id": 1, "name": "Main Store"}]
    store_options = {s["name"]: s["id"] for s in stores}
    if "active_store_id" not in st.session_state:
        st.session_state.active_store_id = next(iter(store_options.values()))
    selected_store_name = st.selectbox("Store", options=list(store_options.keys()))
    st.session_state.active_store_id = store_options[selected_store_name]

   

    
    st.markdown("---")

    allowed_pages = ROLE_PAGES.get(st.session_state.active_role, ROLE_PAGES["staff"])
    page = st.radio(
        "Navigate",
        allowed_pages,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### ⚙️ Quick Actions")

    if st.session_state.active_role == "admin":
        if st.button("🌱 Seed Database", use_container_width=True):
            result = api_post("/seed", {})
            if result:
                st.success(f"✅ Seeded! {result.get('sales_records_loaded', 0)} sales records loaded.")
                st.rerun()
    else:
        st.caption("Seed action is available for admin only.")

    st.markdown("---")
    st.markdown(
        "<p style='color: #666; font-size: 0.75rem; text-align: center;'>"
        "Smart Inventory v1.0<br>Prophet ML Forecasting</p>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.markdown("# 📊 Dashboard")
    st.markdown("Real-time overview of stock levels, sales activity, and alerts across your stores.")
    st.markdown("---")

    # Fetch data for metrics
    products = api_get("/products/")
    inventory_data = api_get("/inventory/")
    if inventory_data:
        inventory_data = [
            i for i in inventory_data if i.get("store_id") == st.session_state.active_store_id
        ]
    alerts_data = api_get("/alerts/")
    if alerts_data:
        alerts_data = [
            a for a in alerts_data if a.get("store_id") == st.session_state.active_store_id
        ]

    if products is not None:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Products", len(products) if products else 0, delta=None)

        with col2:
            total_stock = sum(i["stock"] for i in inventory_data) if inventory_data else 0
            st.metric("Total Stock Units", f"{total_stock:,}")

        with col3:
            low_stock = 0
            if inventory_data:
                low_stock = sum(1 for i in inventory_data if i["stock"] < i["reorder_threshold"])
            st.metric("Low Stock Items", low_stock, delta=f"-{low_stock}" if low_stock > 0 else None,
                       delta_color="inverse")

        with col4:
            open_count = len([a for a in alerts_data if a.get("status", "open") != "resolved"]) if alerts_data else 0
            st.metric("Open Alerts", open_count)

        st.markdown("---")

        # Inventory overview chart
        if inventory_data:
            st.markdown("### 📊 Inventory Overview")
            inv_df = pd.DataFrame(inventory_data)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=inv_df["product_name"],
                y=inv_df["stock"],
                name="Current Stock",
                marker_color="#6366f1",
                marker_line_width=0,
            ))
            fig.add_trace(go.Bar(
                x=inv_df["product_name"],
                y=inv_df["reorder_threshold"],
                name="Reorder Threshold",
                marker_color="#ef4444",
                marker_line_width=0,
                opacity=0.6,
            ))
            fig.update_layout(
                barmode="group",
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                **create_plotly_theme(),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Recent alerts
        if alerts_data:
            open_dash_alerts = [a for a in alerts_data if a.get("status", "open") != "resolved"]
            if open_dash_alerts:
                st.markdown("### 🚨 Recent Alerts")
                for alert in open_dash_alerts[:5]:
                    info = _parse_alert_message(alert["message"])
                    sev = _severity(info["stock"], info["reorder"])
                    icon = "🔴" if sev == "critical" else "🟡"
                    stock_text = f" — <strong>{info['stock']}</strong> in stock, reorder at <strong>{info['reorder']}</strong>" if info["stock"] is not None else ""
                    st.markdown(
                        f'<div class="dash-alert {sev}">'
                        f'<span class="dash-alert-icon">{icon}</span>'
                        f'<span class="dash-alert-text"><strong>{info["product"]}</strong>{stock_text}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )


# ═══════════════════════════════════════════════════════════════════
# PAGE: PRODUCTS
# ═══════════════════════════════════════════════════════════════════
elif page == "Products":
    st.markdown("# 📋 Products")
    st.markdown("Manage your product catalog.")
    st.markdown("---")

    add_tab, scan_tab = st.tabs(["➕ Add Product", "📷 Scan QR to Add"])

    with add_tab:
        col1, col2 = st.columns(2)
        with col1:
            prod_name = st.text_input("Product Name", placeholder="e.g. Name of the product")
        with col2:
            prod_category = st.selectbox("Category", ["Electronics", "Accessories", "Hardware", "Software", "Other"])
        col3, col4 = st.columns(2)
        with col3:
            prod_sku = st.text_input("SKU", placeholder="e.g. P200")
        with col4:
            suppliers = api_get("/master/suppliers") or []
            supplier_options = {"None": None}
            supplier_options.update({s["name"]: s["id"] for s in suppliers})
            supplier_name = st.selectbox("Supplier", list(supplier_options.keys()))

        if st.button("Add Product", use_container_width=True):
            if prod_name:
                result = api_post(
                    "/products/",
                    {
                        "name": prod_name,
                        "category": prod_category,
                        "sku": prod_sku or None,
                        "supplier_id": supplier_options[supplier_name],
                    },
                )
                if result:
                    st.success(f"✅ Product '{prod_name}' created with ID {result['id']}")
                    st.rerun()
            else:
                st.warning("Please enter a product name.")

    with scan_tab:
        st.markdown("Scan a product QR code to **instantly add** it to your catalog and inventory.")

        if "scan_added_product" not in st.session_state:
            st.session_state.scan_added_product = None
        if "scan_last_processed" not in st.session_state:
            st.session_state.scan_last_processed = None

        ctx = webrtc_streamer(
            key="qr-scanner-products",
            video_processor_factory=QRScanner,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        status_placeholder = st.empty()
        result_placeholder = st.empty()

        if ctx.state.playing and ctx.video_processor:
            while ctx.state.playing:
                scanned = ctx.video_processor.get_last_data()
                if scanned:
                    scanned = scanned.strip()

                if scanned and scanned != st.session_state.scan_last_processed:
                    st.session_state.scan_last_processed = scanned
                    st.session_state.scan_added_product = None

                    parsed = None
                    try:
                        parsed = json.loads(scanned)
                    except (TypeError, json.JSONDecodeError):
                        parsed = None

                    existing_products = api_get("/products/") or []
                    sku_map = {
                        str(p["sku"]).strip().upper(): p
                        for p in existing_products
                        if p.get("sku")
                    }

                    if isinstance(parsed, dict):
                        p_name = str(parsed.get("product", "")).strip()
                        p_sku = str(parsed.get("sku", "")).strip()
                        p_category = str(parsed.get("category", "")).strip()

                        if p_name and p_sku and p_category:
                            existing = sku_map.get(p_sku.upper())
                            if existing:
                                st.session_state.scan_added_product = {
                                    "product": existing,
                                    "message": f"Product with SKU **{p_sku}** already exists.",
                                    "is_new": False,
                                }
                            else:
                                created = api_post(
                                    "/products/",
                                    {
                                        "name": p_name,
                                        "category": p_category,
                                        "sku": p_sku,
                                        "supplier_id": None,
                                    },
                                )
                                if created:
                                    api_post("/inventory/update", {
                                        "product_id": created["id"],
                                        "store_id": st.session_state.active_store_id,
                                        "stock": 1,
                                        "reorder_threshold": 10,
                                    })
                                    st.session_state.scan_added_product = {
                                        "product": created,
                                        "message": f"Added **{p_name}** (SKU {p_sku}) to catalog & inventory!",
                                        "is_new": True,
                                    }
                                else:
                                    st.session_state.scan_added_product = {
                                        "product": None,
                                        "message": "Failed to add product to database.",
                                        "is_new": False,
                                    }
                        else:
                            st.session_state.scan_added_product = {
                                "product": None,
                                "message": "QR JSON is missing product, sku, or category fields.",
                                "is_new": False,
                            }
                    else:
                        matched = sku_map.get(scanned.upper()) if scanned else None
                        if matched:
                            st.session_state.scan_added_product = {
                                "product": matched,
                                "message": f"Found product **{matched['name']}** (SKU {matched.get('sku', 'N/A')}).",
                                "is_new": False,
                            }
                        else:
                            st.session_state.scan_added_product = {
                                "product": None,
                                "message": f"Scanned code `{scanned}` did not match any product or valid JSON.",
                                "is_new": False,
                            }

                scan_info = st.session_state.scan_added_product
                if scan_info:
                    if scan_info.get("is_new"):
                        status_placeholder.success(f"✅ {scan_info['message']}")
                    elif scan_info.get("product"):
                        status_placeholder.info(scan_info["message"])
                    else:
                        status_placeholder.warning(scan_info["message"])

                    with result_placeholder.container():
                        prod = scan_info.get("product")
                        if prod:
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Product", prod.get("name", "N/A"))
                            c2.metric("SKU", prod.get("sku", "N/A"))
                            c3.metric("Category", prod.get("category", "N/A"))
                else:
                    status_placeholder.caption("Point your camera at a product QR code...")

                time.sleep(0.4)
        else:
            if st.session_state.scan_added_product and st.session_state.scan_added_product.get("is_new"):
                st.success(f"✅ {st.session_state.scan_added_product['message']}")
                prod = st.session_state.scan_added_product.get("product")
                if prod:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Product", prod.get("name", "N/A"))
                    c2.metric("SKU", prod.get("sku", "N/A"))
                    c3.metric("Category", prod.get("category", "N/A"))
            st.caption("Click **Start** to begin scanning product QR codes.")

    # Product list
    products = api_get("/products/")
    if products:
        st.markdown("### Catalog")
        df = pd.DataFrame(products)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No products yet. Click **Seed Database** in the sidebar or add products above.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: INVENTORY
# ═══════════════════════════════════════════════════════════════════
elif page == "Inventory":
    st.markdown("# 📦 Inventory")
    st.markdown("Track current stock across products and set reorder thresholds to prevent stockouts.")
    st.markdown("---")

    # Update inventory form
    with st.expander("🔄 Update Inventory", expanded=False):
        products = api_get("/products/")
        if products:
            product_options = {p["name"]: p["id"] for p in products}
            selected_product = st.selectbox("Select Product", list(product_options.keys()))
            col1, col2 = st.columns(2)
            with col1:
                new_stock = st.number_input("New Stock Level", min_value=0, value=50, step=1)
            with col2:
                new_threshold = st.number_input("Reorder Threshold", min_value=1, value=10, step=1)

            if st.button("📥 Update Stock", use_container_width=True):
                result = api_post("/inventory/update", {
                    "product_id": product_options[selected_product],
                    "store_id": st.session_state.active_store_id,
                    "stock": new_stock,
                    "reorder_threshold": new_threshold,
                })
                if result:
                    st.success(f"✅ Updated '{selected_product}' → Stock: {new_stock}")
                    st.rerun()

    # Inventory table
    inventory_data = api_get("/inventory/")
    if inventory_data:
        inventory_data = [
            i for i in inventory_data if i.get("store_id") == st.session_state.active_store_id
        ]
    if inventory_data:
        st.markdown("### 📊 Current Inventory Levels")
        inv_df = pd.DataFrame(inventory_data)

        # Highlight low-stock rows
        def highlight_low_stock(row):
            if row["stock"] < row["reorder_threshold"]:
                return ["background-color: rgba(239, 68, 68, 0.2)"] * len(row)
            return [""] * len(row)

        styled_df = inv_df[["product_name", "stock", "reorder_threshold", "last_updated"]].style.apply(
            highlight_low_stock, axis=1
        )
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info("No inventory data. Seed the database first.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: SALES ENTRY
# ═══════════════════════════════════════════════════════════════════
elif page == "Sales Entry":
    st.markdown("# 💰 Sales Entry")
    st.markdown("Log daily sales and track performance trends by product.")
    st.markdown("---")

    products = api_get("/products/")

    if products:
        # Add sale form
        st.markdown("### ➕ Record a Sale")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            product_options = {p["name"]: p["id"] for p in products}
            selected_product = st.selectbox("Product", list(product_options.keys()))
        with col2:
            sale_date = st.date_input("Sale Date", value=date.today())
        with col3:
            quantity = st.number_input("Quantity Sold", min_value=1, value=1, step=1)
        with col4:
            promotion_flag = st.checkbox("Promotion Sale", value=False)
        with col5:
            season_tag = st.selectbox("Season", ["none", "summer", "winter", "festival"])

        if st.button("💾 Save Sale", use_container_width=True):
            result = api_post("/sales/add", {
                "product_id": product_options[selected_product],
                "store_id": st.session_state.active_store_id,
                "date": sale_date.isoformat(),
                "quantity_sold": quantity,
                "promotion_flag": promotion_flag,
                "season_tag": None if season_tag == "none" else season_tag,
            })
            if result:
                st.success(f"✅ Recorded: {quantity} units of '{selected_product}' on {sale_date}")

        st.markdown("---")

        # Sales history
        st.markdown("### 📈 Sales History")
        selected_for_history = st.selectbox("View history for", list(product_options.keys()), key="history_product")
        sales_data = api_get(
            f"/sales/{product_options[selected_for_history]}?store_id={st.session_state.active_store_id}"
        )

        if sales_data:
            sales_df = pd.DataFrame(sales_data)
            sales_df["date"] = pd.to_datetime(sales_df["date"])

            # Sales chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=sales_df["date"],
                y=sales_df["quantity_sold"],
                mode="lines+markers",
                name="Quantity Sold",
                line=dict(color="#6366f1", width=2),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor="rgba(99, 102, 241, 0.1)",
            ))
            fig.update_layout(
                title=f"Sales History — {selected_for_history}",
                xaxis_title="Date",
                yaxis_title="Quantity Sold",
                height=400,
                margin=dict(l=20, r=20, t=50, b=20),
                **create_plotly_theme(),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Data table
            st.dataframe(
                sales_df[["date", "quantity_sold"]].sort_values("date", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No sales data for this product.")
    else:
        st.info("No products. Seed the database first.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: FORECAST (Key Feature)
# ═══════════════════════════════════════════════════════════════════
elif page == "Forecast":
    st.markdown("# 📈 Demand Forecast")
    st.markdown("Run ML-powered predictions to see future demand, safety stock, and reorder points.")
    st.markdown("---")

    products = api_get("/products/")

    if products:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            product_options = {p["name"]: p["id"] for p in products}
            selected_product = st.selectbox("Select Product to Forecast", list(product_options.keys()))
        with col2:
            lead_time = st.number_input("Lead Time (days)", min_value=1, max_value=30, value=3)
        with col3:
            service_level = st.selectbox(
                "Service Level",
                options=[1.28, 1.65, 1.96, 2.33],
                index=1,
                format_func=lambda x: {1.28: "90%", 1.65: "95%", 1.96: "97.5%", 2.33: "99%"}[x],
            )

        if st.button("🚀 Run Forecast", use_container_width=True, type="primary"):
            product_id = product_options[selected_product]

            with st.spinner("🧠 Running Prophet model..."):
                forecast_result = api_get(
                    f"/forecast/{product_id}?store_id={st.session_state.active_store_id}&lead_time={lead_time}&service_level={service_level}"
                )

            if forecast_result is None:
                _show_error_toast(
                    "Forecast Unavailable",
                    "The forecast could not be completed. This usually means the sales data "
                    "is insufficient or contains anomalies.",
                    "Go to <b>Sales Entry</b> and add at least 5–7 days of sales data, then re-run the forecast.",
                )
                st.stop()

            if forecast_result and "forecasts" in forecast_result:
                st.markdown("---")

                # ─── Metrics Row ──────────────────────────────────
                st.markdown("### 📊 Forecast Results")
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Method", forecast_result["method"].capitalize())
                with m2:
                    st.metric("Safety Stock", f"{forecast_result.get('safety_stock', 'N/A'):.1f} units")
                with m3:
                    st.metric("Reorder Point", f"{forecast_result.get('reorder_point', 'N/A'):.1f} units")
                with m4:
                    mae = forecast_result.get("mae")
                    st.metric("MAE", f"{mae:.2f}" if mae else "N/A")

                # RMSE metric
                rmse = forecast_result.get("rmse")
                if rmse:
                    st.caption(f"📐 RMSE: {rmse:.2f}")

                st.markdown("---")

                # ─── Sales + Forecast Chart ───────────────────────
                st.markdown("### 📈 Historical Sales + Forecast")

                # Fetch historical sales for the chart
                sales_data = api_get(f"/sales/{product_id}?store_id={st.session_state.active_store_id}")

                fig = go.Figure()

                # Plot historical sales
                if sales_data:
                    sales_df = pd.DataFrame(sales_data)
                    sales_df["date"] = pd.to_datetime(sales_df["date"])
                    fig.add_trace(go.Scatter(
                        x=sales_df["date"],
                        y=sales_df["quantity_sold"],
                        mode="lines",
                        name="Actual Sales",
                        line=dict(color="#6366f1", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(99, 102, 241, 0.08)",
                    ))

                # Plot forecast
                forecast_df = pd.DataFrame(forecast_result["forecasts"])
                forecast_df["date"] = pd.to_datetime(forecast_df["date"])

                fig.add_trace(go.Scatter(
                    x=forecast_df["date"],
                    y=forecast_df["predicted_value"],
                    mode="lines+markers",
                    name="Forecast",
                    line=dict(color="#f59e0b", width=3, dash="dash"),
                    marker=dict(size=8, symbol="diamond"),
                ))

                # Reorder point line
                reorder_point = forecast_result.get("reorder_point")
                if reorder_point and sales_data:
                    all_dates = list(sales_df["date"]) + list(forecast_df["date"])
                    fig.add_hline(
                        y=reorder_point / lead_time,  # Daily reorder rate
                        line_dash="dot",
                        line_color="#ef4444",
                        annotation_text=f"Daily Reorder Rate ({reorder_point/lead_time:.1f})",
                        annotation_position="top left",
                    )

                fig.update_layout(
                    title=f"Demand Forecast — {selected_product}",
                    xaxis_title="Date",
                    yaxis_title="Quantity",
                    height=500,
                    margin=dict(l=20, r=20, t=50, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    **create_plotly_theme(),
                )
                st.plotly_chart(fig, use_container_width=True)

                # ─── Forecast Table ────────────────────────────────
                st.markdown("### 📋 7-Day Forecast Detail")
                display_df = forecast_df[["date", "predicted_value"]].copy()
                display_df.columns = ["Date", "Predicted Demand"]
                display_df["Predicted Demand"] = display_df["Predicted Demand"].round(2)
                st.dataframe(display_df, use_container_width=True, hide_index=True)

                # ─── Alert Display ─────────────────────────────────
                if forecast_result.get("alert"):
                    st.markdown("---")
                    st.error(f"🚨 {forecast_result['alert']['message']}")

                logs = api_get(
                    f"/forecast-logs/?product_id={product_id}&store_id={st.session_state.active_store_id}"
                )
                if logs:
                    st.markdown("### 📉 Forecast Variance Logs")
                    logs_df = pd.DataFrame(logs)
                    cols = ["horizon_date", "predicted_demand", "actual_demand", "variance", "generated_at"]
                    st.dataframe(logs_df[cols], use_container_width=True, hide_index=True)

            elif forecast_result and "error" in forecast_result:
                st.error(forecast_result["error"])
    else:
        st.info("No products. Seed the database first.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: QR GENERATOR
# ═══════════════════════════════════════════════════════════════════
elif page == "QR Generator":
    st.markdown("# 🧾 QR Generator")
    st.markdown("Generate and store QR code data for product labels.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        qr_product = st.text_input("Product", placeholder="e.g. Widget Alpha")
        qr_sku = st.text_input("SKU", placeholder="e.g. P101")
    with col2:
        qr_category = st.text_input("Category", placeholder="e.g. Electronics")
        qr_price = st.number_input("Price", min_value=0.0, value=0.0, step=1.0)

    if st.button("Generate QR", use_container_width=True, type="primary"):
        if not qr_product.strip() or not qr_sku.strip() or not qr_category.strip():
            st.warning("Please fill Product, SKU, and Category.")
        else:
            payload_dict = {
                "product": qr_product.strip(),
                "sku": qr_sku.strip(),
                "category": qr_category.strip(),
                "price": float(qr_price),
            }
            payload_json = json.dumps(payload_dict, separators=(",", ":"), ensure_ascii=True)
            saved = api_post("/qr-codes/", {**payload_dict, "qr_payload": payload_json})

            if saved:
                qr_image = qrcode.make(payload_json)
                buffer = io.BytesIO()
                qr_image.save(buffer, format="PNG")
                buffer.seek(0)

                st.success("QR generated and stored successfully.")
                st.code(payload_json, language="json")
                st.image(buffer.getvalue(), caption=f"QR for SKU {payload_dict['sku']}", width=280)
                st.download_button(
                    label="⬇️ Download QR PNG",
                    data=buffer.getvalue(),
                    file_name=f"{payload_dict['sku']}_qr.png",
                    mime="image/png",
                    use_container_width=True,
                )

    st.markdown("---")
    st.markdown("### Recent Generated QR Records")
    qr_records = api_get("/qr-codes/") or []
    if qr_records:
        qr_df = pd.DataFrame(qr_records)
        st.dataframe(
            qr_df[["product", "sku", "category", "price", "created_at"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No QR records yet. Generate one above.")



# ═══════════════════════════════════════════════════════════════════
# PAGE: ALERTS
# ═══════════════════════════════════════════════════════════════════
elif page == "Alerts":
    st.markdown("# 🚨 Alerts & Notifications")
    st.markdown("Monitor low-stock warnings and take action before you run out.")
    st.markdown("---")

    alerts_data = api_get("/alerts/")
    if alerts_data:
        alerts_data = [
            a for a in alerts_data if a.get("store_id") == st.session_state.active_store_id
        ]

    if alerts_data:
        open_alerts = [a for a in alerts_data if a.get("status", "open") != "resolved"]
        resolved_alerts = [a for a in alerts_data if a.get("status", "open") == "resolved"]
        critical_alerts = [
            a for a in open_alerts
            if _severity(
                _parse_alert_message(a["message"])["stock"],
                _parse_alert_message(a["message"])["reorder"],
            ) == "critical"
        ]

        # ── Summary pills ────────────────────────────────────
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.markdown(
                f'<div class="summary-pill pill-total">'
                f'<div class="pill-number" style="color:#c4b5fd">{len(alerts_data)}</div>'
                f'<div class="pill-label">Total Alerts</div></div>',
                unsafe_allow_html=True,
            )
        with p2:
            st.markdown(
                f'<div class="summary-pill pill-critical">'
                f'<div class="pill-number" style="color:#f87171">{len(critical_alerts)}</div>'
                f'<div class="pill-label">Critical</div></div>',
                unsafe_allow_html=True,
            )
        with p3:
            st.markdown(
                f'<div class="summary-pill pill-warning">'
                f'<div class="pill-number" style="color:#fbbf24">{len(open_alerts) - len(critical_alerts)}</div>'
                f'<div class="pill-label">Warning</div></div>',
                unsafe_allow_html=True,
            )
        with p4:
            st.markdown(
                f'<div class="summary-pill pill-resolved">'
                f'<div class="pill-number" style="color:#4ade80">{len(resolved_alerts)}</div>'
                f'<div class="pill-label">Resolved</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("")

        # ── Filter tabs ──────────────────────────────────────
        tab_all, tab_open, tab_resolved = st.tabs([
            f"All  ({len(alerts_data)})",
            f"🔴 Open  ({len(open_alerts)})",
            f"✅ Resolved  ({len(resolved_alerts)})",
        ])

        def _render_alert_card(alert, tab_prefix="all"):
            info = _parse_alert_message(alert["message"])
            status = alert.get("status", "open")
            sev = "resolved" if status == "resolved" else _severity(info["stock"], info["reorder"])
            sev_label = {"critical": "Critical", "warning": "Warning", "resolved": "Resolved"}[sev]
            sev_icon = {"critical": "🔴", "warning": "🟡", "resolved": "✅"}[sev]

            stock_html = ""
            if info["stock"] is not None and info["reorder"] is not None:
                deficit = info["reorder"] - info["stock"]
                stock_html = (
                    f'<div class="alert-stats">'
                    f'  <div class="alert-stat">'
                    f'    <span class="alert-stat-label">Current Stock</span>'
                    f'    <span class="alert-stat-value stat-stock">{info["stock"]} units</span>'
                    f'  </div>'
                    f'  <div class="alert-stat">'
                    f'    <span class="alert-stat-label">Reorder Point</span>'
                    f'    <span class="alert-stat-value stat-reorder">{info["reorder"]} units</span>'
                    f'  </div>'
                    f'  <div class="alert-stat">'
                    f'    <span class="alert-stat-label">Deficit</span>'
                    f'    <span class="alert-stat-value stat-deficit">{deficit} units</span>'
                    f'  </div>'
                    f'</div>'
                )

            created = alert.get("created_at", "")
            time_str = ""
            if created:
                time_str = f'<div class="alert-timestamp">🕐 Created {created[:19].replace("T", " at ")}</div>'

            card_html = (
                f'<div class="alert-card {sev}">'
                f'  <span class="alert-severity severity-{sev}">{sev_icon} {sev_label}</span>'
                f'  <div class="alert-product-name">{info["product"]}</div>'
                f'  <div class="alert-store">📍 {info["store"]}</div>'
                f'  {stock_html}'
                f'  {time_str}'
                f'</div>'
            )

            card_col, action_col = st.columns([5, 1])
            with card_col:
                st.markdown(card_html, unsafe_allow_html=True)
            with action_col:
                st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
                if status != "resolved" and st.session_state.active_role in {"admin", "manager"}:
                    if st.button("✅ Resolve", key=f"resolve_{tab_prefix}_{alert['id']}", use_container_width=True):
                        api_post(f"/alerts/{alert['id']}/status?status=resolved", {})
                        st.rerun()
                elif status == "resolved":
                    st.markdown(
                        "<p style='text-align:center;color:#4ade80;font-size:0.85rem;margin-top:8px;'>Resolved</p>",
                        unsafe_allow_html=True,
                    )

        with tab_all:
            for alert in alerts_data:
                _render_alert_card(alert, tab_prefix="all")

        with tab_open:
            if open_alerts:
                for alert in open_alerts:
                    _render_alert_card(alert, tab_prefix="open")
            else:
                st.success("🎉 No open alerts — all stock levels are healthy!")

        with tab_resolved:
            if resolved_alerts:
                for alert in resolved_alerts:
                    _render_alert_card(alert, tab_prefix="resolved")
            else:
                st.info("No resolved alerts yet.")

    else:
        st.markdown("")
        st.markdown(
            '<div style="text-align:center;padding:60px 20px;">'
            '<div style="font-size:3rem;margin-bottom:12px;">✅</div>'
            '<h3 style="color:#4ade80;margin-bottom:8px;">All Clear!</h3>'
            '<p style="color:#8888a8;">No active alerts. All stock levels are healthy.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.balloons()
