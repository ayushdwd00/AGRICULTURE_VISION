"""
pages/5_Government_Schemes.py
=============================
Government Scheme Matcher: Deterministic eligibility matching against 8 official
central-sector agricultural schemes with real application links and statutory comparison plots.
"""

from __future__ import annotations

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
    render_scheme_card,
)
from components.navigation import render_sidebar_status
from components.visualizations import plot_scheme_land_limits
from services.scheme_matcher import (
    find_matching_schemes,
    get_all_schemes,
    get_scheme_options,
)
from utils.validators import validate_land_area

st.set_page_config(
    page_title="Government Schemes · AgriVision",
    page_icon="🏛️",
    layout="wide",
)

inject_botanical_theme()
render_sidebar_status()

render_page_header(
    eyebrow="Agricultural Welfare · Deterministic Scheme Matching",
    title="Government Scheme Matcher",
    description="Match your farm size, state, and crop portfolio against verified central and state agricultural support schemes. Provides genuine portal links without AI fabrication.",
    icon="🏛️",
)

options = get_scheme_options()
regions = options.get("regions", ["All India"])
crops = options.get("crops", ["Any"])
categories = ["Any"] + options.get("categories", [])

# Matching Wizard Card
st.markdown(
    """
    <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);margin-bottom:1.5rem;">
        <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:4px;">Farm Profile & Support Criteria</div>
        <div style="font-size:0.85rem;color:#5E6057;margin-bottom:14px;">Enter your operational landholding and state to evaluate qualifying subsidies and credit programs.</div>
    """,
    unsafe_allow_html=True,
)

with st.form("scheme_match_form"):
    col_w1, col_w2, col_w3, col_w4 = st.columns(4)
    with col_w1:
        land_size = st.number_input("Landholding (Acres)", min_value=0.1, max_value=5000.0, value=2.0, step=0.5)
    with col_w2:
        selected_region = st.selectbox("State / Region", options=regions, index=0)
    with col_w3:
        selected_crop = st.selectbox("Primary Crop", options=crops, index=0)
    with col_w4:
        selected_category = st.selectbox("Support Category", options=categories, index=0)

    match_submit = st.form_submit_button("🏛️ Find Eligible Schemes", type="primary", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Processing
if match_submit or "last_scheme_results" in st.session_state:
    is_valid, err_msg, clean_land = validate_land_area(land_size)
    if not is_valid:
        render_alert_box(err_msg, tone="danger")
    else:
        if match_submit:
            with st.spinner("Matching farm parameters against statutory scheme rules..."):
                results = find_matching_schemes(
                    land_size_acres=clean_land,
                    region=selected_region,
                    crop=selected_crop,
                    category=selected_category,
                )
                st.session_state.last_scheme_results = results
        else:
            results = st.session_state.last_scheme_results

        if results.get("error"):
            render_alert_box(results["error"], tone="danger")
        else:
            matches = results.get("matches", [])
            near_misses = results.get("near_misses", [])

            # KPI summary
            c1, c2, c3 = st.columns(3)
            with c1:
                render_metric_card(
                    label="Eligible Schemes",
                    value=f"{len(matches)} Programs",
                    subtext="Fully meet criteria",
                    border_color="#166534",
                )
            with c2:
                render_metric_card(
                    label="Near Matches",
                    value=f"{len(near_misses)} Programs",
                    subtext="Partial qualification",
                    border_color="#92400E",
                )
            with c3:
                render_metric_card(
                    label="Active Region Filter",
                    value=selected_region,
                    subtext=f"Land: {clean_land} acres",
                    border_color="#0284C7",
                )

            # Matched Programs
            if matches:
                render_section_title(f"Eligible Agricultural Schemes ({len(matches)})", icon="✅")
                for scheme in matches:
                    render_scheme_card(scheme)
            else:
                render_alert_box("No schemes matched all specified criteria. See partial matches below.", tone="warn")

            # Near-Misses
            if near_misses:
                render_section_title(f"Other Considerations & Near Matches ({len(near_misses)})", icon="⚠️")
                for scheme in near_misses:
                    render_scheme_card(scheme)

# Statutory Scheme Landholding Comparison Chart
render_section_title("Scheme Landholding Eligibility Comparison", icon="📊")
all_schemes = get_all_schemes()
if all_schemes:
    fig_schemes = plot_scheme_land_limits(all_schemes)
    st.plotly_chart(fig_schemes, use_container_width=True)

# Full Catalog Browser
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
with st.expander("📚 Explore Complete Central Agricultural Scheme Directory (All 8 Schemes)"):
    search_term = st.text_input("Filter directory by scheme title or keyword", placeholder="e.g. Kisan, Credit, Drone, Irrigation")
    
    filtered_schemes = [
        s for s in all_schemes
        if search_term.lower() in f"{s.get('name', '')} {s.get('description', '')} {s.get('category', '')}".lower()
    ]
    
    for s in filtered_schemes:
        render_scheme_card(s)

render_footer()
