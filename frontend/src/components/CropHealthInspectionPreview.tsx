import { Eye, Info } from "lucide-react";

interface InspectionFeature {
  badge: string;
  label: string;
  sub: string;
}

const INSPECTION_FEATURES: InspectionFeature[] = [
  {
    badge: "1",
    label: "Vascular Veins",
    sub: "Surveys chlorosis & fluid pathways",
  },
  {
    badge: "2",
    label: "Canopy Surface",
    sub: "Evaluates spot clusters & lesion spread",
  },
  {
    badge: "3",
    label: "Leaf Margins",
    sub: "Checks discoloration & edge browning",
  },
];

export function CropHealthInspectionPreview() {
  return (
    <div className="crop-inspection-card">
      {/* Header */}
      <div className="inspection-header">
        <span className="inspection-tag">
          <Eye size={12} style={{ verticalAlign: -1 }} /> Illustrative Visual Assessment
        </span>
        <span className="inspection-sub">
          Optical botanical cue framework guiding diagnostic assessment
        </span>
      </div>

      {/* Dedicated Leaf Stage — Purely Visual Centerpiece */}
      <div className="inspection-stage" aria-label="Botanical leaf inspection diagram">
        <svg
          className="inspection-leaf-svg"
          viewBox="0 0 340 250"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          role="img"
          aria-label="Leaf inspection illustration with three numbered optical assessment zones"
        >
          <defs>
            <linearGradient id="leafBaseGrad" x1="60" y1="30" x2="270" y2="230" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#c5f0c8" stopOpacity="0.85" />
              <stop offset="100%" stopColor="#a5e2a9" stopOpacity="0.6" />
            </linearGradient>

            <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#1b3d26" floodOpacity="0.12" />
            </filter>
          </defs>

          {/* 1. Leaf Blade Contour */}
          <path
            d="M50 220C70 125 140 40 260 40C260 145 185 230 50 220Z"
            fill="url(#leafBaseGrad)"
            stroke="#1b3d26"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />

          {/* 2. Primary Central Stem */}
          <path
            d="M50 220C110 185 170 135 260 40"
            stroke="#1b3d26"
            strokeWidth="2.4"
            strokeLinecap="round"
            opacity="0.9"
          />

          {/* Primary & Secondary Veins */}
          <g stroke="#1b3d26" strokeLinecap="round" opacity="0.75">
            {/* Lower lateral veins */}
            <path d="M95 190C120 160 150 132 185 122" strokeWidth="1.3" />
            <path d="M135 155C160 128 190 106 222 96" strokeWidth="1.2" />
            <path d="M180 115C200 92 225 76 245 70" strokeWidth="1.1" />

            {/* Upper lateral veins */}
            <path d="M115 165C115 135 130 102 158 86" strokeWidth="1.2" />
            <path d="M155 130C160 102 180 82 202 68" strokeWidth="1.0" />
          </g>

          {/* -------------------------------------------------------------
              STATIC NUMBERED MARKER 1: Vascular Veins (Stem Network)
             ------------------------------------------------------------- */}
          <g transform="translate(142, 142)" className="leaf-marker" aria-hidden="true">
            <circle
              cx="0"
              cy="0"
              r="15"
              fill="rgba(190, 237, 192, 0.4)"
              stroke="#1b3d26"
              strokeWidth="1"
              strokeDasharray="2.5 2.5"
            />
            <circle
              cx="0"
              cy="0"
              r="9"
              fill="#1b3d26"
              stroke="#ffffff"
              strokeWidth="1.5"
              filter="url(#softGlow)"
            />
            <text
              x="0"
              y="3.5"
              textAnchor="middle"
              fontSize="9"
              fontWeight="700"
              fill="#ffffff"
              style={{ pointerEvents: "none", userSelect: "none" }}
            >
              1
            </text>
          </g>

          {/* -------------------------------------------------------------
              STATIC NUMBERED MARKER 2: Canopy Surface (Blade Texture)
             ------------------------------------------------------------- */}
          <g transform="translate(208, 92)" className="leaf-marker" aria-hidden="true">
            <circle
              cx="0"
              cy="0"
              r="15"
              fill="rgba(190, 237, 192, 0.4)"
              stroke="#1b3d26"
              strokeWidth="1"
              strokeDasharray="2.5 2.5"
            />
            <circle
              cx="0"
              cy="0"
              r="9"
              fill="#1b3d26"
              stroke="#ffffff"
              strokeWidth="1.5"
              filter="url(#softGlow)"
            />
            <text
              x="0"
              y="3.5"
              textAnchor="middle"
              fontSize="9"
              fontWeight="700"
              fill="#ffffff"
              style={{ pointerEvents: "none", userSelect: "none" }}
            >
              2
            </text>
          </g>

          {/* -------------------------------------------------------------
              STATIC NUMBERED MARKER 3: Leaf Margins (Perimeter Edge)
             ------------------------------------------------------------- */}
          <g transform="translate(186, 196)" className="leaf-marker" aria-hidden="true">
            <circle
              cx="0"
              cy="0"
              r="15"
              fill="rgba(190, 237, 192, 0.4)"
              stroke="#1b3d26"
              strokeWidth="1"
              strokeDasharray="2.5 2.5"
            />
            <circle
              cx="0"
              cy="0"
              r="9"
              fill="#1b3d26"
              stroke="#ffffff"
              strokeWidth="1.5"
              filter="url(#softGlow)"
            />
            <text
              x="0"
              y="3.5"
              textAnchor="middle"
              fontSize="9"
              fontWeight="700"
              fill="#ffffff"
              style={{ pointerEvents: "none", userSelect: "none" }}
            >
              3
            </text>
          </g>
        </svg>
      </div>

      {/* The 3 Information Cards — Preserved Clean Layout */}
      <div className="inspection-features-grid">
        {INSPECTION_FEATURES.map((item) => (
          <div key={item.badge} className="inspection-feature-item">
            <span className="feature-btn-badge">{item.badge}</span>
            <div className="feature-btn-content">
              <strong>{item.label}</strong>
              <span>{item.sub}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Short Explanatory Preview Panel */}
      <div className="inspection-detail-panel">
        <div className="detail-panel-header">
          <span className="detail-panel-title">
            <Info size={13} style={{ verticalAlign: -1 }} />
            Optical Leaf Assessment
          </span>
          <span className="detail-panel-tag">Multi-Zone Analysis</span>
        </div>
        <p className="detail-panel-body">
          AgriVision evaluates vascular fluid pathways, blade surface clusters, and perimeter margins to guide diagnostic assessment.
        </p>
      </div>
    </div>
  );
}
