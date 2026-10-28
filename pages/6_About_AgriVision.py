"""
pages/6_About_AgriVision.py
===========================
About AgriVision: Project overview, verified capabilities, technical architecture,
and Python-first single-runtime deployment details.
"""

from __future__ import annotations

import streamlit as st

from components.botanical_elements import (
    inject_botanical_theme,
    render_page_header,
    render_section_title,
    render_footer,
)
from components.navigation import render_sidebar_status


st.set_page_config(
    page_title="About AgriVision · Agricultural Decision Intelligence",
    page_icon="📖",
    layout="wide",
)

inject_botanical_theme()
render_sidebar_status()

render_page_header(
    eyebrow="Platform & Capabilities Overview",
    title="About AgriVision",
    description="AgriVision is an integrated, Python-first agricultural decision-support platform uniting deep-learning foliage diagnostics, microclimate risk modeling, deterministic nutrient calculations, SQLite input verification, and statutory welfare scheme discovery.",
    icon="📖",
)

# 1. About the Project
render_section_title("About the Project", icon="🌾")

st.markdown(
    """
    <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.6rem 1.8rem;box-shadow:0 3px 14px rgba(0,0,0,0.03);margin-bottom:1.4rem;">
        <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.3rem;color:#1B3D26;margin-bottom:8px;">
            A Unified Agricultural Decision-Support Super-App
        </div>
        <p style="font-size:0.95rem;color:#2A2A26;line-height:1.65;margin-bottom:12px;">
            Modern agricultural production requires synthesizing disparate sources of operational knowledge: identifying crop diseases from leaf tissue, assessing immediate microclimate fungal spore risks, calculating exact fertilizer dosages per acre, safeguarding inputs against counterfeit batches, and navigating statutory government support schemes.
        </p>
        <p style="font-size:0.95rem;color:#4A4D45;line-height:1.65;margin:0;">
            <b>AgriVision</b> unifies these vital advisory tools into one coherent, Python-first application. Engineered specifically for practical farm workflows and agricultural students, the platform emphasizes <b>transparency, deterministic rules, and explainable AI</b>—ensuring recommendations are strictly bounded by agronomic evidence rather than opaque or fabricated outputs.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# 2. Key Capabilities
render_section_title("Key Capabilities", icon="🛠️")

col_cap1, col_cap2 = st.columns(2, gap="large")

with col_cap1:
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem 1.6rem;box-shadow:0 3px 14px rgba(0,0,0,0.03);margin-bottom:1.2rem;min-height:270px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="font-size:1.3rem;">🩺</span>
                <span style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;font-weight:600;">Crop Doctor</span>
            </div>
            <p style="font-size:0.9rem;color:#4A4D45;line-height:1.55;margin-bottom:10px;">
                Dual-signal plant disease diagnostic system combining image-based foliage analysis with farmer-described symptom classification:
            </p>
            <ul style="font-size:0.87rem;color:#2A2A26;line-height:1.6;padding-left:1.2rem;margin:0;">
                <li><b>Vision CNN:</b> PyTorch MobileNetV2 trained across 38 PlantVillage condition classes.</li>
                <li><b>Symptom NLP Classifier:</b> Random Forest pipeline classifying natural language symptom reports.</li>
                <li><b>Visual Grad-CAM Explainability:</b> Activation heatmaps overlaying detected lesion regions.</li>
                <li><b>Conservative 70% Confidence Gate:</b> Flags indeterminate cases for field inspection.</li>
                <li><b>Interactive 3D Plant Model:</b> Three.js foliage viewer with OrbitControls for leaf morphology inspection.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem 1.6rem;box-shadow:0 3px 14px rgba(0,0,0,0.03);margin-bottom:1.2rem;min-height:240px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="font-size:1.3rem;">🌦️</span>
                <span style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;font-weight:600;">Weather Intelligence</span>
            </div>
            <p style="font-size:0.9rem;color:#4A4D45;line-height:1.55;margin-bottom:10px;">
                Hyper-local meteorological observation and disease risk forecasting:
            </p>
            <ul style="font-size:0.87rem;color:#2A2A26;line-height:1.6;padding-left:1.2rem;margin:0;">
                <li><b>Open-Meteo REST Integration:</b> Live geocoded microclimate retrieval with 15-minute response caching.</li>
                <li><b>Fungal Spore Germination Alerts:</b> Deterministic rule triggers when relative humidity &gt; 80% and temperatures sit between 20–30°C.</li>
                <li><b>Heat Stress Warnings:</b> Flags high temperature thresholds that inhibit pollination.</li>
                <li><b>Forecast Timeseries Charts:</b> Interactive Plotly temperature, humidity, and rainfall trends.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_cap2:
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem 1.6rem;box-shadow:0 3px 14px rgba(0,0,0,0.03);margin-bottom:1.2rem;min-height:270px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="font-size:1.3rem;">🧮</span>
                <span style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;font-weight:600;">Fertilizer Planner</span>
            </div>
            <p style="font-size:0.9rem;color:#4A4D45;line-height:1.55;margin-bottom:10px;">
                Deterministic per-acre nutrient calculation based strictly on reference agronomic tables:
            </p>
            <ul style="font-size:0.87rem;color:#2A2A26;line-height:1.6;padding-left:1.2rem;margin:0;">
                <li><b>Pure Table Lookup:</b> Directly reads validated nutrient recommendations from <code>data/fertilizer_data.json</code>.</li>
                <li><b>Bag Counts & Input Sizing:</b> Converts elemental nitrogen, phosphorus, and potassium requirements into exact 45 kg and 50 kg commercial bag units.</li>
                <li><b>Economic Estimation:</b> Provides estimated input costs based on standard market bag pricing.</li>
                <li><b>4R Stewardship Context:</b> Clear educational framework (Right Source, Right Rate, Right Time, Right Place).</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem 1.6rem;box-shadow:0 3px 14px rgba(0,0,0,0.03);margin-bottom:1.2rem;min-height:240px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="font-size:1.3rem;">🔐</span>
                <span style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;font-weight:600;">Product Verification & Scheme Matcher</span>
            </div>
            <p style="font-size:0.9rem;color:#4A4D45;line-height:1.55;margin-bottom:10px;">
                Input security and central welfare program access:
            </p>
            <ul style="font-size:0.87rem;color:#2A2A26;line-height:1.6;padding-left:1.2rem;margin:0;">
                <li><b>SQLite Input Registry:</b> Local registry (<code>data/products.db</code>) verifying batch numbers, expiry dates, and manufacturer credentials.</li>
                <li><b>OpenCV QR Detection:</b> Scans packaging QR images to authenticate genuine products against counterfeit items.</li>
                <li><b>Statutory Scheme Wizard:</b> 4-step eligibility filter matching landholding, region, crop, and assistance category against 8 central welfare schemes.</li>
                <li><b>Verified Application Links:</b> Direct portals for PM-KISAN, PMFBY, KCC, Soil Health Cards, and AIF.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
render_footer()
