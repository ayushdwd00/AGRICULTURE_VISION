import { useEffect, useState, type FormEvent } from "react";
import { Calculator, IndianRupee, Leaf, Ruler } from "lucide-react";
import { get, post } from "../services/api";
import type { FertilizerResult } from "../types";
import { Alert, Button, Card, EmptyState, Field, PageHeader } from "../components/ui";

interface FertilizerOptions {
  crops: string[];
  deficiencies: string[];
}

export default function FertilizerPage() {
  const [options, setOptions] = useState<FertilizerOptions>({ crops: [], deficiencies: [] });
  const [crop, setCrop] = useState("");
  const [deficiency, setDeficiency] = useState("");
  const [area, setArea] = useState("");
  const [unit, setUnit] = useState("acres");
  const [result, setResult] = useState<FertilizerResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [optionsError, setOptionsError] = useState("");

  useEffect(() => {
    get<FertilizerOptions>("/api/fertilizer/options")
      .then((data) => {
        setOptions(data);
        setCrop(data.crops[0] ?? "");
      })
      .catch((cause: unknown) => setOptionsError(cause instanceof Error ? cause.message : "Fertilizer options could not be loaded."));
  }, []);

  useEffect(() => {
    if (!crop) {
      setOptions((current) => ({ ...current, deficiencies: [] }));
      setDeficiency("");
      return;
    }
    const params = new URLSearchParams({ crop });
    get<FertilizerOptions>(`/api/fertilizer/options?${params.toString()}`)
      .then((data) => {
        setOptions((current) => ({ ...current, deficiencies: data.deficiencies }));
        setDeficiency((current) => data.deficiencies.includes(current) ? current : data.deficiencies[0] ?? "");
      })
      .catch((cause: unknown) => setOptionsError(cause instanceof Error ? cause.message : "Deficiency options could not be loaded."));
  }, [crop]);

  async function calculate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!crop || !deficiency || !area || !Number.isFinite(Number(area)) || Number(area) <= 0) {
      setError("Choose a crop and deficiency, then enter a land area greater than zero.");
      return;
    }
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const data = await post<FertilizerResult>("/api/fertilizer/calculate", {
        crop,
        deficiency,
        land_size: Number(area),
        unit,
      });
      if (data.error) setError(data.error);
      else setResult(data);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The fertilizer calculation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Farm planning · Deterministic calculation"
        title="Fertilizer planner"
        description="Get an indicative dose and cost using the existing crop and deficiency lookup table."
      />
      <div className="split-grid fertilizer-layout">
        <Card>
          <div className="card-title"><div><h2>Plan an application</h2><p>Choose the crop and deficiency to use its documented recommendation.</p></div><span className="feature-icon"><Calculator size={16} /></span></div>
          <form className="form-stack" onSubmit={calculate}>
            {optionsError ? <Alert tone="error">{optionsError}</Alert> : null}
            <Field label="Crop" id="fertilizer-crop">
              <select id="fertilizer-crop" className="field" value={crop} onChange={(event) => setCrop(event.target.value)} disabled={!options.crops.length}>
                {options.crops.length ? options.crops.map((item) => <option key={item}>{item}</option>) : <option value="">Loading crops…</option>}
              </select>
            </Field>
            <Field label="Nutrient deficiency" id="fertilizer-deficiency">
              <select id="fertilizer-deficiency" className="field" value={deficiency} onChange={(event) => setDeficiency(event.target.value)} disabled={!options.deficiencies.length}>
                {options.deficiencies.map((item) => <option key={item}>{item}</option>)}
              </select>
            </Field>
            <div className="field-grid">
              <Field label="Farm area" id="fertilizer-area">
                <input id="fertilizer-area" className="field" type="number" min="0.01" step="any" value={area} onChange={(event) => setArea(event.target.value)} placeholder="Enter area" />
              </Field>
              <Field label="Area unit" id="fertilizer-unit">
                <select id="fertilizer-unit" className="field" value={unit} onChange={(event) => setUnit(event.target.value)}><option value="acres">Acres</option><option value="hectares">Hectares</option></select>
              </Field>
            </div>
            {error ? <Alert tone="error">{error}</Alert> : null}
            <Button type="submit" loading={loading}><Calculator size={15} /> Calculate recommendation</Button>
          </form>
          <div className="calculation-note"><Leaf size={14} /><span>Indicative lookup only. Follow your soil test and confirm application with a local agricultural extension officer.</span></div>
        </Card>
        {result ? (
          <div className="stack">
            <Card className="fertilizer-result">
              <div className="result-label">Recommended fertilizer</div>
              <h2>{result.fertilizer}</h2>
              <div className="fertilizer-stat-grid">
                <div className="fertilizer-stat"><span>Estimated quantity</span><strong>{result.quantity} {result.unit}</strong></div>
                <div className="fertilizer-stat"><span>Approx. cost</span><strong><IndianRupee size={15} /> {result.estimated_cost?.toLocaleString("en-IN")} {result.currency}</strong></div>
                <div className="fertilizer-stat"><span>Dosage per acre</span><strong>{result.dosage_per_acre} {result.unit}</strong></div>
                <div className="fertilizer-stat"><span>Area converted</span><strong><Ruler size={14} /> {result.land_size_acres} acres</strong></div>
              </div>
              {result.application ? <div className="result-copy fertilizer-application"><div className="result-label">Application guidance</div>{result.application}</div> : null}
              {result.assumptions ? <p className="home-footnote">{result.assumptions}</p> : null}
            </Card>
          </div>
        ) : (
          <Card><EmptyState icon={<Calculator size={23} />}>Your recommendation, dosage and estimated cost will appear here after a calculation.</EmptyState></Card>
        )}
      </div>
    </>
  );
}
