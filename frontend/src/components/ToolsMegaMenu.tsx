import { useRef, useEffect } from "react";
import {
  BookOpen,
  CloudSun,
  FlaskConical,
  ScanLine,
  ShieldCheck,
  ArrowRight,
  Sparkles,
} from "lucide-react";

export type ToolId = "doctor" | "weather" | "fertilizer" | "products" | "schemes";

interface ToolsMegaMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTool: (toolId: ToolId) => void;
  onScrollToTools: () => void;
}

export const toolRegistry = [
  {
    id: "doctor" as ToolId,
    title: "Crop Doctor",
    eyebrow: "Vision + Symptoms",
    desc: "Dual-signal plant disease detection with MobileNetV2, Random Forest symptom classification, and Grad-CAM visual heatmaps.",
    icon: ScanLine,
    badge: "Grad-CAM",
  },
  {
    id: "weather" as ToolId,
    title: "Weather Intelligence",
    eyebrow: "Microclimate Heuristics",
    desc: "Real-time forecast integration evaluating high-humidity fungal infection windows and thermal heat stress.",
    icon: CloudSun,
    badge: "Risk Rules",
  },
  {
    id: "fertilizer" as ToolId,
    title: "Fertilizer Planner",
    eyebrow: "Agronomic Tables",
    desc: "Deterministic per-acre deficiency lookup calculating precise commercial fertilizer dosages, N-P-K rates, and indicative costs.",
    icon: FlaskConical,
    badge: "Per Acre",
  },
  {
    id: "products" as ToolId,
    title: "Product Verification",
    eyebrow: "Authenticity Registry",
    desc: "Validate agricultural packaging QR codes and manufacturer serial batches against the local SQLite registry to verify authenticity.",
    icon: ShieldCheck,
    badge: "SQLite DB",
  },
  {
    id: "schemes" as ToolId,
    title: "Government Schemes",
    eyebrow: "Public Subsidies",
    desc: "Match farm acreage, state, crop category, and financial support needs with verified subsidies and official application links.",
    icon: BookOpen,
    badge: "Direct Links",
  },
];

export function ToolsMegaMenu({
  isOpen,
  onClose,
  onSelectTool,
  onScrollToTools,
}: ToolsMegaMenuProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={panelRef}
      className="mega-menu-panel"
      role="menu"
      aria-label="Agricultural Tools Menu"
    >
      <div className="mega-menu-header">
        <div className="mega-menu-header-copy">
          <span className="mega-menu-tag">
            <Sparkles size={11} style={{ verticalAlign: -1 }} /> Agricultural Intelligence Suite
          </span>
          <span className="mega-menu-sub">
            Five production engines built for transparent farm management and data-backed decisions.
          </span>
        </div>
      </div>

      <div className="mega-menu-grid">
        {toolRegistry.map((tool) => {
          const Icon = tool.icon;
          return (
            <button
              key={tool.id}
              className="mega-menu-item"
              role="menuitem"
              onClick={() => {
                onSelectTool(tool.id);
                onClose();
              }}
            >
              <div className="mega-item-icon-wrap">
                <Icon size={18} />
              </div>
              <div className="mega-item-body">
                <div className="mega-item-title-row">
                  <span className="mega-item-title">{tool.title}</span>
                  <span className="mega-item-badge">{tool.badge}</span>
                </div>
                <p className="mega-item-desc">{tool.desc}</p>
                <span className="mega-item-link">
                  Open dedicated tool <ArrowRight size={12} />
                </span>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mega-menu-footer">
        <button
          className="mega-menu-overview-link"
          onClick={() => {
            onScrollToTools();
            onClose();
          }}
        >
          View all tools on overview page ↓
        </button>
      </div>
    </div>
  );
}
