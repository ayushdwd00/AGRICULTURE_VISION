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
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from PIL import Image
from pydantic import BaseModel, Field

from backend.security import issue_token, read_token
from modules import crop_doctor, equipment_rental, fertilizer, product_verifier, subsidy_matcher
from modules.symptom_model import predict_symptoms, symptom_model_status
from modules.weather import weather_report, weather_status
from utils.database import init_products_db, init_rental_db
from utils.gemini import fallback_diagnosis, generate_description, recommendation_for_image
from utils.helpers import is_probably_leaf_image, load_image_from_bytes

logger = logging.getLogger("agrivision.api")
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
TOKEN_LIFETIME_SECONDS = 86_400
bearer = HTTPBearer(auto_error=False)


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


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=256)
    role: str = Field(default="farmer", pattern="^(farmer|owner)$")
    full_name: str = Field(default="", max_length=160)
    phone: str = Field(default="", max_length=40)
    location: str = Field(default="", max_length=160)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class MachineRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    machine_type: str = Field(min_length=1, max_length=80)
    hourly_rate: float = Field(gt=0, le=100_000_000)
    daily_rate: float = Field(gt=0, le=100_000_000)
    location: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2_000)


class MachinePatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=160)
    machine_type: Optional[str] = Field(default=None, min_length=1, max_length=80)
    hourly_rate: Optional[float] = Field(default=None, gt=0, le=100_000_000)
    daily_rate: Optional[float] = Field(default=None, gt=0, le=100_000_000)
    location: Optional[str] = Field(default=None, min_length=1, max_length=160)
    description: Optional[str] = Field(default=None, max_length=2_000)
    available: Optional[bool] = None


class BookingRequest(BaseModel):
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: str = Field(default="", max_length=2_000)


def _check_model_availability() -> Dict[str, Optional[str]]:
    """Verify model files exist on disk at startup without loading them into memory."""
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
        init_rental_db()
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


def _current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> Dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    claims = None
    try:
        claims = read_token(credentials.credentials)
        user = equipment_rental.get_user(int(claims["sub"]))
    except (ValueError, TypeError):
        user = None
    if not user or not claims or user.get("role") != claims.get("role"):
        raise HTTPException(401, "Invalid or expired access token.", headers={"WWW-Authenticate": "Bearer"})
    return user


def _require_role(user: Dict[str, Any], role: str) -> None:
    if user.get("role") != role:
        raise HTTPException(403, f"This action requires the {role} role.")


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
        rental_db = equipment_rental.marketplace_status()
    except Exception:
        product_db, rental_db = {"available": False}, {"available": False}
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
        and rental_db.get("available", False)
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
            "equipment": {"available": rental_db.get("available", False)},
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


@app.get("/api/rental/machines")
def machines(
    location: Optional[str] = Query(default=None, max_length=160),
    machine_type: Optional[str] = Query(default=None, max_length=80),
    owner_id: Optional[int] = Query(default=None, ge=1),
    available_only: bool = False,
):
    return {
        "machines": equipment_rental.list_machines(
            location=location,
            machine_type=machine_type,
            owner_id=owner_id,
            include_unavailable=not available_only,
        ),
        "types": equipment_rental.MACHINE_TYPES,
    }


@app.get("/api/rental/machines/{machine_id}")
def machine_detail(machine_id: int):
    result = equipment_rental.get_machine(machine_id)
    if not result:
        raise HTTPException(404, "Machine not found.")
    return result


@app.post("/api/rental/auth/register", status_code=201)
def register(payload: RegisterRequest):
    result = equipment_rental.register_user(**_model_values(payload))
    if not result["ok"]:
        raise HTTPException(409, _scrub(result["error"]))
    user = result["user"]
    return {
        "user": user,
        "access_token": issue_token(user["id"], user["role"], TOKEN_LIFETIME_SECONDS),
        "token_type": "bearer",
        "expires_in": TOKEN_LIFETIME_SECONDS,
    }


@app.post("/api/rental/auth/login")
def login(payload: LoginRequest):
    result = equipment_rental.login_user(payload.username, payload.password)
    if not result["ok"]:
        raise HTTPException(401, "Invalid username or password.")
    user = result["user"]
    return {
        "user": user,
        "access_token": issue_token(user["id"], user["role"], TOKEN_LIFETIME_SECONDS),
        "token_type": "bearer",
        "expires_in": TOKEN_LIFETIME_SECONDS,
    }


@app.get("/api/rental/auth/me")
def current_user(user: Dict[str, Any] = Depends(_current_user)):
    return {"user": user}


@app.post("/api/rental/machines", status_code=201)
def add_machine(payload: MachineRequest, user: Dict[str, Any] = Depends(_current_user)):
    _require_role(user, "owner")
    result = equipment_rental.add_machine(owner_id=user["id"], **payload.model_dump())
    if not result["ok"]:
        raise HTTPException(400, _scrub(result["error"]))
    return {"machine": equipment_rental.get_machine(result["machine_id"])}


@app.patch("/api/rental/machines/{machine_id}")
def update_machine(
    machine_id: int, payload: MachinePatch, user: Dict[str, Any] = Depends(_current_user)
):
    _require_role(user, "owner")
    result = equipment_rental.update_machine(
        machine_id, user["id"], **_model_values(payload, exclude_unset=True)
    )
    if not result["ok"]:
        if result["error"] == "Machine not found.":
            status_code = 404
        elif result["error"] == "You can only edit machines that you listed.":
            status_code = 403
        else:
            status_code = 400
        raise HTTPException(status_code, result["error"])
    return {"machine": equipment_rental.get_machine(machine_id)}


@app.delete("/api/rental/machines/{machine_id}")
def delete_machine(machine_id: int, user: Dict[str, Any] = Depends(_current_user)):
    _require_role(user, "owner")
    result = equipment_rental.delete_machine(machine_id, user["id"])
    if not result["ok"]:
        raise HTTPException(404 if result["error"] == "Machine not found." else 403, result["error"])
    return {"deleted": True}


@app.get("/api/rental/bookings")
def list_bookings(user: Dict[str, Any] = Depends(_current_user)):
    if user["role"] == "owner":
        results = equipment_rental.bookings_for_owner(user["id"])
    else:
        results = equipment_rental.bookings_for_farmer(user["id"])
    return {"bookings": results}


@app.post("/api/rental/machines/{machine_id}/bookings", status_code=201)
def create_booking(
    machine_id: int, payload: BookingRequest, user: Dict[str, Any] = Depends(_current_user)
):
    _require_role(user, "farmer")
    result = equipment_rental.create_booking(
        machine_id, user["id"], payload.start_date, payload.end_date, payload.notes
    )
    if not result["ok"]:
        raise HTTPException(409, _scrub(result["error"]))
    return result


@app.delete("/api/rental/bookings/{booking_id}")
def cancel_booking(booking_id: int, user: Dict[str, Any] = Depends(_current_user)):
    result = equipment_rental.cancel_booking(booking_id, user["id"])
    if not result["ok"]:
        raise HTTPException(403 if "Only the farmer" in result["error"] else 404, result["error"])
    return {"cancelled": True}
