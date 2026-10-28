"""
components/cards.py
===================
Reusable card layouts, confidence indicators, metrics, and result presentation.
"""

from __future__ import annotations

import html
from typing import Any, Dict, List, Optional
import streamlit as st

from utils.config import THEME_COLORS


def render_metric_card(
    label: str,
    value: str,
    subtext: Optional[str] = None,
    border_color: str = "#2D5A27",
) -> None:
    """Render a clean agricultural KPI metric card."""
    sub_html = f'<div style="font-size:0.8rem;color:#5E6057;margin-top:4px;">{subtext}</div>' if subtext else ""
    st.markdown(
        f"""
        <div style="background:#FFF;border:1px solid rgba(27,61,38,0.12);border-left:4px solid {border_color};border-radius:12px;padding:1rem 1.2rem;box-shadow:0 2px 10px rgba(0,0,0,0.03);margin-bottom:0.75rem;">
            <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.07em;color:#5E6057;font-weight:600;">{label}</div>
            <div style="font-size:1.45rem;font-weight:700;color:#1B3D26;margin-top:2px;">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_confidence_bar(confidence: float, threshold: float = 0.70) -> None:
    """Render a visual progress bar showing diagnostic certainty against the threshold."""
    val = max(0.0, min(1.0, float(confidence or 0.0)))
    pct = val * 100
    is_high = val >= threshold
    color = "#1B3D26" if is_high else "#C0392B"
    band = "High (Confident)" if is_high else "Low (Uncertain)"

    st.markdown(
        f"""
        <div style="margin: 0.8rem 0;">
            <div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:4px;">
                <span style="font-weight:600;color:#2A2A26;">Model Confidence: <b style="color:{color};">{pct:.1f}%</b></span>
                <span style="color:#5E6057;">Threshold: {threshold*100:.0f}% · <span style="font-weight:600;color:{color};">{band}</span></span>
            </div>
            <div style="height:10px;background:rgba(27,61,38,0.08);border-radius:999px;overflow:hidden;position:relative;">
                <div style="width:{pct:.1f}%;height:100%;background:{color};border-radius:999px;transition:width 0.4s ease;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert_box(text: str, tone: str = "info") -> None:
    """Render a styled alert message box (good, warn, danger, info)."""
    styles = {
        "good": {"bg": "#ECFDF5", "border": "#A7F3D0", "color": "#065F46", "icon": "✅"},
        "warn": {"bg": "#FFFBEB", "border": "#FDE68A", "color": "#92400E", "icon": "⚠️"},
        "danger": {"bg": "#FEF2F2", "border": "#FECACA", "color": "#991B1B", "icon": "⛔"},
        "info": {"bg": "#F0FDF4", "border": "#BBF7D0", "color": "#166534", "icon": "ℹ️"},
    }
    cfg = styles.get(tone, styles["info"])
    st.markdown(
        f"""
        <div style="background:{cfg['bg']};border:1px solid {cfg['border']};color:{cfg['color']};padding:0.9rem 1.1rem;border-radius:10px;font-size:0.92rem;line-height:1.5;margin:0.75rem 0;">
            <span style="margin-right:6px;">{cfg['icon']}</span> {html.escape(text)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scheme_card(scheme: Dict[str, Any]) -> None:
    """Render a full government subsidy and support scheme card."""
    name = html.escape(scheme.get("name", "Agricultural Scheme"))
    cat = html.escape(scheme.get("category", "Central Scheme"))
    desc = html.escape(scheme.get("description", ""))
    benefit = html.escape(scheme.get("benefit", ""))
    region = html.escape(scheme.get("region", "All India"))
    link = scheme.get("official_link", "")

    eligibility = scheme.get("eligibility", [])
    if isinstance(eligibility, str):
        eligibility = [eligibility]
    
    docs = scheme.get("required_documents", []) or scheme.get("documents_required", [])
    if isinstance(docs, str):
        docs = [docs]

    elig_items = "".join(f"<li style='margin-bottom:3px;'>{html.escape(str(item))}</li>" for item in eligibility[:4])
    doc_tags = "".join(
        f"<span style='background:#EFECE1;color:#1B3D26;padding:2px 8px;border-radius:4px;font-size:0.75rem;margin-right:5px;display:inline-block;margin-bottom:4px;'>📄 {html.escape(str(d))}</span>"
        for d in docs[:5]
    )

    matched_reasons = scheme.get("matched_reasons", [])
    matched_html = ""
    if matched_reasons:
        matched_html = f"<div style='background:#ECFDF5;border:1px solid #A7F3D0;color:#065F46;padding:5px 10px;border-radius:6px;font-size:0.8rem;margin:8px 0;'>✓ Matched on: {' · '.join(matched_reasons)}</div>"

    unmet_reasons = scheme.get("unmet_reasons", [])
    unmet_html = ""
    if unmet_reasons:
        unmet_html = f"<div style='background:#FFFBEB;border:1px solid #FDE68A;color:#92400E;padding:5px 10px;border-radius:6px;font-size:0.8rem;margin:8px 0;'>⚠️ Near match consideration: {' · '.join(unmet_reasons)}</div>"

    link_html = f'<a href="{link}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;margin-top:10px;color:#1B3D26;font-weight:600;font-size:0.88rem;text-decoration:none;">Apply on Official Portal ↗</a>' if link else ""

    st.markdown(
        f"""
        <div style="background:#FFF;border:1px solid rgba(27,61,38,0.12);border-radius:12px;padding:1.4rem;margin-bottom:1.2rem;box-shadow:0 3px 12px rgba(0,0,0,0.03);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span style="background:#E2F7E4;color:#1B3D26;padding:3px 10px;border-radius:999px;font-size:0.75rem;font-weight:600;">{cat}</span>
                <span style="font-size:0.8rem;color:#5E6057;">📍 {region}</span>
            </div>
            <h3 style="margin:0.3rem 0 0.5rem 0;font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.35rem;color:#1B3D26;">{name}</h3>
            <p style="color:#2A2A26;font-size:0.92rem;line-height:1.5;margin-bottom:0.75rem;">{desc}</p>
            {f'<div style="background:#F7F5EE;padding:8px 12px;border-radius:8px;font-size:0.85rem;margin-bottom:8px;"><strong>Benefits:</strong> {benefit}</div>' if benefit else ''}
            {matched_html}
            {unmet_html}
            {f'<div style="margin:8px 0;font-size:0.85rem;"><strong>Eligibility:</strong><ul style="padding-left:18px;margin:4px 0 0 0;">{elig_items}</ul></div>' if elig_items else ''}
            {f'<div style="margin-top:8px;"><strong>Required Documents:</strong><div style="margin-top:4px;">{doc_tags}</div></div>' if doc_tags else ''}
            {link_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
