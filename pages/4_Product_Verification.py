"""
pages/4_Product_Verification.py
===============================
Product Verification: Registry authenticity lookup for pesticides, seeds, and fertilizers
using local SQLite database records, OpenCV QR code scanning, and category breakdown charts.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.botanical_elements import (
    inject_botanical_theme,
    render_footer,
    render_page_header,
    render_section_title,
)
from components.cards import (
    render_alert_box,
    render_metric_card,
)
from components.navigation import render_sidebar_status
from components.visualizations import plot_product_registry_breakdown
from services.product_verification import (
    get_registered_products,
    get_verifier_info,
    verify_product_code,
    verify_product_qr_image,
)
from utils.validators import validate_image_upload, validate_product_code

st.set_page_config(
    page_title="Product Verification · AgriVision",
    page_icon="🔐",
    layout="wide",
)

inject_botanical_theme()
render_sidebar_status()

render_page_header(
    eyebrow="Anti-Counterfeiting · SQLite Input Registry",
    title="Product Verification",
    description="Verify agricultural input authenticity, batch numbers, manufacturer traceability, and expiration dates against the local SQLite registry or by scanning QR package codes.",
    icon="🔐",
)

# Verification Input Layout
col_code, col_qr = st.columns([1, 1], gap="large")

with col_code:
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);">
            <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:4px;">Verify by Product Code</div>
            <div style="font-size:0.85rem;color:#5E6057;margin-bottom:12px;">Type the registration code printed on the container label.</div>
        """,
        unsafe_allow_html=True,
    )

    code_input = st.text_input(
        "Product Code",
        value="",
        placeholder="e.g. AGV-1001, AGV-1003, AGV-1005",
        label_visibility="collapsed",
    )

    col_btn_code, col_demo_code = st.columns([1.5, 1])
    with col_btn_code:
        verify_code_btn = st.button("🔐 Verify Code", type="primary", use_container_width=True)
    with col_demo_code:
        if st.button("Example: AGV-1001", use_container_width=True):
            code_input = "AGV-1001"
            verify_code_btn = True

    st.markdown(
        "<div style='font-size:0.8rem;color:#5E6057;margin-top:6px;'>Sample Demo Codes: <b>AGV-1001</b> (Fungicide) · <b>AGV-1003</b> (Urea) · <b>AGV-1005</b> (Recalled Batch)</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_qr:
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);">
            <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:4px;">Scan Product QR Code</div>
            <div style="font-size:0.85rem;color:#5E6057;margin-bottom:12px;">Upload a close-up photo of the 2D QR label on the bottle or sack.</div>
        """,
        unsafe_allow_html=True,
    )

    qr_file = st.file_uploader(
        "Upload QR Code Image",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )
    scan_qr_btn = st.button("📷 Scan & Verify QR", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Perform Verification
verification_data = None
qr_read_data = None

if verify_code_btn:
    is_valid, err_msg, clean_code = validate_product_code(code_input)
    if not is_valid:
        render_alert_box(err_msg, tone="danger")
    else:
        with st.spinner("Checking SQLite product registry..."):
            verification_data = verify_product_code(clean_code)

elif scan_qr_btn:
    if qr_file is None:
        render_alert_box("Please upload a photo of the QR label to scan.", tone="warn")
    else:
        is_valid, err_msg = validate_image_upload(qr_file)
        if not is_valid:
            render_alert_box(err_msg, tone="danger")
        else:
            with st.spinner("Decoding QR pattern and verifying against registry..."):
                qr_pack = verify_product_qr_image(qr_file.getvalue())
                qr_read_data = qr_pack.get("qr")
                verification_data = qr_pack.get("verification")

# Display Result
if verification_data:
    render_section_title("Registry Lookup Result", icon="🛡️")

    found = verification_data.get("found", False)
    verified = verification_data.get("verified", False)
    product = verification_data.get("product") or {}
    message = verification_data.get("message", "")
    checks = verification_data.get("checks", [])
    expired = verification_data.get("expired", False)
    status = str(product.get("status", "Unknown"))

    if qr_read_data and qr_read_data.get("code"):
        st.info(f"Decoded QR Serial: **{qr_read_data['code']}** (Raw: {qr_read_data.get('raw_text', '')})")

    # Status Alert Banner
    if verified:
        render_alert_box(f"🟢 {message}", tone="good")
    elif found and status.lower() == "recalled":
        render_alert_box(f"🔴 {message}", tone="danger")
    elif found and (expired or status.lower() == "suspended"):
        render_alert_box(f"🟠 {message}", tone="warn")
    else:
        render_alert_box(f"⚪ {message or 'Product code was not found in the verified registry. Exercise extreme caution.'}", tone="danger")

    if found and product:
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        with col_p1:
            render_metric_card(
                label="Product Name",
                value=product.get("product_name", "—"),
                subtext=product.get("product_type", "Chemical/Bio"),
                border_color="#1B3D26",
            )
        with col_p2:
            render_metric_card(
                label="Manufacturer",
                value=product.get("manufacturer", "—"),
                subtext="Registered Producer",
                border_color="#2D5A27",
            )
        with col_p3:
            render_metric_card(
                label="Batch Code",
                value=product.get("batch", "—"),
                subtext=f"Code: {product.get('code')}",
                border_color="#0284C7",
            )
        with col_p4:
            render_metric_card(
                label="Expiry Date",
                value=product.get("expiry", "—"),
                subtext="Passed" if expired else "Valid",
                border_color="#991B1B" if expired else "#166534",
            )

        if checks:
            st.markdown(
                """
                <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:12px;padding:1.2rem;margin-top:10px;">
                    <div style="font-weight:700;color:#1B3D26;font-size:0.95rem;margin-bottom:6px;">Registry Integrity Audits</div>
                """,
                unsafe_allow_html=True,
            )
            for check in checks:
                st.markdown(f"<div style='font-size:0.88rem;color:#2A2A26;'>• {check}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Product Registry Composition Visualization & Browser
st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
render_section_title("Authentic Registry Distribution & Audit Catalog", icon="📊")

col_pie, col_tbl = st.columns([1, 1.2], gap="large")
items = get_registered_products(limit=50)

with col_pie:
    if items:
        fig_pie = plot_product_registry_breakdown(items)
        st.plotly_chart(fig_pie, use_container_width=True)

with col_tbl:
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.2rem;box-shadow:0 3px 12px rgba(0,0,0,0.03);">
            <div style="font-weight:700;color:#1B3D26;font-size:0.95rem;margin-bottom:6px;">Registry Status Overview</div>
            <p style="font-size:0.85rem;color:#5E6057;line-height:1.5;">
                This database mirrors an authentic state agricultural input registry in SQLite. Input products must maintain active, unexpired, and non-recalled status to pass verification.
            </p>
        """,
        unsafe_allow_html=True,
    )
    if items:
        df = pd.DataFrame(items)[["code", "product_name", "product_type", "status", "expiry"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

render_footer()
