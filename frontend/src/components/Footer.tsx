import { Sprout, ArrowRight } from "lucide-react";

interface FooterProps {
  onNavigateSection?: (sectionId: string) => void;
  onOpenTool?: (toolId: "doctor" | "weather" | "fertilizer" | "products" | "schemes") => void;
}

export function Footer({ onNavigateSection, onOpenTool }: FooterProps) {
  const handleScroll = (id: string) => {
    if (onNavigateSection) {
      onNavigateSection(id);
    } else {
      const el = document.getElementById(id);
      if (el) {
        const headerOffset = 90;
        const pos = el.getBoundingClientRect().top + window.pageYOffset - headerOffset;
        window.scrollTo({ top: pos, behavior: "smooth" });
      }
    }
  };

  const handleTool = (toolId: "doctor" | "weather" | "fertilizer" | "products" | "schemes") => {
    if (onOpenTool) {
      onOpenTool(toolId);
    } else {
      handleScroll("tools");
    }
  };

  return (
    <footer className="site-footer" role="contentinfo">
      <div className="footer-container">
        {/* Top Section — Four Columns (Brand, Explore, Platform, Large Botanical Tree) */}
        <div className="footer-top-columns">
          {/* Column 1: Brand Column */}
          <div className="footer-col-brand">
            <div className="footer-brand-header">
              <div className="footer-brand-logo">
                <span className="brand-icon">
                  <Sprout size={18} />
                </span>
                <span className="brand-text">AgriVision</span>
              </div>

              {/* Small original botanical line-art sprout accent near identity */}
              <svg
                width="30"
                height="28"
                viewBox="0 0 34 32"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="footer-sprout-accent"
                aria-hidden="true"
              >
                <path
                  d="M17 28C17 20 18 13 22 7"
                  stroke="#1b3d26"
                  strokeWidth="1.2"
                  strokeLinecap="round"
                />
                <path
                  d="M22 7C24 13 22 18 17 21C14 18 15 11 22 7Z"
                  fill="#beedc0"
                  fillOpacity="0.75"
                  stroke="#1b3d26"
                  strokeWidth="1.1"
                />
                <path
                  d="M17 19C13 18 10 14 11 9C15 8 18 12 17 19Z"
                  fill="#d4f2d6"
                  fillOpacity="0.65"
                  stroke="#1b3d26"
                  strokeWidth="1"
                />
              </svg>
            </div>

            <p className="footer-tagline">
              Thoughtful technology for healthier crops.
            </p>

            <p className="footer-description">
              AI-grounded crop disease diagnosis, microclimate weather risk forecasting,
              deterministic fertilizer planning, genuine input verification, and verified public
              agricultural schemes in one connected workspace.
            </p>

            <button
              type="button"
              onClick={() => handleScroll("tools")}
              className="footer-explore-link"
            >
              <span>Explore tools</span>
              <ArrowRight size={13} className="footer-link-arrow" />
            </button>
          </div>

          {/* Column 2: Explore Tools */}
          <div className="footer-col-nav">
            <span className="footer-col-title">Explore Tools</span>
            <ul className="footer-nav-list">
              <li>
                <button
                  type="button"
                  onClick={() => handleTool("doctor")}
                  className="footer-nav-btn"
                >
                  Crop Doctor
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleTool("weather")}
                  className="footer-nav-btn"
                >
                  Weather Intelligence
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleTool("fertilizer")}
                  className="footer-nav-btn"
                >
                  Fertilizer Planner
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleTool("products")}
                  className="footer-nav-btn"
                >
                  Product Verification
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleTool("schemes")}
                  className="footer-nav-btn"
                >
                  Government Schemes
                </button>
              </li>
            </ul>
          </div>

          {/* Column 3: Platform */}
          <div className="footer-col-nav">
            <span className="footer-col-title">Platform</span>
            <ul className="footer-nav-list">
              <li>
                <button
                  type="button"
                  onClick={() => handleScroll("overview")}
                  className="footer-nav-btn"
                >
                  Overview
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleScroll("crop-intelligence")}
                  className="footer-nav-btn"
                >
                  Crop Intelligence
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleScroll("workflow")}
                  className="footer-nav-btn"
                >
                  System Architecture
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleScroll("about")}
                  className="footer-nav-btn"
                >
                  About AgriVision
                </button>
              </li>
            </ul>
          </div>

          {/* Column 4: Large Elegant Botanical Tree Illustration on one side */}
          <div className="footer-col-art" aria-hidden="true">
            <svg
              className="footer-tree-illustration"
              viewBox="0 0 200 230"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <defs>
                <linearGradient id="treeCanopyGrad1" x1="50" y1="30" x2="150" y2="150" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stopColor="#d4f2d6" stopOpacity="0.85" />
                  <stop offset="100%" stopColor="#beedc0" stopOpacity="0.7" />
                </linearGradient>
                <linearGradient id="treeCanopyGrad2" x1="80" y1="20" x2="160" y2="130" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stopColor="#beedc0" stopOpacity="0.9" />
                  <stop offset="100%" stopColor="#a3e2a7" stopOpacity="0.65" />
                </linearGradient>
              </defs>

              {/* Ground horizon line with subtle soil tufts */}
              <path
                d="M15 205C45 202 85 204 100 205C125 206 160 203 185 205"
                stroke="#1b3d26"
                strokeWidth="1.3"
                strokeLinecap="round"
                opacity="0.45"
              />
              <path
                d="M30 208C42 208 55 209 68 208 M130 208C145 209 160 208 170 208"
                stroke="#1b3d26"
                strokeWidth="0.8"
                strokeLinecap="round"
                strokeDasharray="2 3"
                opacity="0.3"
              />

              {/* Root network anchoring into soil */}
              <g stroke="#1b3d26" strokeWidth="1.2" strokeLinecap="round" opacity="0.65">
                <path d="M96 205C90 212 80 218 70 222" />
                <path d="M104 205C110 213 120 219 132 222" />
                <path d="M94 207C88 214 82 216 76 218" strokeWidth="0.8" />
                <path d="M106 207C112 214 118 217 124 219" strokeWidth="0.8" />
              </g>

              {/* Visible Organic Trunk with bark details and branching */}
              <path
                d="M93 205C92 180 90 155 93 132C94 122 92 110 88 100C84 90 76 80 68 74"
                stroke="#1b3d26"
                strokeWidth="2.4"
                strokeLinecap="round"
              />
              <path
                d="M107 205C108 180 110 155 107 132C106 120 109 108 116 96C122 86 130 78 138 72"
                stroke="#1b3d26"
                strokeWidth="2.4"
                strokeLinecap="round"
              />
              {/* Central crown branch */}
              <path
                d="M100 132C100 110 101 88 100 65C99 52 101 40 100 32"
                stroke="#1b3d26"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
              {/* Sub-branches */}
              <path d="M90 102C82 104 70 108 58 116" stroke="#1b3d26" strokeWidth="1.3" strokeLinecap="round" />
              <path d="M114 98C124 102 136 106 148 114" stroke="#1b3d26" strokeWidth="1.3" strokeLinecap="round" />
              <path d="M98 78C90 70 82 62 76 54" stroke="#1b3d26" strokeWidth="1.2" strokeLinecap="round" />
              <path d="M102 78C110 70 120 62 128 52" stroke="#1b3d26" strokeWidth="1.2" strokeLinecap="round" />

              {/* Bark texture striations */}
              <path d="M98 195C97 182 98 170 99 155" stroke="#1b3d26" strokeWidth="0.8" strokeLinecap="round" opacity="0.4" />
              <path d="M102 190C103 178 102 165 101 150" stroke="#1b3d26" strokeWidth="0.8" strokeLinecap="round" opacity="0.4" />

              {/* Layered Foliage Clusters with Refined Outlines */}
              {/* Lower left foliage cloud */}
              <path
                d="M45 125C32 120 25 105 32 92C38 80 52 78 62 82C68 72 82 68 92 75C100 82 100 95 94 105C90 115 80 125 65 126C58 126 50 128 45 125Z"
                fill="url(#treeCanopyGrad1)"
                stroke="#1b3d26"
                strokeWidth="1.3"
                strokeLinejoin="round"
              />
              {/* Lower right foliage cloud */}
              <path
                d="M155 122C168 118 174 102 166 90C160 80 148 78 138 82C132 72 118 68 108 76C100 84 102 96 108 106C112 115 122 124 136 125C144 125 150 126 155 122Z"
                fill="url(#treeCanopyGrad2)"
                stroke="#1b3d26"
                strokeWidth="1.3"
                strokeLinejoin="round"
              />
              {/* Mid left crown cluster */}
              <path
                d="M58 80C48 74 46 60 52 48C58 38 72 36 82 42C88 32 102 30 112 38C118 44 118 54 114 62C108 72 96 80 80 82C72 82 65 82 58 80Z"
                fill="url(#treeCanopyGrad2)"
                stroke="#1b3d26"
                strokeWidth="1.2"
                strokeLinejoin="round"
              />
              {/* Mid right crown cluster */}
              <path
                d="M142 78C152 72 154 58 146 46C138 36 126 36 116 42C110 32 98 32 88 40C84 46 84 56 90 64C96 72 108 80 122 82C130 82 136 82 142 78Z"
                fill="url(#treeCanopyGrad1)"
                stroke="#1b3d26"
                strokeWidth="1.2"
                strokeLinejoin="round"
              />
              {/* Top central crown spire */}
              <path
                d="M80 44C76 34 82 22 94 18C104 14 115 20 118 30C122 24 130 24 134 32C136 40 130 48 122 52C112 56 98 56 88 50C84 48 82 46 80 44Z"
                fill="#d4f2d6"
                fillOpacity="0.8"
                stroke="#1b3d26"
                strokeWidth="1.2"
                strokeLinejoin="round"
              />

              {/* Delicate Leaf Details & Veins within canopy */}
              <path d="M55 102C62 98 70 98 76 102" stroke="#1b3d26" strokeWidth="0.8" strokeLinecap="round" opacity="0.5" />
              <path d="M135 100C142 96 150 96 156 100" stroke="#1b3d26" strokeWidth="0.8" strokeLinecap="round" opacity="0.5" />
              <path d="M85 58C92 54 100 54 106 58" stroke="#1b3d26" strokeWidth="0.8" strokeLinecap="round" opacity="0.5" />

              {/* Small Ivory Blossoms with golden centers */}
              <g transform="translate(62, 94)">
                <circle cx="0" cy="0" r="2.8" fill="#faf7eb" stroke="#1b3d26" strokeWidth="0.7" />
                <circle cx="0" cy="0" r="1.1" fill="#f7e59c" />
              </g>
              <g transform="translate(142, 92)">
                <circle cx="0" cy="0" r="2.8" fill="#faf7eb" stroke="#1b3d26" strokeWidth="0.7" />
                <circle cx="0" cy="0" r="1.1" fill="#f7e59c" />
              </g>
              <g transform="translate(100, 42)">
                <circle cx="0" cy="0" r="2.4" fill="#faf7eb" stroke="#1b3d26" strokeWidth="0.6" />
                <circle cx="0" cy="0" r="0.9" fill="#f7e59c" />
              </g>
              <g transform="translate(86, 74)">
                <circle cx="0" cy="0" r="2.2" fill="#faf7eb" stroke="#1b3d26" strokeWidth="0.6" />
                <circle cx="0" cy="0" r="0.8" fill="#f7e59c" />
              </g>
              <g transform="translate(122, 70)">
                <circle cx="0" cy="0" r="2.2" fill="#faf7eb" stroke="#1b3d26" strokeWidth="0.6" />
                <circle cx="0" cy="0" r="0.8" fill="#f7e59c" />
              </g>
            </svg>
            <span className="footer-art-caption">Ecosystem Grounding</span>
          </div>
        </div>

        {/* 1st Horizontal Divider */}
        <div className="footer-divider" />

        {/* Outlined AgriVision Wordmark Stage (TechReck-Inspired Reference) */}
        <div className="footer-wordmark-stage">
          <div className="footer-wordmark-meta">
            <span>Agricultural Intelligence Platform</span>
            <span>Grounded Botanical Reasoning</span>
          </div>
          <div className="footer-wordmark-text" aria-label="AgriVision">
            AGRI <span className="footer-wordmark-italic">Vision</span>
          </div>
        </div>

        {/* 2nd Horizontal Divider */}
        <div className="footer-divider" />

        {/* Compact Bottom Copyright Bar */}
        <div className="footer-bottom-bar">
          <span className="footer-copy-text">
            &copy; 2026 AgriVision Platform. All rights reserved.
          </span>
          <span className="footer-tag-text">
            Thoughtful technology for healthier crops &middot; Grounded Diagnostics &amp; Farm Planning
          </span>
        </div>
      </div>
    </footer>
  );
}
