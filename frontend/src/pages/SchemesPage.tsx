import { useEffect, useState, type FormEvent } from "react";
import { BookOpen, ExternalLink, FileText, Landmark, Search } from "lucide-react";
import { get, post } from "../services/api";
import type { SchemeRecord } from "../types";
import { Alert, Button, Card, EmptyState, Field, PageHeader } from "../components/ui";

interface SchemeOptions {
  regions: string[];
  crops: string[];
  categories: string[];
}

interface SchemesResponse {
  schemes: SchemeRecord[];
  meta?: Record<string, unknown>;
}

interface MatchResponse {
  matches?: SchemeRecord[];
  near_misses?: SchemeRecord[];
  error?: string | null;
}

function stringItems(value: unknown): string[] {
  if (typeof value === "string") return [value];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function SchemeCard({ scheme }: { scheme: SchemeRecord }) {
  const eligibility = stringItems(scheme.eligibility);
  const documents = stringItems(scheme.required_documents ?? scheme.documents_required);
  return (
    <Card className="scheme-card">
      <div className="scheme-card-top">
        <span className="status-pill">{scheme.category ?? "Agriculture scheme"}</span>
        {scheme.region ? <span className="scheme-region"><Landmark size={12} /> {scheme.region}</span> : null}
      </div>
      <h3>{scheme.name}</h3>
      <p>{scheme.description ?? "Scheme details are available through the official portal."}</p>
      {scheme.benefit ? <div className="scheme-benefit"><strong>Benefits</strong><p>{scheme.benefit}</p></div> : null}
      {eligibility.length ? <div className="scheme-detail"><strong>Eligibility</strong><ul>{eligibility.slice(0, 3).map((item) => <li key={item}>{item}</li>)}</ul></div> : null}
      {documents.length ? <div className="scheme-detail"><strong><FileText size={12} /> Required documents</strong><div className="tag-row">{documents.slice(0, 5).map((item) => <span className="tag" key={item}>{item}</span>)}</div></div> : null}
      {scheme.matched_reasons?.length ? <div className="scheme-match-note">{scheme.matched_reasons.join(" · ")}</div> : null}
      {scheme.unmet_reasons?.length ? <div className="scheme-unmet-note">{scheme.unmet_reasons.join(" · ")}</div> : null}
      {scheme.official_link ? <a className="scheme-link" href={scheme.official_link} target="_blank" rel="noreferrer">Official information <ExternalLink size={12} /></a> : null}
    </Card>
  );
}

export default function SchemesPage() {
  const [options, setOptions] = useState<SchemeOptions>({ regions: [], crops: [], categories: [] });
  const [schemes, setSchemes] = useState<SchemeRecord[]>([]);
  const [matches, setMatches] = useState<SchemeRecord[] | null>(null);
  const [nearMisses, setNearMisses] = useState<SchemeRecord[]>([]);
  const [land, setLand] = useState("");
  const [region, setRegion] = useState("All India");
  const [crop, setCrop] = useState("Any");
  const [category, setCategory] = useState("Any");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<"match" | "all">("match");

  useEffect(() => {
    Promise.all([get<SchemeOptions>("/api/schemes/options"), get<SchemesResponse>("/api/schemes")])
      .then(([schemeOptions, schemeData]) => {
        setOptions(schemeOptions);
        setSchemes(schemeData.schemes);
      })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Scheme data could not be loaded."));
  }, []);

  async function findMatches(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!land || !Number.isFinite(Number(land)) || Number(land) <= 0) {
      setError("Enter your farm area in acres to find matching schemes.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const data = await post<MatchResponse>("/api/schemes/match", {
        land_size_acres: Number(land),
        region,
        crop,
        category: category === "Any" ? null : category,
      });
      if (data.error) throw new Error(data.error);
      setMatches(data.matches ?? []);
      setNearMisses(data.near_misses ?? []);
      setView("match");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Scheme matching failed.");
    } finally {
      setLoading(false);
    }
  }

  const source = view === "all" ? schemes : matches ?? [];
  const visible = source.filter((scheme) => {
    const haystack = `${scheme.name} ${scheme.description ?? ""} ${scheme.category ?? ""}`.toLowerCase();
    return haystack.includes(search.toLowerCase());
  });

  return (
    <>
      <PageHeader
        eyebrow="Government support · Scheme data"
        title="Scheme matcher"
        description="Explore the existing scheme dataset and find options relevant to your farm."
      />
      <Card className="scheme-filters">
        <div className="card-title"><div><h2>Tell us about your farm</h2><p>Matching uses land size, state, crop and scheme category.</p></div><span className="feature-icon"><Landmark size={16} /></span></div>
        <form onSubmit={findMatches}>
          <div className="field-grid scheme-filter-grid">
            <Field label="Farm area (acres)" id="scheme-land"><input id="scheme-land" className="field" type="number" min="0.01" step="any" value={land} onChange={(event) => setLand(event.target.value)} placeholder="Enter acres" /></Field>
            <Field label="State / region" id="scheme-region"><select id="scheme-region" className="field" value={region} onChange={(event) => setRegion(event.target.value)}>{options.regions.map((item) => <option key={item}>{item}</option>)}</select></Field>
            <Field label="Crop" id="scheme-crop"><select id="scheme-crop" className="field" value={crop} onChange={(event) => setCrop(event.target.value)}>{options.crops.map((item) => <option key={item}>{item}</option>)}</select></Field>
            <Field label="Support type" id="scheme-category"><select id="scheme-category" className="field" value={category} onChange={(event) => setCategory(event.target.value)}><option>Any</option>{options.categories.map((item) => <option key={item}>{item}</option>)}</select></Field>
          </div>
          <div className="scheme-actions"><Button type="submit" loading={loading}><Search size={14} /> Find matching schemes</Button><Button type="button" variant="secondary" onClick={() => { setView("all"); setMatches(null); }}>Browse all schemes</Button></div>
        </form>
      </Card>
      {error ? <Alert tone="error">{error}</Alert> : null}
      <div className="scheme-toolbar">
        <div className="tabs">
          <button className={`tab${view === "match" ? " active" : ""}`} onClick={() => setView("match")}>Your matches {matches ? `(${matches.length})` : ""}</button>
          <button className={`tab${view === "all" ? " active" : ""}`} onClick={() => setView("all")}>All schemes ({schemes.length})</button>
        </div>
        <div className="search-wrap scheme-search"><Search size={14} /><input className="field" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search schemes" aria-label="Search schemes" /></div>
      </div>
      {view === "match" && !matches ? (
        <Card><EmptyState icon={<BookOpen size={23} />}>Enter your farm information to match schemes from the existing dataset. You can also browse every scheme above.</EmptyState></Card>
      ) : visible.length ? (
        <div className="scheme-grid">{visible.map((scheme) => <SchemeCard key={scheme.id ?? scheme.name} scheme={scheme} />)}</div>
      ) : (
        <Card><EmptyState icon={<Search size={22} />}>No schemes match this search. Try another term or browse all available schemes.</EmptyState></Card>
      )}
      {view === "match" && matches?.length === 0 && nearMisses.length ? <div className="near-misses"><div className="section-row"><h2>Other schemes to explore</h2><span>These did not match all your farm details.</span></div><div className="scheme-grid">{nearMisses.slice(0, 4).map((scheme) => <SchemeCard key={scheme.id ?? scheme.name} scheme={scheme} />)}</div></div> : null}
      <div className="scheme-source-note">Scheme descriptions, eligibility and official links come from the local dataset. Verify current rules and application dates on the official scheme portal.</div>
    </>
  );
}
