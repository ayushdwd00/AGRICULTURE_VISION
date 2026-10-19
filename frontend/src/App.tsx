import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowDown,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  CloudSun,
  FlaskConical,
  Menu,
  ScanLine,
  ShieldCheck,
  Sprout,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { get } from "./services/api";
import type { ApiHealth } from "./types";
import { Button, Card } from "./components/ui";
import { BotanicalLeaf } from "./components/BotanicalLeaf";
import { HeroCropIllustration } from "./components/HeroCropIllustration";
import { ToolsMegaMenu } from "./components/ToolsMegaMenu";
import { CropHealthInspectionPreview } from "./components/CropHealthInspectionPreview";
import { Footer } from "./components/Footer";
import CropDoctor from "./pages/CropDoctor";
import WeatherPage from "./pages/WeatherPage";
import FertilizerPage from "./pages/FertilizerPage";
import ProductPage from "./pages/ProductPage";
import SchemesPage from "./pages/SchemesPage";

export type ToolPageId = "doctor" | "weather" | "fertilizer" | "products" | "schemes";
export type AppView = "home" | ToolPageId;

interface SectionNavEntry {
  id: string;
  label: string;
}

const homepageSections: SectionNavEntry[] = [
  { id: "overview", label: "Overview" },
  { id: "tools", label: "Agricultural Tools" },
  { id: "crop-intelligence", label: "Crop Intelligence" },
  { id: "weather-fertilizer", label: "Weather & Fertilizer" },
  { id: "verification-schemes", label: "Verification & Schemes" },
  { id: "about", label: "About" },
];

const toolPages: Array<{ id: ToolPageId; label: string; icon: LucideIcon; desc: string }> = [
  {
    id: "doctor",
    label: "Crop Doctor",
    icon: ScanLine,
    desc: "Dual-signal leaf disease vision & symptom classification",
  },
  {
    id: "weather",
    label: "Weather Intelligence",
    icon: CloudSun,
    desc: "Microclimate forecasts & fungal infection heuristics",
  },
  {
    id: "fertilizer",
    label: "Fertilizer Planner",
    icon: FlaskConical,
    desc: "Deterministic per-acre nutrient dosage calculations",
  },
  {
    id: "products",
    label: "Product Verification",
    icon: ShieldCheck,
    desc: "SQLite registry check for authentic input batches",
  },
  {
    id: "schemes",
    label: "Government Schemes",
    icon: BookOpen,
    desc: "Public agricultural subsidies matched to farm size",
  },
];

function ContinuousHomePage({
  openTool,
  health,
}: {
  openTool: (tool: ToolPageId) => void;
  health: ApiHealth | null;
}) {
  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (!el) return;
    const headerOffset = 90;
    const elementPosition = el.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
    window.scrollTo({
      top: offsetPosition,
      behavior: "smooth",
    });
  };

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.querySelectorAll(".homepage-section").forEach((el) => {
        el.classList.add("section-revealed");
      });
      return;
    }

    const sections = document.querySelectorAll(".homepage-section");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("section-revealed");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -30px 0px" }
    );

    sections.forEach((sec) => observer.observe(sec));
    return () => observer.disconnect();
  }, []);

  return (
    <>
      {/* 1. HERO SECTION */}
      <section id="overview" className="hero-section">
        <div className="hero-copy">
          {/* Phase 5: Zero botanical overlap with hero headline, eyebrow, description, or CTA buttons */}
          <div className="eyebrow-accent">
            <Sprout size={13} style={{ display: "inline", marginRight: 5, verticalAlign: -2 }} />
            Agricultural Intelligence Platform
          </div>

          <h1 className="hero-headline">
            Grow with <span className="home-hero__accent">Confidence.</span>
          </h1>

          <p className="hero-description">
            AI-powered intelligence for smarter agriculture. Grounded diagnostics,
            local weather risks, deterministic fertilizer guidance, and verified public schemes
            in one connected workspace.
          </p>

          <div className="hero-actions">
            <Button onClick={() => openTool("doctor")}>
              Start a diagnosis <ArrowRight size={15} />
            </Button>
            <Button variant="secondary" onClick={() => scrollToSection("tools")}>
              Explore agricultural tools <ArrowDown size={14} />
            </Button>
          </div>
        </div>

        {/* Hero Crop Botanical Artwork with Flowering Foliage - Single far-right accent */}
        <div className="hero-preview botanical-card-wrap">
          <BotanicalLeaf position="outer-top-right" variant="flower-branch" />
          <HeroCropIllustration />
        </div>
      </section>

      {/* 2. AGRICULTURAL TOOLS */}
      <section id="tools" className="homepage-section">
        <div className="section-head">
          <div>
            <div className="eyebrow">Agricultural Tools</div>
            <h2>Five integrated intelligence engines for daily farm decisions</h2>
          </div>
          <p>Every tool connects to verifiable models, local databases, or official sources.</p>
        </div>

        <div className="tools-editorial-grid">
          {/* Tool 1: Crop Doctor (with Botanical decoration visibly beside outer left edge) */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-left" variant="side-bloom" />
            <div className="tool-card" onClick={() => openTool("doctor")} role="button" tabIndex={0}>
              <div className="tool-card-icon">
                <ScanLine size={19} />
              </div>
              <h3>Crop Doctor</h3>
              <p>Computer vision leaf disease detection with MobileNetV2, Random Forest symptom classification, and Grad-CAM visual heatmaps.</p>
              <div className="tool-card-action">
                Open full tool <ArrowRight size={13} />
              </div>
            </div>
          </div>

          {/* Tool 2: Weather Intelligence (with Botanical flower branch peeking outer top right) */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="outer-top-right" variant="flower-branch" />
            <div className="tool-card" onClick={() => openTool("weather")} role="button" tabIndex={0}>
              <div className="tool-card-icon">
                <CloudSun size={19} />
              </div>
              <h3>Weather Intelligence</h3>
              <p>Local agricultural weather forecasts paired with deterministic rules evaluating fungal infection and heat stress risks.</p>
              <div className="tool-card-action">
                Open full tool <ArrowRight size={13} />
              </div>
            </div>
          </div>

          {/* Tool 3: Fertilizer Planner (with Botanical sprig visibly beside outer right edge) */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-right" variant="side-sprig" />
            <div className="tool-card" onClick={() => openTool("fertilizer")} role="button" tabIndex={0}>
              <div className="tool-card-icon">
                <FlaskConical size={19} />
              </div>
              <h3>Fertilizer Planner</h3>
              <p>Agronomic per-acre lookup table calculating exact fertilizer requirements, dosage, and indicative costs for your crop deficiency.</p>
              <div className="tool-card-action">
                Open full tool <ArrowRight size={13} />
              </div>
            </div>
          </div>

          {/* Tool 4: Product Verification (with Botanical blossom sprig peeking outer bottom left) */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="outer-bottom-left" variant="blossom-sprig" />
            <div className="tool-card" onClick={() => openTool("products")} role="button" tabIndex={0}>
              <div className="tool-card-icon">
                <ShieldCheck size={19} />
              </div>
              <h3>Product Verification</h3>
              <p>Validate packaging QR codes and product serial numbers against the local SQLite registry to verify genuine agricultural inputs.</p>
              <div className="tool-card-action">
                Open full tool <ArrowRight size={13} />
              </div>
            </div>
          </div>

          {/* Tool 5: Government Schemes (with Botanical flowering stem peeking outer bottom right) */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="outer-bottom-right" variant="flowering-stem" />
            <div className="tool-card" onClick={() => openTool("schemes")} role="button" tabIndex={0}>
              <div className="tool-card-icon">
                <BookOpen size={19} />
              </div>
              <h3>Government Schemes</h3>
              <p>Match your farm land size, state, crop, and support category with verified government subsidies and official application links.</p>
              <div className="tool-card-action">
                Open full tool <ArrowRight size={13} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. HOW AGRIVISION WORKS */}
      <section id="workflow" className="homepage-section">
        <div className="section-head">
          <div>
            <div className="eyebrow">System Architecture</div>
            <h2>How AgriVision works</h2>
          </div>
          <p>Transparent, model-backed reasoning from input to field recommendation.</p>
        </div>

        <div className="workflow-grid">
          {/* Step 1 with Botanical accent visibly beside left side */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-left" variant="side-sprig" />
            <div className="workflow-step">
              <div className="workflow-step-num">01</div>
              <h4>Observe &amp; Capture</h4>
              <p>Submit close-up leaf photographs, enter observed visual symptoms, or specify farm coordinates for microclimate intelligence.</p>
            </div>
          </div>

          {/* Step 2 with Botanical accent peeking outer top right */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="outer-top-right" variant="flower-branch" />
            <div className="workflow-step">
              <div className="workflow-step-num">02</div>
              <h4>Verified Engines</h4>
              <p>Fine-tuned MobileNetV2 CNN, Random Forest symptom classifier, Open-Meteo risk rules, and SQLite registries process your query.</p>
            </div>
          </div>

          {/* Step 3 with Botanical accent visibly beside right side */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-right" variant="side-bloom" />
            <div className="workflow-step">
              <div className="workflow-step-num">03</div>
              <h4>Actionable Guidance</h4>
              <p>Receive Grad-CAM visual heatmaps, per-acre fertilizer dosage calculations, and verified official scheme links.</p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. CROP INTELLIGENCE — FARMER-FOCUSED CROP HEALTH INSIGHTS */}
      <section id="crop-intelligence" className="homepage-section">
        <div className="section-head">
          <div>
            <div className="eyebrow">CROP HEALTH INSIGHTS</div>
            <h2>Understand what your crop is telling you</h2>
          </div>
          <p>Turn visual crop cues and observed symptoms into clear, actionable guidance.</p>
        </div>

        <div className="botanical-card-wrap">
          {/* Dual corner botanical framing with flower branch and blossom sprig */}
          <BotanicalLeaf position="outer-top-right" variant="flower-branch" />
          <BotanicalLeaf position="outer-bottom-left" variant="blossom-sprig" />

          <div className="feature-spotlight">
            <div className="feature-spotlight-copy">
              <h3>Turn crop signs into clearer insights</h3>
              <p>
                Explore potential plant health issues from leaf photographs or observed symptoms to guide timely field care.
              </p>

              <div className="feature-key-points">
                <div className="feature-key-point">
                  <CheckCircle2 size={16} />
                  <span>
                    <strong>Image-based assessment</strong> — Upload leaf photos to identify potential health issues.
                  </span>
                </div>
                <div className="feature-key-point">
                  <CheckCircle2 size={16} />
                  <span>
                    <strong>Symptom-based guidance</strong> — Share observed field symptoms when photos are unavailable.
                  </span>
                </div>
                <div className="feature-key-point">
                  <CheckCircle2 size={16} />
                  <span>
                    <strong>Visual context</strong> — Inspect highlighted regions that influenced the model's assessment.
                  </span>
                </div>
              </div>

              <Button onClick={() => openTool("doctor")}>
                Explore Crop Doctor <ArrowRight size={15} />
              </Button>
            </div>

            {/* Farmer-focused crop health inspection preview - clean dedicated presentation */}
            <CropHealthInspectionPreview />
          </div>
        </div>
      </section>

      {/* 5. WEATHER & FERTILIZER SPOTLIGHT */}
      <section id="weather-fertilizer" className="homepage-section">
        <div className="section-head">
          <div>
            <div className="eyebrow">Farm Decision Engines</div>
            <h2>Weather intelligence &amp; fertilizer planning</h2>
          </div>
          <p>Deterministic calculations that safeguard yields and prevent over-fertilization.</p>
        </div>

        <div className="twin-pillars-grid">
          {/* Weather Pillar with Botanical accent beside left edge and outer top right */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-left" variant="side-bloom" />
            <BotanicalLeaf position="outer-top-right" variant="flower-branch" />
            <div className="pillar-card">
              <span className="eyebrow">
                <CloudSun size={13} style={{ verticalAlign: -2, marginRight: 4 }} /> Open-Meteo Integration
              </span>
              <h3>Local weather risk intelligence</h3>
              <p>
                Monitors ambient temperature, relative humidity, and precipitation against agronomic thresholds
                to flag elevated fungal infection risks and extreme heat stress before they spread.
              </p>
              <div className="pillar-preview-box">
                <div className="preview-stat-label">Calculated Signals</div>
                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  <span className="status-pill">Fungal risk evaluator</span>
                  <span className="status-pill">Heat stress monitor</span>
                  <span className="status-pill">Manual observation mode</span>
                </div>
              </div>
              <Button variant="secondary" onClick={() => openTool("weather")}>
                Open Weather tool <ArrowRight size={14} />
              </Button>
            </div>
          </div>

          {/* Fertilizer Pillar with Botanical accent beside right edge and outer bottom left */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-right" variant="side-sprig" />
            <BotanicalLeaf position="outer-bottom-left" variant="flowering-stem" />
            <div className="pillar-card">
              <span className="eyebrow">
                <FlaskConical size={13} style={{ verticalAlign: -2, marginRight: 4 }} /> Per-Acre Lookup Table
              </span>
              <h3>Deterministic fertilizer planner</h3>
              <p>
                Eliminates guesswork with verified per-acre agronomic lookup rates. Select your crop
                and deficiency to receive precise nutrient quantities and indicative cost estimates.
              </p>
              <div className="pillar-preview-box">
                <div className="preview-stat-label">Calculated Metrics</div>
                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  <span className="status-pill">Dosage per acre</span>
                  <span className="status-pill">Total bag quantity</span>
                  <span className="status-pill">Cost in INR (₹)</span>
                </div>
              </div>
              <Button variant="secondary" onClick={() => openTool("fertilizer")}>
                Open Fertilizer Planner <ArrowRight size={14} />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 6. VERIFICATION & SCHEMES */}
      <section id="verification-schemes" className="homepage-section">
        <div className="section-head">
          <div>
            <div className="eyebrow">Farm Protection &amp; Support</div>
            <h2>Input verification &amp; government schemes</h2>
          </div>
          <p>Guard against counterfeit inputs and access verified public subsidy schemes.</p>
        </div>

        <div className="twin-pillars-grid">
          {/* Product Verification Pillar with Botanical accent */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-left" variant="side-sprig" />
            <BotanicalLeaf position="outer-top-left" variant="blossom-sprig" />
            <div className="pillar-card">
              <span className="eyebrow">
                <ShieldCheck size={13} style={{ verticalAlign: -2, marginRight: 4 }} /> SQLite Input Registry
              </span>
              <h3>Product authenticity validator</h3>
              <p>
                Scan product QR labels via computer vision or look up manufacturer batch codes
                against the SQLite registry to verify genuine seeds, fertilizers, and crop chemicals.
              </p>
              <div className="pillar-preview-box">
                <div className="preview-stat-label">Registry Features</div>
                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  <span className="status-pill">OpenCV QR decoding</span>
                  <span className="status-pill">Batch &amp; Expiry audit</span>
                  <span className="status-pill">Registration verification</span>
                </div>
              </div>
              <Button variant="secondary" onClick={() => openTool("products")}>
                Verify product codes <ArrowRight size={14} />
              </Button>
            </div>
          </div>

          {/* Government Schemes Pillar with Botanical accent */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-right" variant="side-bloom" />
            <BotanicalLeaf position="outer-bottom-right" variant="flower-branch" />
            <div className="pillar-card">
              <span className="eyebrow">
                <BookOpen size={13} style={{ verticalAlign: -2, marginRight: 4 }} /> Scheme Matcher
              </span>
              <h3>Government scheme matching</h3>
              <p>
                Filter central and state public agriculture subsidies matching your farm land size,
                region, and crops with direct official government portal links.
              </p>
              <div className="pillar-preview-box">
                <div className="preview-stat-label">Scheme Categories</div>
                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  <span className="status-pill">Financial income support</span>
                  <span className="status-pill">Crop insurance</span>
                  <span className="status-pill">Irrigation &amp; infrastructure</span>
                </div>
              </div>
              <Button variant="secondary" onClick={() => openTool("schemes")}>
                Find matching schemes <ArrowRight size={14} />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 7. ABOUT SECTION */}
      <section id="about" className="homepage-section">
        <div className="section-head">
          <div>
            <div className="eyebrow">Platform Philosophy</div>
            <h2>About AgriVision</h2>
          </div>
          <p>Practical agricultural intelligence, grounded in verifiable models and local data.</p>
        </div>

        <div className="split-grid">
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="outer-top-left" variant="flower-branch" />
            <Card>
              <div className="card-title">
                <div>
                  <h2>Mission &amp; Principles</h2>
                  <p>AI assists decisions; it does not replace agricultural judgment.</p>
                </div>
              </div>

              <div className="about-point">
                <div className="about-point-icon"><ScanLine size={16} /></div>
                <div>
                  <strong>Vision &amp; Symptom Understanding</strong>
                  <p>Combines visual leaf cues with farmer observations to provide transparent diagnostics.</p>
                </div>
              </div>

              <div className="about-point">
                <div className="about-point-icon"><CloudSun size={16} /></div>
                <div>
                  <strong>Deterministic Calculations</strong>
                  <p>Fertilizer tables, weather risk signals, and subsidy matching follow strict agricultural rules rather than guesses.</p>
                </div>
              </div>

              <div className="about-point">
                <div className="about-point-icon"><ShieldCheck size={16} /></div>
                <div>
                  <strong>Open Data &amp; Verification</strong>
                  <p>Authentic product databases and verified official government scheme links protect farmers from misinformation.</p>
                </div>
              </div>
            </Card>
          </div>

          <div className="botanical-card-wrap">
            <BotanicalLeaf position="outer-top-right" variant="side-bloom" />
            <Card>
              <div className="card-title">
                <div>
                  <h2>Live Service Health</h2>
                  <p>Real-time connectivity to the AgriVision backend.</p>
                </div>
              </div>

              <div className="risk-row">
                <span>FastAPI Backend API</span>
                <span className="status-pill">{health ? health.status : "Offline / Connecting"}</span>
              </div>

              {health?.services &&
                Object.entries(health.services).map(([service, state]) => (
                  <div className="risk-row" key={service}>
                    <span style={{ textTransform: "capitalize" }}>{service.replace(/_/g, " ")}</span>
                    <span className="status-pill">{String(state)}</span>
                  </div>
                ))}

              <p className="home-footnote">
                API secrets remain on the backend. Weather APIs and optional intelligence features require server environment variables.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* 8. FINAL CALL TO ACTION with Botanical Framing */}
      <div className="botanical-card-wrap" style={{ marginTop: 24 }}>
        <BotanicalLeaf position="outer-top-right" variant="flower-branch" />
        <BotanicalLeaf position="outer-bottom-left" variant="blossom-sprig" />
        <div id="cta" className="cta-banner">
          <div>
            <h3>Ready to analyze crop health on your farm?</h3>
            <p>Upload a leaf photograph or enter field observations to evaluate plant diseases with transparent guidance.</p>
          </div>
          <Button onClick={() => openTool("doctor")}>
            Start a Diagnosis <ArrowRight size={15} />
          </Button>
        </div>
      </div>
    </>
  );
}

export default function App() {
  const [currentView, setCurrentView] = useState<AppView>("home");
  const [activeSection, setActiveSection] = useState<string>("overview");
  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [mobileToolsExpanded, setMobileToolsExpanded] = useState(false);
  const [megaMenuOpen, setMegaMenuOpen] = useState(false);

  // Health check on mount
  useEffect(() => {
    const controller = new AbortController();
    get<ApiHealth>("/api/health", controller.signal)
      .then((data) => setHealth(data))
      .catch(() => setHealth(null));
    return () => controller.abort();
  }, []);

  // Section Observer for active navbar highlighting
  useEffect(() => {
    if (currentView !== "home") return;

    const sectionIds = [
      "overview",
      "tools",
      "workflow",
      "crop-intelligence",
      "weather-fertilizer",
      "verification-schemes",
      "about",
    ];

    const sectionElements = sectionIds
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => Boolean(el));

    if (sectionElements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntries = entries.filter((e) => e.isIntersecting);
        if (visibleEntries.length > 0) {
          visibleEntries.sort(
            (a, b) => Math.abs(a.boundingClientRect.top) - Math.abs(b.boundingClientRect.top)
          );
          setActiveSection(visibleEntries[0].target.id);
        }
      },
      {
        rootMargin: "-20% 0px -40% 0px",
        threshold: [0, 0.2, 0.5, 0.8],
      }
    );

    sectionElements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [currentView]);

  const navigateToSection = (sectionId: string) => {
    if (currentView !== "home") {
      setCurrentView("home");
      setTimeout(() => {
        const el = document.getElementById(sectionId);
        if (el) {
          const headerOffset = 90;
          const pos = el.getBoundingClientRect().top + window.pageYOffset - headerOffset;
          window.scrollTo({ top: pos, behavior: "smooth" });
        }
      }, 80);
    } else {
      const el = document.getElementById(sectionId);
      if (el) {
        const headerOffset = 90;
        const pos = el.getBoundingClientRect().top + window.pageYOffset - headerOffset;
        window.scrollTo({ top: pos, behavior: "smooth" });
      }
    }
    setActiveSection(sectionId);
    setMobileNavOpen(false);
    setMegaMenuOpen(false);
  };

  const openTool = (tool: ToolPageId) => {
    setCurrentView(tool);
    setMobileNavOpen(false);
    setMegaMenuOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const returnToHome = () => {
    setCurrentView("home");
    setMobileNavOpen(false);
    setMegaMenuOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="app-shell">
      {/* Sticky Top Navigation Bar - 3 Distinct Areas: Brand, Nav Pill, Separate Get Started */}
      <header className="site-header">
        <div className="header-navbar-row">
          {/* 1. Brand: AgriVision logo and wordmark on the left */}
          <a
            className="brand"
            href="#"
            onClick={(e) => {
              e.preventDefault();
              returnToHome();
            }}
          >
            <span className="brand-icon">
              <Sprout size={18} />
            </span>
            <span className="brand-text">AgriVision</span>
            <span className="brand-tag">Intelligence</span>
          </a>

          {/* 2. Navigation Container (Standalone Pill) */}
          {currentView === "home" ? (
            /* Scroll-aware links with Agricultural Tools mega menu on homepage */
            <nav className="nav-pill-container" aria-label="Main Navigation">
              {/* Overview */}
              <button
                className={`nav-link${activeSection === "overview" ? " active" : ""}`}
                onClick={() => navigateToSection("overview")}
              >
                Overview
              </button>

              {/* Agricultural Tools with Expandable Mega Menu */}
              <div
                className={`nav-mega-wrap${megaMenuOpen ? " is-open" : ""}`}
                onMouseEnter={() => setMegaMenuOpen(true)}
                onMouseLeave={() => setMegaMenuOpen(false)}
              >
                <button
                  className={`nav-link${activeSection === "tools" || activeSection === "workflow" ? " active" : ""}`}
                  onClick={() => {
                    setMegaMenuOpen((prev) => !prev);
                    navigateToSection("tools");
                  }}
                  aria-expanded={megaMenuOpen}
                  aria-haspopup="true"
                >
                  <span>Agricultural Tools</span>
                  <ChevronDown size={11} className="nav-link-dropdown-arrow" />
                </button>

                <ToolsMegaMenu
                  isOpen={megaMenuOpen}
                  onClose={() => setMegaMenuOpen(false)}
                  onSelectTool={openTool}
                  onScrollToTools={() => navigateToSection("tools")}
                />
              </div>

              {/* Crop Intelligence */}
              <button
                className={`nav-link${activeSection === "crop-intelligence" ? " active" : ""}`}
                onClick={() => navigateToSection("crop-intelligence")}
              >
                Crop Intelligence
              </button>

              {/* Weather & Fertilizer */}
              <button
                className={`nav-link${activeSection === "weather-fertilizer" ? " active" : ""}`}
                onClick={() => navigateToSection("weather-fertilizer")}
              >
                Weather &amp; Fertilizer
              </button>

              {/* Verification & Schemes */}
              <button
                className={`nav-link${activeSection === "verification-schemes" ? " active" : ""}`}
                onClick={() => navigateToSection("verification-schemes")}
              >
                Verification &amp; Schemes
              </button>

              {/* About */}
              <button
                className={`nav-link${activeSection === "about" ? " active" : ""}`}
                onClick={() => navigateToSection("about")}
              >
                About
              </button>
            </nav>
          ) : (
            /* Dedicated tool page navigation */
            <nav className="nav-pill-container" aria-label="Tool Navigation">
              <button className="tool-return-btn" onClick={returnToHome}>
                ← Back to Overview
              </button>
              {toolPages.map(({ id, label }) => (
                <button
                  key={id}
                  className={`nav-link${currentView === id ? " active" : ""}`}
                  onClick={() => openTool(id)}
                >
                  {label}
                </button>
              ))}
            </nav>
          )}

          {/* 3. Get Started Button: Separate area outside the navigation container on the right */}
          <div className="header-cta-area">
            <button
              className="get-started-btn"
              onClick={() => openTool("doctor")}
            >
              Get Started
            </button>

            <button
              className="mobile-menu-toggle"
              aria-label="Open navigation menu"
              onClick={() => setMobileNavOpen(true)}
            >
              <Menu size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer Menu */}
      {mobileNavOpen ? (
        <>
          <div className="mobile-nav-scrim" onClick={() => setMobileNavOpen(false)} />
          <aside className="mobile-nav-panel">
            <div className="mobile-nav-header">
              <div className="brand">
                <span className="brand-icon"><Sprout size={16} /></span>
                <span className="brand-text">AgriVision</span>
              </div>
              <button
                className="mobile-menu-toggle"
                style={{ display: "inline-flex" }}
                aria-label="Close menu"
                onClick={() => setMobileNavOpen(false)}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ marginBottom: 16 }}>
              <span className="eyebrow" style={{ paddingLeft: 14 }}>Homepage Sections</span>
              <nav className="mobile-nav-list">
                {homepageSections.map(({ id, label }) => (
                  <button
                    key={id}
                    className={`mobile-nav-item${currentView === "home" && activeSection === id ? " active" : ""}`}
                    onClick={() => navigateToSection(id)}
                  >
                    <span>{label}</span>
                  </button>
                ))}
              </nav>
            </div>

            <div style={{ marginBottom: 16 }}>
              <button
                className="mobile-nav-item"
                style={{ fontWeight: 600, justifyContent: "space-between" }}
                onClick={() => setMobileToolsExpanded((prev) => !prev)}
              >
                <span>Agricultural Tools Suite</span>
                <ChevronDown
                  size={16}
                  style={{
                    transform: mobileToolsExpanded ? "rotate(180deg)" : "rotate(0deg)",
                    transition: "transform 0.2s ease",
                  }}
                />
              </button>

              {mobileToolsExpanded ? (
                <nav className="mobile-nav-list" style={{ paddingLeft: 12, marginTop: 6 }}>
                  {toolPages.map(({ id, label, icon: Icon, desc }) => (
                    <button
                      key={id}
                      className={`mobile-nav-item${currentView === id ? " active" : ""}`}
                      onClick={() => openTool(id)}
                      style={{ flexDirection: "column", alignItems: "flex-start", gap: 3 }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <Icon size={16} />
                        <span style={{ fontWeight: 600 }}>{label}</span>
                      </div>
                      <span style={{ fontSize: 12, color: "var(--color-muted)", paddingLeft: 24 }}>
                        {desc}
                      </span>
                    </button>
                  ))}
                </nav>
              ) : null}
            </div>

            <div style={{ marginTop: "auto", paddingTop: 16 }}>
              <button
                className="get-started-btn"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() => openTool("doctor")}
              >
                Get Started with Diagnostics
              </button>
            </div>
          </aside>
        </>
      ) : null}

      {/* Main Content Area */}
      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
          >
            {currentView === "home" ? (
              <ContinuousHomePage openTool={openTool} health={health} />
            ) : null}
            {currentView === "doctor" ? <CropDoctor /> : null}
            {currentView === "weather" ? <WeatherPage /> : null}
            {currentView === "fertilizer" ? <FertilizerPage /> : null}
            {currentView === "products" ? <ProductPage /> : null}
            {currentView === "schemes" ? <SchemesPage /> : null}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Redesigned Orchara-Inspired Editorial Landscape Footer */}
      <Footer onNavigateSection={navigateToSection} onOpenTool={openTool} />
    </div>
  );
}
