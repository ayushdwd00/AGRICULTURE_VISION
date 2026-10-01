"""
utils/gemini.py
===============
Small, defensive wrapper around the Google Gemini API used by AgriVision.

Design rules (from the project brief)
-------------------------------------
* The API key always comes from ``.env`` (``GEMINI_API_KEY``) - it is never
  hardcoded and never logged.
* Gemini only *explains* results produced by the models.  It must not invent a
  different diagnosis: the prompt receives the classifier outputs and the
  disagreement flag, and is told to report both possibilities when the two
  models disagree.
* Every function is failure-proof: when the key is missing, the network is down
  or the API errors out, a clearly labelled **offline fallback** text built
  from deterministic templates is returned instead, and the Streamlit app keeps
  working.

Public helpers
--------------
``is_configured()``            - is a Gemini key available?
``gemini_status()``            - status dictionary for the UI
``generate_description()``     - Crop Doctor diagnosis (3-4 sentences)
``generate_weather_message()`` - farmer friendly weather / disease-risk warning
``ask_assistant()``            - free-form agriculture Q&A
``build_diagnosis_prompt()``   - the exact prompt (useful for the report)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from utils.helpers import PROJECT_ROOT, disease_category, is_healthy_label, pretty_label

DEFAULT_MODEL: str = "gemini-2.0-flash"
_ENV_LOADED = False

#: Guard rails shared by every prompt - keeps Gemini inside its role.
SAFETY_RULES: str = (
    "Rules:\n"
    "1. Base your answer ONLY on the classifier results and the farmer's words given below.\n"
    "2. Never replace or contradict the classifier labels; if the evidence is mixed, say so.\n"
    "3. Do not invent government scheme names, fertiliser quantities or product verification results.\n"
    "4. Never promise a chemical dosage; suggest confirming with a local agricultural extension officer.\n"
    "5. Be concise, avoid jargon, and write for a farmer with basic schooling."
)

class GeminiError(RuntimeError):
    """Raised internally when the Gemini call cannot be completed."""

def _load_environment() -> None:
    """Load ``.env`` from the project root exactly once."""
    global _ENV_LOADED
    if not _ENV_LOADED:
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        _ENV_LOADED = True

def get_api_key() -> Optional[str]:
    """Return the configured Gemini API key (or ``None``)."""
    _load_environment()
    key = (os.getenv("GEMINI_API_KEY") or "").strip()
    return key or None

def get_model_name() -> str:
    """Model id from ``GEMINI_MODEL`` (falls back to ``gemini-2.0-flash``)."""
    _load_environment()
    return (os.getenv("GEMINI_MODEL") or "").strip() or DEFAULT_MODEL

def is_configured() -> bool:
    """True when a Gemini API key is present."""
    return get_api_key() is not None

def gemini_status() -> Dict[str, Any]:
    """Status dictionary used by the sidebar / dashboard."""
    return {
        "configured": is_configured(),
        "model": get_model_name(),
        "env_file": str(PROJECT_ROOT / ".env"),
        "sdk": _detect_sdk(),
    }

def _detect_sdk() -> str:
    """
    Which Google SDK can we talk to?

    ``google-genai`` (current) is preferred, ``google-generativeai`` (legacy)
    is kept as a fallback because both appear in the wild.
    """
    try:  # pragma: no cover - depends on installed packages
        import google.genai  # noqa: F401

        return "google-genai"
    except Exception:
        pass
    try:  # pragma: no cover
        import google.generativeai  # noqa: F401

        return "google-generativeai"
    except Exception:
        return "not installed"

def _generate(prompt: str, system_instruction: str, temperature: float = 0.4) -> str:
    """Call Gemini and return the text. Raises :class:`GeminiError` on failure."""
    api_key = get_api_key()
    if not api_key:
        raise GeminiError(
            "GEMINI_API_KEY is not set. Add it to the .env file to enable AI explanations."
        )
    model_name = get_model_name()

    try:
        from google import genai  # type: ignore

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": temperature,
            },
        )
        text = (getattr(response, "text", None) or "").strip()
        if text:
            return text
        raise GeminiError("Gemini returned an empty response.")
    except GeminiError:
        raise
    except Exception as exc:  # noqa: BLE001 - try the legacy SDK before giving up
        first_error = f"{type(exc).__name__}: {exc}"

    try:
        import google.generativeai as legacy  # type: ignore

        legacy.configure(api_key=api_key)
        model = legacy.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            generation_config={"temperature": temperature},
        )
        response = model.generate_content(prompt)
        text = (getattr(response, "text", None) or "").strip()
        if text:
            return text
        raise GeminiError("Gemini returned an empty response.")
    except GeminiError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise GeminiError(
            f"Gemini call failed ({first_error} | {type(exc).__name__}: {exc})"
        ) from exc

# Deterministic offline fallbacks (used when Gemini is unavailable)

def _image_phrase(image_result: Optional[Dict[str, Any]]) -> str:
    if not image_result or image_result.get("error") or not image_result.get("label"):
        return "the photo could not be analysed"
    pretty = image_result.get("pretty_label") or pretty_label(image_result["label"])
    confidence = float(image_result.get("confidence") or 0.0) * 100
    return f"the leaf photo points to {pretty} ({confidence:.0f}% confidence)"

def _symptom_phrase(symptom_result: Optional[Dict[str, Any]]) -> str:
    if not symptom_result or symptom_result.get("error") or not symptom_result.get("label"):
        return ""
    confidence = float(symptom_result.get("confidence") or 0.0) * 100
    return (
        f"the described symptoms fit {symptom_result['label']} "
        f"({confidence:.0f}% confidence)"
    )

def recommendation_for_image(image_result: Optional[Dict[str, Any]]) -> str:
    """Return the existing safe next step for an image prediction (never a dosage)."""
    if not image_result or not image_result.get("label"):
        return "Please add a clearer photograph and describe the symptoms in your own words."
    label = str(image_result["label"])
    if is_healthy_label(label):
        return "Keep monitoring the crop and continue your normal care routine."
    advice = {
        "fungal": "Remove the worst affected leaves, avoid wetting the foliage and ask your local "
                  "agricultural officer about a suitable fungicide schedule.",
        "bacterial": "Avoid overhead watering, remove infected plants and clean your tools before "
                     "moving to healthy beds.",
        "viral": "There is no direct cure for viral diseases - control the insect vector and remove "
                 "infected plants so the rest of the field stays healthy.",
        "pest": "Check the underside of the leaves and act early with an approved control before the "
                "pest population grows.",
    }.get(disease_category(label))
    if advice:
        return advice
    return "Show these results to your local agricultural extension officer before spraying anything."

def fallback_diagnosis(
    image_result: Optional[Dict[str, Any]] = None,
    symptom_result: Optional[Dict[str, Any]] = None,
    combined: Optional[Dict[str, Any]] = None,
    symptom_text: str = "",
) -> str:
    """
    Deterministic, clearly labelled replacement for the Gemini explanation.

    It is assembled purely from the classifier outputs and the confidence rule,
    so it cannot invent information - it only phrases what the models decided.
    """
    parts: List[str] = [
        "Offline summary (AI explanation unavailable - no Gemini API key, or the "
        "service could not be reached):"
    ]
    statements = [
        phrase
        for phrase in (_image_phrase(image_result), _symptom_phrase(symptom_result))
        if phrase
    ]
    parts.append(
        "Based on the analysis, " + " and ".join(statements) + "."
        if statements
        else "No model result is available for this input yet."
    )

    combined = combined or {}
    if combined.get("disagreement_note"):
        parts.append(str(combined["disagreement_note"]))
    if combined.get("is_confident") is False:
        parts.append(
            "The combined confidence is below the 70% threshold, so treat this as an "
            "indication only and confirm it with an agricultural expert."
        )
    if symptom_text.strip():
        parts.append(f'You described: "{symptom_text.strip()[:180]}".')
    parts.append(recommendation_for_image(image_result))
    return " ".join(parts)

def build_diagnosis_prompt(
    image_result: Optional[Dict[str, Any]] = None,
    symptom_result: Optional[Dict[str, Any]] = None,
    symptom_text: str = "",
    combined: Optional[Dict[str, Any]] = None,
) -> str:
    """The exact prompt sent to Gemini (also stored for the project report)."""
    image_ok = bool(image_result and not image_result.get("error") and image_result.get("label"))
    image_label = (
        (image_result.get("pretty_label") or image_result.get("label")) if image_ok else "not available"
    )
    image_confidence = image_result.get("confidence") if image_ok else None
    symptom_label = symptom_result.get("label") if symptom_result else "not provided"
    symptom_confidence = symptom_result.get("confidence") if symptom_result else None
    combined = combined or {}

    def _percent(value: Any) -> str:
        return f"{float(value):.2%}" if isinstance(value, (int, float)) else "n/a"

    lines = [
        "You are an agricultural advisor writing for a farmer.",
        "",
        "IMAGE MODEL RESULT (MobileNetV2 plant-disease classifier):",
        f"- predicted class : {image_label}",
        f"- confidence      : {_percent(image_confidence)}",
        "",
        "SYMPTOM CLASSIFIER RESULT (Random Forest on the farmer's description):",
        f"- predicted class : {symptom_label}",
        f"- confidence      : {_percent(symptom_confidence)}",
        "- extracted symptom features : "
        + (", ".join(symptom_result.get("detected_features") or []) if symptom_result else "none"),
        "",
        f"FARMER'S OWN WORDS: {symptom_text.strip() or '(not provided)'}",
        "",
        "COMBINED CONFIDENCE (min of the available model confidences): "
        f"{_percent(combined.get('combined_confidence', 0.0))} "
        f"(threshold {combined.get('threshold', 0.7):.0%})",
        f"MODELS AGREE: {'yes' if combined.get('agreement', True) else 'NO - they disagree'}",
    ]
    if combined.get("disagreement_note"):
        lines.append(f"DISAGREEMENT DETAIL: {combined['disagreement_note']}")
    lines += [
        "",
        "TASK: Write a 3-4 sentence diagnosis for the farmer.",
        "Sentence 1-2: the most likely problem and why it fits this evidence.",
        "Sentence 3: what the farmer should do next (no chemical doses).",
        "Sentence 4: if the two models disagree, mention BOTH possibilities explicitly and ask "
        "the farmer to confirm; otherwise suggest one simple confirmation step such as checking "
        "the underside of the leaves.",
        "",
        SAFETY_RULES,
    ]
    return "\n".join(lines)

# Public API

def _result(
    text: str, source: str, error: Optional[str] = None, prompt: Optional[str] = None
) -> Dict[str, Any]:
    """Uniform return payload for every Gemini helper."""
    return {
        "text": text,
        "source": source,          # "gemini" or "offline-fallback"
        "used_ai": source == "gemini",
        "model": get_model_name() if source == "gemini" else None,
        "error": error,
        "prompt": prompt,
    }

def generate_description(
    image_result: Optional[Dict[str, Any]] = None,
    symptom_result: Optional[Dict[str, Any]] = None,
    symptom_text: str = "",
    combined: Optional[Dict[str, Any]] = None,
    include_prompt: bool = False,
) -> Dict[str, Any]:
    """
    Generate the 3-4 sentence farmer-friendly diagnosis for the Crop Doctor.

    Parameters
    ----------
    image_result, symptom_result:
        Outputs of :func:`modules.crop_doctor.predict_image` and
        :func:`modules.symptom_model.predict_symptoms`.
    symptom_text:
        The farmer's raw description.
    combined:
        Output of :func:`modules.crop_doctor.combine_signals` (confidence rule).
    include_prompt:
        Also return the prompt that was sent (used by the report page).

    Returns
    -------
    ``{"text", "source", "used_ai", "model", "error", "prompt"}`` - never raises.
    """
    prompt = build_diagnosis_prompt(image_result, symptom_result, symptom_text, combined)
    system_instruction = (
        "You are AgriVision's crop doctor assistant. You explain the results of a plant "
        "disease image classifier and a symptom classifier to a farmer. " + SAFETY_RULES
    )
    try:
        text = _generate(prompt, system_instruction, temperature=0.35)
        return _result(text, "gemini", error=None, prompt=prompt if include_prompt else None)
    except GeminiError as exc:
        return _result(
            fallback_diagnosis(image_result, symptom_result, combined, symptom_text),
            "offline-fallback",
            error=str(exc),
            prompt=prompt if include_prompt else None,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return _result(
            fallback_diagnosis(image_result, symptom_result, combined, symptom_text),
            "offline-fallback",
            error=f"{type(exc).__name__}: {exc}",
            prompt=prompt if include_prompt else None,
        )

def fallback_weather_message(weather: Dict[str, Any], risks: List[Dict[str, Any]]) -> str:
    """Deterministic wording for the weather module when Gemini is unavailable."""
    city = weather.get("city") or "your area"
    temperature = weather.get("temperature")
    humidity = weather.get("humidity")
    description = weather.get("description") or ""
    parts = [
        "Offline weather summary (AI wording unavailable - no Gemini API key or the "
        "service could not be reached):",
        f"{city}: {temperature} C, humidity {humidity}%, {description}.",
    ]
    if risks:
        parts.append(
            "Risk flags: "
            + "; ".join(
                f"{risk.get('level', '')} {risk.get('title', '')}".strip() for risk in risks
            )
            + "."
        )
        parts.append(
            "Practical step: scout the field early in the morning, look under the leaves "
            "for spots or insects, and ask your extension officer before spraying."
        )
    else:
        parts.append(
            "No disease-risk rule was triggered by the current weather values. "
            "Continue normal field monitoring."
        )
    return " ".join(parts)

def generate_weather_message(
    weather: Dict[str, Any], risks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Turn the deterministic weather-risk rules into a farmer-friendly warning.

    The rules themselves are computed in ``modules/weather.py`` - Gemini only
    rephrases them, it never invents a new risk level.
    """
    rule_lines = [
        f"- {risk.get('level', '')} {risk.get('title', '')}: {risk.get('detail', '')}"
        for risk in risks
    ] or ["- no rule triggered"]
    prompt = "\n".join(
        [
            "A farmer wants a short weather advisory for their crop.",
            f"City: {weather.get('city')}",
            f"Temperature: {weather.get('temperature')} C (feels like {weather.get('feels_like')} C)",
            f"Humidity: {weather.get('humidity')} %",
            f"Rain (last hour): {weather.get('rain_1h')}",
            f"Conditions: {weather.get('description')}",
            f"Wind: {weather.get('wind_speed')} m/s",
            "",
            "RISK RULES THAT TRIGGERED:",
            *rule_lines,
            "",
            "TASK: Write 2-3 short sentences (max 60 words) telling the farmer what the "
            "weather means for their crop and one concrete action to take today.",
            "Do NOT invent a different risk level and do NOT mention pesticide doses.",
            "",
            SAFETY_RULES,
        ]
    )
    system_instruction = "You are AgriVision's weather advisory assistant. " + SAFETY_RULES
    try:
        text = _generate(prompt, system_instruction, temperature=0.4)
        return _result(text, "gemini")
    except GeminiError as exc:
        return _result(fallback_weather_message(weather, risks), "offline-fallback", error=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        return _result(
            fallback_weather_message(weather, risks),
            "offline-fallback",
            error=f"{type(exc).__name__}: {exc}",
        )

ASSISTANT_PREAMBLE: str = (
    "You are the AgriVision agriculture assistant for Indian farmers. AgriVision has these "
    "tools: Crop Doctor (leaf photo + symptom description -> disease diagnosis with Grad-CAM), "
    "Weather & Crop Risk, Fertilizer Calculator (rule based, per acre), "
    "Product Verifier (registered product codes), Government Schemes matcher and an "
    "Equipment Rental marketplace."
)

def fallback_assistant_answer(question: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Rule-based assistant reply used when Gemini is unavailable."""
    lowered = (question or "").lower()
    context = context or {}
    hints: List[str] = []
    if context.get("last_diagnosis"):
        hints.append(f"your last Crop Doctor result was {context['last_diagnosis']}")
    if context.get("weather"):
        hints.append(f"the last weather check showed {context['weather']}")

    if any(word in lowered for word in ("yellow", "chlorosis", "pale")):
        reply = (
            "Yellowing can come from nutrient deficiency (often nitrogen), water stress or a "
            "disease. Upload a clear leaf photo in Crop Doctor and describe the symptoms there "
            "for a specific analysis."
        )
    elif any(word in lowered for word in ("spot", "blight", "fungus", "fungal", "mildew")):
        reply = (
            "Spots and blights are usually fungal or bacterial. Crop Doctor can classify a leaf "
            "photo, and the Weather page shows when humidity and temperature favour fungal "
            "spread."
        )
    elif any(word in lowered for word in ("fertiliser", "fertilizer", "urea", "dose", "npk")):
        reply = (
            "For doses use the Fertilizer Calculator - it is a fixed per-acre lookup table, not an "
            "AI guess. A soil test report tells you which nutrient is actually missing."
        )
    elif any(word in lowered for word in ("scheme", "subsidy", "loan", "insurance", "government")):
        reply = (
            "Open the Government Schemes page: it matches your land size, region and crop against "
            "the official scheme list and links to the real application pages."
        )
    elif any(word in lowered for word in ("rent", "tractor", "harvester", "machine", "equipment")):
        reply = (
            "The Equipment Rental page lists machines with hourly and daily rates. You can list "
            "your own machine there too."
        )
    elif any(word in lowered for word in ("weather", "rain", "humidity", "temperature")):
        reply = (
            "Enter your city on the Weather & Crop Risk page to see the current temperature, "
            "humidity and the disease-risk rules that apply."
        )
    else:
        reply = (
            "I can help with crop disease diagnosis, weather risk, fertiliser "
            "planning, scheme matching and equipment rental. "
            "Start with Crop Doctor: upload a leaf photo and describe what you see."
        )

    prefix = "Offline answer (no Gemini API key or the service could not be reached). "
    if hints:
        prefix += "I can use your AgriVision context: " + "; ".join(hints) + ". "
    return prefix + reply

def ask_assistant(
    question: str,
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Free-form agriculture question for the AI Agriculture Assistant page.

    ``context`` carries recent AgriVision results (last diagnosis, weather) and
    ``history`` a short chat transcript so follow-up questions make sense.
    """
    context = context or {}
    transcript_lines: List[str] = []
    for turn in (history or [])[-6:]:
        role = "Farmer" if turn.get("role") == "user" else "Assistant"
        transcript_lines.append(f"{role}: {str(turn.get('content', ''))[:400]}")

    prompt_lines = [
        ASSISTANT_PREAMBLE,
        "",
        "AGRIVISION CONTEXT (results the farmer already has):",
        f"- last crop diagnosis : {context.get('last_diagnosis') or 'none yet'}",
        f"- last weather result : {context.get('weather') or 'none yet'}",
        f"- detected symptom features: {context.get('symptom_features') or 'none'}",
    ]
    if transcript_lines:
        prompt_lines += ["", "RECENT CONVERSATION:", *transcript_lines]
    prompt_lines += [
        "",
        f"FARMER'S QUESTION: {question.strip()}",
        "",
        "TASK: Answer in 2-5 short sentences. Be practical and specific. If the question needs "
        "data AgriVision does not have, say which page of the app can produce it. Never invent "
        "scheme names, official links, exact fertiliser doses or product verification results.",
        "",
        SAFETY_RULES,
    ]
    system_instruction = "You are the AgriVision agriculture assistant. " + SAFETY_RULES
    try:
        text = _generate("\n".join(prompt_lines), system_instruction, temperature=0.5)
        return _result(text, "gemini")
    except GeminiError as exc:
        return _result(
            fallback_assistant_answer(question, context), "offline-fallback", error=str(exc)
        )
    except Exception as exc:  # pragma: no cover - defensive
        return _result(
            fallback_assistant_answer(question, context),
            "offline-fallback",
            error=f"{type(exc).__name__}: {exc}",
        )
