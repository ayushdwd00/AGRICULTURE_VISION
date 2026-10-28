"""
components/navigation.py
========================
AgriVision Professional SaaS Sidebar Navigation & System Status.
"""

from __future__ import annotations

import streamlit as st
from modules.crop_doctor import model_status
from modules.product_verifier import verifier_status


def render_sidebar() -> None:
    """Render the professional agricultural SaaS sidebar."""
    with st.sidebar:
        # 1. Brand Header at the top
        st.markdown(
            """
            <div class="agv-sidebar-brand">
                <div class="agv-sidebar-brand-row">
                    <div class="agv-sidebar-logo-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 22V11" stroke="#1B3D26" stroke-width="2.2" stroke-linecap="round"/>
                            <path d="M12 11C12 6 16.5 2.5 21 2.5C21 7 17 11 12 11Z" fill="#2D5A27"/>
                            <path d="M12 15C12 11.2 8.5 8.5 4 8.5C4 12.2 7.5 15 12 15Z" fill="#4A7C59"/>
                        </svg>
                    </div>
                    <div class="agv-sidebar-brand-text">
                        <span class="agv-sidebar-brand-name">AgriVision</span>
                        <span class="agv-sidebar-brand-subtitle">Agricultural Decision Intelligence</span>
                    </div>
                </div>
            </div>
            <div class="agv-sidebar-divider"></div>
            """,
            unsafe_allow_html=True,
        )

        # 2. Custom Navigation Menu
        st.markdown('<div class="agv-sidebar-section-label">Navigation</div>', unsafe_allow_html=True)
        st.page_link("app.py", label="Home", icon="🌾")
        st.page_link("pages/1_Crop_Doctor.py", label="Crop Doctor", icon="🩺")
        st.page_link("pages/2_Weather_Intelligence.py", label="Weather Intelligence", icon="🌦️")
        st.page_link("pages/3_Fertilizer_Planner.py", label="Fertilizer Planner", icon="🧮")
        st.page_link("pages/4_Product_Verification.py", label="Product Verification", icon="🔐")
        st.page_link("pages/5_Government_Schemes.py", label="Government Schemes", icon="🏛️")
        st.page_link("pages/6_About_AgriVision.py", label="About AgriVision", icon="📖")

        st.markdown('<div class="agv-sidebar-divider"></div>', unsafe_allow_html=True)

        # 3. System Status Panel
        # Fetch actual application status data
        try:
            m_stat = model_status()
            active_model = m_stat.get("active") or "agrivision_cnn.pth"
            device = m_stat.get("device", "cpu").upper()
        except Exception:
            active_model = "agrivision_cnn.pth"
            device = "CPU"

        try:
            p_stat = verifier_status()
            batch_count = p_stat.get("count", 10)
        except Exception:
            batch_count = 10

        try:
            from services.scheme_matcher import get_all_schemes
            schemes = get_all_schemes()
            scheme_count = len(schemes) if schemes else 8
        except Exception:
            scheme_count = 8

        st.markdown(
            f"""
            <div class="agv-status-card">
                <div class="agv-status-header">
                    <span class="agv-status-pulse-dot"></span>
                    <span>System Readiness</span>
                </div>
                <div class="agv-status-items">
                    <div class="agv-status-row">
                        <div class="agv-status-row-label">
                            <span class="agv-status-row-icon">🧠</span>
                            <span>Vision CNN</span>
                        </div>
                        <div class="agv-status-row-value">
                            <code>{active_model}</code> <span class="agv-status-tag">({device})</span>
                        </div>
                    </div>
                    <div class="agv-status-row">
                        <div class="agv-status-row-label">
                            <span class="agv-status-row-icon">🔐</span>
                            <span>Product Registry</span>
                        </div>
                        <div class="agv-status-row-value">
                            <span class="agv-status-count">{batch_count}</span> authentic batches
                        </div>
                    </div>
                    <div class="agv-status-row">
                        <div class="agv-status-row-label">
                            <span class="agv-status-row-icon">🌦️</span>
                            <span>Weather Source</span>
                        </div>
                        <div class="agv-status-row-value">
                            Open-Meteo <span class="agv-status-live-badge">Live</span>
                        </div>
                    </div>
                    <div class="agv-status-row">
                        <div class="agv-status-row-label">
                            <span class="agv-status-row-icon">🏛️</span>
                            <span>Scheme Catalog</span>
                        </div>
                        <div class="agv-status-row-value">
                            <span class="agv-status-count">{scheme_count}</span> Central Schemes
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4. Footer
        st.markdown(
            """
            <div class="agv-sidebar-divider"></div>
            <div class="agv-sidebar-footer">
                AgriVision v2.0 · Python-First Streamlit
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar_status() -> None:
    """Backward-compatible entry point for pages."""
    render_sidebar()
