"""
pages/2_Weather_Intelligence.py
===============================
Weather Intelligence: Microclimate weather fetching via Open-Meteo with 15-minute
caching, real 72-hour forecast time-series, deterministic risk flags, and manual simulation mode.
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
from components.visualizations import (
    plot_weather_forecast_timeseries,
    plot_weather_indicators,
)
from services.weather_service import (
    get_cached_forecast,
    get_cached_weather,
    get_manual_weather,
)
from utils.validators import validate_city_name

st.set_page_config(
    page_title="Weather Intelligence · AgriVision",
    page_icon="🌦️",
    layout="wide",
)

inject_botanical_theme()
render_sidebar_status()

render_page_header(
    eyebrow="Microclimate Monitoring · Agronomic Risk Modeling",
    title="Weather Intelligence",
    description="Live atmospheric readings from Open-Meteo combined with deterministic plant-pathology risk models. Evaluates fungal spore germination risk, heat stress thresholds, and optimal spraying conditions.",
    icon="🌦️",
)

# Search & Controls Layout
col_search, col_options = st.columns([1.2, 0.8], gap="large")

with col_search:
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);">
            <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:4px;">Search Agricultural Location</div>
            <div style="font-size:0.85rem;color:#5E6057;margin-bottom:12px;">Enter your town, district, or agricultural zone to pull live meteorological conditions.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_input, col_go = st.columns([2.5, 1])
    with col_input:
        city_input = st.text_input(
            "Location name",
            value="Pune",
            placeholder="e.g., Pune, Varanasi, Lucknow, Nagpur",
            label_visibility="collapsed",
        )
    with col_go:
        check_btn = st.button("🌦️ Get Weather", type="primary", use_container_width=True)

    # Quick Location Chips
    st.markdown(
        "<div style='font-size:0.8rem;color:#5E6057;margin-top:6px;'>Quick Select: "
        "<b>Pune</b> · <b>Varanasi</b> · <b>Nagpur</b> · <b>Ludhiana</b> · <b>Indore</b></div>",
        unsafe_allow_html=True,
    )

with col_options:
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);">
            <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:4px;">Weather Input Mode</div>
            <div style="font-size:0.85rem;color:#5E6057;margin-bottom:10px;">Switch between live satellite/weather API data and manual field observations.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    manual_mode = st.toggle("Enter Manual Weather Readings (Simulation)", value=False)
    if manual_mode:
        st.caption("Manual mode allows you to simulate high humidity or heatwaves to test crop risk rules.")

# Manual Values Input
if manual_mode:
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        manual_temp = st.number_input("Field Temperature (°C)", min_value=-10.0, max_value=60.0, value=28.0, step=0.5)
    with c_m2:
        manual_hum = st.slider("Relative Humidity (%)", min_value=0, max_value=100, value=85, step=1)
    with c_m3:
        manual_rain = st.number_input("Recent Rainfall (mm)", min_value=0.0, max_value=300.0, value=12.0, step=1.0)

# Execution & Processing
weather_data = None
forecast_data = None
weather_err = None

if check_btn or ("last_weather" in st.session_state and not manual_mode):
    is_valid, err_msg, clean_city = validate_city_name(city_input)
    if not is_valid:
        render_alert_box(err_msg, tone="danger")
    else:
        with st.spinner(f"Querying Open-Meteo microclimate metrics for {clean_city}..."):
            try:
                if manual_mode:
                    weather_data = get_manual_weather(
                        city=clean_city,
                        temperature=manual_temp,
                        humidity=manual_hum,
                        rainfall=manual_rain,
                        use_ai=True,
                    )
                else:
                    weather_data = get_cached_weather(city=clean_city, use_ai=True)
                    forecast_data, _ = get_cached_forecast(city=clean_city, days=3)
                st.session_state.last_weather = weather_data
                st.session_state.last_forecast = forecast_data
            except Exception as exc:
                weather_err = str(exc)

if weather_err:
    render_alert_box(f"Weather query failed: {weather_err}", tone="danger")
elif weather_data and weather_data.get("error"):
    render_alert_box(weather_data["error"], tone="danger")
elif weather_data:
    w = weather_data.get("weather", {})
    risks = weather_data.get("risks", [])
    risk_level = weather_data.get("risk_level", "LOW")
    f_data = st.session_state.get("last_forecast")

    render_section_title(f"Field Weather Metrics · {weather_data.get('city', city_input)}", icon="🌡️")

    # Main Metrics Grid
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_metric_card(
            label="Temperature",
            value=f"{w.get('temperature', '—')} °C",
            subtext=f"Feels like {w.get('feels_like', '—')} °C",
            border_color="#1B3D26",
        )
    with kpi2:
        render_metric_card(
            label="Humidity",
            value=f"{w.get('humidity', '—')}%",
            subtext="Relative atmospheric",
            border_color="#0284C7" if (w.get("humidity") or 0) < 80 else "#D97706",
        )
    with kpi3:
        render_metric_card(
            label="Conditions",
            value=str(w.get("description", "Current")).title(),
            subtext="Observation status",
            border_color="#166534",
        )
    with kpi4:
        render_metric_card(
            label="Wind Velocity",
            value=f"{w.get('wind_speed', '0')} m/s",
            subtext="Spraying suitability",
            border_color="#4A7C59",
        )
    with kpi5:
        render_metric_card(
            label="Disease Risk Level",
            value=risk_level,
            subtext="Rule evaluation",
            border_color="#16A34A" if risk_level == "LOW" else "#DC2626",
        )

    # Risk Gauges & Rules Breakdown
    col_vis, col_risk = st.columns([1, 1], gap="medium")

    with col_vis:
        temp_val = float(w.get("temperature", 25.0) or 25.0)
        hum_val = int(w.get("humidity", 50) or 50)
        rain_val = float(w.get("rain_1h", 0.0) or 0.0)
        gauge_fig = plot_weather_indicators(
            temperature=temp_val,
            humidity=hum_val,
            rainfall=rain_val,
            risk_level=risk_level,
        )
        st.plotly_chart(gauge_fig, use_container_width=True)

    with col_risk:
        st.markdown(
            """
            <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 3px 12px rgba(0,0,0,0.03);">
                <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:8px;">Agricultural Risk Rule Engine</div>
            """,
            unsafe_allow_html=True,
        )

        if not risks:
            render_alert_box(
                "🟢 Low Pathological Risk: Current temperatures and humidity levels do not indicate active fungal spore blooms or extreme heat stress.",
                tone="good",
            )
        else:
            for risk in risks:
                title = risk.get("title") or risk.get("name", "Active Risk Alert")
                detail = risk.get("detail") or risk.get("description", "")
                render_alert_box(f"⚠️ {title}: {detail}", tone="warn")

        # Agronomic message / advice
        msg = weather_data.get("message")
        if msg:
            advice_text = msg.get("text") if isinstance(msg, dict) else str(msg)
            st.markdown(
                f"""
                <div style="margin-top:12px;background:#F7F5EE;padding:12px;border-radius:10px;font-size:0.9rem;line-height:1.5;color:#1C241B;">
                    <b>🌾 Agronomic Advisory:</b> {advice_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # 72-Hour Interactive Forecast Time-Series (Open-Meteo Real Data)
    if f_data and not manual_mode:
        render_section_title("72-Hour Interactive Weather Time-Series", icon="📈")
        st.markdown(
            "<p style='font-size:0.9rem;color:#5E6057;'>Interactive forecast tracking hourly ambient temperature, relative humidity, and rainfall probability over the next 3 days. Orange dashed line marks the 80% humidity threshold.</p>",
            unsafe_allow_html=True,
        )
        fig_forecast = plot_weather_forecast_timeseries(f_data)
        st.plotly_chart(fig_forecast, use_container_width=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.caption(
        f"Data Source: {w.get('source', 'Open-Meteo')} · Coordinates: Lat {w.get('latitude', '—')}, Lon {w.get('longitude', '—')} · Cached for 15 minutes."
    )

render_footer()
