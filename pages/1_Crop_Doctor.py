"""
pages/1_Crop_Doctor.py
======================
Crop Doctor: Plant pathology diagnosis combining fine-tuned MobileNetV2 vision,
Random Forest symptom classification, Grad-CAM heatmap explainability, and multi-category
plant part support (Leaves, Fruits, Vegetables, Field Crops, Whole Plants).
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image
import streamlit as st

from components.botanical_elements import (
    inject_botanical_theme,
    render_page_header,
    render_section_title,
    render_footer,
)
from components.cards import (
    render_alert_box,
    render_confidence_bar,
    render_metric_card,
)
from components.navigation import render_sidebar_status
from components.three_scene import render_3d_plant_scene
from components.visualizations import plot_top_predictions
from modules.crop_doctor import (
    EXTENDED_AGRICULTURAL_CROPS,
    PLANT_PART_OPTIONS,
    VERIFIED_VISION_CROPS,
)
from services.crop_diagnosis import (
    check_diagnostic_eligibility,
    check_vision_model_status,
    generate_gradcam_explanation,
    run_crop_diagnosis,
)
from utils.config import CONFIDENCE_THRESHOLD
from utils.image_processing import load_image_safely, resize_thumbnail
from utils.validators import validate_image_upload

st.set_page_config(
    page_title="Crop Doctor · AgriVision",
    page_icon="🩺",
    layout="wide",
)

inject_botanical_theme()
render_sidebar_status()

render_page_header(
    eyebrow="Agricultural Diagnostic Intelligence · Multi-Category Support",
    title="Crop Doctor",
    description="Diagnose crop conditions across leaves, fruits, vegetables, field crops, and whole plants. Automated CNN vision inference is powered by verified MobileNetV2 models for foliar pathology, backed by symptom NLP classification, Grad-CAM explainability, and educational agronomic guides.",
    icon="🩺",
)

# Build crop selection list
SUPPORTED_CROP_LIST = ["Auto-detect from supported crops"] + list(VERIFIED_VISION_CROPS.keys())
CROP_OPTIONS = SUPPORTED_CROP_LIST + ["────────── Extended Crops ──────────"] + EXTENDED_AGRICULTURAL_CROPS

# Session state initialization for Crop Doctor
if "crop_image" not in st.session_state:
    st.session_state.crop_image = None
if "crop_filename" not in st.session_state:
    st.session_state.crop_filename = None
if "plant_part" not in st.session_state:
    st.session_state.plant_part = PLANT_PART_OPTIONS[0]
if "selected_crop" not in st.session_state:
    st.session_state.selected_crop = SUPPORTED_CROP_LIST[0]
if "diagnosis_result" not in st.session_state:
    st.session_state.diagnosis_result = None
if "gradcam_result" not in st.session_state:
    st.session_state.gradcam_result = None

# Diagnostic Input Layout
col_upload, col_preview = st.columns([1.1, 0.9], gap="large")

with col_upload:
    # 1. Specimen Category & Crop Selectors
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);margin-bottom:14px;">
            <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:4px;">1. Select Plant Part & Crop Category</div>
            <div style="font-size:0.85rem;color:#5E6057;margin-bottom:12px;">Choose the plant anatomical part and crop species to align the diagnostic engine with genuine model capabilities.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_part, col_crop = st.columns(2)
    with col_part:
        part_idx = 0
        if st.session_state.plant_part in PLANT_PART_OPTIONS:
            part_idx = PLANT_PART_OPTIONS.index(st.session_state.plant_part)
        selected_part = st.selectbox(
            "Plant Part / Organ",
            options=PLANT_PART_OPTIONS,
            index=part_idx,
            help="Select whether you are inspecting leaves, fruit bodies, tubers, whole plants, or field crops.",
        )
        if selected_part != st.session_state.plant_part:
            st.session_state.plant_part = selected_part
            st.session_state.diagnosis_result = None
            st.session_state.gradcam_result = None

    with col_crop:
        crop_idx = 0
        if st.session_state.selected_crop in CROP_OPTIONS:
            crop_idx = CROP_OPTIONS.index(st.session_state.selected_crop)
        chosen_crop = st.selectbox(
            "Crop Species",
            options=CROP_OPTIONS,
            index=crop_idx,
            help="Select the specific agricultural crop.",
        )
        # Prevent selecting the divider
        if "──────" in chosen_crop:
            chosen_crop = "Other / General Crop"
        if chosen_crop != st.session_state.selected_crop:
            st.session_state.selected_crop = chosen_crop
            st.session_state.diagnosis_result = None
            st.session_state.gradcam_result = None

    # Check diagnostic eligibility dynamically
    eligibility_check = check_diagnostic_eligibility(
        plant_part=st.session_state.plant_part,
        crop=st.session_state.selected_crop,
    )

    # Check vision model readiness
    model_ready, model_err = check_vision_model_status()
    part_name_short = st.session_state.plant_part.split(" ", 1)[-1].split("/")[0].strip()

    # Compact Vision Model Status Indicator
    if model_ready:
        st.markdown(
            """
            <div style="display:inline-flex;align-items:center;gap:6px;background:rgba(226,247,228,0.75);border:1px solid rgba(45,90,39,0.22);border-radius:6px;padding:3px 10px;font-size:0.82rem;font-weight:600;color:#1B3D26;margin-bottom:12px;">
                <span style="color:#2D5A27;font-size:0.9rem;font-weight:700;">✓</span>
                <span>Vision Model Ready</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="display:inline-flex;align-items:center;gap:6px;background:rgba(254,226,226,0.75);border:1px solid rgba(153,27,27,0.22);border-radius:6px;padding:3px 10px;font-size:0.82rem;font-weight:600;color:#991B1B;margin-bottom:12px;">
                <span style="font-size:0.85rem;">⚠️</span>
                <span>Vision Model Unavailable</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if model_err:
            with st.expander("Technical Model Details", expanded=False):
                st.caption(f"Error loading model weights: {model_err}")

    if not eligibility_check["can_run_cnn"]:
        st.markdown(
            f"""
            <div style="display:inline-flex;align-items:center;gap:6px;background:rgba(254,243,199,0.65);border:1px solid rgba(217,119,6,0.22);border-radius:6px;padding:3px 10px;font-size:0.82rem;font-weight:500;color:#92400E;margin-bottom:12px;margin-left:6px;">
                <span>ℹ️</span>
                <span>Advisory Guidance ({part_name_short})</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Upload Photo Card
    st.markdown(
        f"""
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);">
            <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:4px;">2. Upload {part_name_short} Photo</div>
            <div style="font-size:0.85rem;color:#5E6057;margin-bottom:12px;">Upload a clear photograph of the affected {part_name_short.lower()} (JPEG, PNG, WebP · max 8 MiB).</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        f"Choose {part_name_short.lower()} image",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        is_valid, err_msg = validate_image_upload(uploaded_file)
        if not is_valid:
            render_alert_box(err_msg, tone="danger")
        else:
            pil_img, load_err = load_image_safely(uploaded_file.getvalue())
            if load_err:
                render_alert_box(load_err, tone="danger")
            else:
                if st.session_state.crop_filename != uploaded_file.name:
                    st.session_state.crop_image = pil_img
                    st.session_state.crop_filename = uploaded_file.name
                    st.session_state.diagnosis_result = None
                    st.session_state.gradcam_result = None

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 3. Symptom text input
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);">
            <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:4px;">3. Describe Field Symptoms (Optional)</div>
            <div style="font-size:0.85rem;color:#5E6057;margin-bottom:10px;">Mention noticeable traits such as discoloration, rot spots, wilting, curling, lesions, or stunted growth.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    symptom_placeholder = (
        "e.g., Lower leaves are developing dark brown circular spots with yellow halos, and younger foliage is curling upward."
        if eligibility_check["can_run_cnn"] else
        f"e.g., Fruits show dark sunken patches at the blossom end, or tubers exhibit brown dry rotting beneath the skin."
    )

    symptom_text = st.text_area(
        "Field symptoms",
        placeholder=symptom_placeholder,
        height=100,
        label_visibility="collapsed",
    )

    col_btn1, col_btn2 = st.columns([1.5, 1])
    with col_btn1:
        run_btn = st.button("🩺 Run Diagnostic Analysis", type="primary", use_container_width=True)
    with col_btn2:
        if st.button("↺ Reset All", use_container_width=True):
            st.session_state.crop_image = None
            st.session_state.crop_filename = None
            st.session_state.plant_part = PLANT_PART_OPTIONS[0]
            st.session_state.selected_crop = SUPPORTED_CROP_LIST[0]
            st.session_state.diagnosis_result = None
            st.session_state.gradcam_result = None
            st.rerun()

with col_preview:
    if st.session_state.crop_image is not None:
        img_w, img_h = st.session_state.crop_image.size
        st.markdown(
            f"""
            <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.1rem 1.3rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);margin-bottom:10px;">
                <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:2px;">{part_name_short} Preview</div>
                <div style="font-size:0.83rem;color:#5E6057;">Selected: <b>{st.session_state.crop_filename or 'Uploaded Image'}</b> · {img_w} × {img_h} px · {st.session_state.plant_part}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        display_img = resize_thumbnail(st.session_state.crop_image, max_dim=600)
        st.image(
            display_img,
            use_container_width=True,
        )
    else:
        icon_map = {
            "leaf": "🍃",
            "fruit": "🍎",
            "vegetable": "🥔",
            "tuber": "🥔",
            "field": "🌾",
            "whole": "🪴",
            "stem": "🪴",
        }
        chosen_icon = "🍃"
        for k, v in icon_map.items():
            if k in st.session_state.plant_part.lower():
                chosen_icon = v
                break
        st.markdown(
            f"""
            <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 4px 16px rgba(0,0,0,0.03);">
                <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:12px;">{part_name_short} Preview</div>
                <div style="border:1.5px dashed rgba(27,61,38,0.18);border-radius:10px;padding:2.2rem 1rem;background:rgba(247,245,238,0.45);text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                    <div style="font-size:2rem;margin-bottom:6px;line-height:1;">{chosen_icon}</div>
                    <div style="font-weight:600;font-size:0.95rem;color:#1B3D26;margin-bottom:4px;">No {part_name_short} Image Selected</div>
                    <div style="font-size:0.84rem;color:#5E6057;">Upload a clear photo of your plant to preview and diagnose.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Run Inference
if run_btn:
    if st.session_state.crop_image is None and not symptom_text.strip():
        render_alert_box("Please upload an image or provide symptom descriptions to run diagnostic analysis.", tone="warn")
    else:
        with st.spinner("Analyzing agricultural specimen and evaluating symptoms..."):
            try:
                res = run_crop_diagnosis(
                    image=st.session_state.crop_image,
                    symptom_text=symptom_text,
                    plant_part=st.session_state.plant_part,
                    crop=st.session_state.selected_crop,
                )
                st.session_state.diagnosis_result = res
                st.session_state.gradcam_result = None
            except Exception as exc:
                render_alert_box(f"Diagnosis failed: {exc}", tone="danger")

# Display Diagnostic Results
diag = st.session_state.diagnosis_result
if diag is not None:
    render_section_title("Diagnostic Assessment & Findings", icon="🔬")

    img_res = diag.get("image_result")
    symp_res = diag.get("symptom_result")
    combined = diag.get("combined", {})
    explanation = diag.get("explanation", {})
    recommendations = diag.get("recommendations", [])
    leaf_warning = diag.get("leaf_warning")
    eligibility = diag.get("eligibility", {})
    can_run_cnn = eligibility.get("can_run_cnn", True)

    if leaf_warning:
        render_alert_box(leaf_warning, tone="warn")

    if can_run_cnn:
        # 1. Primary Diagnosis KPI Card for supported foliage CNN
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

        primary_label = "Uncertain Condition"
        if img_res and img_res.get("pretty_label"):
            primary_label = img_res["pretty_label"]
        elif symp_res and symp_res.get("pretty_label"):
            primary_label = symp_res["pretty_label"]

        with col_kpi1:
            render_metric_card(
                label="Condition",
                value=primary_label,
                subtext="Primary classification",
                border_color="#1B3D26",
            )

        with col_kpi2:
            conf_val = combined.get("combined_confidence", 0.0)
            render_metric_card(
                label="Combined Confidence",
                value=f"{conf_val * 100:.1f}%",
                subtext=f"Band: {combined.get('confidence_band', 'Standard')}",
                border_color="#2D5A27" if conf_val >= CONFIDENCE_THRESHOLD else "#C0392B",
            )

        with col_kpi3:
            sev = combined.get("severity") or (img_res.get("severity") if img_res else None) or "Moderate"
            render_metric_card(
                label="Severity Rating",
                value=sev,
                subtext="Estimated field impact",
                border_color="#92400E",
            )

        with col_kpi4:
            category = (img_res.get("category") if img_res else None) or (symp_res.get("family") if symp_res else None) or "General"
            render_metric_card(
                label="Etiology / Family",
                value=category.title(),
                subtext=f"Signals: {combined.get('signals_used', 1)} active",
                border_color="#166534",
            )

        # Confidence Threshold & Disagreement Check
        render_confidence_bar(conf_val, threshold=CONFIDENCE_THRESHOLD)

        if not combined.get("is_confident"):
            render_alert_box(
                combined.get("message")
                or "Prediction uncertain. Combined confidence is below the 70% threshold. Treat this output as an advisory indicator only and consult an agronomist.",
                tone="warn",
            )

        if combined.get("disagreement_note"):
            render_alert_box(combined["disagreement_note"], tone="warn")

        # Breakdown Columns: Predictions Chart & Detailed AI Explanation
        col_breakdown1, col_breakdown2 = st.columns([1.1, 0.9], gap="medium")

        with col_breakdown1:
            if img_res and img_res.get("top_predictions"):
                chart_fig = plot_top_predictions(img_res["top_predictions"])
                st.plotly_chart(chart_fig, use_container_width=True)

            if symp_res and not symp_res.get("error"):
                st.markdown(
                    f"""
                    <div style="background:#FFF;border:1px solid rgba(27,61,38,0.12);border-radius:12px;padding:1rem 1.2rem;margin-top:10px;">
                        <div style="font-weight:600;color:#1B3D26;font-size:0.95rem;">Symptom NLP Classifier Findings</div>
                        <div style="font-size:0.88rem;color:#2A2A26;margin-top:4px;"><b>Detected Traits:</b> {", ".join(symp_res.get("detected_features", []) or ["None specifically flagged"])}</div>
                        <div style="font-size:0.88rem;color:#2A2A26;margin-top:2px;"><b>Symptom Prediction:</b> {symp_res.get("pretty_label")} ({symp_res.get("confidence", 0.0)*100:.1f}%)</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_breakdown2:
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-left:4px solid #1B3D26;border-radius:12px;padding:1.4rem;box-shadow:0 3px 12px rgba(0,0,0,0.03);">
                    <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.25rem;color:#1B3D26;margin-bottom:6px;">Expert Explanation & Agronomic Summary</div>
                    <div style="font-size:0.8rem;color:#5E6057;margin-bottom:10px;">
                        {'Generated via Gemini 2.0 Flash' if explanation.get('used_ai') else 'Deterministic Offline Synthesis'}
                    </div>
                    <p style="font-size:0.95rem;line-height:1.6;color:#1C241B;margin:0;">{explanation.get('text', 'No explanation generated.')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if recommendations:
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.markdown(
                    """
                    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;padding:1.2rem;">
                        <div style="font-weight:700;color:#166534;font-size:0.95rem;margin-bottom:6px;">🌱 Recommended Field Actions</div>
                    """,
                    unsafe_allow_html=True,
                )
                for rec in recommendations:
                    st.markdown(f"<div style='font-size:0.9rem;color:#14532D;margin-bottom:4px;'>• {rec}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # Grad-CAM Visual Explainability Section (Side-by-side display)
        if st.session_state.crop_image is not None and img_res and not img_res.get("error"):
            render_section_title("Visual Explainability (Grad-CAM Activation Heatmap)", icon="🔍")
            st.markdown(
                "<p style='font-size:0.9rem;color:#5E6057;'>Grad-CAM isolates the specific receptive fields and lesion contours that influenced the MobileNetV2 neural network. Displayed directly alongside the original leaf image.</p>",
                unsafe_allow_html=True,
            )

            col_cam_ctrl, col_cam_btn = st.columns([2, 1])
            with col_cam_ctrl:
                cam_alpha = st.slider("Heatmap Intensity Overlay (Alpha)", min_value=0.1, max_value=0.9, value=0.45, step=0.05)
            with col_cam_btn:
                st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
                generate_cam = st.button("Generate Grad-CAM Heatmap", use_container_width=True)

            if generate_cam or st.session_state.gradcam_result is not None:
                if generate_cam:
                    with st.spinner("Computing class activation gradients..."):
                        target_lbl = img_res.get("label")
                        st.session_state.gradcam_result = generate_gradcam_explanation(
                            image=st.session_state.crop_image,
                            target_label=target_lbl,
                            alpha=cam_alpha,
                        )

                gc = st.session_state.gradcam_result
                if gc and not gc.get("error"):
                    col_g1, col_g2, col_g3 = st.columns(3)
                    with col_g1:
                        st.image(gc["original_image"], caption="1. Original Preprocessed Foliage", use_container_width=True)
                    with col_g2:
                        st.image(gc["heatmap_image"], caption="2. Grad-CAM Activation Heatmap", use_container_width=True)
                    with col_g3:
                        st.image(gc["overlay_image"], caption=f"3. Combined Diagnostic Overlay ({gc.get('explained_label', '')})", use_container_width=True)
                elif gc and gc.get("error"):
                    render_alert_box(gc["error"], tone="warn")

    else:
        # 2. Transparent Scope & Capability Notice for Non-Foliar / Extended Crop inputs
        st.markdown(
            f"""
            <div style="background:#FFFDF7;border:1px solid #FDE68A;border-left:5px solid #D97706;border-radius:14px;padding:1.4rem;box-shadow:0 3px 12px rgba(0,0,0,0.03);margin-bottom:1.4rem;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <span style="font-size:1.4rem;">🛡️</span>
                    <span style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.3rem;color:#92400E;font-weight:700;">
                        {eligibility.get("notice_title") or "Model Diagnostic Scope Notice"}
                    </span>
                </div>
                <p style="font-size:0.93rem;line-height:1.6;color:#78350F;margin:0 0 10px 0;">
                    {eligibility.get("notice_text")}
                </p>
                <div style="background:rgba(254,243,199,0.7);border-radius:8px;padding:10px 14px;font-size:0.84rem;color:#92400E;line-height:1.55;">
                    <b>Agricultural Safety Safeguard:</b> AgriVision's vision model is trained strictly on 38 PlantVillage leaf classes. The model was not trained on fruit bodies, tubers, whole plants, or field crops such as wheat, rice, or cotton. Forcibly running a leaf-disease model on these categories would produce false, dangerous classifications. Genuine multi-crop and multi-organ diagnosis requires separately trained vision models.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Show symptom NLP results if farmer provided symptom text
        if symp_res and not symp_res.get("error"):
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:14px;padding:1.4rem;box-shadow:0 3px 12px rgba(0,0,0,0.03);margin-bottom:1.4rem;">
                    <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:1.2rem;color:#1B3D26;margin-bottom:6px;">
                        🌾 Symptom NLP Diagnostic Findings (Text-Based Advisory)
                    </div>
                    <div style="font-size:0.82rem;color:#5E6057;margin-bottom:12px;">Evaluated independently via Random Forest symptom classifier.</div>
                    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px;margin-bottom:12px;">
                        <div style="background:#F7F5EE;padding:10px 12px;border-radius:8px;">
                            <div style="font-size:0.75rem;color:#5E6057;text-transform:uppercase;">Predicted Condition</div>
                            <div style="font-weight:700;color:#1B3D26;font-size:1rem;">{symp_res.get('pretty_label')}</div>
                        </div>
                        <div style="background:#F7F5EE;padding:10px 12px;border-radius:8px;">
                            <div style="font-size:0.75rem;color:#5E6057;text-transform:uppercase;">NLP Confidence</div>
                            <div style="font-weight:700;color:#166534;font-size:1rem;">{symp_res.get('confidence', 0.0)*100:.1f}%</div>
                        </div>
                        <div style="background:#F7F5EE;padding:10px 12px;border-radius:8px;">
                            <div style="font-size:0.75rem;color:#5E6057;text-transform:uppercase;">Severity</div>
                            <div style="font-weight:700;color:#92400E;font-size:1rem;">{symp_res.get('severity', 'Moderate')}</div>
                        </div>
                    </div>
                    <div style="font-size:0.9rem;color:#2A2A26;line-height:1.5;">
                        <b>Detected Symptoms:</b> {", ".join(symp_res.get('detected_features', []) or ["General indicators"])}<br/>
                        <b>Agronomic Advice:</b> {symp_res.get('advice', 'Consult a local agronomist.')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Show educational pathology guide
        guide = eligibility.get("guide")
        if guide:
            render_section_title(f"Agronomic Pathology Guide · {guide.get('title', 'Field Guidance')}", icon="📖")
            col_ed1, col_ed2 = st.columns([1.1, 0.9], gap="medium")

            with col_ed1:
                st.markdown(
                    """
                    <div style="background:#FFFFFF;border:1px solid rgba(27,61,38,0.12);border-radius:12px;padding:1.3rem;box-shadow:0 3px 12px rgba(0,0,0,0.03);">
                        <div style="font-weight:700;color:#1B3D26;font-size:1rem;margin-bottom:10px;">Common Conditions & Visual Symptoms</div>
                    """,
                    unsafe_allow_html=True,
                )
                for cond in guide.get("common_conditions", []):
                    st.markdown(f"<div style='font-size:0.88rem;color:#2A2A26;margin-bottom:8px;line-height:1.55;'>• {cond}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_ed2:
                st.markdown(
                    """
                    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;padding:1.3rem;">
                        <div style="font-weight:700;color:#166534;font-size:1rem;margin-bottom:10px;">🌱 Recommended Field & Scouting Actions</div>
                    """,
                    unsafe_allow_html=True,
                )
                for act in guide.get("field_actions", []):
                    st.markdown(f"<div style='font-size:0.88rem;color:#14532D;margin-bottom:8px;line-height:1.55;'>• {act}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # Interactive 3D Specimen Inspection View
    with st.expander("🌿 Interactive 3D Plant Specimen Inspection (Rotate & Zoom)"):
        st.markdown(
            "<p style='font-size:0.85rem;color:#5E6057;'>Inspect an interactive 3D model of plant foliage structure. Drag to rotate 360°, scroll to zoom in on upper or lower leaf tiers.</p>",
            unsafe_allow_html=True,
        )
        render_3d_plant_scene(height=340, view_mode="plant", auto_rotate=False)

    # Agricultural Uncertainty Disclaimer
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:0.9rem 1.2rem;font-size:0.85rem;color:#92400E;line-height:1.5;">
            <b>⚠️ Agricultural Advisory Notice:</b> Crop Doctor's machine learning outputs are intended as decision-support heuristics and should never be treated as guaranteed legal or chemical determinations. Always inspect live plants in person, monitor field progression, and confirm chemical interventions with your local Krishi Vigyan Kendra (KVK) or certified agricultural extension officer.
        </div>
        """,
        unsafe_allow_html=True,
    )

render_footer()
