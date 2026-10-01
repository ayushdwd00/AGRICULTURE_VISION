import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  Bell,
  BookOpen,
  CloudSun,
  FlaskConical,
  Gauge,
  Leaf,
  Menu,
  ScanLine,
  ShieldCheck,
  Sprout,
  Tractor,
  Wheat,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { get } from "./services/api";
import type { ApiHealth } from "./types";
import { Button, Card, PageHeader } from "./components/ui";
import CropDoctor from "./pages/CropDoctor";
import WeatherPage from "./pages/WeatherPage";
import FertilizerPage from "./pages/FertilizerPage";
import ProductPage from "./pages/ProductPage";
import SchemesPage from "./pages/SchemesPage";
import EquipmentPage from "./pages/EquipmentPage";

type PageId = "home" | "doctor" | "weather" | "fertilizer" | "products" | "schemes" | "equipment" | "about";
type PageEntry = { id: PageId; label: string; icon: LucideIcon };

const pages: PageEntry[] = [
  { id: "home", label: "Overview", icon: Gauge },
  { id: "doctor", label: "Crop Doctor", icon: ScanLine },
  { id: "weather", label: "Weather intelligence", icon: CloudSun },
  { id: "fertilizer", label: "Fertilizer planner", icon: FlaskConical },
  { id: "products", label: "Product verification", icon: ShieldCheck },
  { id: "schemes", label: "Scheme matcher", icon: BookOpen },
  { id: "equipment", label: "Equipment rental", icon: Tractor },
  { id: "about", label: "About AgriVision", icon: Sprout },
];

function statusText(status: ApiHealth | null): string {
  if (!status) return "Connecting to services…";
  return status.status.toLowerCase() === "ok" || status.status.toLowerCase() === "healthy"
    ? "All systems operational"
    : "Some services need attention";
}

function HomePage({
  health,
  openPage,
}: {
  health: ApiHealth | null;
  openPage: (page: PageId) => void;
}) {
  const highlights: Array<{
    icon: LucideIcon;
    title: string;
    copy: string;
    page: PageId;
  }> = [
    { icon: ScanLine, title: "Crop Doctor", copy: "See disease predictions, symptom signals and visual explanations.", page: "doctor" },
    { icon: CloudSun, title: "Weather intelligence", copy: "Check local conditions and rule-based crop risk signals.", page: "weather" },
    { icon: FlaskConical, title: "Fertilizer planner", copy: "Estimate quantities and indicative cost from the existing lookup table.", page: "fertilizer" },
    { icon: ShieldCheck, title: "Product verification", copy: "Check a product code against the local registry.", page: "products" },
    { icon: BookOpen, title: "Scheme matcher", copy: "Find relevant public schemes using your farm details.", page: "schemes" },
    { icon: Tractor, title: "Equipment rental", copy: "Browse farm equipment and manage rental bookings.", page: "equipment" },
  ];

  return (
    <>
      <section className="hero-card">
        <div className="hero-copy">
          <div className="hero-pill"><Sprout size={13} /> FARMING, WITH MORE CLARITY</div>
          <h1 aria-label="Grow with confidence">
            <span>Grow</span>
            <span>with</span>
            <em>confidence.</em>
          </h1>
          <p>
            AI-powered intelligence for smarter agriculture. Understand crop health,
            local weather, and the decisions that keep your farm moving.
          </p>
          <div className="hero-actions">
            <Button onClick={() => openPage("doctor")}>Start a diagnosis <ArrowRight size={15} /></Button>
            <Button variant="secondary" onClick={() => openPage("weather")}>Explore the platform</Button>
          </div>
        </div>
      </section>

      <div className="home-status-row">
        <div><span className={`service-indicator${health ? " is-connected" : ""}`} />{statusText(health)}</div>
        <span>Existing models · datasets · databases preserved</span>
      </div>

      <section className="home-section">
        <div className="section-row">
          <h2>Tools for your farm</h2>
          <span>One connected agriculture workspace</span>
        </div>
        <div className="feature-grid">
          {highlights.map(({ icon: Icon, title, copy, page }) => (
            <button className="feature-card card" key={page} onClick={() => openPage(page)}>
              <span className="feature-icon"><Icon size={17} /></span>
              <span className="feature-arrow"><ArrowRight size={15} /></span>
              <h3>{title}</h3>
              <p>{copy}</p>
            </button>
          ))}
        </div>
      </section>

      <div className="home-lower">
        <Card>
          <div className="card-title">
            <div><h2>Built on your existing AgriVision logic</h2><p>Predictions and calculations come from the connected backend.</p></div>
            <span className="feature-icon"><Activity size={16} /></span>
          </div>
          <ul className="list">
            <li>Fine-tuned MobileNetV2 with symptom classification and Grad-CAM.</li>
            <li>Weather risks, fertilizer rates and scheme matches use existing rules and datasets.</li>
            <li>Product records and equipment bookings are read from the SQLite databases.</li>
          </ul>
          <p className="home-footnote">No demo diagnoses, invented weather readings, or fabricated schemes are shown.</p>
        </Card>
        <Card>
          <div className="card-title"><div><h2>From the field, to the next step</h2><p>Choose a tool to get started.</p></div><Wheat size={17} color="#6c8962" /></div>
          <div className="activity-row"><span className="activity-icon"><ScanLine size={15} /></span><div><strong>Check a crop symptom</strong><span>Image and symptom analysis</span></div></div>
          <div className="activity-row"><span className="activity-icon"><CloudSun size={15} /></span><div><strong>Understand local conditions</strong><span>Weather and crop risk</span></div></div>
          <div className="activity-row"><span className="activity-icon"><Tractor size={15} /></span><div><strong>Find farm equipment</strong><span>Browse and book locally</span></div></div>
        </Card>
      </div>
    </>
  );
}

function AboutPage({ health }: { health: ApiHealth | null }) {
  return (
    <>
      <PageHeader
        eyebrow="The platform"
        title="Agriculture intelligence, made practical."
        description="AgriVision brings your existing crop models and farm tools into one clear, connected workspace."
      />
      <div className="about-banner">
        <div className="about-mark"><Leaf size={24} /></div>
        <div><div className="eyebrow">AI-POWERED INTELLIGENCE FOR SMARTER AGRICULTURE</div><h2>Better-informed farming starts with better-connected tools.</h2></div>
      </div>
      <div className="split-grid about-grid">
        <Card>
          <div className="card-title"><div><h2>What powers the platform</h2><p>Existing project components are reused rather than replaced.</p></div></div>
          <div className="about-point"><span className="feature-icon"><ScanLine size={16} /></span><div><strong>Crop Doctor</strong><p>Fine-tuned MobileNetV2, a Random Forest symptom classifier, Grad-CAM and optional Gemini explanations.</p></div></div>
          <div className="about-point"><span className="feature-icon"><CloudSun size={16} /></span><div><strong>Farm planning tools</strong><p>Open-Meteo with deterministic risk rules, fertilizer lookup calculations and local product/scheme data.</p></div></div>
          <div className="about-point"><span className="feature-icon"><Tractor size={16} /></span><div><strong>Marketplace</strong><p>SQLite-backed equipment listings, farmer and owner workflows, and booking overlap prevention.</p></div></div>
        </Card>
        <Card>
          <div className="card-title"><div><h2>Service status</h2><p>Current connection to the AgriVision API.</p></div><span className="feature-icon"><Activity size={16} /></span></div>
          <div className="risk-row"><span>Backend API</span><span className={`risk-level ${health ? "" : "status-offline"}`}>{health ? health.status : "Not connected"}</span></div>
          {health?.services && Object.entries(health.services).map(([service, state]) => (
            <div className="risk-row" key={service}><span>{service.replace(/_/g, " ")}</span><span className="risk-level">{String(state)}</span></div>
          ))}
          <p className="home-footnote">API keys remain on the backend. Weather and Gemini features require their corresponding server environment variables.</p>
        </Card>
      </div>
    </>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState<PageId>("home");
  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    get<ApiHealth>("/api/health", controller.signal)
      .then(setHealth)
      .catch(() => setHealth(null));
    return () => controller.abort();
  }, []);

  const selectedPage = pages.find((page) => page.id === activePage) ?? pages[0];
  const openPage = (page: PageId) => {
    setActivePage(page);
    setMobileNavOpen(false);
  };

  return (
    <div className="app-shell">
      {mobileNavOpen ? <button className="mobile-scrim" aria-label="Close menu" onClick={() => setMobileNavOpen(false)} /> : null}
      <aside className={`sidebar${mobileNavOpen ? " sidebar-open" : ""}`}>
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); openPage("home"); }}>
          <span className="brand-mark"><Sprout size={21} /></span>
          <span className="brand-copy"><span className="brand-title">AgriVision</span><span className="brand-sub">Farm intelligence</span></span>
        </a>
        <button className="sidebar-close" aria-label="Close navigation" onClick={() => setMobileNavOpen(false)}><X size={18} /></button>
        <div className="side-label">Workspace</div>
        <nav className="nav-list" aria-label="Main navigation">
          {pages.map(({ id, label, icon: Icon }) => (
            <button
              className={`nav-item${activePage === id ? " active" : ""}`}
              key={id}
              onClick={() => openPage(id)}
              aria-current={activePage === id ? "page" : undefined}
              title={label}
            >
              <Icon size={17} strokeWidth={1.8} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="workspace-card">
            <div className="workspace-label"><span className="workspace-dot" /> API CONNECTION</div>
            <strong>{health ? "Connected" : "Checking services"}</strong>
            <p>{health ? "Your farm tools are ready." : "Start the backend to use live tools."}</p>
          </div>
          <div className="profile">
            <div className="avatar">AV</div>
            <div><strong>Farm workspace</strong><span>AgriVision platform</span></div>
          </div>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setMobileNavOpen(true)}><Menu size={18} /></button>
          <div className="breadcrumb">Workspace <span> / </span> <strong>{selectedPage.label}</strong></div>
          <div className="topbar-actions">
            <span className="connection-label"><span className={`service-indicator${health ? " is-connected" : ""}`} /> {health ? "Systems live" : "API offline"}</span>
            <button className="icon-button" aria-label="Notifications"><Bell size={16} /><span className="notification-dot" /></button>
            <div className="avatar top-avatar">AV</div>
          </div>
        </header>
        <main className="main-content">
          <AnimatePresence mode="wait">
            <motion.div
              key={activePage}
              initial={{ opacity: 0, y: 100 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
            >
              {activePage === "home" ? <HomePage health={health} openPage={openPage} /> : null}
              {activePage === "about" ? <AboutPage health={health} /> : null}
              {activePage === "doctor" ? <CropDoctor /> : null}
              {activePage === "weather" ? <WeatherPage /> : null}
              {activePage === "fertilizer" ? <FertilizerPage /> : null}
              {activePage === "products" ? <ProductPage /> : null}
              {activePage === "schemes" ? <SchemesPage /> : null}
              {activePage === "equipment" ? <EquipmentPage /> : null}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
