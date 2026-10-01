import { useState, type FormEvent } from "react";
import { CloudSun, MapPin, RefreshCw, ThermometerSun } from "lucide-react";
import { get } from "../services/api";
import type { JsonValue } from "../types";
import { Alert, Button, Card, EmptyState, Field, PageHeader } from "../components/ui";

interface WeatherResponse {
  city?: string;
  weather?: {
    temperature?: number;
    feels_like?: number;
    humidity?: number;
    wind_speed?: number;
    description?: string;
    [key: string]: JsonValue | undefined;
  } | null;
  risks?: Array<{
    name?: string;
    title?: string;
    key?: string;
    level?: string;
    description?: string;
    detail?: string;
    message?: string;
  }>;
  risk_level?: string | null;
  message?: string | { text?: string; source?: string } | null;
  error?: string | null;
  fetched_at?: string;
}

function riskTone(level?: string | null): string {
  return level?.toLowerCase() === "high" ? "risk-high" : level?.toLowerCase() === "moderate" ? "risk-moderate" : "";
}

export default function WeatherPage() {
  const [city, setCity] = useState("");
  const [manualMode, setManualMode] = useState(false);
  const [temperature, setTemperature] = useState("25");
  const [humidity, setHumidity] = useState("70");
  const [rainfall, setRainfall] = useState("0");
  const [result, setResult] = useState<WeatherResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!city.trim()) {
      setError("Enter a city to check its current weather.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const params = new URLSearchParams({ city: city.trim() });
      if (manualMode) {
        if (!temperature || !humidity || !Number.isFinite(Number(temperature)) || !Number.isFinite(Number(humidity))) {
          throw new Error("Enter a valid temperature and humidity for your own weather observation.");
        }
        if (Number(humidity) < 0 || Number(humidity) > 100 || Number(temperature) < -80 || Number(temperature) > 65) {
          throw new Error("Temperature must be between -80 and 65°C and humidity between 0 and 100%.");
        }
        if (rainfall && (Number(rainfall) < 0 || Number(rainfall) > 500 || !Number.isFinite(Number(rainfall)))) {
          throw new Error("Rainfall must be between 0 and 500 mm.");
        }
        params.set("temperature", temperature);
        params.set("humidity", humidity);
        if (rainfall) params.set("rainfall", rainfall);
      }
      setResult(await get<WeatherResponse>(`/api/weather?${params.toString()}`));
    } catch (cause) {
      setResult(null);
      setError(cause instanceof Error ? cause.message : "Weather data could not be retrieved.");
    } finally {
      setLoading(false);
    }
  }

  const weather = result?.weather;
  const message = typeof result?.message === "string" ? result.message : result?.message?.text;
  const heat = result?.risks?.find((risk) => /heat/i.test(`${risk.key ?? ""} ${risk.name ?? ""}`));
  const fungal = result?.risks?.find((risk) => /fung/i.test(`${risk.key ?? ""} ${risk.name ?? ""}`));

  return (
    <>
      <PageHeader
        eyebrow="Weather · Crop risk"
        title="Weather intelligence"
        description="Current local conditions and deterministic agricultural risk signals from the existing weather service."
      />
      <Card className="weather-search">
        <form className="weather-search-form" onSubmit={search}>
          <Field label="City" id="weather-city">
            <div className="input-with-icon"><MapPin size={15} /><input id="weather-city" className="field" value={city} onChange={(event) => setCity(event.target.value)} placeholder="For example, Pune" maxLength={160} /></div>
          </Field>
          <Button type="submit" loading={loading}><CloudSun size={15} /> {manualMode ? "Analyze readings" : "Check weather"}</Button>
          {result ? <Button variant="secondary" type="button" onClick={() => { setResult(null); setCity(""); setError(""); }}><RefreshCw size={14} /> Clear</Button> : null}
        </form>
        <label className="manual-weather-toggle"><input type="checkbox" checked={manualMode} onChange={(event) => { setManualMode(event.target.checked); setResult(null); setError(""); }} /> Enter my own weather readings</label>
        {manualMode ? (
          <div className="manual-weather-fields">
            <Field label="Temperature (°C)" id="manual-temperature"><input id="manual-temperature" className="field" type="number" min="-80" max="65" step="any" value={temperature} onChange={(event) => setTemperature(event.target.value)} /></Field>
            <Field label="Humidity (%)" id="manual-humidity"><input id="manual-humidity" className="field" type="number" min="0" max="100" value={humidity} onChange={(event) => setHumidity(event.target.value)} /></Field>
            <Field label="Rainfall (mm, optional)" id="manual-rainfall"><input id="manual-rainfall" className="field" type="number" min="0" max="500" step="any" value={rainfall} onChange={(event) => setRainfall(event.target.value)} /></Field>
          </div>
        ) : null}
        <div className="weather-note">{manualMode ? "The risk rules analyze only the readings you enter; these values are not presented as live weather." : "Live readings use the free Open-Meteo service. No sample readings are substituted."}</div>
      </Card>
      {error ? <Alert tone="error">{error}</Alert> : null}
      {weather ? (
        <div className="weather-results">
          <div className="split-grid weather-grid">
            <Card className="weather-main">
              <div className="weather-city"><MapPin size={14} /> {result?.city ?? city}</div>
              <div className="weather-sky"><CloudSun size={43} strokeWidth={1.3} /><div><div className="weather-temp">{weather.temperature ?? "—"}°</div><div className="weather-desc">{weather.description || "Current conditions"}</div></div></div>
              <div className="weather-details">
                <div><span>Feels like</span><strong>{weather.feels_like ?? "—"}°C</strong></div>
                <div><span>Humidity</span><strong>{weather.humidity ?? "—"}%</strong></div>
                <div><span>Wind</span><strong>{weather.wind_speed ?? "—"} m/s</strong></div>
              </div>
            </Card>
            <Card>
              <div className="card-title"><div><h2>Farm risk overview</h2><p>Calculated from current observed conditions.</p></div><span className={`risk-level ${riskTone(result?.risk_level)}`}>{result?.risk_level ?? "No risk data"}</span></div>
              <div className="risk-row"><span>Fungal risk</span><span className={`risk-level ${riskTone(fungal?.level)}`}>{fungal?.level ?? "No signal"}</span></div>
              <div className="risk-row"><span>Heat stress</span><span className={`risk-level ${riskTone(heat?.level)}`}>{heat?.level ?? "No signal"}</span></div>
              {(result?.risks ?? []).filter((risk) => risk !== fungal && risk !== heat).map((risk, index) => (
                <div className="risk-row" key={`${risk.key ?? risk.title ?? risk.name}-${index}`}><span>{risk.title ?? risk.name ?? risk.key ?? "Crop risk"}</span><span className={`risk-level ${riskTone(risk.level)}`}>{risk.level ?? "—"}</span></div>
              ))}
            </Card>
          </div>
          {message ? <Card className="weather-message"><div className="card-title"><div><h2>Field note</h2><p>{result?.fetched_at ? `Updated ${result.fetched_at}` : "From the weather risk service"}</p></div></div><p>{message}</p></Card> : null}
          {result?.risks?.map((risk, index) => risk.description || risk.detail || risk.message ? <Card key={`detail-${index}`} className="risk-detail"><strong>{risk.title ?? risk.name ?? risk.key}</strong><p>{risk.description ?? risk.detail ?? risk.message}</p></Card> : null)}
        </div>
      ) : !error && !loading ? (
        <Card><EmptyState icon={<ThermometerSun size={23} />}>Enter a city to view live temperature, humidity, wind, weather conditions and crop risks.</EmptyState></Card>
      ) : null}
    </>
  );
}
