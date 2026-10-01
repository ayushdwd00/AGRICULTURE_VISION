"""
app.py
======
AgriVision - Smart Agriculture Super-App (Streamlit entry point).

Run with::

    streamlit run app.py

This file only holds presentation code: one render function per page plus the
sidebar navigation. All logic lives in ``modules/`` and ``utils/``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

from utils.helpers import (
    CONFIDENCE_THRESHOLD,
    UNCERTAIN_MESSAGE,
    confidence_band,
    ensure_directories,
    format_percent,
    pretty_label,
    timestamp,
)

st.set_page_config(
    page_title="AgriVision - Smart Agriculture Super-App",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES: List[str] = [
    "🏠 Dashboard",
    "🩺 Crop Doctor",
    "🌦️ Weather & Risk",
    "🧮 Fertilizer Calculator",
    "🔐 Product Verifier",
    "🏛️ Government Schemes",
    "🚜 Equipment Rental",
    "🤖 AI Agriculture Assistant",
]

DASHBOARD_ACTIONS: List[tuple] = [
    ("🩺 Diagnose Crop", "🩺 Crop Doctor"),
    ("🌦️ Check Weather", "🌦️ Weather & Risk"),
    ("🧮 Fertilizer Calculator", "🧮 Fertilizer Calculator"),
]

SESSION_DEFAULTS: Dict[str, Any] = {
    "page": PAGES[0],
    "diagnosis_history": [],
    "uploaded_image_bytes": None,
    "uploaded_image_name": None,
    "last_diagnosis": None,
    "symptom_text": "",
    "weather_result": None,
    "weather_city": "",
    "user": None,
    "rental_selected_machine": None,
    "assistant_history": [],
}

# Colours shared by the custom HTML blocks.
TONE_COLORS = {
    "good": "#1f8a4c",
    "warn": "#c77700",
    "bad": "#c0392b",
    "info": "#1a6fb5",
    "muted": "#6b7280",
}

APP_CSS = """
<style>
  :root {
    --agv-radius: 14px;
    --agv-border: rgba(127, 127, 127, 0.22);
    --agv-surface: rgba(127, 127, 127, 0.07);
    --agv-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
  }

  .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1200px; }
  h1, h2, h3, h4 { letter-spacing: -0.01em; }
  h1 { font-weight: 700; }

  /* page header */
  .agv-hero {
    padding: 1.1rem 1.3rem; margin-bottom: 0.4rem;
    border: 1px solid var(--agv-border); border-radius: var(--agv-radius);
    background: linear-gradient(135deg, var(--agv-surface), transparent 70%);
  }
  .agv-hero h1 { margin: 0 0 0.25rem 0; font-size: 1.85rem; }
  .agv-hero p { margin: 0; opacity: 0.78; font-size: 0.95rem; }

  /* status / info cards */
  .agv-card {
    border: 1px solid var(--agv-border); border-radius: var(--agv-radius);
    padding: 0.85rem 1rem; margin-bottom: 0.7rem; background: var(--agv-surface);
    box-shadow: var(--agv-shadow);
  }
  .agv-card .agv-label {
    font-size: 0.74rem; font-weight: 600; letter-spacing: 0.07em;
    text-transform: uppercase; opacity: 0.7; margin-bottom: 0.25rem;
  }
  .agv-card .agv-value { font-size: 1.05rem; font-weight: 600; line-height: 1.35; }

  .agv-section {
    font-size: 1.08rem; font-weight: 650; margin: 1.1rem 0 0.55rem 0;
    padding-left: 0.6rem; border-left: 4px solid #1f8a4c;
  }

  /* confidence bar */
  .agv-bar-track {
    height: 9px; border-radius: 999px; background: rgba(127, 127, 127, 0.18);
    overflow: hidden; margin: 0.35rem 0 0.3rem 0;
  }
  .agv-bar-fill { height: 100%; border-radius: 999px; }
  .agv-bar-caption { font-size: 0.8rem; opacity: 0.75; }

  .agv-ai {
    border: 1px solid var(--agv-border); border-left: 4px solid #1a6fb5;
    border-radius: var(--agv-radius); padding: 0.9rem 1.1rem;
    background: var(--agv-surface); margin: 0.35rem 0 0.2rem 0; line-height: 1.55;
  }

  /* buttons */
  .stButton > button {
    border-radius: 10px; font-weight: 550; padding: 0.45rem 0.9rem;
    transition: transform 0.08s ease, box-shadow 0.15s ease;
  }
  .stButton > button:hover { transform: translateY(-1px); box-shadow: var(--agv-shadow); }

  /* sidebar */
  section[data-testid="stSidebar"] { border-right: 1px solid var(--agv-border); }
  section[data-testid="stSidebar"] .agv-brand {
    padding: 0.2rem 0 0.6rem 0; border-bottom: 1px solid var(--agv-border);
    margin-bottom: 0.5rem;
  }
  section[data-testid="stSidebar"] .agv-brand .agv-title { font-size: 1.25rem; font-weight: 700; }
  section[data-testid="stSidebar"] .agv-brand .agv-sub { font-size: 0.78rem; opacity: 0.7; }
  section[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding: 0.35rem 0.5rem; border-radius: 9px; margin-bottom: 0.12rem;
  }
  section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: var(--agv-surface);
  }

  /* metrics & expanders */
  div[data-testid="stMetric"] {
    border: 1px solid var(--agv-border); border-radius: var(--agv-radius);
    padding: 0.7rem 0.9rem; background: var(--agv-surface);
  }
  div[data-testid="stMetricValue"] { font-size: 1.35rem; }
  details[data-testid="stExpander"] {
    border-radius: var(--agv-radius); border: 1px solid var(--agv-border);
  }
</style>
"""

def init_session_state() -> None:
    """Create the session-state keys AgriVision relies on."""
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, list) else value
    if st.session_state.get("page") not in PAGES:
        st.session_state["page"] = PAGES[0]

def goto(page: str) -> None:
    """Switch page from a button callback."""
    st.session_state["page"] = page

def inject_styles() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)

def page_header(title: str, subtitle: str, icon: str = "🌾") -> None:
    st.markdown(
        f'<div class="agv-hero"><h1>{icon} {title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )

def section_title(text: str) -> None:
    st.markdown(f'<div class="agv-section">{text}</div>', unsafe_allow_html=True)

def status_chip(label: str, value: str, tone: str = "info") -> None:
    """Colour-coded status card."""
    color = TONE_COLORS.get(tone, TONE_COLORS["info"])
    st.markdown(
        f"""<div class="agv-card" style="border-left:4px solid {color};">
              <div class="agv-label">{label}</div>
              <div class="agv-value" style="color:{color};">{value}</div>
            </div>""",
        unsafe_allow_html=True,
    )

def confidence_bar(value: float, caption: str = "Confidence") -> None:
    """Thin bar showing the confidence value and its band."""
    value = max(0.0, min(1.0, float(value or 0.0)))
    band = confidence_band(value)
    color = {"High": TONE_COLORS["good"], "Medium": TONE_COLORS["warn"]}.get(
        band, TONE_COLORS["bad"]
    )
    st.markdown(
        f"""<div class="agv-bar-track">
              <div class="agv-bar-fill" style="width:{value * 100:.1f}%;background:{color};"></div>
            </div>
            <div class="agv-bar-caption">{caption}: <b>{format_percent(value)}</b> ({band})</div>""",
        unsafe_allow_html=True,
    )

def show_ai_result(result: Dict[str, Any], heading: str = "AI Explanation") -> None:
    """Show a Gemini answer (or its offline fallback) with its source."""
    section_title(heading)
    st.caption(
        f"Generated by Gemini ({result.get('model')})"
        if result.get("used_ai")
        else "Offline fallback text (no AI) - " + str(result.get("error") or "Gemini unavailable")
    )
    st.markdown(
        f'<div class="agv-ai">{result.get("text") or "No text returned."}</div>',
        unsafe_allow_html=True,
    )

VOICE_COMPONENT_HTML = """
<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;">
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
    <button id="agv-mic"
      style="background:#1e8e3e;color:#fff;border:none;border-radius:8px;
             padding:10px 16px;font-size:15px;cursor:pointer;">🎙️ Start speaking</button>
    <button id="agv-copy"
      style="background:#1565c0;color:#fff;border:none;border-radius:8px;
             padding:10px 16px;font-size:15px;cursor:pointer;">📋 Copy transcript</button>
    <span id="agv-status" style="font-size:13px;opacity:0.85;"></span>
  </div>
  <textarea id="agv-text" rows="3" placeholder="Your speech appears here - then copy it into
the symptom box below."
    style="width:100%;margin-top:10px;border-radius:8px;border:1px solid #bbb;padding:8px;
           font-size:14px;"></textarea>
</div>
<script>
  const statusEl = document.getElementById('agv-status');
  const textEl = document.getElementById('agv-text');
  const micBtn = document.getElementById('agv-mic');
  const copyBtn = document.getElementById('agv-copy');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SR) {
    statusEl.textContent = 'Speech recognition is not supported by this browser - please type or paste your description.';
    micBtn.disabled = true;
    micBtn.style.opacity = 0.5;
  } else {
    const recognition = new SR();
    recognition.lang = 'en-IN';
    recognition.continuous = true;
    recognition.interimResults = true;
    let listening = false;

    recognition.onresult = (event) => {
      let finalText = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) finalText += event.results[i][0].transcript + ' ';
      }
      if (finalText) textEl.value = (textEl.value + ' ' + finalText).trim();
    };
    recognition.onerror = (event) => {
      statusEl.textContent = 'Microphone error: ' + event.error +
        ' (the embedded frame may be blocked - use the text box below instead).';
      listening = false;
      micBtn.textContent = '🎙️ Start speaking';
    };
    recognition.onend = () => { listening = false; micBtn.textContent = '🎙️ Start speaking'; };

    micBtn.onclick = () => {
      if (listening) { recognition.stop(); return; }
      try {
        recognition.start();
        listening = true;
        micBtn.textContent = '⏹️ Stop';
        statusEl.textContent = 'Listening... speak clearly about what you see on the plant.';
      } catch (err) {
        statusEl.textContent = 'Could not start the microphone: ' + err.message;
      }
    };
  }

  copyBtn.onclick = async () => {
    try {
      await navigator.clipboard.writeText(textEl.value);
      statusEl.textContent = 'Transcript copied - paste it into the symptom box below.';
    } catch (err) {
      textEl.select();
      statusEl.textContent = 'Press Ctrl+C to copy the selected transcript.';
    }
  };
</script>
"""

def render_voice_input() -> None:
    """
    Browser-side speech-to-text (Web Speech API) rendered in an iframe component.

    Streamlit cannot read a value out of a raw HTML component, so the transcript
    is copied to the clipboard from inside the component and pasted into the
    symptom box - the reliable fallback required by the brief.  If the browser or
    the embedded frame blocks the microphone, typing still works.
    """
    st.caption(
        "Voice → speech-to-text runs fully in the browser (no extra speech model). "
        "Speak, then copy the transcript into the symptom box below."
    )
    st.components.v1.html(VOICE_COMPONENT_HTML, height=210, scrolling=False)

def symptom_input_area() -> str:
    """Symptom description box + optional voice panel. Returns the current text."""
    voice_col, _spacer = st.columns([1, 3])
    with voice_col:
        with st.expander("🎙️ Voice input", expanded=False):
            render_voice_input()

    text = st.text_area(
        "Describe the symptoms",
        value=st.session_state.get("symptom_text", ""),
        height=140,
        key="symptom_text_input",
        placeholder=(
            "Example: lower leaves are turning yellow with brown spots, the plant looks "
            "small and the soil is very wet."
        ),
    )
    st.session_state["symptom_text"] = text
    if text.strip():
        st.caption(
            "Symptom features are derived from this text by documented keyword rules. "
            "Mentioning leaf colour, spot pattern, wilting, curling and growth speed helps "
            "the classifier reach the 70% confidence threshold."
        )
    return text

def clear_crop_doctor_inputs() -> None:
    """Reset the Crop Doctor inputs (widget keys are dropped, not overwritten)."""
    st.session_state["uploaded_image_bytes"] = None
    st.session_state["uploaded_image_name"] = None
    st.session_state["last_diagnosis"] = None
    st.session_state["symptom_text"] = ""
    st.session_state.pop("symptom_text_input", None)  # resets the text area widget
    st.session_state.pop("cd_uploader", None)         # resets the file uploader widget

def load_evaluation_summary(path: Any) -> Optional[Dict[str, Any]]:
    """Read ``data/evaluation/evaluation_summary.json`` (``None`` when absent)."""
    from utils.helpers import load_json

    summary = load_json(path)
    return summary if isinstance(summary, dict) and summary.get("before") else None

# MODULE 1 - Crop Doctor

def run_crop_doctor(image_bytes: Optional[bytes], symptom_text: str) -> Dict[str, Any]:
    """
    Full Crop Doctor pipeline (image model + symptom model + confidence rule + AI).

    Never raises: every failure ends up in the returned dictionary so the page can
    show a friendly message (missing model, invalid image, API error, ...).
    """
    from modules.crop_doctor import combine_signals, gradcam_for_image, predict_image
    from modules.symptom_model import predict_symptoms
    from utils.gemini import generate_description
    from utils.helpers import load_image_from_bytes

    bundle: Dict[str, Any] = {
        "created_at": timestamp(),
        "image_result": None,
        "symptom_result": None,
        "combined": None,
        "explanation": None,
        "gradcam": None,
        "image_bytes": image_bytes,
        "symptom_text": symptom_text,
    }

    progress = st.progress(0.0, text="Starting the analysis ...")

    # 1) Image model ---------------------------------------------------------
    if image_bytes:
        with st.spinner("Analysing the leaf photograph (MobileNetV2) ..."):
            bundle["image_result"] = predict_image(image_bytes)
    progress.progress(0.40, text="Image model done.")

    # 2) Symptom classifier --------------------------------------------------
    if symptom_text.strip():
        with st.spinner("Classifying the described symptoms (Random Forest) ..."):
            bundle["symptom_result"] = predict_symptoms(symptom_text)
    progress.progress(0.65, text="Symptom model done.")

    # 3) Confidence rule: min(image_conf, symptom_conf) >= 0.70 --------------
    bundle["combined"] = combine_signals(bundle["image_result"], bundle["symptom_result"])

    # 4) Gemini explanation (only when the combined confidence is trusted) ---
    if bundle["combined"]["is_confident"]:
        with st.spinner("Writing the diagnosis with Gemini ..."):
            bundle["explanation"] = generate_description(
                image_result=bundle["image_result"],
                symptom_result=bundle["symptom_result"],
                symptom_text=symptom_text,
                combined=bundle["combined"],
                include_prompt=True,
            )
    progress.progress(0.85, text="Explanation ready.")

    # 5) Grad-CAM visual explanation ----------------------------------------
    if image_bytes:
        with st.spinner("Building the Grad-CAM visual explanation ..."):
            try:
                image = load_image_from_bytes(image_bytes)
                target = None
                if bundle["image_result"] and bundle["image_result"].get("label"):
                    target = bundle["image_result"]["label"]
                bundle["gradcam"] = gradcam_for_image(image, target_label=target)
            except Exception as exc:  # pragma: no cover - defensive
                bundle["gradcam"] = {"error": f"Grad-CAM failed: {exc}"}
    progress.progress(1.0, text="Finished.")
    return bundle

def render_diagnosis(bundle: Dict[str, Any]) -> None:
    """Render the 'Diagnosis Result' + 'AI Explanation' + 'Visual Explanation' blocks."""
    image_result = bundle.get("image_result") or {}
    symptom_result = bundle.get("symptom_result") or {}
    combined = bundle.get("combined") or {}

    image_error = image_result.get("error")
    symptom_error = symptom_result.get("error")

    st.subheader("Diagnosis Result")

    if not image_result and not symptom_result:
        st.warning("Upload a leaf photo and/or describe the symptoms before diagnosing.")
        return

    if image_error:
        st.error(f"Crop image analysis: {image_error}")
    if symptom_error:
        st.warning(f"Symptom analysis: {symptom_error}")

    column_image, column_symptom, column_severity = st.columns(3)
    with column_image:
        if image_result and not image_error:
            st.metric(
                "Disease (from photo)",
                image_result.get("condition") or pretty_label(image_result.get("label", "")),
            )
            st.caption(f"Crop: {image_result.get('crop')}")
            confidence_bar(image_result.get("confidence", 0.0), "Image confidence")
        else:
            st.metric("Disease (from photo)", "not available")
    with column_symptom:
        if symptom_result and not symptom_error:
            st.metric("Symptom Analysis", symptom_result.get("label"))
            confidence_bar(symptom_result.get("confidence", 0.0), "Symptom confidence")
            features = symptom_result.get("detected_features") or []
            if features:
                st.caption("Extracted features: " + ", ".join(features))
        else:
            st.metric("Symptom Analysis", "not provided")
    with column_severity:
        st.metric("Severity", combined.get("severity") or "unknown")
        st.metric(
            "Combined confidence", format_percent(combined.get("combined_confidence", 0.0))
        )

    st.divider()

    if not combined.get("is_confident", False):
        st.warning(UNCERTAIN_MESSAGE)
        st.caption(
            "Rule used: min(image confidence, symptom confidence) >= "
            f"{format_percent(CONFIDENCE_THRESHOLD, 0)} is required before an AI explanation "
            "is generated."
        )
    if not combined.get("agreement", True):
        st.info("⚠️ The two models disagree: " + str(combined.get("disagreement_note")))

    if bundle.get("explanation"):
        show_ai_result(bundle["explanation"], "AI Explanation")
    elif not combined.get("is_confident", False):
        st.caption("No AI explanation was generated because the combined confidence is low.")

    st.divider()
    st.subheader("Visual Explanation")
    gradcam = bundle.get("gradcam") or {}
    if gradcam.get("error"):
        st.info(f"Grad-CAM unavailable: {gradcam['error']}")
    elif gradcam.get("overlay_image") is not None:
        with st.expander("What does Grad-CAM show?", expanded=False):
            st.write(
                "Grad-CAM highlights the regions of the leaf that pushed the CNN toward the "
                "predicted class. Warm colours (red/yellow) are the most influential pixels. "
                "If the heat sits on the leaf lesion rather than the background, the prediction "
                "is based on real symptoms."
            )
        left, right = st.columns(2)
        with left:
            st.image(
                bundle.get("image_bytes"), caption="Original image", width="stretch"
            )
        with right:
            st.image(
                gradcam["overlay_image"], caption="Grad-CAM overlay", width="stretch"
            )
        heatmap_column, _spacer = st.columns([1, 1])
        with heatmap_column:
            st.image(
                gradcam["heatmap_image"],
                caption="Raw activation heat map",
                width="stretch",
            )
    else:
        st.caption("Upload a photo to see the Grad-CAM visual explanation.")

def crop_doctor_page() -> None:
    """🩺 Crop Doctor - the core AI module."""
    page_header(
        "Crop Doctor",
        "Upload a leaf photo and/or describe the symptoms. The image model, the symptom "
        "classifier and Gemini explain what is happening to your crop.",
        icon="🩺",
    )

    from utils.gemini import is_configured as gemini_configured

    try:
        from modules.crop_doctor import model_status
        from modules.symptom_model import symptom_model_status

        crop_status = model_status()
        symptom_status = symptom_model_status()
    except Exception as exc:  # pragma: no cover - defensive
        crop_status, symptom_status = {"active": None}, {"available": False}
        st.error(f"Could not inspect the models: {exc}")

    status_columns = st.columns(3)
    with status_columns[0]:
        status_chip(
            "Vision model",
            crop_status.get("active") or "not found",
            "good" if crop_status.get("active") else "bad",
        )
    with status_columns[1]:
        status_chip(
            "Symptom model",
            "ready" if symptom_status.get("available") else "not found",
            "good" if symptom_status.get("available") else "bad",
        )
    with status_columns[2]:
        status_chip(
            "Gemini AI",
            "configured" if gemini_configured() else "no API key (offline fallback)",
            "good" if gemini_configured() else "warn",
        )
    accuracy = symptom_status.get("accuracy")
    if accuracy is not None:
        st.caption(
            f"Symptom classifier trained on {symptom_status.get('n_rows')} labelled rows "
            f"(held-out accuracy {format_percent(accuracy)})."
        )
    if not crop_status.get("active"):
        st.error(
            "No vision model found. Run `python training/download_model.py` "
            "(and optionally `python training/fine_tune.py`) to enable the image analysis."
        )

    left_column, right_column = st.columns([1.05, 1])

    with left_column:
        section_title("1. Upload crop image")
        uploaded = st.file_uploader(
            "Crop leaf photo", type=["jpg", "jpeg", "png", "bmp", "webp"], key="cd_uploader"
        )
        image_bytes: Optional[bytes] = None
        if uploaded is not None:
            image_bytes = uploaded.getvalue()
            st.session_state["uploaded_image_bytes"] = image_bytes
            st.session_state["uploaded_image_name"] = uploaded.name
        elif st.session_state.get("uploaded_image_bytes"):
            image_bytes = st.session_state["uploaded_image_bytes"]
            st.caption(
                "Re-using the previously uploaded image: "
                f"{st.session_state.get('uploaded_image_name')}"
            )

        if image_bytes:
            from utils.helpers import is_probably_leaf_image, load_image_from_bytes

            try:
                preview = load_image_from_bytes(image_bytes)
                st.image(preview, caption="Image preview", width="stretch")
                if not is_probably_leaf_image(preview):
                    st.warning(
                        "This image looks very small or colourless - predictions may be "
                        "unreliable. A close-up photo of a single leaf works best."
                    )
            except ValueError as exc:
                st.error(str(exc))
                image_bytes = None

    with right_column:
        section_title("2. Describe symptoms")
        symptom_text = symptom_input_area()
        diagnose_clicked = st.button("🔍 Diagnose", type="primary", width="stretch")
        if st.button("🧹 Clear inputs", width="stretch"):
            clear_crop_doctor_inputs()
            st.rerun()

    if diagnose_clicked:
        if not image_bytes and not symptom_text.strip():
            st.warning("Please upload a photo and/or describe the symptoms first.")
        else:
            bundle = run_crop_doctor(image_bytes, symptom_text)
            st.session_state["last_diagnosis"] = bundle
            history: List[Dict[str, Any]] = st.session_state.get("diagnosis_history", [])
            history.insert(
                0,
                {
                    "time": bundle["created_at"],
                    "image": st.session_state.get("uploaded_image_name"),
                    "disease": (bundle.get("image_result") or {}).get("pretty_label"),
                    "image_confidence": (bundle.get("image_result") or {}).get("confidence"),
                    "symptom": (bundle.get("symptom_result") or {}).get("label"),
                    "symptom_confidence": (bundle.get("symptom_result") or {}).get("confidence"),
                    "combined_confidence": (bundle.get("combined") or {}).get(
                        "combined_confidence"
                    ),
                    "severity": (bundle.get("combined") or {}).get("severity"),
                    "confident": (bundle.get("combined") or {}).get("is_confident"),
                },
            )
            st.session_state["diagnosis_history"] = history[:20]
        st.divider()

    bundle = st.session_state.get("last_diagnosis")
    if bundle:
        render_diagnosis(bundle)

        image_result = bundle.get("image_result") or {}
        candidates = image_result.get("top_predictions") or []
        if candidates:
            with st.expander("Top-3 image model candidates", expanded=False):
                for rank, candidate in enumerate(candidates, start=1):
                    st.write(
                        f"{rank}. **{candidate['pretty_label']}** "
                        f"({format_percent(candidate['confidence'])})"
                    )
        explanation = bundle.get("explanation") or {}
        if explanation.get("prompt"):
            with st.expander("Prompt sent to Gemini (for the project report)", expanded=False):
                st.code(explanation["prompt"], language="text")

    history = st.session_state.get("diagnosis_history") or []
    if history:
        with st.expander(f"📋 Recent diagnoses ({len(history)})", expanded=False):
            for record in history[:8]:
                st.write(
                    f"**{record['time']}** — {record.get('disease') or 'no photo'} | "
                    f"symptoms: {record.get('symptom') or 'not provided'} | "
                    f"combined confidence: "
                    f"{format_percent(record.get('combined_confidence') or 0)} | "
                    f"{record.get('severity')}"
                )

# 🏠 Dashboard

def _crop_health_summary() -> tuple:
    """(text, tone) describing crop health from the last diagnosis."""
    bundle = st.session_state.get("last_diagnosis")
    if not bundle:
        return "No diagnosis yet", "muted"
    combined = bundle.get("combined") or {}
    image_result = bundle.get("image_result") or {}
    if not combined.get("is_confident"):
        return "Uncertain - retake photo", "warn"
    if image_result.get("is_healthy"):
        return "🟢 Good (leaf looks healthy)", "good"
    severity = combined.get("severity") or "unknown"
    tone = "bad" if severity == "Severe" else "warn"
    return f"🟠 {severity} - {image_result.get('condition') or 'issue detected'}", tone

def _disease_risk_summary() -> tuple:
    """(text, tone) from the weather result (rule based) or the last diagnosis."""
    weather = st.session_state.get("weather_result")
    if weather and weather.get("risks"):
        level = weather.get("risk_level") or "LOW"
        tone = {"HIGH": "bad", "MODERATE": "warn", "LOW": "good"}.get(level, "info")
        titles = ", ".join(risk.get("title", "") for risk in weather["risks"][:2])
        return f"{level} - {titles}", tone
    bundle = st.session_state.get("last_diagnosis")
    if bundle:
        category = ((bundle.get("image_result") or {}).get("category")) or "unknown"
        fungal_like = category in {"fungal", "bacterial"}
        return (
            ("Medium - " if fungal_like else "Low - ") + f"last result: {category}",
            "warn" if fungal_like else "good",
        )
    return "Check weather for risk", "muted"

def _weather_summary() -> tuple:
    weather = st.session_state.get("weather_result")
    if not weather or weather.get("error"):
        return "Not checked (enter a city)", "muted"
    return f"🌦️ {weather.get('temperature')}°C, {weather.get('humidity')}% humidity", "info"

def dashboard_page() -> None:
    """🏠 Dashboard - quick status of every AgriVision module."""
    page_header(
        "AgriVision Dashboard",
        "One screen for crop health, disease risk and weather.",
        icon="🌾",
    )

    columns = st.columns(3)
    with columns[0]:
        text, tone = _crop_health_summary()
        status_chip("Crop health", text, tone)
    with columns[1]:
        text, tone = _disease_risk_summary()
        status_chip("Disease risk", text, tone)
    with columns[2]:
        text, tone = _weather_summary()
        status_chip("Weather", text, tone)

    section_title("Quick actions")
    action_columns = st.columns(3)
    for column, (label, target) in zip(action_columns, DASHBOARD_ACTIONS):
        with column:
            st.button(label, width="stretch", on_click=goto, args=(target,))

    st.divider()
    left, right = st.columns([1.2, 1])

    with left:
        section_title("Recent diagnosis")
        history = st.session_state.get("diagnosis_history") or []
        if history:
            latest = history[0]
            st.write(f"**{latest['time']}**")
            st.write(f"- Disease (photo): {latest.get('disease') or 'not available'}")
            st.write(f"- Symptoms: {latest.get('symptom') or 'not provided'}")
            st.write(
                f"- Combined confidence: {format_percent(latest.get('combined_confidence') or 0)} "
                f"({confidence_band(latest.get('combined_confidence') or 0)})"
            )
            st.write(f"- Severity: {latest.get('severity')}")
            st.caption(f"{len(history)} diagnosis result(s) kept in this session.")
        else:
            st.info("No diagnosis yet. Start with the Crop Doctor to analyse a leaf photo.")

        section_title("Session context used by the AI assistant")
        st.write(
            "- Last diagnosis: "
            f"{(st.session_state.get('last_diagnosis') or {}).get('created_at', 'none')}"
        )
        st.write(
            "- Last weather check: "
            f"{(st.session_state.get('weather_result') or {}).get('city', 'none')}"
        )

    with right:
        section_title("Modules")
        st.markdown(
            "- 🩺 **Crop Doctor** - CNN disease detection + symptom classifier + Grad-CAM\n"
            "- 🌦️ **Weather & Risk** - rule-based disease / pest early warning\n"
            "- 🧮 **Fertilizer Calculator** - deterministic per-acre lookup\n"
            "- 🔐 **Product Verifier** - SQLite product registry\n"
            "- 🏛️ **Government Schemes** - static scheme matching wizard\n"
            "- 🚜 **Equipment Rental** - SQLite listings and bookings\n"
            "- 🤖 **AI Assistant** - Gemini chat with AgriVision context"
        )
        st.caption(
            "The vision model is not trained from scratch: it starts from a pretrained "
            "MobileNetV2 plant-disease checkpoint and is further fine-tuned on an additional "
            "agriculture dataset."
        )

    st.divider()
    section_title("Model performance (before vs after fine-tuning)")
    from utils.helpers import EVALUATION_DIR

    summary = load_evaluation_summary(EVALUATION_DIR / "evaluation_summary.json")
    if not summary:
        st.caption(
            "No evaluation report found yet. Run `python training/evaluate.py` to generate "
            "data/evaluation/evaluation_summary.json."
        )
    else:
        before = summary.get("before") or {}
        after = summary.get("after") or {}
        metric_columns = st.columns(4)
        with metric_columns[0]:
            st.metric("Pretrained accuracy", format_percent(before.get("accuracy") or 0.0))
        with metric_columns[1]:
            st.metric(
                "Fine-tuned accuracy",
                format_percent(after.get("accuracy") or 0.0),
                f"{(summary.get('accuracy_delta') or 0) * 100:+.2f}%",
            )
        with metric_columns[2]:
            st.metric("Pretrained loss", f"{(before.get('loss') or 0):.4f}")
        with metric_columns[3]:
            st.metric(
                "Fine-tuned loss",
                f"{(after.get('loss') or 0):.4f}",
                f"{(summary.get('loss_delta') or 0):+.4f}",
            )
        st.caption(
            f"Evaluated on {summary.get('val_images')} validation images covering "
            f"{summary.get('val_classes')} classes ({summary.get('device')}). Full plots and "
            "classification reports are stored in data/evaluation/."
        )
        comparison_plot = EVALUATION_DIR / "metrics_comparison.png"
        if comparison_plot.exists():
            with st.expander("Accuracy / loss comparison chart", expanded=False):
                st.image(str(comparison_plot), width="stretch")

def weather_page() -> None:
    """🌦️ Weather & Crop Risk - Open-Meteo + deterministic risk rule engine."""
    page_header(
        "Weather & Crop Risk",
        "Enter a city to fetch the current weather and see which crop-disease risk rules are "
        "triggered by the temperature and humidity.",
        icon="🌦️",
    )

    from modules.weather import weather_report, weather_status
    from utils.gemini import is_configured as gemini_configured

    status = weather_status()
    columns = st.columns(3)
    with columns[0]:
        status_chip(
            "Open-Meteo",
            "free live service",
            "good",
        )
    with columns[1]:
        status_chip("Risk rules", "deterministic (no ML)", "info")
    with columns[2]:
        status_chip(
            "AI warning",
            "Gemini" if gemini_configured() else "offline fallback",
            "good" if gemini_configured() else "warn",
        )

    city_column, button_column = st.columns([3, 1])
    with city_column:
        city = st.text_input(
            "City (no geolocation used - type it manually)",
            value=st.session_state.get("weather_city", "Varanasi"),
            key="weather_city_input",
            placeholder="Varanasi",
        )
    with button_column:
        st.write("")
        check_clicked = st.button("🌦️ Check weather", type="primary", width="stretch")

    manual_values: Optional[Dict[str, Any]] = None
    with st.expander("🛠️ Manual weather values (offline analysis)", expanded=False):
            st.caption(
                "Type the values from any weather app and the same rule engine + AI warning "
                "will run."
            )
            manual_columns = st.columns(3)
            with manual_columns[0]:
                manual_temperature = st.number_input("Temperature (°C)", value=28.0, step=0.5)
            with manual_columns[1]:
                manual_humidity = st.number_input("Humidity (%)", value=84, min_value=0, max_value=100)
            with manual_columns[2]:
                manual_rain = st.number_input("Rainfall (mm, last hour)", value=0.0, step=0.5)
            if st.button("▶️ Run rules with these values"):
                manual_values = {
                    "temperature": manual_temperature,
                    "humidity": manual_humidity,
                    "rainfall": manual_rain,
                    "description": "manually entered values",
                }
                check_clicked = True

    if check_clicked:
        if not city.strip() and not manual_values:
            st.warning("Please enter a city name.")
        else:
            with st.spinner("Fetching weather and applying the risk rules ..."):
                result = weather_report(city, manual_values=manual_values)
            st.session_state["weather_result"] = result
            st.session_state["weather_city"] = city
        st.divider()

    result = st.session_state.get("weather_result")
    if not result:
        return

    if result.get("error"):
        st.warning(result["error"])
        st.caption(
            "This is the AgriVision equivalent of a 404: the city could not be resolved by the "
            "Open-Meteo geocoding service."
        )
        return

    weather = result["weather"]
    st.subheader(f"Weather in {result['city']}"
                 + (f", {weather.get('region')}" if weather.get("region") else ""))

    metric_columns = st.columns(4)
    with metric_columns[0]:
        st.metric("Temperature", f"{weather['temperature']} °C")
    with metric_columns[1]:
        st.metric("Humidity", f"{weather['humidity']} %")
    with metric_columns[2]:
        rainfall = weather.get("rain_1h")
        st.metric("Rain (1 h)", f"{rainfall} mm" if rainfall is not None else "n/a")
    with metric_columns[3]:
        st.metric("Feels like", f"{weather.get('feels_like')} °C")

    st.caption(
        f"Conditions: {weather.get('description') or 'n/a'} | wind: "
        f"{weather.get('wind_speed')} m/s | source: {weather.get('source')} | "
        f"fetched: {weather.get('fetched_at')}"
    )

    risks = result.get("risks") or []
    level = result.get("risk_level") or "LOW"
    icon = {"HIGH": "🔴", "MODERATE": "🟡", "LOW": "🟢"}.get(level, "⚪")
    st.markdown(f"### {icon} Overall risk level: {level}")

    if risks:
        for risk in risks:
            badge = "🔴 HIGH" if risk["level"] == "HIGH" else "🟡 MODERATE"
            st.warning(f"**{badge} — {risk['title']}**\n\n{risk['detail']}\n\nRule: `{risk['rule']}`")
    else:
        st.success("No disease-risk rule was triggered by the current weather values.")

    if result.get("message"):
        show_ai_result(result["message"], "AI Warning")

def fertilizer_page() -> None:
    """🧮 Fertilizer Calculator - deterministic per-acre lookup (no ML, no LLM doses)."""
    page_header(
        "Fertilizer Calculator",
        "Pick your crop and the deficient nutrient to get the fertilizer, the quantity for your "
        "land size and an estimated cost.",
        icon="🧮",
    )

    from modules.fertilizer import available_crops, calculate, deficiencies_for_crop

    st.info(
        "**Deterministic / rule-based module.** The dose comes from a fixed per-acre lookup table "
        "(`data/fertilizer_data.json`) - this is not machine learning, and Gemini is never asked "
        "to invent a fertilizer quantity or price. Always confirm with your soil test report."
    )

    crops = available_crops()
    if not crops:
        st.error("The fertilizer lookup table could not be loaded (data/fertilizer_data.json).")
        return

    crop_column, deficiency_column, size_column, unit_column = st.columns([1.2, 1.2, 1, 1])
    with crop_column:
        crop = st.selectbox("Crop", crops, index=crops.index("Tomato") if "Tomato" in crops else 0)
    with deficiency_column:
        deficiency_options = deficiencies_for_crop(crop)
        deficiency = st.selectbox(
            "Deficiency",
            deficiency_options,
            index=0,
        )
    with size_column:
        land_size = st.number_input("Land size", min_value=0.1, value=2.5, step=0.1, format="%.2f")
    with unit_column:
        unit = st.selectbox("Unit", ["acres", "hectares"], index=0)

    calculate_clicked = st.button("🧮 Calculate", type="primary")

    if calculate_clicked:
        st.session_state["fertilizer_result"] = calculate(crop, deficiency, land_size, unit)
        st.divider()

    result = st.session_state.get("fertilizer_result")
    if not result:
        return

    if result.get("error"):
        st.warning(result["error"])
        return

    st.subheader("Recommendation")
    metric_columns = st.columns(4)
    with metric_columns[0]:
        st.metric("Fertilizer", result["fertilizer"])
    with metric_columns[1]:
        st.metric("Quantity", f"{result['quantity']:g} {result['unit']}")
    with metric_columns[2]:
        st.metric("Estimated cost", f"₹ {result['estimated_cost']:,.0f}")
    with metric_columns[3]:
        st.metric("Land size", f"{result['land_size_acres']:g} acres")

    st.markdown(
        f"- **Crop:** {result['crop']}\n"
        f"- **Deficiency:** {result['deficiency']}\n"
        f"- **Base dose:** {result['dosage_per_acre']:g} {result['unit']} per acre "
        f"(INR {result['cost_per_unit']:g} per {result['unit']})\n"
        f"- **How to apply:** {result['application']}"
    )
    st.success(result["summary"])
    st.caption("Assumptions: " + result["assumptions"])

    if result["land_size_unit"].lower().startswith("hect"):
        st.caption(
            f"Converted from {result['land_size_input']:g} hectares using "
            "1 hectare = 2.47105 acres."
        )

    with st.expander("Lookup row used (audit trail)", expanded=False):
        st.json(
            {
                "crop": result["crop"],
                "deficiency": result["deficiency"],
                "fertilizer": result["fertilizer"],
                "dosage_per_acre": result["dosage_per_acre"],
                "unit": result["unit"],
                "cost_per_unit": result["cost_per_unit"],
                "computation": (
                    f"{result['dosage_per_acre']:g} {result['unit']}/acre x "
                    f"{result['land_size_acres']:g} acres = {result['quantity']:g} {result['unit']}"
                ),
            }
        )

def product_verifier_page() -> None:
    """🔐 Product Verifier - SQLite product registry + QR scan."""
    page_header(
        "Product Verifier",
        "Check an agricultural product code against the registry before you buy or spray.",
        icon="🔐",
    )

    from modules.product_verifier import (
        decode_qr_from_image,
        list_registry,
        verify_product,
        verifier_status,
    )

    status = verifier_status()
    columns = st.columns(3)
    with columns[0]:
        status_chip(
            "Registry",
            f"{status.get('count', 0)} demo products",
            "good" if status.get("available") else "bad",
        )
    with columns[1]:
        status_chip("QR scanning", "OpenCV QRCodeDetector", "info")
    with columns[2]:
        status_chip("Barcode (EAN)", "manual entry fallback", "warn")

    st.warning(
        "**Simulated registry (college demo).** This SQLite database is seeded with demo "
        "products (`utils/database.py`). A real deployment would need access to a trusted "
        "manufacturer or authorised-registry database, so treat results as a demonstration."
    )

    code_column, qr_column = st.columns([1.1, 1])
    with code_column:
        section_title("Manual code entry")
        # Versioned widget key: the QR button below can then safely replace the
        # contents of this text input on the next run.
        code_version = st.session_state.get("product_code_version", 0)
        code = st.text_input(
            "Product code",
            value=st.session_state.get("product_code_value", ""),
            placeholder="AGV-1001",
            key=f"product_code_input_{code_version}",
        )
        st.session_state["product_code_value"] = code
        verify_clicked = st.button("🔎 Verify", type="primary", width="stretch")
    with qr_column:
        section_title("Or scan the QR code on the pack")
        qr_image = st.file_uploader(
            "QR code image", type=["jpg", "jpeg", "png", "bmp"], key="qr_uploader"
        )
        if st.button("📷 Decode QR and verify", width="stretch"):
            if qr_image is None:
                st.warning("Upload a photo of the QR code first.")
            else:
                decoded = decode_qr_from_image(qr_image.getvalue())
                if decoded.get("error"):
                    st.warning(decoded["error"])
                else:
                    st.success(f"QR decoded: {decoded['raw_text']}")
                    st.session_state["qr_code_result"] = verify_product(decoded["code"])
                    st.session_state["product_code_value"] = decoded["code"]
                    st.session_state["product_code_version"] = code_version + 1
                    st.rerun()

    if verify_clicked:
        if not code.strip():
            st.warning("Enter a product code (for example AGV-1001).")
        else:
            st.session_state["product_result"] = verify_product(code)
            st.session_state.pop("qr_code_result", None)
        st.divider()

    result = st.session_state.get("product_result") or st.session_state.get("qr_code_result")
    if result:
        message = result["message"]
        if result.get("verified"):
            st.success(message)
        elif result.get("found"):
            st.warning(message)
        else:
            st.error(message)

        product = result.get("product")
        if product:
            detail_columns = st.columns(4)
            with detail_columns[0]:
                st.metric("Product", product.get("product_name") or "-")
            with detail_columns[1]:
                st.metric("Manufacturer", product.get("manufacturer") or "-")
            with detail_columns[2]:
                st.metric("Batch", product.get("batch") or "-")
            with detail_columns[3]:
                st.metric("Expiry", product.get("expiry") or "-")
            st.caption(
                f"Type: {product.get('product_type') or 'n/a'} | registered status: "
                f"{product.get('status')} | registered on: {product.get('registered_on')}"
            )
            with st.expander("Verification checks performed", expanded=True):
                for check in result.get("checks", []):
                    st.write(f"- {check}")
        elif result.get("found") is False and not result.get("error"):
            st.caption(
                "The code is not in the demo registry. Check for a typing error - codes look like "
                "AGV-1001."
            )
        st.divider()

    with st.expander("Show the demo registry contents", expanded=False):
        rows = list_registry()
        if rows:
            st.dataframe(rows, width="stretch", hide_index=True)
        else:
            st.caption("Registry is empty.")

def schemes_page() -> None:
    """🏛️ Government Schemes - 4-step wizard + static rule matching."""
    page_header(
        "Government Schemes",
        "A four-step wizard matches your land size, region, crop and area of interest against "
        "publicly available agricultural schemes, with links to the official application pages.",
        icon="🏛️",
    )

    from modules.subsidy_matcher import (
        REGIONS,
        crop_options,
        match_schemes,
        scheme_categories,
    )

    st.caption(
        "Matching uses the static rules in `data/schemes.json` (deterministic, no ML). "
        "Scheme names and application links are never generated by an AI model."
    )

    if "scheme_step" not in st.session_state:
        st.session_state["scheme_step"] = 1
    if "scheme_inputs" not in st.session_state:
        st.session_state["scheme_inputs"] = {
            "land_size_acres": 2.5,
            "region": "All India",
            "crop": "Any",
            "category": "Any",
        }

    step = int(st.session_state["scheme_step"])
    st.progress(min(step, 4) / 4.0, text=f"Step {min(step, 4)} of 4")

    inputs = st.session_state["scheme_inputs"]

    if step == 1:
        section_title("Step 1 — How much land do you farm?")
        inputs["land_size_acres"] = st.number_input(
            "Land size (acres)", min_value=0.05, value=float(inputs["land_size_acres"]),
            step=0.25, format="%.2f",
        )
        st.caption("1 acre = 0.4047 hectare. If you only know hectares, multiply by 2.471.")
    elif step == 2:
        section_title("Step 2 — Which state are you in?")
        inputs["region"] = st.selectbox(
            "State / region", REGIONS, index=REGIONS.index(inputs.get("region", "All India"))
        )
    elif step == 3:
        section_title("Step 3 — Which crop do you grow?")
        crops = crop_options()
        inputs["crop"] = st.selectbox(
            "Crop",
            crops,
            index=crops.index(inputs.get("crop", "Any"))
            if inputs.get("crop", "Any") in crops else 0,
        )
    else:
        section_title("Step 4 — What kind of support are you looking for?")
        categories = ["Any"] + scheme_categories()
        inputs["category"] = st.selectbox(
            "Support type",
            categories,
            index=categories.index(inputs.get("category", "Any"))
            if inputs.get("category", "Any") in categories else 0,
        )
        st.caption("Leave it on **Any** to see every scheme that fits your farm profile.")

    back_column, next_column, reset_column = st.columns(3)
    with back_column:
        if step > 1 and st.button("⬅️ Back", width="stretch"):
            st.session_state["scheme_step"] = step - 1
            st.rerun()
    with next_column:
        if step < 4:
            if st.button("Next ➡️", type="primary", width="stretch"):
                st.session_state["scheme_step"] = step + 1
                st.rerun()
        else:
            if st.button("🔍 Find matching schemes", type="primary", width="stretch"):
                st.session_state["scheme_result"] = match_schemes(
                    inputs["land_size_acres"], inputs["region"], inputs["crop"], inputs["category"]
                )
                st.divider()
    with reset_column:
        if st.button("🔄 Start over", width="stretch"):
            st.session_state["scheme_step"] = 1
            st.session_state.pop("scheme_result", None)
            st.rerun()

    result = st.session_state.get("scheme_result")
    if not result:
        return

    if result.get("error"):
        st.error(result["error"])
        return

    profile = result["inputs"]
    st.subheader("Matching schemes")
    st.caption(
        f"Profile: {profile['land_size_acres']:g} acres | {profile['region']} | "
        f"crop: {profile['crop']} | support: {profile['category']}"
    )

    matches = result.get("matches") or []
    if not matches:
        st.warning(
            "No scheme matched this exact combination. Try a different support type, or check the "
            "official state agriculture department portal for state-specific schemes."
        )
    for scheme in matches:
        with st.container(border=True):
            st.markdown(f"### {scheme['name']}")
            st.caption(
                f"Category: {scheme['category']} | Region: {scheme['region']} | Land size: "
                f"{scheme['land_size_min_acres']:g}-{scheme['land_size_max_acres']:g} acres"
            )
            st.write(scheme["description"])
            st.markdown(f"**Benefit:** {scheme['benefit']}")
            eligibility_column, documents_column = st.columns(2)
            with eligibility_column:
                st.markdown("**Eligibility**")
                for item in scheme["eligibility"]:
                    st.write(f"- {item}")
            with documents_column:
                st.markdown("**Documents usually required**")
                for item in scheme["required_documents"]:
                    st.write(f"- {item}")
            st.markdown(
                f"**Official application / information page:** "
                f"[{scheme['official_link']}]({scheme['official_link']})"
            )
            if scheme.get("matched_reasons"):
                with st.expander("Why this matched", expanded=False):
                    for reason in scheme["matched_reasons"]:
                        st.write(f"- {reason}")
            for note in scheme.get("unmet_reasons") or []:
                st.caption(f"Note: {note}")

    near_misses = result.get("near_misses") or []
    if near_misses:
        with st.expander(f"Schemes that did not match ({len(near_misses)})", expanded=False):
            for scheme in near_misses:
                st.markdown(f"**{scheme['name']}** — {'; '.join(scheme['unmet_reasons'])}")
                st.caption(f"Official page: {scheme['official_link']}")

    st.info(
        "AgriVision only lists publicly available schemes and links to their official portals. "
        "Eligibility rules and cut-off dates change, so always confirm on the official page or at "
        "your block agriculture office."
    )

def equipment_rental_page() -> None:
    """🚜 Equipment Rental - SQLite marketplace with two roles (farmer / owner)."""
    page_header(
        "Equipment Rental",
        "List, view and book agricultural machines. Farmers book machines; machine owners manage "
        "their listings.",
        icon="🚜",
    )

    from modules.equipment_rental import (
        MACHINE_TYPES,
        ROLES,
        add_machine,
        bookings_for_farmer,
        bookings_for_machine,
        bookings_for_owner,
        cancel_booking,
        create_booking,
        delete_machine,
        estimate_cost,
        list_machines,
        login_user,
        marketplace_status,
        register_user,
        update_machine,
    )

    status = marketplace_status()
    columns = st.columns(4)
    with columns[0]:
        status_chip("Users", str(status.get("users", 0)), "info")
    with columns[1]:
        status_chip("Machines listed", str(status.get("machines", 0)), "info")
    with columns[2]:
        status_chip("Bookings", str(status.get("bookings", 0)), "info")
    user = st.session_state.get("user")
    with columns[3]:
        status_chip(
            "Signed in as",
            f"{user['username']} ({ROLES.get(user['role'], user['role'])})" if user else "not signed in",
            "good" if user else "warn",
        )

    if not user:
        login_tab, register_tab = st.tabs(["🔑 Sign in", "🆕 Create account"])
        with login_tab:
            st.caption("Demo accounts: farmer_demo / farmer123 and owner_demo / owner123")
            with st.form("login_form"):
                username = st.text_input("Username", value="farmer_demo")
                password = st.text_input("Password", value="farmer123", type="password")
                role_hint = st.selectbox("I am a", list(ROLES.values()))
                if st.form_submit_button("Sign in", type="primary"):
                    result = login_user(username, password)
                    if result["ok"]:
                        st.session_state["user"] = result["user"]
                        st.rerun()
                    else:
                        st.error(result["error"])
                else:
                    st.caption(
                        f"Role selected for display only: {role_hint}. The role stored on the "
                        "account is what decides your permissions."
                    )
        with register_tab:
            with st.form("register_form"):
                new_username = st.text_input("Choose a username")
                new_password = st.text_input("Choose a password (min 6 characters)", type="password")
                new_role = st.selectbox("I am a", ["farmer", "owner"], format_func=lambda r: ROLES[r])
                full_name = st.text_input("Full name")
                phone = st.text_input("Phone")
                place = st.text_input("Village / city")
                if st.form_submit_button("Create account", type="primary"):
                    result = register_user(
                        new_username, new_password, new_role, full_name, phone, place
                    )
                    if result["ok"]:
                        st.session_state["user"] = result["user"]
                        st.rerun()
                    else:
                        st.error(result["error"])
        st.divider()
    else:
        if st.button("🚪 Sign out"):
            st.session_state["user"] = None
            st.session_state["rental_selected_machine"] = None
            st.rerun()
        st.divider()

    browse_tab, my_bookings_tab, list_tab, manage_tab = st.tabs(
        ["🚜 Available Machines", "📅 My Bookings", "🛠️ List Your Machine", "⚙️ My Listings"]
    )

    with browse_tab:
        filter_columns = st.columns(3)
        with filter_columns[0]:
            location_filter = st.text_input("Filter by location", placeholder="Varanasi")
        with filter_columns[1]:
            type_filter = st.selectbox("Filter by type", ["Any"] + MACHINE_TYPES)
        with filter_columns[2]:
            only_available = st.checkbox("Only available machines", value=False)

        machines = list_machines(
            location=location_filter or None,
            machine_type=type_filter,
            include_unavailable=not only_available,
        )
        if not machines:
            st.info("No machines match these filters. Try clearing the location filter.")
        for machine in machines:
            with st.container(border=True):
                info_column, rate_column = st.columns([2, 1])
                with info_column:
                    section_title(machine['name'])
                    st.caption(
                        f"{machine.get('machine_type') or 'machine'} | {machine.get('location')} | "
                        f"owner: {machine.get('owner_name') or machine.get('owner_username')}"
                    )
                    st.write(machine.get("description") or "")
                    if not machine.get("available"):
                        st.warning("Currently marked unavailable by the owner.")
                with rate_column:
                    st.metric("Hourly", f"₹{machine['hourly_rate']:,.0f}")
                    st.metric("Daily", f"₹{machine['daily_rate']:,.0f}")
                    st.caption(f"{machine.get('upcoming_bookings', 0)} upcoming booking(s)")

                with st.expander("View / Book this machine", expanded=False):
                    existing = bookings_for_machine(int(machine["id"]))
                    if existing:
                        st.markdown("**Booked dates**")
                        for booking in existing:
                            if booking.get("status") == "cancelled":
                                continue
                            st.write(
                                f"- {booking['start_date']} → {booking['end_date']} "
                                f"({booking.get('status')})"
                            )
                    else:
                        st.caption("No bookings yet - the machine is free.")

                    if not user:
                        st.info("Sign in as a farmer (or create a farmer account) to book.")
                    else:
                        date_columns = st.columns(2)
                        with date_columns[0]:
                            start = st.date_input(
                                "Start date", key=f"book_start_{machine['id']}", format="YYYY-MM-DD"
                            )
                        with date_columns[1]:
                            end = st.date_input(
                                "End date", key=f"book_end_{machine['id']}", format="YYYY-MM-DD"
                            )
                        notes = st.text_input("Notes for the owner (optional)",
                                              key=f"book_notes_{machine['id']}")
                        estimate = estimate_cost(machine, start, end)
                        st.caption(
                            f"Estimated cost: ₹{estimate['total_cost']:,.0f} "
                            f"for {estimate['days']} day(s) at ₹{estimate['daily_rate']:,.0f}/day"
                        )
                        if st.button("📅 Book this machine", key=f"book_btn_{machine['id']}",
                                     type="primary"):
                            if user["role"] != "farmer":
                                st.warning(
                                    "You are signed in as a machine owner. Sign in with a farmer "
                                    "account to book a machine."
                                )
                            else:
                                result = create_booking(
                                    int(machine["id"]), int(user["id"]), start, end, notes
                                )
                                if result["ok"]:
                                    st.success(
                                        f"Booking confirmed (#{result['booking_id']}) — "
                                        f"₹{result['total_cost']:,.0f} for {result['days']} day(s). "
                                        "No payment is handled by this demo."
                                    )
                                    st.rerun()
                                else:
                                    st.error(result["error"])

    with my_bookings_tab:
        if not user:
            st.info("Sign in to see your bookings.")
        else:
            bookings = (
                bookings_for_farmer(int(user["id"]))
                if user["role"] == "farmer"
                else bookings_for_owner(int(user["id"]))
            )
            if not bookings:
                st.info("No bookings yet.")
            for booking in bookings:
                with st.container(border=True):
                    st.markdown(f"**{booking['machine_name']}** ({booking.get('machine_type')})")
                    st.write(
                        f"{booking['start_date']} → {booking['end_date']} | "
                        f"status: {booking['status']} | "
                        f"cost: ₹{(booking.get('total_cost') or 0):,.0f}"
                    )
                    st.caption(
                        f"Farmer: {booking.get('farmer_name') or booking.get('farmer_username')} | "
                        f"owner: {booking.get('owner_username')} | location: "
                        f"{booking.get('machine_location')}"
                    )
                    if booking["status"] != "cancelled" and st.button(
                        "Cancel booking", key=f"cancel_{booking['id']}"
                    ):
                        result = cancel_booking(int(booking["id"]), int(user["id"]))
                        if result["ok"]:
                            st.success("Booking cancelled.")
                            st.rerun()
                        else:
                            st.error(result["error"])

    with list_tab:
        if not user or user["role"] != "owner":
            st.info(
                "Sign in with a **machine owner** account (demo: owner_demo / owner123) or create "
                "one to list a machine."
            )
        else:
            with st.form("add_machine_form"):
                section_title("Machine details")
                form_columns = st.columns(2)
                with form_columns[0]:
                    machine_name = st.text_input("Machine name")
                    machine_type = st.selectbox("Type", MACHINE_TYPES)
                    machine_location = st.text_input("Location (village / city)")
                with form_columns[1]:
                    hourly = st.number_input("Hourly rate (₹)", min_value=1.0, value=700.0, step=50.0)
                    daily = st.number_input("Daily rate (₹)", min_value=1.0, value=4500.0, step=100.0)
                    description = st.text_input("Short description")
                submitted = st.form_submit_button("➕ Add machine", type="primary")
            if submitted:
                result = add_machine(
                    int(user["id"]), machine_name, machine_type, hourly, daily,
                    machine_location, description,
                )
                if result["ok"]:
                    st.success(f"Machine listed (#{result['machine_id']}).")
                else:
                    st.error(result["error"])

    with manage_tab:
        if not user or user["role"] != "owner":
            st.info("This tab shows the machines you listed - available to machine owner accounts.")
        else:
            owned = list_machines(owner_id=int(user["id"]))
            if not owned:
                st.info("You have not listed any machine yet.")
            for machine in owned:
                with st.container(border=True):
                    section_title(f"{machine['name']} (id {machine['id']})")
                    with st.form(f"update_machine_{machine['id']}"):
                        edit_columns = st.columns(3)
                        with edit_columns[0]:
                            new_name = st.text_input("Name", value=machine["name"])
                            new_type = st.selectbox(
                                "Type",
                                MACHINE_TYPES,
                                index=MACHINE_TYPES.index(machine["machine_type"])
                                if machine.get("machine_type") in MACHINE_TYPES else 0,
                            )
                        with edit_columns[1]:
                            new_hourly = st.number_input(
                                "Hourly rate (₹)", min_value=1.0,
                                value=float(machine["hourly_rate"]), step=50.0,
                            )
                            new_daily = st.number_input(
                                "Daily rate (₹)", min_value=1.0,
                                value=float(machine["daily_rate"]), step=100.0,
                            )
                        with edit_columns[2]:
                            new_location = st.text_input(
                                "Location", value=machine.get("location") or ""
                            )
                            new_available = st.checkbox(
                                "Available for booking", value=bool(machine.get("available"))
                            )
                        new_description = st.text_input(
                            "Description", value=machine.get("description") or ""
                        )
                        update_submitted = st.form_submit_button("💾 Save changes")
                    if update_submitted:
                        result = update_machine(
                            int(machine["id"]), int(user["id"]), name=new_name,
                            machine_type=new_type, hourly_rate=new_hourly, daily_rate=new_daily,
                            location=new_location, description=new_description,
                            available=new_available,
                        )
                        if result["ok"]:
                            st.success("Machine updated.")
                        else:
                            st.error(result["error"])

                    machine_bookings = bookings_for_machine(int(machine["id"]))
                    if machine_bookings:
                        with st.expander(f"Bookings for this machine ({len(machine_bookings)})"):
                            for booking in machine_bookings:
                                st.write(
                                    f"- {booking['start_date']} → {booking['end_date']} | "
                                    f"{booking.get('farmer_name') or booking.get('farmer_username')}"
                                    f" | {booking['status']} | "
                                    f"₹{(booking.get('total_cost') or 0):,.0f}"
                                )
                    if st.button("🗑️ Delete this machine", key=f"delete_{machine['id']}"):
                        result = delete_machine(int(machine["id"]), int(user["id"]))
                        if result["ok"]:
                            st.success("Machine deleted.")
                            st.rerun()
                        else:
                            st.error(result["error"])

    st.caption(
        "MVP scope: list, view and book. No payments and no reviews are handled (as specified). "
        "Bookings live in data/rentals.db and overlapping bookings for the same machine are rejected."
    )

def assistant_page() -> None:
    """🤖 AI Agriculture Assistant - Gemini chat with AgriVision context."""
    page_header(
        "AI Agriculture Assistant",
        "Ask general agriculture questions. The assistant also knows the results you produced in "
        "this session (Crop Doctor, weather, soil report).",
        icon="🤖",
    )

    from utils.gemini import ask_assistant, gemini_status, is_configured

    status = gemini_status()
    if is_configured():
        st.caption(f"Connected to Gemini (`{status['model']}` via {status['sdk']}).")
    else:
        st.warning(
            "No GEMINI_API_KEY is configured, so the assistant replies with a **rule-based offline "
            "fallback**. Add the key to `.env` to enable full natural-language answers. "
            "AgriVision never lets the assistant invent scheme names, fertiliser doses or product "
            "verification results in either mode."
        )

    # Context assembled from the other pages in this session.
    bundle = st.session_state.get("last_diagnosis") or {}
    image_result = bundle.get("image_result") or {}
    symptom_result = bundle.get("symptom_result") or {}
    weather = st.session_state.get("weather_result") or {}

    context = {
        "last_diagnosis": (
            f"{image_result.get('pretty_label')} "
            f"({format_percent(image_result.get('confidence') or 0)})"
            if image_result.get("label") else None
        ),
        "symptom_features": symptom_result.get("detected_features"),
        "weather": (
            f"{weather.get('city')}: {weather.get('temperature')}°C, "
            f"humidity {weather.get('humidity')}%, risk {weather.get('risk_level')}"
            if weather.get("weather") else None
        ),
    }

    with st.expander("Context available to the assistant", expanded=False):
        for key, value in context.items():
            st.write(f"- **{key}**: {value or 'none'}")

    history: List[Dict[str, str]] = st.session_state.setdefault("assistant_history", [])
    for message in history:
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.write(message["content"])

    if not history:
        st.markdown("**Try one of these:**")
        suggestion_columns = st.columns(3)
        suggestions = [
            "My tomato leaves are turning yellow. What should I check?",
            "How do I reduce fungal disease risk in humid weather?",
            "Which government scheme helps with drip irrigation?",
        ]
        for column, suggestion in zip(suggestion_columns, suggestions):
            with column:
                if st.button(suggestion, width="stretch"):
                    st.session_state["assistant_pending"] = suggestion
                    st.rerun()

    pending = st.session_state.pop("assistant_pending", None)
    question = st.chat_input("Ask about your crop, weather, fertiliser, schemes or equipment...")
    question = question or pending

    if question:
        history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking ..."):
                answer = ask_assistant(question, context=context, history=history[:-1])
            st.write(answer["text"])
            if not answer["used_ai"]:
                st.caption(f"Offline fallback reply — {answer['error']}")
        history.append({"role": "assistant", "content": answer["text"]})
        st.session_state["assistant_history"] = history[-20:]

    if history and st.button("🧹 Clear conversation"):
        st.session_state["assistant_history"] = []
        st.rerun()

# Navigation & entry point

PAGE_RENDERERS: Dict[str, Any] = {
    "🏠 Dashboard": dashboard_page,
    "🩺 Crop Doctor": crop_doctor_page,
    "🌦️ Weather & Risk": weather_page,
    "🧮 Fertilizer Calculator": fertilizer_page,
    "🔐 Product Verifier": product_verifier_page,
    "🏛️ Government Schemes": schemes_page,
    "🚜 Equipment Rental": equipment_rental_page,
    "🤖 AI Agriculture Assistant": assistant_page,
}

def sidebar_navigation() -> str:
    """Sidebar with the AgriVision navigation + live system status."""
    with st.sidebar:
        st.markdown(
            '<div class="agv-brand"><div class="agv-title">🌾 AgriVision</div>'
            '<div class="agv-sub">Smart Agriculture Super-App</div></div>',
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Navigation",
            PAGES,
            index=PAGES.index(st.session_state["page"]),
            label_visibility="collapsed",
        )
        st.session_state["page"] = page

        st.divider()
        with st.expander("⚙️ System status", expanded=False):
            try:
                from modules.crop_doctor import model_status
                from utils.gemini import gemini_status
                from utils.helpers import FERTILIZER_DATA_PATH, SCHEMES_PATH

                crop_status = model_status()
                ai_status = gemini_status()
                st.write(f"- Vision model: `{crop_status.get('active') or 'missing'}`")
                st.write(f"- Class labels: {crop_status.get('num_classes')}")
                st.write(f"- Device: {crop_status.get('device')}")
                st.write(f"- Gemini: {'configured' if ai_status['configured'] else 'offline fallback'}")
                st.write(f"- Gemini model: `{ai_status['model']}`")
                st.write(f"- Gemini SDK: {ai_status['sdk']}")
                from utils.helpers import FINE_TUNED_MODEL_PATH

                st.write(
                    "- Fine-tuned weights: "
                    f"{'yes' if FINE_TUNED_MODEL_PATH.exists() else 'no (using pretrained)'}"
                )
                st.write(f"- Fertilizer table: {'yes' if FERTILIZER_DATA_PATH.exists() else 'no'}")
                st.write(f"- Scheme list: {'yes' if SCHEMES_PATH.exists() else 'no'}")
            except Exception as exc:  # pragma: no cover - defensive
                st.write(f"status unavailable: {exc}")

        st.divider()
        st.caption(
            "Educational college project. Always confirm a diagnosis with a local "
            "agricultural expert before spraying."
        )
    return page

def main() -> None:
    """Initialise state, draw the sidebar and render the selected page."""
    ensure_directories()
    init_session_state()
    inject_styles()
    page = sidebar_navigation()
    renderer = PAGE_RENDERERS.get(page, dashboard_page)
    try:
        renderer()
    except Exception as exc:  # pragma: no cover - top level guard
        st.error(f"This page hit an unexpected error: {type(exc).__name__}: {exc}")
        with st.expander("Technical details", expanded=False):
            import traceback

            st.code(traceback.format_exc(), language="text")

main()
