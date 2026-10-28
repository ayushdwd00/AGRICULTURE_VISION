"""
components/field_illustration.py
=================================
Top-down illustrated agricultural field visualization.
Uses custom SVG and botanical CSS to represent continuous crop rows,
soil beds, earthen furrows, and boundary irrigation channels.
Lightweight vector illustration — no charts, scatter plots, or 3D models.
"""

from __future__ import annotations
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

from utils.config import ASSETS_DIR


def get_field_illustration_svg() -> str:
    """Generate high-fidelity vector SVG of a top-down agricultural farm plot."""

    # Generate continuous scalloped foliage rows
    # 6 distinct crop rows running from x=105 to x=615
    y_rows = [118, 166, 214, 262, 310, 358]
    row_paths = []

    for idx, y_c in enumerate(y_rows):
        is_even = idx % 2 == 0
        base_fill = "url(#foliage-grad-1)" if is_even else "url(#foliage-grad-2)"
        mid_fill = "url(#foliage-mid-1)" if is_even else "url(#foliage-mid-2)"
        accent_fill = "#73A86F" if is_even else "#81B87D"

        # Continuous undulating canopy path
        # Wave loops spanning from 105 to 615 in 20px steps
        top_d = ["M 105 %d" % y_c]
        bot_d = []
        for x in range(105, 615, 20):
            # top lobes
            h = 13 if (x // 20) % 2 == 0 else 16
            top_d.append("Q %d %d, %d %d" % (x + 10, y_c - h, x + 20, y_c))
            # bottom lobes (stored in reverse)
            hb = 13 if (x // 20) % 2 == 1 else 15
            bot_d.insert(0, "Q %d %d, %d %d" % (x + 10, y_c + hb, x, y_c))

        full_d = " ".join(top_d) + " " + " ".join(bot_d) + " Z"

        # Secondary inner highlight ribbon
        inner_d = ["M 115 %d" % y_c]
        inner_bot = []
        for x in range(115, 605, 25):
            h_in = 7 if (x // 25) % 2 == 0 else 9
            inner_d.append("Q %d %d, %d %d" % (x + 12, y_c - h_in, x + 25, y_c))
            hb_in = 7 if (x // 25) % 2 == 1 else 8
            inner_bot.insert(0, "Q %d %d, %d %d" % (x + 12, y_c + hb_in, x, y_c))
        full_inner = " ".join(inner_d) + " " + " ".join(inner_bot) + " Z"

        # Centerline leaf texture marks
        leaf_accents = []
        for x in range(125, 600, 32):
            leaf_accents.append(
                f'<ellipse cx="{x}" cy="{y_c - 1}" rx="3.5" ry="1.8" fill="{accent_fill}" opacity="0.85" transform="rotate(-15 {x} {y_c})" />'
            )
            leaf_accents.append(
                f'<ellipse cx="{x + 16}" cy="{y_c + 1}" rx="3.5" ry="1.8" fill="{accent_fill}" opacity="0.85" transform="rotate(15 {x + 16} {y_c})" />'
            )

        row_group = f"""
        <!-- Crop Row #{idx + 1} -->
        <g class="crop-row-group">
            <!-- Soil mound base -->
            <rect x="98" y="{y_c - 17}" width="524" height="34" rx="10" fill="url(#soil-ridge-grad)" />
            <!-- Continuous outer foliage canopy with drop shadow -->
            <path d="{full_d}" fill="{base_fill}" filter="url(#foliage-shadow)" />
            <!-- Interior canopy layer for depth -->
            <path d="{full_inner}" fill="{mid_fill}" opacity="0.92" />
            <!-- Botanical leaf accents -->
            {''.join(leaf_accents)}
        </g>
        """
        row_paths.append(row_group)

    svg_content = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 420" width="100%" height="100%" style="display:block;border-radius:12px;background:#F9F7F1;">
        <defs>
            <!-- Shadow for crop rows -->
            <filter id="foliage-shadow" x="-5%" y="-15%" width="110%" height="140%">
                <feDropShadow dx="0" dy="2.5" stdDeviation="2.2" flood-color="#3D3020" flood-opacity="0.32" />
            </filter>
            <!-- Shadow for parcel frame -->
            <filter id="plot-shadow" x="-3%" y="-3%" width="106%" height="108%">
                <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#2D281E" flood-opacity="0.12" />
            </filter>

            <!-- Base Soil Gradients -->
            <linearGradient id="plot-soil" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#C7B69D" />
                <stop offset="50%" stop-color="#BAA58A" />
                <stop offset="100%" stop-color="#B09A7E" />
            </linearGradient>

            <linearGradient id="soil-ridge-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#8C775D" stop-opacity="0.5" />
                <stop offset="50%" stop-color="#6E5A42" stop-opacity="0.8" />
                <stop offset="100%" stop-color="#8C775D" stop-opacity="0.5" />
            </linearGradient>

            <!-- Irrigation Water Gradient -->
            <linearGradient id="water-flow" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stop-color="#6497A9" />
                <stop offset="35%" stop-color="#7BB0C2" />
                <stop offset="70%" stop-color="#6295A7" />
                <stop offset="100%" stop-color="#73A7B9" />
            </linearGradient>

            <!-- Foliage Canopy Gradients -->
            <linearGradient id="foliage-grad-1" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#326639" />
                <stop offset="45%" stop-color="#234D29" />
                <stop offset="100%" stop-color="#193B1F" />
            </linearGradient>

            <linearGradient id="foliage-grad-2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#3C7343" />
                <stop offset="45%" stop-color="#2A5831" />
                <stop offset="100%" stop-color="#1B4022" />
            </linearGradient>

            <linearGradient id="foliage-mid-1" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#4E8C56" />
                <stop offset="100%" stop-color="#34683C" />
            </linearGradient>

            <linearGradient id="foliage-mid-2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#55995E" />
                <stop offset="100%" stop-color="#3B7443" />
            </linearGradient>

            <!-- Furrow Line Pattern -->
            <pattern id="soil-texture" width="12" height="12" patternUnits="userSpaceOnUse">
                <line x1="0" y1="6" x2="12" y2="6" stroke="#AA957A" stroke-width="0.8" stroke-dasharray="3,3" opacity="0.6" />
            </pattern>
        </defs>

        <!-- Outer Agricultural Parcel Margin -->
        <rect x="18" y="14" width="684" height="392" rx="14" fill="#EDE7DA" stroke="#D3C7B2" stroke-width="1.5" />

        <!-- Main Cultivated Field Plot Bed -->
        <rect x="36" y="32" width="648" height="356" rx="10" fill="url(#plot-soil)" filter="url(#plot-shadow)" stroke="#A69175" stroke-width="1" />
        <rect x="36" y="32" width="648" height="356" rx="10" fill="url(#soil-texture)" opacity="0.4" />

        <!-- Irrigation Channel (Runs along top edge) -->
        <g id="irrigation-channel">
            <!-- Channel Earthen Banks -->
            <rect x="36" y="44" width="648" height="38" fill="#99866F" />
            <line x1="36" y1="44" x2="684" y2="44" stroke="#87745E" stroke-width="1.5" />
            <line x1="36" y1="82" x2="684" y2="82" stroke="#87745E" stroke-width="1.5" />
            <!-- Water Body -->
            <rect x="42" y="52" width="636" height="22" rx="4" fill="url(#water-flow)" />
            <!-- Water Ripples / Flow Highlights -->
            <line x1="60" y1="60" x2="160" y2="60" stroke="#B1D8E5" stroke-width="1.2" stroke-dasharray="24,14" opacity="0.8" />
            <line x1="200" y1="65" x2="340" y2="65" stroke="#B1D8E5" stroke-width="1.2" stroke-dasharray="30,18" opacity="0.8" />
            <line x1="380" y1="59" x2="520" y2="59" stroke="#B1D8E5" stroke-width="1.2" stroke-dasharray="26,16" opacity="0.8" />
            <line x1="560" y1="64" x2="650" y2="64" stroke="#B1D8E5" stroke-width="1.2" stroke-dasharray="20,12" opacity="0.8" />
            <!-- Sluice Inflow Marker -->
            <rect x="70" y="46" width="16" height="34" rx="2" fill="#5A4A38" stroke="#3D3022" stroke-width="1" />
            <text x="94" y="66" font-family="-apple-system, sans-serif" font-size="9" font-weight="600" fill="#E2F1F7" letter-spacing="0.5">BOUNDARY IRRIGATION CANAL</text>
        </g>

        <!-- Headland Turning Zones (Left and Right tractor/footpaths) -->
        <!-- Left Headland -->
        <rect x="36" y="82" width="60" height="306" fill="#C2B198" opacity="0.5" />
        <line x1="96" y1="82" x2="96" y2="388" stroke="#A8947C" stroke-width="1.5" stroke-dasharray="6,4" />
        <!-- Right Headland -->
        <rect x="624" y="82" width="60" height="306" fill="#C2B198" opacity="0.5" />
        <line x1="624" y1="82" x2="624" y2="388" stroke="#A8947C" stroke-width="1.5" stroke-dasharray="6,4" />

        <!-- Earthen Furrow Walkways between rows -->
        <g stroke="#9D886F" stroke-width="1" stroke-dasharray="4,6" opacity="0.65">
            <line x1="96" y1="142" x2="624" y2="142" />
            <line x1="96" y1="190" x2="624" y2="190" />
            <line x1="96" y1="238" x2="624" y2="238" />
            <line x1="96" y1="286" x2="624" y2="286" />
            <line x1="96" y1="334" x2="624" y2="334" />
        </g>

        <!-- Continuous Lush Crop Rows -->
        {''.join(row_paths)}

        <!-- Left Headland Turning Arc Tracks -->
        <g stroke="#9E8A72" stroke-width="1.2" fill="none" opacity="0.45">
            <path d="M 96 118 C 65 118, 65 166, 96 166" />
            <path d="M 96 214 C 65 214, 65 262, 96 262" />
            <path d="M 96 310 C 65 310, 65 358, 96 358" />
        </g>

        <!-- Right Headland Turning Arc Tracks -->
        <g stroke="#9E8A72" stroke-width="1.2" fill="none" opacity="0.45">
            <path d="M 624 118 C 655 118, 655 166, 624 166" />
            <path d="M 624 214 C 655 214, 655 262, 624 262" />
            <path d="M 624 310 C 655 310, 655 358, 624 358" />
        </g>

        <!-- Zone Labels on Left Margins -->
        <text x="50" y="146" font-family="-apple-system, sans-serif" font-size="8.5" font-weight="700" fill="#75624C">ZONE A</text>
        <text x="50" y="242" font-family="-apple-system, sans-serif" font-size="8.5" font-weight="700" fill="#75624C">ZONE B</text>
        <text x="50" y="338" font-family="-apple-system, sans-serif" font-size="8.5" font-weight="700" fill="#75624C">ZONE C</text>

        <!-- Bottom Buffer Strip & Windbreak Foliage -->
        <g id="windbreak-shrubs" opacity="0.85">
            <!-- Small rounded hedge clusters along bottom edge -->
            <circle cx="55" cy="384" r="5" fill="#244B29" />
            <circle cx="68" cy="385" r="6" fill="#2E5C34" />
            <circle cx="82" cy="384" r="5" fill="#244B29" />

            <circle cx="638" cy="384" r="5" fill="#244B29" />
            <circle cx="652" cy="385" r="6" fill="#2E5C34" />
            <circle cx="665" cy="384" r="5" fill="#244B29" />
        </g>

        <!-- Compass Rose (Top Right) -->
        <g transform="translate(642, 28)">
            <circle cx="0" cy="0" r="10" fill="#FFFFFF" stroke="#D3C7B2" stroke-width="1" />
            <polygon points="0,-8 3,-1 0,1" fill="#1B3D26" />
            <polygon points="0,1 3,-1 0,8" fill="#B09A7E" />
            <polygon points="0,-8 -3,-1 0,1" fill="#427A3A" />
            <polygon points="0,1 -3,-1 0,8" fill="#8C775D" />
            <text x="-3" y="-12" font-family="Georgia, serif" font-size="8" font-weight="700" fill="#1B3D26">N</text>
        </g>

        <!-- Scale Bar (Bottom Left) -->
        <g transform="translate(108, 382)">
            <line x1="0" y1="0" x2="60" y2="0" stroke="#66543E" stroke-width="2" />
            <line x1="0" y1="-3" x2="0" y2="3" stroke="#66543E" stroke-width="2" />
            <line x1="30" y1="-2" x2="30" y2="2" stroke="#66543E" stroke-width="1" />
            <line x1="60" y1="-3" x2="60" y2="3" stroke="#66543E" stroke-width="2" />
            <text x="18" y="-4" font-family="-apple-system, sans-serif" font-size="7.5" font-weight="600" fill="#5E4E3B">20 METERS</text>
        </g>

        <!-- Technical Label (Bottom Right) -->
        <text x="495" y="380" font-family="-apple-system, sans-serif" font-size="8" font-weight="500" fill="#75624C" letter-spacing="0.3">
            0.75m Row Spacing · Raised Furrow Beds
        </text>
    </svg>
    """
    return svg_content


def render_field_illustration() -> None:
    """Render the top-down agricultural field illustration card with its legend."""
    svg_markup = get_field_illustration_svg()

    card_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,500;1,600&family=Rubik:wght@400;500;600&display=swap');
      * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }}
      body {{
        background: transparent;
        font-family: 'Rubik', -apple-system, sans-serif;
        color: #2A2A26;
        padding: 1px;
      }}
      .field-card {{
        background: #FFFFFF;
        border: 1px solid rgba(27,61,38,0.12);
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        box-shadow: 0 3px 14px rgba(0,0,0,0.03);
      }}
      .field-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-style: italic;
        font-size: 1.35rem;
        color: #1B3D26;
        margin-bottom: 4px;
      }}
      .field-desc {{
        font-size: 0.86rem;
        color: #5E6057;
        line-height: 1.5;
        margin-bottom: 12px;
      }}
      .svg-container {{
        width: 100%;
        border-radius: 10px;
        overflow: hidden;
      }}
      .field-legend {{
        display: flex;
        align-items: center;
        justify-content: center;
        flex-wrap: wrap;
        gap: 16px;
        padding-top: 10px;
        margin-top: 10px;
        border-top: 1px solid rgba(27,61,38,0.08);
        font-size: 0.82rem;
        color: #3D4035;
      }}
      .legend-item {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }}
      .swatch {{
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 3px;
      }}
    </style>
    </head>
    <body>
      <div class="field-card">
        <div class="field-title">Illustrated Top-Down Field Layout</div>
        <div class="field-desc">Architectural top-down perspective showing continuous raised crop rows, natural furrow spacing, and boundary irrigation flow.</div>
        <div class="svg-container">
          {svg_markup}
        </div>
        <div class="field-legend">
          <div class="legend-item">
            <span class="swatch" style="background: linear-gradient(135deg, #326639, #193B1F);"></span>
            <span>Zone A (North Rows)</span>
          </div>
          <div class="legend-item">
            <span class="swatch" style="background: linear-gradient(135deg, #3C7343, #1B4022);"></span>
            <span>Zone B &amp; C (Canopy Beds)</span>
          </div>
          <div class="legend-item">
            <span class="swatch" style="background: #BAA58A; border: 1px solid #8C775D;"></span>
            <span>Earthen Furrows</span>
          </div>
          <div class="legend-item">
            <span class="swatch" style="background: #6497A9;"></span>
            <span>Irrigation Canal</span>
          </div>
          <div class="legend-item">
            <span class="swatch" style="background: #C2B198; border: 1px dashed #A8947C;"></span>
            <span>Headland Turn Paths</span>
          </div>
        </div>
      </div>
    </body>
    </html>
    """

    components.html(card_html, height=545, scrolling=False)


