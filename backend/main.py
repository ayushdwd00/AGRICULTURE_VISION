"""FastAPI adapter exposing AgriVision's existing feature modules."""

from __future__ import annotations

import base64
import io
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel, Field

from modules import crop_doctor, fertilizer, product_verifier, subsidy_matcher
from modules.symptom_model import predict_symptoms, symptom_model_status
from modules.weather import weather_report, weather_status
from utils.database import init_products_db
from utils.gemini import fallback_diagnosis, generate_description, recommendation_for_image
from utils.helpers import is_probably_leaf_image, load_image_from_bytes

logger = logging.getLogger("agrivision.api")
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


class SymptomsRequest(BaseModel):
    text: str = Field(min_length=3, max_length=5_000)


class FertilizerRequest(BaseModel):
    crop: str = Field(min_length=1, max_length=100)
    deficiency: str = Field(min_length=1, max_length=100)
    land_size: float = Field(gt=0, le=1_000_000)
    unit: str = Field(default="acres", pattern="^(acres|hectares)$")


class ProductCodeRequest(BaseModel):
    code: str = Field(min_length=3, max_length=100)


class SchemeMatchRequest(BaseModel):
    land_size_acres: float = Field(gt=0, le=1_000_000)
    region: str = Field(default="All India", min_length=1, max_length=100)
    crop: str = Field(default="Any", min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)


def _check_model_availability() -> Dict[str, Optional[str]]:
    """Check existence of model weight files without loading into memory."""
    issues: Dict[str, Optional[str]] = {"crop_model": None, "symptom_model": None}
    try:
        status = crop_doctor.model_status()
        if not status.get("active"):
            issues["crop_model"] = "No vision model weights found in 'models/'"
    except Exception as exc:
        issues["crop_model"] = f"{type(exc).__name__}: model status check failed"
        logger.warning("Crop model status check failed: %s", exc)
    try:
        s_status = symptom_model_status()
        if not s_status.get("available"):
            issues["symptom_model"] = "Symptom model file not found in 'models/'"
    except Exception as exc:
        issues["symptom_model"] = f"{type(exc).__name__}: symptom status check failed"
        logger.warning("Symptom model status check failed: %s", exc)
    return issues


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model_load_issues = _check_model_availability()
    try:
        init_products_db()
        app.state.database_error = None
    except Exception as exc:
        app.state.database_error = type(exc).__name__
        logger.exception("Database initialization failed")
    yield


app = FastAPI(title="AgriVision API", version="1.0.0", lifespan=lifespan)
origins = [
    origin.strip()
    for origin in os.getenv(
        "AGRIVISION_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cap_request_size(request, call_next):
    """Reject oversized multipart/API payloads before they are parsed when sized."""
    length = request.headers.get("content-length")
    if length:
        try:
            if int(length) > MAX_UPLOAD_BYTES + 64 * 1024:
                return _json_error(413, "Request body is too large (maximum upload is 8 MiB).")
        except ValueError:
            return _json_error(400, "Invalid Content-Length header.")
    return await call_next(request)


def _json_error(status_code: int, detail: str):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status_code, content={"detail": detail})


@app.exception_handler(Exception)
async def safe_unhandled_exception(_request, exc: Exception):
    logger.exception("Unhandled API error (%s)", type(exc).__name__)
    return _json_error(500, "An unexpected server error occurred.")


def _read_upload(upload: UploadFile) -> bytes:
    content = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image exceeds the 8 MiB upload limit.")
    if not content:
        raise HTTPException(400, "The uploaded file is empty.")
    return content


def _validated_image(data: bytes) -> Image.Image:
    try:
        return load_image_from_bytes(data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def _scrub(value: Any) -> Any:
    """Remove configured API-key values from module-generated response text."""
    if isinstance(value, dict):
        return {key: _scrub(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        for name in ("GEMINI_API_KEY",):
            secret = os.getenv(name, "")
            if secret:
                value = value.replace(secret, "[redacted]")
        return value
    return value


def _module_result(result: Dict[str, Any], *, status_code: int = 400) -> Dict[str, Any]:
    if result.get("error"):
        raise HTTPException(status_code, _scrub(str(result["error"])))
    return _scrub(result)


def _model_values(model: BaseModel, *, exclude_unset: bool = False) -> Dict[str, Any]:
    """Support both Pydantic v2 and older FastAPI/Pydantic combinations."""
    dump = getattr(model, "model_dump", None)
    return dump(exclude_unset=exclude_unset) if dump else model.dict(exclude_unset=exclude_unset)


@app.get("/api/health")
def health():
    vision = crop_doctor.model_status()
    symptoms = symptom_model_status()
    try:
        product_db = product_verifier.verifier_status()
    except Exception:
        product_db = {"available": False}
    db_error = getattr(app.state, "database_error", None)
    try:
        scheme_available = bool(subsidy_matcher.load_schemes().get("schemes"))
    except (FileNotFoundError, OSError, ValueError):
        scheme_available = False
    fertilizer_available = bool(fertilizer.available_crops())
    ready = bool(
        vision["active"]
        and symptoms["available"]
        and fertilizer_available
        and scheme_available
        and product_db.get("available", False)
        and not db_error
    )
    return {
        "status": "ok" if ready else "degraded",
        "service": "agrivision-api",
        "features": {
            "crop_diagnosis": {
                "available": bool(vision["active"]),
                "model": vision["active"],
                "loaded": bool(vision.get("loaded", False)),
            },
            "symptom_analysis": {
                "available": symptoms["available"],
                "loaded": bool(symptoms.get("loaded", False)),
            },
            "gradcam": {
                "available": bool(vision["active"]),
                "loaded": bool(vision.get("loaded", False)),
            },
            "weather": {"available": True, "live_configured": weather_status()["configured"]},
            "fertilizer": {"available": fertilizer_available},
            "product_verification": {"available": product_db.get("available", False)},
            "schemes": {"available": scheme_available},
        },
        "errors": {
            key: value for key, value in getattr(app.state, "model_load_issues", {}).items() if value
        } | ({"database": db_error} if db_error else {}),
    }


@app.post("/api/crop/diagnose")
def diagnose_crop(
    image: UploadFile = File(...),
    symptoms: Optional[str] = Form(default=None, max_length=5_000),
):
    data = _read_upload(image)
    pil_image = _validated_image(data)
    image_result = crop_doctor.predict_image(data)
    symptom_result = predict_symptoms(symptoms) if symptoms and symptoms.strip() else None
    combined = crop_doctor.combine_signals(image_result, symptom_result)
    if combined.get("is_confident"):
        explanation = generate_description(image_result, symptom_result, symptoms or "", combined)
    else:
        explanation = {
            "text": fallback_diagnosis(image_result, symptom_result, combined, symptoms or ""),
            "source": "offline-fallback",
            "used_ai": False,
            "model": None,
            "error": None,
            "prompt": None,
        }
    recommendations = []
    if image_result and not image_result.get("error") and image_result.get("label"):
        recommendations.append(recommendation_for_image(image_result))
    elif symptom_result and not symptom_result.get("error") and symptom_result.get("advice"):
        recommendations.append(symptom_result["advice"])
    result = {
        "image": image_result,
        "symptoms": symptom_result,
        "combined": combined,
        "explanation": explanation,
        "recommendations": recommendations,
        "image_warning": None if is_probably_leaf_image(pil_image) else
            "This image may be unsuitable for leaf diagnosis; use a clear, close-up crop photo.",
    }
    return _scrub(result)


@app.post("/api/symptoms/predict")
def symptom_prediction(payload: SymptomsRequest):
    result = predict_symptoms(payload.text)
    return _module_result(result)


@app.post("/api/crop/gradcam")
def gradcam(
    image: UploadFile = File(...),
    target_label: Optional[str] = Query(default=None, max_length=160),
    alpha: float = Query(default=0.45, ge=0.0, le=1.0),
):
    pil_image = _validated_image(_read_upload(image))
    if not is_probably_leaf_image(pil_image):
        logger.info("Grad-CAM requested for an image that may not show a leaf")
    alpha_val = float(getattr(alpha, "default", alpha))
    result = crop_doctor.gradcam_for_image(pil_image, target_label=target_label, alpha=alpha_val)
    if result.get("error"):
        raise HTTPException(503, _scrub(str(result["error"])))
    images = {}
    for key in ("overlay_image", "heatmap_image", "original_image"):
        buffer = io.BytesIO()
        result[key].save(buffer, format="PNG")
        images[key.replace("_image", "")] = base64.b64encode(buffer.getvalue()).decode("ascii")
    return _scrub({
        "label": result.get("label"),
        "explained_label": result.get("explained_label"),
        "predicted_index": result.get("predicted_index"),
        "confidence": result.get("confidence"),
        "alpha": result.get("alpha"),
        "model_used": result.get("model_used"),
        "images": images,
    })


@app.get("/api/weather")
def weather(
    city: str = Query(min_length=1, max_length=160),
    use_ai: bool = True,
    temperature: Optional[float] = Query(default=None, ge=-80, le=65),
    humidity: Optional[int] = Query(default=None, ge=0, le=100),
    rainfall: Optional[float] = Query(default=None, ge=0, le=500),
):
    if (temperature is None) != (humidity is None):
        raise HTTPException(422, "Manual weather requires both temperature and humidity.")
    manual_values = (
        {"temperature": temperature, "humidity": humidity, "rainfall": rainfall}
        if temperature is not None and humidity is not None
        else None
    )
    result = weather_report(city.strip(), manual_values=manual_values, use_ai=use_ai)
    if result.get("error"):
        raise HTTPException(503, _scrub(str(result["error"])))
    return _scrub(result)


@app.get("/api/fertilizer/options")
def fertilizer_options(crop: Optional[str] = Query(default=None, max_length=100)):
    crops = fertilizer.available_crops()
    return {
        "crops": crops,
        "deficiencies": fertilizer.deficiencies_for_crop(crop) if crop else [],
    }


@app.post("/api/fertilizer/calculate")
def fertilizer_calculation(payload: FertilizerRequest):
    return _module_result(
        fertilizer.calculate(payload.crop, payload.deficiency, payload.land_size, payload.unit)
    )


@app.post("/api/products/verify")
def verify_product(payload: ProductCodeRequest):
    result = product_verifier.verify_product(payload.code)
    if result.get("error") and not result.get("found"):
        if result["error"] == "empty code":
            raise HTTPException(422, "Please enter a product code.")
        raise HTTPException(503, "The product registry is temporarily unavailable.")
    return _scrub(result)


@app.post("/api/products/verify-qr")
def verify_qr(image: UploadFile = File(...)):
    data = _read_upload(image)
    _validated_image(data)
    decoded = product_verifier.decode_qr_from_image(data)
    if decoded.get("error"):
        raise HTTPException(422, _scrub(str(decoded["error"])))
    verified = product_verifier.verify_product(decoded["code"])
    if verified.get("error") and not verified.get("found"):
        raise HTTPException(503, "The product registry is temporarily unavailable.")
    return _scrub({"qr": decoded, "verification": verified})


@app.get("/api/products")
def product_registry(limit: int = Query(default=100, ge=1, le=500)):
    return {"products": product_verifier.list_registry(limit=limit)}


@app.get("/api/schemes")
def list_schemes():
    try:
        data = subsidy_matcher.load_schemes()
    except FileNotFoundError:
        raise HTTPException(503, "Scheme data is currently unavailable.")
    return {"schemes": data["schemes"], "meta": data.get("meta", {})}


@app.get("/api/schemes/options")
def scheme_options():
    return {
        "regions": subsidy_matcher.REGIONS,
        "crops": subsidy_matcher.crop_options(),
        "categories": subsidy_matcher.scheme_categories(),
    }


@app.post("/api/schemes/match")
def match_schemes(payload: SchemeMatchRequest):
    result = subsidy_matcher.match_schemes(
        payload.land_size_acres, payload.region, payload.crop, payload.category
    )
    return _module_result(result, status_code=503)
