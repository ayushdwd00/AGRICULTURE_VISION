import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Lenis from "lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ArrowDown,
  ArrowRight,
  BookOpen,
  Camera,
  CheckCircle2,
  ChevronDown,
  CloudSun,
  FlaskConical,
  MapPin,
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

gsap.registerPlugin(ScrollTrigger);

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
  onActiveSection,
  scrollToSection,
}: {
  openTool: (tool: ToolPageId) => void;
  health: ApiHealth | null;
  onActiveSection: (id: string) => void;
  scrollToSection: (id: string) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const ctx = gsap.context(() => {
      // 1. Synchronized Active Section Tracking using ScrollTrigger
      const sectionIds = [
        "overview",
        "tools",
        "workflow",
        "crop-intelligence",
        "weather-fertilizer",
        "verification-schemes",
        "about",
      ];

      sectionIds.forEach((id) => {
        const el = document.getElementById(id);
        if (!el) return;
        ScrollTrigger.create({
          trigger: el,
          start: "top 40%",
          end: "bottom 40%",
          onEnter: () => onActiveSection(id),
          onEnterBack: () => onActiveSection(id),
        });
      });

      if (prefersReducedMotion) {
        // Reduced motion: ensure all sections, cards, and decorations are immediately visible
        gsap.set(
          ".homepage-section, .section-head, .tools-featured-card, .tool-utility-card, .tool-card, .workflow-timeline-step, .workflow-step, .pillar-card, .split-card, .botanical-leaf-wrap, .crop-editorial-left, .crop-inspection-card, .weather-module-card, .cultivation-module-card, .landscape-panorama-frame, .cta-banner",
          { opacity: 1, y: 0, x: 0, scale: 1, clearProps: "all" }
        );
        return;
      }

      // 2. Section Entrances: Fade in and gently move section content into place as it enters viewport
      gsap.utils.toArray<HTMLElement>(".homepage-section").forEach((sec) => {
        gsap.fromTo(
          sec,
          { opacity: 0, y: 28 },
          {
            opacity: 1,
            y: 0,
            duration: 0.95,
            ease: "power2.out",
            scrollTrigger: {
              trigger: sec,
              start: "top 88%",
              once: true,
            },
          }
        );
      });

      // 3. Section Headings: Subtle entrance animations while preserving existing typography
      gsap.utils.toArray<HTMLElement>(".section-head").forEach((head) => {
        gsap.fromTo(
          head,
          { opacity: 0, y: 18 },
          {
            opacity: 1,
            y: 0,
            duration: 0.85,
            ease: "power2.out",
            scrollTrigger: {
              trigger: head,
              start: "top 88%",
              once: true,
            },
          }
        );
      });

      // 4. Agricultural Tools Featured Lead & Utility Cards Reveal
      gsap.fromTo(
        ".tools-featured-card",
        { opacity: 0, y: 24 },
        {
          opacity: 1,
          y: 0,
          duration: 0.85,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".tools-editorial-layout",
            start: "top 85%",
            once: true,
          },
        }
      );

      gsap.fromTo(
        ".tools-utility-grid .tool-utility-card, .tools-editorial-grid .tool-card",
        { opacity: 0, y: 20 },
        {
          opacity: 1,
          y: 0,
          duration: 0.85,
          stagger: 0.08,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".tools-utility-grid",
            start: "top 85%",
            once: true,
          },
        }
      );

      // 5. Workflow Timeline Steps Stagger
      gsap.fromTo(
        ".workflow-timeline .workflow-timeline-step, .workflow-grid .workflow-step",
        { opacity: 0, y: 22 },
        {
          opacity: 1,
          y: 0,
          duration: 0.85,
          stagger: 0.1,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".workflow-timeline",
            start: "top 85%",
            once: true,
          },
        }
      );

      // 6. Crop Health Insights Editorial Spread & Inspection Leaf
      gsap.fromTo(
        "#crop-intelligence .crop-editorial-left",
        { opacity: 0, x: -18 },
        {
          opacity: 1,
          x: 0,
          duration: 0.9,
          ease: "power2.out",
          scrollTrigger: {
            trigger: "#crop-intelligence",
            start: "top 82%",
            once: true,
          },
        }
      );

      gsap.fromTo(
        "#crop-intelligence .crop-inspection-card",
        { opacity: 0, x: 18 },
        {
          opacity: 1,
          x: 0,
          duration: 0.9,
          ease: "power2.out",
          scrollTrigger: {
            trigger: "#crop-intelligence",
            start: "top 82%",
            once: true,
          },
        }
      );

      gsap.fromTo(
        "#crop-intelligence .inspection-leaf-svg",
        { opacity: 0.75, scale: 0.95 },
        {
          opacity: 1,
          scale: 1,
          duration: 1.0,
          ease: "power2.out",
          scrollTrigger: {
            trigger: "#crop-intelligence",
            start: "top 80%",
            once: true,
          },
        }
      );

      // 7. Aerial Farmland Landscape Panorama & Decision Engines
      gsap.fromTo(
        ".landscape-panorama-frame",
        { opacity: 0, scale: 0.98 },
        {
          opacity: 1,
          scale: 1,
          duration: 0.95,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".landscape-panorama-wrap",
            start: "top 85%",
            once: true,
          },
        }
      );

      gsap.fromTo(
        ".weather-cultivation-split > div, .twin-pillars-grid .pillar-card",
        { opacity: 0, y: 24 },
        {
          opacity: 1,
          y: 0,
          duration: 0.85,
          stagger: 0.12,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".weather-cultivation-split",
            start: "top 85%",
            once: true,
          },
        }
      );

      // 8. Split Grid (About Section)
      gsap.fromTo(
        ".split-grid .botanical-card-wrap",
        { opacity: 0, y: 22 },
        {
          opacity: 1,
          y: 0,
          duration: 0.85,
          stagger: 0.1,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".split-grid",
            start: "top 85%",
            once: true,
          },
        }
      );

      // 9. CTA Banner
      gsap.fromTo(
        "#cta",
        { opacity: 0, y: 20 },
        {
          opacity: 1,
          y: 0,
          duration: 0.85,
          ease: "power2.out",
          scrollTrigger: {
            trigger: "#cta",
            start: "top 88%",
            once: true,
          },
        }
      );

      // 10. Botanical Foliage: Restrained gentle reveal
      gsap.utils.toArray<HTMLElement>(".botanical-leaf-wrap").forEach((leaf) => {
        gsap.fromTo(
          leaf,
          { opacity: 0, scale: 0.94 },
          {
            opacity: 1,
            scale: 1,
            duration: 0.95,
            ease: "power2.out",
            scrollTrigger: {
              trigger: leaf,
              start: "top 92%",
              once: true,
            },
          }
        );
      });

      // 11. Botanical Parallax on Desktop (wide screens >= 1024px only)
      if (window.innerWidth >= 1024) {
        gsap.utils.toArray<HTMLElement>(".botanical-leaf-wrap").forEach((leaf) => {
          gsap.to(leaf, {
            yPercent: -10,
            ease: "none",
            scrollTrigger: {
              trigger: leaf,
              start: "top bottom",
              end: "bottom top",
              scrub: 1.6,
            },
          });
        });
      }
    }, containerRef);

    return () => ctx.revert();
  }, [onActiveSection]);

  return (
    <div ref={containerRef}>
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

        <div className="tools-editorial-layout">
          {/* Featured Anchor: Crop Doctor with Unsplash Crop Photography */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-left" variant="side-bloom" />
            <div className="tools-featured-card">
              <div className="tools-featured-photo-wrap">
                <div className="editorial-photo-frame tools-featured-photo-frame">
                  <img
                    src="/images/crop-photography.jpg"
                    alt="Field crop foliage close-up showing leaf structure and health conditions"
                    className="editorial-photo-img"
                    loading="lazy"
                  />
                </div>
                <div className="editorial-photo-caption">
                  <span>
                    <Camera size={12} /> Crop foliage scouting
                  </span>
                  <span className="editorial-photo-source">Unsplash</span>
                </div>
              </div>

              <div className="tools-featured-copy">
                <span className="tools-featured-badge">Dual-Signal Vision Engine</span>
                <h3>Crop Doctor</h3>
                <p>
                  Combines visual leaf inspection with farmer symptom observations. Uses MobileNetV2
                  transfer learning to identify disease markers and Random Forest for symptom heuristics.
                </p>
                <div className="tools-tech-pill-row">
                  <span className="tools-tech-pill">MobileNetV2 CNN</span>
                  <span className="tools-tech-pill">Grad-CAM Heatmaps</span>
                  <span className="tools-tech-pill">Symptom Classifier</span>
                </div>
                <div>
                  <Button onClick={() => openTool("doctor")}>
                    Launch Crop Doctor <ArrowRight size={14} />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Secondary 2x2 Utility Grid for Other Engines */}
          <div className="tools-utility-grid">
            {/* Tool 2: Weather Intelligence */}
            <div
              className="tool-utility-card"
              onClick={() => openTool("weather")}
              role="button"
              tabIndex={0}
            >
              <div className="tool-utility-head">
                <div className="tool-utility-icon">
                  <CloudSun size={18} />
                </div>
                <span className="tool-utility-tag">Open-Meteo</span>
              </div>
              <h3>Weather Intelligence</h3>
              <p>
                Microclimate risk forecasting evaluating temperature, relative humidity, and rainfall
                thresholds for fungal germination and heat stress.
              </p>
              <div className="tool-utility-action">
                Open weather tool <ArrowRight size={12} />
              </div>
            </div>

            {/* Tool 3: Fertilizer Planner */}
            <div
              className="tool-utility-card"
              onClick={() => openTool("fertilizer")}
              role="button"
              tabIndex={0}
            >
              <div className="tool-utility-head">
                <div className="tool-utility-icon">
                  <FlaskConical size={18} />
                </div>
                <span className="tool-utility-tag">Per-Acre Rates</span>
              </div>
              <h3>Fertilizer Planner</h3>
              <p>
                Agronomic lookup table calculating exact nutrient deficiency dosages, required bag quantities,
                and indicative input costs for your acreage.
              </p>
              <div className="tool-utility-action">
                Open planner <ArrowRight size={12} />
              </div>
            </div>

            {/* Tool 4: Product Verification */}
            <div
              className="tool-utility-card"
              onClick={() => openTool("products")}
              role="button"
              tabIndex={0}
            >
              <div className="tool-utility-head">
                <div className="tool-utility-icon">
                  <ShieldCheck size={18} />
                </div>
                <span className="tool-utility-tag">SQLite Registry</span>
              </div>
              <h3>Product Verification</h3>
              <p>
                Verify packaging QR labels and product serial codes against the local registry
                to protect against counterfeit agricultural chemicals and seeds.
              </p>
              <div className="tool-utility-action">
                Verify packaging <ArrowRight size={12} />
              </div>
            </div>

            {/* Tool 5: Government Schemes */}
            <div
              className="tool-utility-card"
              onClick={() => openTool("schemes")}
              role="button"
              tabIndex={0}
            >
              <div className="tool-utility-head">
                <div className="tool-utility-icon">
                  <BookOpen size={18} />
                </div>
                <span className="tool-utility-tag">Subsidies</span>
              </div>
              <h3>Government Schemes</h3>
              <p>
                Match farm acreage, state, crop, and support categories with verified central and state
                public subsidy schemes and official portals.
              </p>
              <div className="tool-utility-action">
                Find subsidies <ArrowRight size={12} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. HOW AGRIVISION WORKS — ARCHITECTURAL PROCESS TIMELINE */}
      <section id="workflow" className="homepage-section">
        <div className="section-head">
          <div>
            <div className="eyebrow">System Architecture</div>
            <h2>How AgriVision works</h2>
          </div>
          <p>Transparent, model-backed reasoning from input to field recommendation.</p>
        </div>

        <div className="workflow-timeline">
          {/* Step 1 with Botanical accent peeking outer top left */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="outer-top-left" variant="side-sprig" />
            <div className="workflow-timeline-step">
              <div className="workflow-num-row">
                <span className="workflow-num-large">01</span>
                <span className="workflow-step-badge">Field Ingestion</span>
              </div>
              <h4>Observe &amp; Capture</h4>
              <p>
                Submit close-up leaf photographs, enter observed visual symptoms, or specify farm coordinates
                for local microclimate intelligence.
              </p>
            </div>
          </div>

          {/* Step 2 */}
          <div className="workflow-timeline-step">
            <div className="workflow-num-row">
              <span className="workflow-num-large">02</span>
              <span className="workflow-step-badge">Engine Evaluation</span>
            </div>
            <h4>Deterministic &amp; Neural Inference</h4>
            <p>
              Fine-tuned MobileNetV2 CNN, Random Forest symptom classifier, Open-Meteo risk rules, and SQLite
              registries process your query simultaneously.
            </p>
          </div>

          {/* Step 3 with Botanical accent beside right */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-right" variant="side-bloom" />
            <div className="workflow-timeline-step">
              <div className="workflow-num-row">
                <span className="workflow-num-large">03</span>
                <span className="workflow-step-badge">Field Action</span>
              </div>
              <h4>Actionable Guidance</h4>
              <p>
                Receive Grad-CAM visual heatmaps, per-acre fertilizer dosage calculations, and verified official
                scheme links for immediate farm care.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. CROP INTELLIGENCE — FARMER-FOCUSED CROP HEALTH INSIGHTS WITH WHEAT FIELD PHOTOGRAPHY */}
      <section id="crop-intelligence" className="homepage-section">
        <div className="section-head">
          <div>
            <div className="eyebrow">CROP HEALTH INSIGHTS</div>
            <h2>Understand what your crop is telling you</h2>
          </div>
          <p>Turn visual crop cues and observed symptoms into clear, actionable guidance.</p>
        </div>

        <div className="botanical-card-wrap">
          <BotanicalLeaf position="outer-top-right" variant="flower-branch" />
          <BotanicalLeaf position="outer-bottom-left" variant="blossom-sprig" />

          <div className="crop-editorial-spread">
            {/* Left: Editorial Narrative + Wheat Field Photography */}
            <div className="crop-editorial-left">
              <div className="crop-editorial-photo-box">
                <figure className="editorial-photo-figure">
                  <div className="editorial-photo-frame">
                    <img
                      src="/images/wheat-field.jpg"
                      alt="Golden rye and wheat field with mature grain ears ready for scouting"
                      className="editorial-photo-img"
                      loading="lazy"
                    />
                  </div>
                  <figcaption className="editorial-photo-caption">
                    <span>
                      <Camera size={12} /> Cereal grain scouting &amp; early rust detection
                    </span>
                    <span className="editorial-photo-source">Pixabay</span>
                  </figcaption>
                </figure>
              </div>

              <div className="crop-editorial-narrative">
                <h3>Turn crop signs into clearer insights</h3>
                <p>
                  Explore potential plant health issues from leaf photographs or observed symptoms
                  to guide timely field care before disease spreads across your acreage.
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
                      <strong>Visual context</strong> — Inspect highlighted regions that influenced the model&apos;s assessment.
                    </span>
                  </div>
                </div>

                <div>
                  <Button onClick={() => openTool("doctor")}>
                    Explore Crop Doctor <ArrowRight size={15} />
                  </Button>
                </div>
              </div>
            </div>

            {/* Right: Farmer-focused crop health inspection preview - clean dedicated presentation */}
            <CropHealthInspectionPreview />
          </div>
        </div>
      </section>

      {/* 5. WEATHER & FERTILIZER SPOTLIGHT WITH FARMLAND BANNER & TRACTOR FERTILIZER SPREADING */}
      <section id="weather-fertilizer" className="homepage-section">
        <div className="section-head">
          <div>
            <div className="eyebrow">Farm Decision Engines</div>
            <h2>Weather intelligence &amp; fertilizer planning</h2>
          </div>
          <p>Deterministic calculations that safeguard yields and prevent over-fertilization.</p>
        </div>

        {/* Wide Landscape Composition: Farmland Banner (Down To Earth / iStock) */}
        <div className="landscape-panorama-wrap">
          <figure className="editorial-photo-figure">
            <div className="landscape-panorama-frame">
              <span className="landscape-panorama-badge">
                <MapPin size={12} /> Field Intelligence &amp; Topography
              </span>
              <img
                src="/images/farmland-banner.jpg"
                alt="Agricultural farmland landscape with crop fields and contoured topography"
                className="landscape-panorama-img"
                loading="lazy"
              />
            </div>
            <figcaption className="editorial-photo-caption">
              <span>
                <Camera size={12} /> Agricultural field landscape &amp; terrain monitoring
              </span>
              <span className="editorial-photo-source">Down To Earth / iStock</span>
            </figcaption>
          </figure>
        </div>

        {/* Asymmetric 2-Column Split: Weather Intelligence & Cultivation / Fertilizer */}
        <div className="weather-cultivation-split">
          {/* Weather Pillar */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-left" variant="side-bloom" />
            <div className="weather-module-card">
              <div>
                <span className="eyebrow">
                  <CloudSun size={13} style={{ verticalAlign: -2, marginRight: 4 }} /> Open-Meteo Integration
                </span>
                <h3>Local weather risk intelligence</h3>
                <p>
                  Monitors ambient temperature, relative humidity, and precipitation against agronomic thresholds
                  to flag elevated fungal infection risks and extreme heat stress before they spread.
                </p>
              </div>

              <div className="pillar-preview-box">
                <div className="preview-stat-label">Calculated Signals</div>
                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  <span className="status-pill">Fungal risk evaluator</span>
                  <span className="status-pill">Heat stress monitor</span>
                  <span className="status-pill">Manual observation mode</span>
                </div>
              </div>

              <div>
                <Button variant="secondary" onClick={() => openTool("weather")}>
                  Open Weather tool <ArrowRight size={14} />
                </Button>
              </div>
            </div>
          </div>

          {/* Fertilizer & Cultivation Guidance Pillar */}
          <div className="botanical-card-wrap">
            <BotanicalLeaf position="beside-right" variant="side-sprig" />
            <div className="cultivation-module-card">
              <div>
                <span className="eyebrow">
                  <FlaskConical size={13} style={{ verticalAlign: -2, marginRight: 4 }} /> Per-Acre Lookup Table
                </span>
                <h3>Deterministic fertilizer planner</h3>
                <p>
                  Eliminates guesswork with verified per-acre agronomic lookup rates. Select your crop
                  and deficiency to receive precise nutrient quantities and indicative cost estimates.
                </p>
              </div>

              <div className="pillar-preview-box">
                <div className="preview-stat-label">Calculated Metrics</div>
                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  <span className="status-pill">Dosage per acre</span>
                  <span className="status-pill">Total bag quantity</span>
                  <span className="status-pill">Cost in INR (₹)</span>
                </div>
              </div>

              <div>
                <Button variant="secondary" onClick={() => openTool("fertilizer")}>
                  Open Fertilizer Planner <ArrowRight size={14} />
                </Button>
              </div>
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
    </div>
  );
}

export default function App() {
  const [currentView, setCurrentView] = useState<AppView>("home");
  const [activeSection, setActiveSection] = useState<string>("overview");
  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [mobileToolsExpanded, setMobileToolsExpanded] = useState(false);
  const [megaMenuOpen, setMegaMenuOpen] = useState(false);
  const lenisRef = useRef<Lenis | null>(null);

  // Health check on mount
  useEffect(() => {
    const controller = new AbortController();
    get<ApiHealth>("/api/health", controller.signal)
      .then((data) => setHealth(data))
      .catch(() => setHealth(null));
    return () => controller.abort();
  }, []);

  // Initialize Lenis Smooth Scrolling and synchronize with GSAP ScrollTrigger
  useEffect(() => {
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced) {
      return;
    }

    const lenis = new Lenis({
      lerp: 0.072, // Signature butter-smooth continuous momentum interpolation
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 0.95,
      touchMultiplier: 1.25,
      autoResize: true,
    });

    lenisRef.current = lenis;

    // Synchronize Lenis with GSAP ScrollTrigger official pattern
    lenis.on("scroll", ScrollTrigger.update);

    const tickerCallback = (time: number) => {
      lenis.raf(time * 1000);
    };

    gsap.ticker.add(tickerCallback);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(tickerCallback);
      lenis.destroy();
      lenisRef.current = null;
    };
  }, []);

  // Refresh ScrollTrigger and scroll to top on route change
  useEffect(() => {
    if (lenisRef.current) {
      lenisRef.current.scrollTo(0, { immediate: true });
    } else {
      window.scrollTo({ top: 0 });
    }

    const timer = setTimeout(() => {
      ScrollTrigger.refresh();
    }, 120);

    return () => clearTimeout(timer);
  }, [currentView]);

  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (!el) return;
    if (lenisRef.current) {
      lenisRef.current.scrollTo(el, {
        offset: -90,
        duration: 1.35,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      });
    } else {
      const headerOffset = 90;
      const elementPosition = el.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth",
      });
    }
  };

  const navigateToSection = (sectionId: string) => {
    if (currentView !== "home") {
      setCurrentView("home");
      setTimeout(() => {
        scrollToSection(sectionId);
      }, 120);
    } else {
      scrollToSection(sectionId);
    }
    setActiveSection(sectionId);
    setMobileNavOpen(false);
    setMegaMenuOpen(false);
  };

  const openTool = (tool: ToolPageId) => {
    setCurrentView(tool);
    setMobileNavOpen(false);
    setMegaMenuOpen(false);
    if (lenisRef.current) {
      lenisRef.current.scrollTo(0, { immediate: true });
    } else {
      window.scrollTo({ top: 0 });
    }
  };

  const returnToHome = () => {
    setCurrentView("home");
    setMobileNavOpen(false);
    setMegaMenuOpen(false);
    if (lenisRef.current) {
      lenisRef.current.scrollTo(0, { immediate: true });
    } else {
      window.scrollTo({ top: 0 });
    }
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
              <ContinuousHomePage
                openTool={openTool}
                health={health}
                onActiveSection={setActiveSection}
                scrollToSection={scrollToSection}
              />
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
