import { useState, type FormEvent } from "react";
import { CheckCircle2, ExternalLink, PackageCheck, QrCode, ShieldCheck } from "lucide-react";
import { post, postFile } from "../services/api";
import { Alert, Button, Card, EmptyState, Field, PageHeader } from "../components/ui";

interface Verification {
  found?: boolean;
  verified?: boolean;
  product?: Record<string, unknown> | null;
  message?: string;
  checks?: string[];
  expired?: boolean;
  error?: string | null;
}

interface VerificationResponse extends Verification {
  qr?: { code?: string; raw_text?: string; error?: string | null };
  verification?: Verification;
}

export default function ProductPage() {
  const [code, setCode] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);

  async function verify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!code.trim()) {
      setError("Enter the product code printed on the label.");
      return;
    }
    setError("");
    setResult(null);
    setLoading(true);
    try {
      setResult(await post<VerificationResponse>("/api/products/verify", { code: code.trim() }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The product registry could not be checked.");
    } finally {
      setLoading(false);
    }
  }

  async function scanQr() {
    if (!file) {
      setError("Choose a photo containing a product QR code first.");
      return;
    }
    if (!file.type.startsWith("image/") || file.size > 8 * 1024 * 1024) {
      setError("Choose an image file that is 8 MiB or smaller.");
      return;
    }
    setError("");
    setResult(null);
    setScanLoading(true);
    try {
      const data = await postFile<VerificationResponse>("/api/products/verify-qr", file);
      setResult(data);
      if (data.qr?.code) setCode(data.qr.code);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The QR code could not be read.");
    } finally {
      setScanLoading(false);
    }
  }

  const verification = result?.verification ?? result;
  const product = verification?.product;

  return (
    <>
      <PageHeader
        eyebrow="Product assurance · Registry lookup"
        title="Product verification"
        description="Check a product code against the AgriVision SQLite registry or read it from a QR label."
      />
      <div className="split-grid product-layout">
        <Card>
          <div className="card-title"><div><h2>Verify by product code</h2><p>Enter the code as it appears on the package label.</p></div><span className="feature-icon"><ShieldCheck size={16} /></span></div>
          <form className="form-stack" onSubmit={verify}>
            <Field label="Product code" id="product-code"><input id="product-code" className="field" value={code} onChange={(event) => setCode(event.target.value)} placeholder="For example, AGV-…" minLength={3} maxLength={100} /></Field>
            <Button type="submit" loading={loading}><ShieldCheck size={15} /> Verify product</Button>
          </form>
          <div className="product-divider"><span>OR SCAN A QR CODE</span></div>
          <label className="upload-zone qr-upload">
            <input type="file" accept="image/*" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
            <span>
              <span className="upload-icon"><QrCode size={19} /></span>
              <strong>{file ? file.name : "Choose a QR code photo"}</strong>
              <span>QR images only · up to 8 MiB</span>
            </span>
          </label>
          <Button className="qr-scan-button" variant="secondary" onClick={scanQr} loading={scanLoading}><QrCode size={15} /> Scan and verify QR</Button>
          {error ? <Alert tone="error">{error}</Alert> : null}
          <p className="home-footnote">The local product registry is a simulated demonstration dataset, not an official manufacturer registry.</p>
        </Card>
        <Card>
          <div className="card-title"><div><h2>Verification result</h2><p>Registry status and recorded product details.</p></div><span className="feature-icon"><PackageCheck size={16} /></span></div>
          {verification ? (
            <>
              <div className={`verification-status ${verification.verified ? "verified" : verification.found ? "warning" : "not-found"}`}>
                {verification.verified ? <CheckCircle2 size={21} /> : <ShieldCheck size={21} />}
                <div><strong>{verification.verified ? "Verified in registry" : verification.found ? "Warning — check details" : "Not found in registry"}</strong><span>{verification.message}</span></div>
              </div>
              {product ? (
                <div className="product-details">
                  {([
                    ["Product", product.product_name],
                    ["Manufacturer", product.manufacturer],
                    ["Batch", product.batch],
                    ["Expiry", product.expiry],
                    ["Status", product.status],
                    ["Type", product.product_type],
                  ] as Array<[string, unknown]>).filter(([, value]) => value !== undefined && value !== null && value !== "").map(([label, value]) => (
                    <div className="risk-row" key={label}><span>{label}</span><strong>{String(value)}</strong></div>
                  ))}
                </div>
              ) : null}
              {Array.isArray(verification.checks) && verification.checks.length ? <ul className="list verification-checks">{verification.checks.map((check) => <li key={check}>{check}</li>)}</ul> : null}
              {result?.qr?.code ? <div className="alert alert-info">QR code read: <strong>{result.qr.code}</strong></div> : null}
            </>
          ) : (
            <EmptyState icon={<ShieldCheck size={23} />}>Submit a product code or scan a QR label to see the status recorded in the registry.</EmptyState>
          )}
        </Card>
      </div>
      <div className="registry-note"><ExternalLink size={13} /> For safety, confirm the result with the manufacturer or authorized supplier.</div>
    </>
  );
}
