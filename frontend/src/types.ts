export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export interface ApiHealth {
  status: string;
  services?: Record<string, JsonValue>;
  [key: string]: JsonValue | undefined;
}

export interface CropPrediction {
  disease?: string;
  label?: string;
  confidence?: number;
  severity?: string;
  symptom_analysis?: string | Record<string, JsonValue>;
  explanation?: string;
  recommendations?: string[];
  gradcam_image?: string;
  gradcam?: string;
  top_predictions?: Array<{ label?: string; disease?: string; confidence?: number }>;
  error?: string | null;
}

export interface FertilizerResult {
  error?: string | null;
  crop?: string;
  deficiency?: string;
  fertilizer?: string;
  dosage_per_acre?: number;
  unit?: string;
  land_size_acres?: number;
  quantity?: number;
  estimated_cost?: number;
  currency?: string;
  application?: string;
  assumptions?: string;
  summary?: string;
}

export interface SchemeRecord {
  id?: string;
  name: string;
  description?: string;
  benefit?: string;
  eligibility?: string | string[];
  required_documents?: string[];
  documents_required?: string[];
  official_link?: string;
  category?: string;
  region?: string;
  matched_reasons?: string[];
  unmet_reasons?: string[];
  [key: string]: JsonValue | undefined;
}
