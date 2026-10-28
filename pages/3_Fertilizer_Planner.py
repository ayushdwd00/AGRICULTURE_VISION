"""
pages/3_Fertilizer_Planner.py
=============================
Fertilizer Planner: Deterministic agricultural nutrient dosage calculations based
on static agronomic lookup tables, bag calculations, indicative costs, Plotly comparisons,
and Britannica educational reference.
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
)
from components.navigation import render_sidebar_status
from components.visualizations import plot_fertilizer_crop_comparison
from services.fertilizer_service import (
    calculate_fertilizer_plan,
    get_cached_fertilizer_data,
    get_crops,
    get_deficiencies,
)
from utils.config import BRITANNICA_FERTILIZER_URL
from utils.validators import validate_land_area

st.set_page_config(
    page_title="Fertilizer Planner · AgriVision",
    page_icon="🧮",
    layout="wide",
)

inject_botanical_theme()
render_sidebar_status()

render_page_header(
    eyebrow="Nutrient Stewardship · Deterministic Agronomic Modeling",
    title="Fertilizer Planner",
    description="Calculate indicative fertilizer quantities, bag requirements, and estimated input costs using standard agricultural lookup tables. Never relies on generative AI approximations for chemical rates.",
    icon="🧮",
)

crops = get_crops()
if not crops:
    render_alert_box("The fertilizer lookup table (data/fertilizer_data.json) could not be loaded.", tone="danger")
    st.stop()

# Calculator Layout
col_form, col_edu = st.columns([1.1, 0.9], gap="large")

with col_form:
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);">
            <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:4px;">Field & Nutrient Parameters</div>
            <div style="font-size:0.85rem;color:#5E6057;margin-bottom:14px;">Select your standing crop and observed deficiency or nutrient target.</div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("fertilizer_form"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            selected_crop = st.selectbox("Crop", options=crops, index=0)
        with col_c2:
            deficiencies = get_deficiencies(selected_crop)
            selected_deficiency = st.selectbox("Nutrient Target / Deficiency", options=deficiencies)

        col_a1, col_a2 = st.columns([1.5, 1])
        with col_a1:
            land_input = st.number_input("Field Area", min_value=0.05, max_value=10000.0, value=2.5, step=0.5)
        with col_a2:
            unit_input = st.selectbox("Unit", options=["acres", "hectares"], index=0)

        bag_size = st.selectbox("Standard Bag Size", options=[45, 50], index=0, format_func=lambda x: f"{x} kg bag")

        submit_btn = st.form_submit_button("🧮 Calculate Fertilizer Plan", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

with col_edu:
    st.markdown(
        f"""
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);">
            <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:6px;">Fertilizer Education & 4R Stewardship</div>
            <p style="font-size:0.88rem;color:#2A2A26;line-height:1.55;">
                Fertilizers provide essential macronutrients (Nitrogen, Phosphorus, Potassium) and micronutrients (Zinc, Boron) critical for cellular synthesis, root architecture, and crop yield.
            </p>
            <div style="background:#F7F5EE;padding:10px 14px;border-radius:8px;font-size:0.82rem;color:#1B3D26;margin:10px 0;line-height:1.5;">
                <b>The 4R Nutrient Framework:</b><br/>
                • <b>Right Source:</b> Match fertilizer type to crop and soil pH.<br/>
                • <b>Right Rate:</b> Avoid nutrient burn and runoff.<br/>
                • <b>Right Time:</b> Split applications across growth stages.<br/>
                • <b>Right Place:</b> Place nutrients where roots can readily absorb them.
            </div>
            <p style="font-size:0.85rem;color:#5E6057;">
                Learn more in-depth about chemical and organic fertilizer categories via the authoritative Britannica guide:
            </p>
            <a href="{BRITANNICA_FERTILIZER_URL}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;color:#1B3D26;font-weight:600;font-size:0.88rem;text-decoration:none;">
                Explore Britannica Fertilizer Reference ↗
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Result Processing
if submit_btn or "last_fert_result" in st.session_state:
    if submit_btn:
        is_valid, err_msg, land_val = validate_land_area(land_input)
        if not is_valid:
            render_alert_box(err_msg, tone="danger")
            res = None
        else:
            with st.spinner("Executing deterministic dosage arithmetic..."):
                res = calculate_fertilizer_plan(
                    crop=selected_crop,
                    deficiency=selected_deficiency,
                    land_size=land_val,
                    unit=unit_input,
                    bag_weight_kg=float(bag_size),
                )
                st.session_state.last_fert_result = res
                st.session_state.last_fert_crop = selected_crop
    else:
        res = st.session_state.last_fert_result
        selected_crop = st.session_state.get("last_fert_crop", selected_crop)

    if res and res.get("error"):
        render_alert_box(res["error"], tone="danger")
    elif res:
        render_section_title("Calculated Application Plan", icon="📋")

        # Metrics row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_card(
                label="Recommended Input",
                value=res.get("fertilizer", "Fertilizer"),
                subtext=f"Target: {res.get('deficiency')}",
                border_color="#1B3D26",
            )
        with m2:
            render_metric_card(
                label="Total Quantity",
                value=f"{res.get('quantity', 0):,.1f} {res.get('unit', 'kg')}",
                subtext=f"For {res.get('land_size_acres')} acres",
                border_color="#2D5A27",
            )
        with m3:
            render_metric_card(
                label="Bags Required",
                value=f"{res.get('bags_to_buy', '—')} bags",
                subtext=f"Standard {res.get('bag_weight_kg', 45)} kg bags ({res.get('bags_exact', 0)} exact)",
                border_color="#92400E",
            )
        with m4:
            render_metric_card(
                label="Estimated Cost",
                value=f"₹ {res.get('estimated_cost', 0):,.0f}",
                subtext=f"@ ₹ {res.get('cost_per_unit', 0)} / {res.get('unit', 'kg')}",
                border_color="#166534",
            )

        # Application Advice and Guidance Card
        col_plan1, col_plan2 = st.columns([1.2, 0.8], gap="medium")

        with col_plan1:
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 3px 12px rgba(0,0,0,0.03);">
                    <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:6px;">Application Guidance & Timing</div>
                    <p style="font-size:0.95rem;line-height:1.6;color:#1C241B;">
                        {res.get('application', 'Apply evenly according to standard cultivation practices.')}
                    </p>
                    <div style="background:#F7F5EE;padding:12px;border-radius:8px;font-size:0.85rem;color:#5E6057;margin-top:10px;">
                        <b>Summary:</b> {res.get('summary', '')}<br/>
                        <b>Per-acre Rate:</b> {res.get('dosage_per_acre')} {res.get('unit')} per acre.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_plan2:
            st.markdown(
                """
                <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 3px 12px rgba(0,0,0,0.03);">
                    <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.2rem;color:#1B3D26;margin-bottom:6px;">Field Soil Test Notice</div>
                    <p style="font-size:0.85rem;color:#5E6057;line-height:1.5;">
                        These calculated dosages represent baseline agronomic norms. Actual fertilizer efficiency depends on soil texture, existing organic carbon, and residual nitrogen levels. Always consult your official Soil Health Card before applying bulk chemical amendments.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Interactive Crop Nutrients Comparison Plot
        render_section_title(f"Nutrient Comparison for {selected_crop}", icon="📊")
        try:
            raw_data = get_cached_fertilizer_data()
            crop_dict = raw_data.get("crops", {}).get(selected_crop, {})
            if crop_dict:
                fig_comp = plot_fertilizer_crop_comparison(crop_dict, selected_crop)
                st.plotly_chart(fig_comp, use_container_width=True)
        except Exception:
            pass

render_footer()
