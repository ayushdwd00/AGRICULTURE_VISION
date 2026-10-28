"""
components/botanical_elements.py
================================
AgriVision visual identity: Botanical editorial CSS, typography, grid background,
badges, header cards, subtle animations, and accessibility transitions.
"""

from __future__ import annotations

import streamlit as st


BOTANICAL_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400;1,500;1,600&family=Rubik:wght@300;400;500;600&family=DM+Sans:wght@400;500;700&display=swap');

  :root {
    --color-linen: #F7F5EE;
    --color-cream: #FFFFF3;
    --color-surface: #FFFFFF;
    --color-ink: #111812;
    --color-charcoal: #2A2A26;
    --color-muted: #5E6057;
    --color-muted-light: #828479;
    --color-border: rgba(27, 61, 38, 0.12);
    --color-border-strong: rgba(27, 61, 38, 0.24);
    --color-sage: #2D5A27;
    --color-sage-deep: #1B3D26;
    --color-sage-soft: #E2F7E4;
    --color-sage-accent: #BEEDC0;
    --color-amber-soft: #FEF3C7;
    --color-amber-text: #92400E;
    --color-rose-soft: #FEE2E2;
    --color-rose-text: #991B1B;
    --radius-card: 14px;
    --radius-pill: 999px;
    --shadow-soft: 0 4px 20px rgba(27, 61, 38, 0.05);
  }

  /* Global background architectural cross-grid */
  .stApp {
    background-color: var(--color-linen);
    background-size: 32px 32px;
    background-image:
      linear-gradient(to right, rgba(27, 61, 38, 0.038) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(27, 61, 38, 0.038) 1px, transparent 1px);
    background-repeat: repeat;
    background-attachment: fixed;
    color: var(--color-ink);
    font-family: 'Rubik', 'DM Sans', -apple-system, sans-serif;
  }

  /* Container width & padding - ensure content starts cleanly below Streamlit's header */
  .block-container {
    max-width: 1180px;
    padding-top: 4.8rem !important;
    padding-bottom: 4rem;
  }

  @media (max-width: 768px) {
    .block-container {
      padding-top: 4.2rem !important;
      padding-left: 1rem !important;
      padding-right: 1rem !important;
    }
  }

  /* Keyframe entrance animations */
  @keyframes agvFadeSlideUp {
    from {
      opacity: 0;
      transform: translateY(12px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Editorial Headings */
  h1:not(.hero-title), h2, h3, h4, h5 {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-style: italic !important;
    font-weight: 500 !important;
    color: var(--color-sage-deep) !important;
    letter-spacing: -0.015em !important;
  }

  /* Hero Headline */
  .hero-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-weight: 700;
    font-style: normal;
    color: var(--color-sage-deep);
    letter-spacing: -0.02em;
    line-height: 1.15;
    margin-bottom: 0.5rem;
  }

  /* Page Header Card with Entrance Animation */
  .agv-page-header {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(242, 247, 240, 0.88));
    border: 1px solid var(--color-border);
    border-radius: var(--radius-card);
    padding: 1.6rem 2rem;
    margin-bottom: 1.6rem;
    box-shadow: var(--shadow-soft);
    position: relative;
    overflow: hidden;
    animation: agvFadeSlideUp 0.35s ease-out;
  }
  .agv-page-header::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #1B3D26, #4A7C59, #BEEDC0);
  }
  .agv-page-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--color-sage);
    margin-bottom: 0.4rem;
  }
  .agv-page-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-style: italic;
    font-size: 2.1rem;
    font-weight: 600;
    color: var(--color-sage-deep);
    margin: 0.1rem 0 0.4rem 0;
    line-height: 1.2;
  }
  .agv-page-desc {
    font-size: 1rem;
    color: var(--color-muted);
    margin: 0;
    line-height: 1.5;
    max-width: 850px;
  }

  /* Botanical Badges and Pills */
  .agv-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 0.28rem 0.75rem;
    border-radius: var(--radius-pill);
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  .agv-pill-sage {
    background: var(--color-sage-soft);
    color: var(--color-sage-deep);
    border: 1px solid rgba(27, 61, 38, 0.18);
  }
  .agv-pill-amber {
    background: var(--color-amber-soft);
    color: var(--color-amber-text);
    border: 1px solid rgba(146, 64, 14, 0.2);
  }
  .agv-pill-rose {
    background: var(--color-rose-soft);
    color: var(--color-rose-text);
    border: 1px solid rgba(153, 27, 27, 0.2);
  }

  /* Refined Card Containers with Subtle Motion */
  .agv-card {
    background: #FFFFFF;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-card);
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: var(--shadow-soft);
    animation: agvFadeSlideUp 0.4s ease-out;
    transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s ease;
  }
  .agv-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(27, 61, 38, 0.08);
  }

  /* Botanical Section Subheading */
  .agv-section-heading {
    font-family: 'Playfair Display', Georgia, serif;
    font-style: italic;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--color-sage-deep);
    margin: 1.4rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid var(--color-border);
    padding-bottom: 0.4rem;
  }

  /* Button Styling */
  .stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.5rem 1.2rem !important;
    border: 1px solid var(--color-border-strong) !important;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
  }
  .stButton > button:hover {
    transform: translateY(-1.5px) !important;
    box-shadow: 0 4px 14px rgba(27, 61, 38, 0.12) !important;
  }

  /* Respect User Reduced Motion Preferences */
  @media (prefers-reduced-motion: reduce) {
    *, ::before, ::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }

  /* =====================================================================
     AgriVision Professional SaaS Sidebar Design
     ===================================================================== */
  [data-testid="stSidebar"] {
    background-color: #F4F0E8 !important;
    border-right: 1px solid rgba(27, 61, 38, 0.12) !important;
  }
  
  /* Suppress default Streamlit auto-nav completely */
  [data-testid="stSidebarNav"] {
    display: none !important;
  }
  
  /* Collapse empty header space so sidebar content begins cleanly near top */
  [data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    display: none !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
  }
  
  [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 0.9rem !important;
    padding-bottom: 1.4rem !important;
    padding-left: 0.85rem !important;
    padding-right: 0.85rem !important;
  }
  
  [data-testid="stSidebarUserContent"] {
    padding-top: 0 !important;
  }

  /* 1. Brand Header */
  .agv-sidebar-brand {
    padding: 0.1rem 0.2rem 0.65rem 0.2rem;
  }
  .agv-sidebar-brand-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .agv-sidebar-logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: #E3ECE0;
    border: 1px solid rgba(27, 61, 38, 0.16);
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    flex-shrink: 0;
  }
  .agv-sidebar-brand-text {
    display: flex;
    flex-direction: column;
  }
  .agv-sidebar-brand-name {
    font-family: 'Playfair Display', Georgia, serif;
    font-style: italic;
    font-weight: 700;
    font-size: 1.38rem;
    color: #1B3D26;
    letter-spacing: -0.015em;
    line-height: 1.1;
  }
  .agv-sidebar-brand-subtitle {
    font-size: 0.74rem;
    font-weight: 500;
    color: #555D50;
    margin-top: 2px;
    letter-spacing: 0.015em;
  }

  /* Subtle Divider */
  .agv-sidebar-divider {
    height: 1px;
    background: rgba(27, 61, 38, 0.11);
    margin: 0.7rem 0.1rem;
  }

  /* Navigation Section Label */
  .agv-sidebar-section-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    font-weight: 700;
    color: #6C7267;
    margin: 0.5rem 0.4rem 0.4rem 0.4rem;
  }

  /* 2. Navigation Items (st.page_link) */
  [data-testid="stSidebar"] [data-testid="stPageLink"] {
    margin-bottom: 3px !important;
  }

  [data-testid="stSidebar"] [data-testid="stPageLink"] a {
    display: flex !important;
    align-items: center !important;
    gap: 9px !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 8px !important;
    border-left: 3px solid transparent !important;
    background-color: transparent !important;
    color: #384035 !important;
    font-family: 'DM Sans', 'Rubik', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    transition: background-color 0.14s ease, border-left-color 0.14s ease, color 0.14s ease !important;
    width: 100% !important;
    box-sizing: border-box !important;
  }

  [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    background-color: rgba(27, 61, 38, 0.065) !important;
    color: #1B3D26 !important;
    border-left-color: rgba(27, 61, 38, 0.4) !important;
  }

  /* Active Navigation State */
  [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
  [data-testid="stSidebar"] [data-testid="stPageLink"] a:has([aria-current="page"]) {
    background-color: #E2EBE0 !important;
    color: #1B3D26 !important;
    font-weight: 600 !important;
    border-left: 3px solid #1B3D26 !important;
  }

  /* Icon sizing inside nav link */
  [data-testid="stSidebar"] [data-testid="stPageLink"] [data-testid="stPageLink-Icon"],
  [data-testid="stSidebar"] [data-testid="stPageLink"] span:first-child {
    font-size: 1.05rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
  }

  [data-testid="stSidebar"] [data-testid="stPageLink"] [data-testid="stPageLink-Label"] {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
  }

  /* 3. System Status Panel */
  .agv-status-card {
    background: #FAF8F3;
    border: 1px solid rgba(27, 61, 38, 0.13);
    border-radius: 10px;
    padding: 0.75rem 0.85rem;
    margin: 0.3rem 0.1rem 0.4rem 0.1rem;
    box-shadow: 0 1px 4px rgba(27, 61, 38, 0.03);
  }
  .agv-status-header {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #2D5A27;
    margin-bottom: 0.6rem;
  }
  .agv-status-pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #16A34A;
    box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.22);
    display: inline-block;
  }
  .agv-status-items {
    display: flex;
    flex-direction: column;
    gap: 7px;
  }
  .agv-status-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.79rem;
    line-height: 1.35;
    padding: 2px 0;
  }
  .agv-status-row-label {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #4A5146;
    font-weight: 500;
    font-size: 0.78rem;
  }
  .agv-status-row-icon {
    font-size: 0.85rem;
    display: inline-flex;
    align-items: center;
  }
  .agv-status-row-value {
    color: #1E261D;
    font-size: 0.77rem;
    text-align: right;
  }
  .agv-status-row-value code {
    font-family: 'SF Mono', Consolas, Monaco, monospace;
    font-size: 0.73rem;
    background: rgba(27, 61, 38, 0.07);
    color: #1B3D26;
    padding: 1px 4px;
    border-radius: 4px;
    border: 1px solid rgba(27, 61, 38, 0.1);
  }
  .agv-status-tag {
    font-size: 0.69rem;
    color: #6C7267;
    font-weight: 500;
  }
  .agv-status-count {
    font-weight: 600;
    color: #1B3D26;
  }
  .agv-status-live-badge {
    display: inline-block;
    background: #E0F2FE;
    color: #0369A1;
    font-size: 0.66rem;
    font-weight: 600;
    padding: 1px 5px;
    border-radius: 4px;
    border: 1px solid rgba(3, 105, 161, 0.2);
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-left: 2px;
  }

  /* 4. Sidebar Footer */
  .agv-sidebar-footer {
    padding: 0.35rem 0.2rem 0.15rem 0.2rem;
    font-size: 0.73rem;
    color: #7A8175;
    text-align: center;
    letter-spacing: 0.01em;
  }
</style>
"""


def inject_botanical_theme() -> None:
    """Inject core CSS stylesheets into Streamlit."""
    st.markdown(BOTANICAL_CSS, unsafe_allow_html=True)


def render_page_header(
    eyebrow: str,
    title: str,
    description: str,
    icon: str = "🌾",
) -> None:
    """Render a polished, botanical header card."""
    st.markdown(
        f"""
        <div class="agv-page-header">
            <div class="agv-page-eyebrow"><span>{icon}</span> {eyebrow}</div>
            <div class="agv-page-title">{title}</div>
            <p class="agv-page-desc">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str, icon: str = "🌿") -> None:
    """Render a styled botanical section title."""
    st.markdown(
        f'<div class="agv-section-heading"><span>{icon}</span> {title}</div>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the application footer."""
    st.markdown(
        """
        <div style="margin-top:3.5rem;padding-top:1.5rem;border-top:1px solid rgba(27,61,38,0.12);color:#5E6057;font-size:0.85rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
            <div><strong>🌾 AgriVision</strong> — Intelligent Agriculture Super-App · Python Streamlit Architecture</div>
            <div>Built for Indian Agriculture · Open-Meteo · MobileNetV2 · SQLite Demo Registry</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
