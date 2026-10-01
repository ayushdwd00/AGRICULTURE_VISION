import { useState, type ChangeEvent, type FormEvent } from "react";
import { Camera, Check, Image as ImageIcon, Leaf, Mic, Sparkles, UploadCloud } from "lucide-react";
import { post, postFile } from "../services/api";
import type { CropPrediction } from "../types";
import { Alert, Button, Card, Field, PageHeader } from "../components/ui";

interface DiagnosisResponse {
  image?: CropPrediction | null;
  symptoms?: CropPrediction | null;
  combined?: CropPrediction | null;
  explanation?: string | { text?: string; source?: string };
  image_warning?: string | null;
}

interface GradcamResponse {
  label?: string;
  explained_label?: string;
  confidence?: number;
  images?: { overlay?: string; heatmap?: string; original?: string };
}

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" ? value as Record<string, unknown> : null;
}

function text(value: unknown): string {
  if (typeof value === "string" || typeof value === "number") return String(value);
  const item = record(value);
  if (!item) return "";
  return [item.label, item.pretty_label, item.summary, item.message, item.text]
    .find((part) => typeof part === "string") as string | undefined ?? "";
}

function predictionName(value: unknown): string {
  const item = record(value);
  if (!item) return "";
  return text(item.disease ?? item.label ?? item.final_disease ?? item.prediction);
}

function imageSource(value: string): string {
  return value.startsWith("data:") ? value : `data:image/png;base64,${value}`;
}

export default function CropDoctor() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [symptoms, setSymptoms] = useState("");
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState<DiagnosisResponse | CropPrediction | null>(null);
  const [gradcam, setGradcam] = useState<GradcamResponse | null>(null);
  const [error, setError] = useState("");
  const [gradcamError, setGradcamError] = useState("");
  const [loading, setLoading] = useState(false);

  function selectImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("Choose an image file to continue.");
      event.target.value = "";
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setError("The image must be 8 MiB or smaller.");
      event.target.value = "";
      return;
    }
    setError("");
    setImageFile(file);
    setPreview(URL.createObjectURL(file));
    setResult(null);
    setGradcam(null);
  }

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!imageFile && !symptoms.trim()) {
      setError("Add a plant image or describe the symptoms before analyzing.");
      return;
    }
    setError("");
    setGradcamError("");
    setResult(null);
    setGradcam(null);
    setLoading(true);
    try {
      if (imageFile) {
        const diagnosis = await postFile<DiagnosisResponse>(
          "/api/crop/diagnose",
          imageFile,
          symptoms.trim() ? { symptoms: symptoms.trim() } : {},
        );
        setResult(diagnosis);
        if (diagnosis.image) {
          const label = predictionName(diagnosis.image);
          try {
            const visualization = await postFile<GradcamResponse>(
              `/api/crop/gradcam${label ? `?target_label=${encodeURIComponent(label)}` : ""}`,
              imageFile,
            );
            setGradcam(visualization);
          } catch (cause) {
            setGradcamError(cause instanceof Error ? cause.message : "Grad-CAM could not be generated.");
          }
        }
      } else {
        setResult(await post<CropPrediction>("/api/symptoms/predict", { text: symptoms.trim() }));
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Crop analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const bundle = record(result);
  const imageResult = bundle?.image ?? result;
  const symptomsResult = bundle?.symptoms;
  const combinedResult = bundle?.combined;
  const primary = record(combinedResult) ?? record(imageResult) ?? {};
  const disease =
    predictionName(primary) ||
    predictionName(imageResult) ||
    predictionName(symptomsResult);
  const confidenceValue =
    primary.combined_confidence ??
    primary.confidence ??
    record(imageResult)?.confidence ??
    record(symptomsResult)?.confidence;
  const confidence =
    typeof confidenceValue === "number"
      ? Math.max(0, Math.min(100, confidenceValue <= 1 ? confidenceValue * 100 : confidenceValue))
      : null;
  const severity = text(primary.severity ?? record(imageResult)?.severity ?? record(symptomsResult)?.severity);
  const explanation = text(bundle?.explanation ?? primary.explanation ?? record(imageResult)?.explanation);
  const recommendationValue =
    primary.recommendations ??
    bundle?.recommendations ??
    record(imageResult)?.recommendations ??
    record(symptomsResult)?.advice ??
    (bundle?.symptoms ? record(bundle.symptoms)?.advice : undefined);
  const recommendations =
    Array.isArray(recommendationValue)
      ? recommendationValue
      : typeof recommendationValue === "string"
        ? [recommendationValue]
        : [];
  const topPredictions = record(imageResult)?.top_predictions;
  const symptomDetails = text(
    record(symptomsResult)?.advice ??
      record(symptomsResult)?.summary ??
      record(symptomsResult)?.pretty_label ??
      record(symptomsResult)?.label ??
      record(result)?.advice ??
      record(result)?.pretty_label ??
      record(result)?.label ??
      (bundle?.symptoms ? bundle.symptoms : ""),
  );
  const combinedMessage = text(record(combinedResult)?.message);
  const disagreementNote = text(record(combinedResult)?.disagreement_note);
  const explanationSource = text(record(bundle?.explanation)?.source);
  const gradcamImage = gradcam?.images?.overlay;

  return (
    <>
      <PageHeader
        eyebrow="Crop health · AI-assisted"
        title="Crop Doctor"
        description="Upload a clear leaf image, describe what you see, or use both signals together."
      />
      <form onSubmit={analyze}>
        <div className="split-grid crop-input-grid">
          <Card>
            <div className="card-title">
              <div><h2>Plant image</h2><p>Clear, well-lit leaf photos help the model assess crop health.</p></div>
              <span className="feature-icon"><Camera size={16} /></span>
            </div>
            {preview ? (
              <div className="image-preview-wrap">
                <img className="preview-image" src={preview} alt="Selected plant leaf" />
                <div className="image-file-name"><ImageIcon size={13} /> {imageFile?.name}</div>
              </div>
            ) : (
              <label className="upload-zone">
                <input type="file" accept="image/*" onChange={selectImage} />
                <span>
                  <span className="upload-icon"><UploadCloud size={19} /></span>
                  <strong>Drop a crop photo or browse</strong>
                  <span>JPG, PNG or WebP · up to 8 MiB</span>
                </span>
              </label>
            )}
            {preview ? <label className="replace-image"><input type="file" accept="image/*" onChange={selectImage} />Choose a different image</label> : null}
            <p className="form-note"><Leaf size={12} /> Use a close-up photo of the affected leaf where possible.</p>
          </Card>
          <Card>
            <div className="card-title">
              <div><h2>Describe the symptoms</h2><p>Tell us what changed, and when it started.</p></div>
              <span className="feature-icon"><Mic size={16} /></span>
            </div>
            <Field label="Symptoms or observations" id="crop-symptoms">
              <textarea
                id="crop-symptoms"
                className="field"
                value={symptoms}
                onChange={(event) => setSymptoms(event.target.value)}
                placeholder="For example: lower leaves have yellow patches with brown edges…"
                maxLength={5000}
              />
            </Field>
            <div className="symptom-meta"><span>Optional when an image is provided</span><span>{symptoms.length}/5000</span></div>
            <p className="form-note"><Sparkles size={12} /> Image and symptom analysis use the existing AgriVision models.</p>
          </Card>
        </div>
        {error ? <Alert tone="error">{error}</Alert> : null}
        <div className="diagnose-actions">
          <Button type="submit" loading={loading}><Sparkles size={15} /> {loading ? "Analyzing crop…" : "Analyze crop"}</Button>
          <span className="privacy-note">Your image is analyzed by the AgriVision backend and is not included in frontend code.</span>
        </div>
      </form>

      {result ? (
        <div className="diagnosis-results">
          <Card className="result-card">
            <div className="result-head">
              <div>
                <div className="result-label">Diagnosis from existing model</div>
                <h2>{disease || "Analysis complete"}</h2>
                {severity ? <span className="result-badge">{severity} severity</span> : null}
              </div>
              {confidence !== null ? (
                <div className="confidence-meter"><strong>{confidence.toFixed(1)}%</strong><span>confidence</span></div>
              ) : null}
            </div>
            {confidence !== null ? <div className="progress-track confidence-track"><div className="progress-fill" style={{ width: `${confidence}%` }} /></div> : null}
            {typeof bundle?.image_warning === "string" && bundle.image_warning ? <Alert>{bundle.image_warning}</Alert> : null}
            {combinedMessage ? <Alert>{combinedMessage}</Alert> : null}
            {disagreementNote ? <Alert tone="error">{disagreementNote}</Alert> : null}
            <div className="result-grid">
              {symptomDetails ? <div><div className="result-label">Symptom analysis</div><div className="result-copy">{symptomDetails}</div></div> : null}
              {explanation ? <div><div className="result-label">Explanation{explanationSource === "offline-fallback" ? " · Offline summary" : explanationSource ? " · Gemini" : ""}</div><div className="result-copy">{explanation}</div></div> : null}
              {Array.isArray(recommendations) && recommendations.length ? (
                <div><div className="result-label">Recommendations</div><ul className="list">{recommendations.filter((item): item is string => typeof item === "string").map((item, index) => <li key={index}>{item}</li>)}</ul></div>
              ) : null}
              {Array.isArray(topPredictions) && topPredictions.length ? (
                <div>
                  <div className="result-label">Other model predictions</div>
                  <ul className="list">
                    {topPredictions.slice(0, 3).map((item, index) => {
                      const prediction = record(item);
                      const label = predictionName(prediction);
                      const score = prediction?.confidence;
                      if (!label) return null;
                      return <li key={`${label}-${index}`}>{label}{typeof score === "number" ? ` · ${(score <= 1 ? score * 100 : score).toFixed(1)}%` : ""}</li>;
                    })}
                  </ul>
                </div>
              ) : null}
            </div>
          </Card>
          {gradcamImage ? (
            <Card className="gradcam-card">
              <div className="card-title"><div><h2>Visual explanation · Grad-CAM</h2><p>Highlighted regions show where the model focused for this prediction.</p></div><span className="result-badge"><Check size={12} /> Model generated</span></div>
              <img className="gradcam-image" src={imageSource(gradcamImage)} alt="Grad-CAM crop disease visualization" />
            </Card>
          ) : imageFile && gradcamError ? <Alert tone="error">The diagnosis completed, but the Grad-CAM visualization failed: {gradcamError}</Alert> : null}
        </div>
      ) : null}
    </>
  );
}
