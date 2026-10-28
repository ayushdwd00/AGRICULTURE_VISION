"""
services/crop_diagnosis.py
==========================
Service managing crop leaf disease vision inference, symptom NLP classification,
Grad-CAM heatmaps, explanation synthesis, and multi-category plant part handling
with Streamlit resource caching.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import streamlit as st

from modules import crop_doctor
from modules.crop_doctor import (
    EXTENDED_AGRICULTURAL_CROPS,
    PLANT_PART_OPTIONS,
    VERIFIED_VISION_CROPS,
)
from modules.symptom_model import predict_symptoms, symptom_model_status
from utils.caching import cached_resource
from utils.config import SAMPLE_IMAGES_DIR
from utils.gemini import (
    GeminiError,
    fallback_diagnosis,
    generate_description,
    generate_visual_observations,
    recommendation_for_image,
)
from utils.image_processing import check_leaf_suitability, load_image_safely, resize_thumbnail

__all__ = [
    "EXTENDED_AGRICULTURAL_CROPS",
    "PLANT_PART_OPTIONS",
    "VERIFIED_VISION_CROPS",
    "EDUCATIONAL_PATHOLOGY_GUIDES",
    "get_cached_vision_model",
    "check_vision_model_status",
    "get_cached_symptom_status",
    "get_available_sample_images",
    "check_diagnostic_eligibility",
    "run_crop_diagnosis",
    "generate_gradcam_explanation",
]


@cached_resource
def get_cached_vision_model() -> Tuple[Any, List[str], Path]:
    """Cache the PyTorch MobileNetV2 model in memory across Streamlit reruns."""
    return crop_doctor.get_model(prefer_fine_tuned=True)


def check_vision_model_status() -> Tuple[bool, Optional[str]]:
    """
    Check if the vision model is successfully loaded and ready for inference.
    Returns (is_ready, error_message).
    """
    try:
        model, class_names, weights_path = get_cached_vision_model()
        if model is not None and weights_path and weights_path.exists():
            return True, None
        return False, "Model file not found or corrupted."
    except Exception as exc:
        return False, str(exc)


@cached_resource
def get_cached_symptom_status() -> Dict[str, Any]:
    """Check symptom classification model file status."""
    return symptom_model_status()


def get_available_sample_images() -> List[Dict[str, Any]]:
    """Return available sample leaf images for quick demonstration."""
    samples = []
    if SAMPLE_IMAGES_DIR.exists():
        for p in sorted(SAMPLE_IMAGES_DIR.glob("*.*")):
            if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                label = p.stem.replace("sample_", "").replace("_", " ").title()
                # Determine matching crop
                stem_lower = p.stem.lower()
                crop_name = "Tomato"
                if "pepper" in stem_lower:
                    crop_name = "Pepper (Bell)"
                elif "potato" in stem_lower:
                    crop_name = "Potato"
                elif "apple" in stem_lower:
                    crop_name = "Apple"
                elif "corn" in stem_lower:
                    crop_name = "Corn (Maize)"
                elif "grape" in stem_lower:
                    crop_name = "Grape"

                samples.append({
                    "name": label,
                    "path": p,
                    "filename": p.name,
                    "crop": crop_name,
                    "part": "🍃 Leaf / Foliage",
                })
    return samples


EDUCATIONAL_PATHOLOGY_GUIDES: Dict[Tuple[str, str], Dict[str, Any]] = {
    # Fruit guides
    ("Fruit", "Tomato"): {
        "title": "Tomato Fruit Pathology & Physiological Disorders",
        "common_conditions": [
            "Blossom End Rot: Dark, sunken leathery patch at the blossom end caused by localized calcium deficiency aggravated by uneven watering.",
            "Anthracnose (Colletotrichum coccodes): Circular, sunken water-soaked spots with dark concentric rings on ripening fruit.",
            "Sunscald: White, papery, blistered areas on fruit surfaces exposed to intense direct sunlight following canopy loss.",
            "Catfacing: Severe scarring, puckering, and deep indents on blossom end caused by cold weather during pollination.",
            "Fruit Borer (Helicoverpa armigera): Entry holes near calyx with larval frass, inducing secondary bacterial soft rot.",
        ],
        "field_actions": [
            "Maintain uniform soil moisture with drip irrigation to ensure steady calcium uptake.",
            "Foliar spray of 0.5% calcium nitrate during early fruit setting.",
            "Apply neem-based formulations or recommended bio-pesticides for early borer management.",
            "For automated AI vision diagnosis, upload a close-up photo of symptomatic foliage.",
        ],
    },
    ("Fruit", "Apple"): {
        "title": "Apple Fruit Pathology & Storage Disorders",
        "common_conditions": [
            "Apple Scab (Venturia inaequalis): Dark, scabby, olive-black crusty lesions causing fruit cracking and distortion.",
            "Bitter Rot (Colletotrichum fioriniae): Brown sunken circular lesions producing salmon-pink spore masses in humid weather.",
            "Black Rot (Diplodia seriata): Firm brown decay turning coal-black, mummifying fruit on the spur.",
            "Sooty Blotch and Flyspeck: Superficial dark smudges and tiny shiny black dots blemishing cuticle quality.",
        ],
        "field_actions": [
            "Prune canopy for adequate light penetration and fast leaf/fruit drying.",
            "Apply protective orchard fungicides at pink-bud and petal-fall stages.",
            "Remove mummified fruits and dead twigs to deplete overwintering inoculum.",
        ],
    },
    ("Fruit", "Orange (Citrus)"): {
        "title": "Citrus Fruit Pathology & Quality Disorders",
        "common_conditions": [
            "Citrus Canker (Xanthomonas axonopodis pv. citri): Corky, crater-like raised lesions with water-soaked margins on fruit rinds.",
            "Huanglongbing (HLB / Citrus Greening): Small, lopsided, poorly colored fruit with inverted color break (green at stylar end).",
            "Citrus Black Spot (Phyllosticta citricarpa): Hard circular spots with dark brown margins and gray depressed centers.",
            "Anthracnose (Colletotrichum gloeosporioides): Tear-staining and reddish-brown peel staining following wet spells.",
        ],
        "field_actions": [
            "Vector control for Asian citrus psyllid (Diaphorina citri) to prevent HLB spread.",
            "Copper hydroxide / oxychloride sprays following post-bloom fruit enlargement.",
            "Prune infected branches and avoid overhead sprinkler irrigation.",
        ],
    },
    ("Fruit", "Grape"): {
        "title": "Grape Cluster Pathology & Bunch Rot Complex",
        "common_conditions": [
            "Black Rot of Grapes (Guignardia bidwellii): Berries turn light brown, shrivel rapidly, and transform into hard, shrunken black mummies.",
            "Botrytis Bunch Rot (Gray Mold): Soft rotting of berries with mouse-gray fuzzy fungal sporulation within tight clusters.",
            "Powdery Mildew on Clusters: Berries coated in ash-gray powder, failing to size, skin cracking and exposing seeds.",
            "Anthracnose (Bird's Eye Rot): Sunken circular spots on berries with dark purple-brown rings and grayish centers.",
        ],
        "field_actions": [
            "Leaf-plucking in the fruiting zone to enhance cluster aeration and spray coverage.",
            "Maintain preventative fungicide protection from pre-bloom through bunch closure.",
            "Avoid bunch bruising and manage berry moth pests.",
        ],
    },
    ("Fruit", "Mango"): {
        "title": "Mango Fruit Pathology & Post-Harvest Disorders",
        "common_conditions": [
            "Anthracnose (Colletotrichum gloeosporioides): Dark brown to black irregular sunken spots on developing and ripe fruits.",
            "Powdery Mildew (Oidium mangiferae): White powdery coating on panicles and young pea-sized fruitlets, causing massive drop.",
            "Mango Bacterial Canker: Dark, star-shaped cracks on fruit skin exuding gummy sap.",
            "Fruit Fly Damage (Bactrocera dorsalis): Oviposition punctures leading to pulp softening, internal rot, and premature fruit fall.",
        ],
        "field_actions": [
            "Install methyl eugenol pheromone traps (10 traps/ha) for fruit fly suppression.",
            "Pre-harvest spray with copper oxychloride (0.25%) or azoxystrobin (0.1%).",
            "Post-harvest hot water treatment (52°C for 10 minutes) for fruit quality preservation.",
        ],
    },
    ("Fruit", "Banana"): {
        "title": "Banana Bunch & Fruit Peel Pathology",
        "common_conditions": [
            "Anthracnose (Colletotrichum musae): Black diamond-shaped specks expanding into large sunken lesions on ripening fingers.",
            "Cigar End Rot (Verticillium theobromae): Dry, black rot resembling the burning tip of a cigar, progressing from the perianth.",
            "Finger Drop Disorder: Weak pedicels causing fruit detachment during ripening.",
            "Banana Freckle: Raised dark sandpaper-like spots on peel caused by Phyllosticta musarum.",
        ],
        "field_actions": [
            "Remove dried floral parts (perianth) manually after bunch emergence.",
            "Bag bunches with perforated polyethylene sleeves to shield fruits from rain and insect blemishes.",
            "Apply recommended protective sprays at bunch shoot formation.",
        ],
    },
    # Vegetable guides
    ("Vegetable", "Potato"): {
        "title": "Potato Tuber Pathology & Storage Disorders",
        "common_conditions": [
            "Late Blight Tuber Rot (Phytophthora infestans): Brownish dry granular rot penetrating beneath the peel, leading to secondary wet rot.",
            "Common Scab (Streptomyces scabies): Corky, pitted or raised surface lesions on tuber skin, compromising marketable grade.",
            "Black Scurf (Rhizoctonia solani): Hard, black dirt-like sclerotial masses adhering firmly to tuber skin ('dirt that won't wash off').",
            "Bacterial Soft Rot (Pectobacterium carotovorum): Water-soaked, foul-smelling liquefaction of tuber flesh in warm, wet soils.",
        ],
        "field_actions": [
            "Ensure certified disease-free seed tubers treated with carbendazim or mancozeb.",
            "Hilling up ridge height to prevent rain-washed blight zoospores from contacting tubers.",
            "Allow skin curing (10-14 days after dehaulming) before harvesting in dry weather.",
        ],
    },
    ("Vegetable", "Onion"): {
        "title": "Onion Bulb Pathology & Storage Disorders",
        "common_conditions": [
            "Purple Blotch (Alternaria porri): Deep purple sunken lesions on leaf blades and bulb necks.",
            "Basal Rot (Fusarium oxysporum f. sp. cepae): Softening of the bulb base and root decay, yellowing foliage.",
            "Black Mold (Aspergillus niger): Black powdery spore masses along outer bulb scale veins in warm storage.",
            "Bacterial Soft Rot: Water-soaked collapse of inner fleshy scales with pungent sour odor.",
        ],
        "field_actions": [
            "Crop rotation with non-allium crops for at least 3 years to lower Fusarium inoculum.",
            "Proper bulb field curing (outer dry neck) before warehouse grading.",
            "Ensure well-ventilated, moisture-controlled storage racks.",
        ],
    },
    ("Vegetable", "Pepper (Bell)"): {
        "title": "Bell Pepper Pod & Vegetable Pathology",
        "common_conditions": [
            "Blossom End Rot: Water-soaked, flat, light brown lesion at the blossom tip due to calcium imbalance.",
            "Sunscald: Bleached, parchment-like collapsed fruit wall caused by direct midday thermal radiation.",
            "Anthracnose Fruit Rot: Circular sunken spots with concentric rings of salmon-pink gelatinous spore masses.",
            "Bacterial Spot on Pods: Small, raised blisters that become brown, cratered, and rough-surfaced.",
        ],
        "field_actions": [
            "Maintain uniform drip irrigation scheduling to prevent calcium transport lapses.",
            "Avoid excessive nitrogen fertilization which causes lush canopy but vulnerable fruit.",
            "Apply copper-based protectants before heavy monsoon rain intervals.",
        ],
    },
    ("Vegetable", "Eggplant (Brinjal)"): {
        "title": "Eggplant (Brinjal) Vegetable & Fruit Pathology",
        "common_conditions": [
            "Phomopsis Blight & Fruit Rot (Phomopsis vexans): Large, pale, sunken spots on fruit with tiny black pycnidia, softening the flesh.",
            "Bacterial Wilt (Ralstonia solanacearum): Rapid daytime wilting and vascular browning without prior leaf yellowing.",
            "Shoot and Fruit Borer (Leucinodes orbonalis): Bored holes plugged with frass, causing fruit deformation and unmarketable crop.",
            "Little Leaf of Brinjal: Severe leaf reduction, bushy appearance, and failure to produce viable floral buds.",
        ],
        "field_actions": [
            "Clip and destroy wilting shoot tips and borer-damaged fruits weekly.",
            "Use pheromone traps (Lucin-lure, 25 traps/ha) for mass borer capture.",
            "Drench soil with biocontrol agents (Trichoderma viride + Pseudomonas fluorescens) against soil-borne wilt.",
        ],
    },
    ("Vegetable", "Cucumber"): {
        "title": "Cucumber Vegetable & Fruit Pathology",
        "common_conditions": [
            "Downy Mildew (Pseudoperonospora cubensis): Angular yellow chlorotic patches constrained by leaf veins with purplish sporulation below.",
            "Powdery Mildew (Podosphaera xanthii): White powdery fungal talcum covering foliage, stunting cucumber fruit enlargement.",
            "Anthracnose Fruit Rot: Sunken circular lesions with salmon-pink spore droplets on cucumber fruit bodies.",
            "Cucumber Mosaic Virus (CMV): Stunted, pale, warted, and mottled fruit distortion transmitted by aphid vectors.",
        ],
        "field_actions": [
            "Provide vertical trellis training to lift fruits off moist soil and improve aeration.",
            "Spray systemic fungicides (metalaxyl or cymoxanil + mancozeb) upon initial downy mildew detection.",
            "Control aphid vector colonies early using yellow sticky cards and insecticidal soap.",
        ],
    },
    # Field Crop guides
    ("Field Crop", "Wheat"): {
        "title": "Wheat Field Crop Pathology & Rust Monitoring",
        "common_conditions": [
            "Yellow / Stripe Rust (Puccinia striiformis): Lemon-yellow pustules arranged in characteristic narrow parallel stripes along leaf blades.",
            "Brown / Leaf Rust (Puccinia triticina): Small, round, scattered orange-brown pustules on upper leaf surfaces.",
            "Karnal Bunt (Tilletia indica): Partial conversion of grains into black, pungent (trimethylamine) powdery teliospore masses.",
            "Loose Smut (Ustilago tritici): Entire ear head transformed into a black sooty mass of fungal spores at ear emergence.",
            "Powdery Mildew: White cottony patches turning dull gray with black cleistothecia on lower canopy.",
        ],
        "field_actions": [
            "Conduct structured field surveillance weekly for yellow rust focal foci.",
            "Spray propiconazole 25% EC (0.1%) or tebuconazole upon initial stripe rust detection.",
            "Treat seed with carboxin or tebuconazole to eliminate seed-borne loose smut.",
        ],
    },
    ("Field Crop", "Rice"): {
        "title": "Rice Paddy Pathology & Panicle Diseases",
        "common_conditions": [
            "Rice Blast (Magnaporthe oryzae): Spindle-shaped eye lesions on leaves; brownish-black rotting of the panicle neck (Neck Blast).",
            "Bacterial Leaf Blight (Xanthomonas oryzae pv. oryzae): Water-soaked streaks starting from leaf margins turning yellowish-white with bacterial ooze.",
            "Sheath Blight (Rhizoctonia solani): Oval, greenish-gray snake-skin lesions on leaf sheaths near the water line.",
            "False Smut (Ustilaginoidea virens): Individual rice grains transform into velvety yellow-orange or greenish-black spore balls.",
        ],
        "field_actions": [
            "Split nitrogen doses (basal, tillering, panicle initiation) rather than heavy single applications.",
            "Apply tricyclazole 75% WP (0.06%) at boot leaf stage to protect against neck blast.",
            "Drain field temporarily to reduce relative humidity around plant bases when sheath blight appears.",
        ],
    },
    ("Field Crop", "Cotton"): {
        "title": "Cotton Field Crop & Boll Pathology",
        "common_conditions": [
            "Cotton Leaf Curl Virus (CLCuV): Thickened veins, upward leaf curling, and enations (leaf-like outgrowths) on lower leaf surfaces.",
            "Bacterial Blight / Angular Leaf Spot (Xanthomonas citri pv. malvacearum): Angular water-soaked leaf spots and black arm stem lesions.",
            "Boll Rot Complex: Rotting of internal lint and seed caused by fungi/bacteria following insect puncture wounds.",
            "Fusarium / Verticillium Wilt: Interveinal chlorosis ('tiger stripe' pattern) followed by vascular browning in the stem xylem.",
        ],
        "field_actions": [
            "Manage whitefly (Bemisia tabaci) populations vigorously to prevent viral transmission.",
            "Apply copper oxychloride (0.3%) + streptocycline (100 ppm) for bacterial blight outbreaks.",
            "Avoid excessive irrigation during boll formation to prevent high humidity in dense canopies.",
        ],
    },
    ("Field Crop", "Corn (Maize)"): {
        "title": "Maize (Corn) Field Crop & Ear Pathology",
        "common_conditions": [
            "Northern Corn Leaf Blight (Exserohilum turcicum): Long, elliptical, grayish-green to tan lesions up to 15 cm long.",
            "Common Rust (Puccinia sorghi): Golden brown to cinnamon-brown powdery pustules on both upper and lower leaf surfaces.",
            "Maydis Leaf Blight: Rectangular tan lesions bounded by veins.",
            "Fusarium Ear Rot / Gibberella: White to pink mold growth on ear kernels starting from the tip down.",
        ],
        "field_actions": [
            "Foliar application of azoxystrobin + tebuconazole or mancozeb at tasseling stage.",
            "Deep summer plowing to bury infected crop residues.",
            "Ensure proper ear drying before sheller harvesting to avoid mycotoxin build-up.",
        ],
    },
    ("Field Crop", "Soybean"): {
        "title": "Soybean Field Crop & Pod Pathology",
        "common_conditions": [
            "Soybean Rust (Phakopsora pachyrhizi): Tiny brown to tan lesions with eruptive raised volcanic pustules on undersides of leaves.",
            "Anthracnose & Pod Blight (Colletotrichum truncatum): Irregular brown spots on stems and pods with black acervuli setae.",
            "Yellow Mosaic Virus (MYMV): Irregular bright yellow and green mottling of foliage spread by whiteflies.",
            "Charcoal Rot (Macrophomina phaseolina): Premature senescence with silvery gray discoloration and microsclerotia inside split stems.",
        ],
        "field_actions": [
            "Maintain optimum plant spacing to avoid excessive canopy humidity.",
            "Seed treatment with thiram + carbendazim (2:1 at 3g/kg seed).",
            "Apply hexaconazole or propiconazole at first appearance of rust pustules.",
        ],
    },
    # Whole Plant guides
    ("Whole Plant", "General"): {
        "title": "Whole Plant, Stem & Root Pathology Guidelines",
        "common_conditions": [
            "Vascular Wilt Syndrome (Fusarium / Verticillium): Progressive daytime wilting, vascular cylinder browning when stem is sliced lengthwise.",
            "Damping-off & Collar Rot (Pythium / Rhizoctonia / Sclerotium): Dark, water-soaked constriction at soil line causing collapse of young stems.",
            "Stem Blight & Cankers: Depressed dark necrotic lesions girdling main stems or lateral scaffold branches.",
            "Root Rot Complex: Decayed, black or brown spongy roots stripped of feeder hair roots, resulting in generalized stunting and chlorosis.",
        ],
        "field_actions": [
            "Uproot and dissect one representative symptomatic plant to inspect internal stem vascular color and root health.",
            "Ensure raised bed drainage to avoid soil waterlogging and hypoxic root asphyxiation.",
            "Incorporate bio-fungicides (Trichoderma harzianum @ 5 kg/ha in farmyard manure) at soil preparation.",
            "For automated AI vision diagnosis, upload a clear close-up photograph of an affected leaf blade.",
        ],
    },
}


def check_diagnostic_eligibility(
    plant_part: str = "🍃 Leaf / Foliage",
    crop: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Determine whether the selected plant part and crop are within the leaf CNN's
    validated PlantVillage scope.
    """
    part_clean = plant_part.strip()
    is_leaf = "leaf" in part_clean.lower() or "foliage" in part_clean.lower()

    crop_clean = (crop or "").strip()
    is_auto = not crop_clean or "auto" in crop_clean.lower() or "all" in crop_clean.lower()
    is_supported_crop = is_auto or crop_clean in crop_doctor.VERIFIED_VISION_CROPS

    can_run = is_leaf and is_supported_crop

    # Standardize category key
    if "fruit" in part_clean.lower():
        category_key = "Fruit"
    elif "vegetable" in part_clean.lower() or "tuber" in part_clean.lower():
        category_key = "Vegetable"
    elif "field" in part_clean.lower():
        category_key = "Field Crop"
    elif "whole" in part_clean.lower() or "stem" in part_clean.lower():
        category_key = "Whole Plant"
    elif "leaf" in part_clean.lower() or "foliage" in part_clean.lower():
        category_key = "Leaf"
    else:
        category_key = "Other"

    return {
        "can_run_cnn": can_run,
        "is_leaf": is_leaf,
        "is_supported_crop": is_supported_crop,
        "category_key": category_key,
        "crop_clean": crop_clean,
        "guide": None,
    }


def run_crop_diagnosis(
    image: Optional[Image.Image] = None,
    symptom_text: Optional[str] = None,
    plant_part: str = "🍃 Leaf / Foliage",
    crop: Optional[str] = None,
    use_ai_visual_review: bool = False,
) -> Dict[str, Any]:
    """
    Run the validated leaf CNN only for supported crop leaves. For other image
    categories, return a preliminary report without making a CNN prediction.
    """
    eligibility = check_diagnostic_eligibility(plant_part=plant_part, crop=crop)
    image_result: Optional[Dict[str, Any]] = None
    leaf_warning: Optional[str] = None
    visual_review: Optional[Dict[str, Any]] = None
    visual_review_error: Optional[str] = None

    if image is not None:
        if eligibility["can_run_cnn"]:
            is_suitable, warning = check_leaf_suitability(image)
            if not is_suitable:
                leaf_warning = warning

            # Efficiently downsample large image before inference
            scaled_img = resize_thumbnail(image, max_dim=800)
            try:
                model, class_names, weights_path = get_cached_vision_model()
                image_result = crop_doctor.predict_from_image(
                    image=scaled_img,
                    model=model,
                    class_names=class_names,
                    weights_path=weights_path,
                    top_k=3,
                )
            except Exception as exc:
                image_result = crop_doctor._empty_result(
                    f"Vision model unavailable: {exc}. Please verify model weights or provide field symptoms."
                )
        else:
            # Model cannot diagnose this category - do not run CNN to prevent false predictions
            image_result = None
            if use_ai_visual_review:
                try:
                    visual_review = generate_visual_observations(
                        resize_thumbnail(image, max_dim=900),
                        crop=crop if crop and "auto-detect" not in crop.lower() else None,
                    )
                except GeminiError as exc:
                    visual_review_error = str(exc)

    symptom_result: Optional[Dict[str, Any]] = None
    cleaned_symptoms = (symptom_text or "").strip()
    if cleaned_symptoms:
        symptom_result = predict_symptoms(cleaned_symptoms)

    recommendations: List[str] = []
    image_prediction = bool(
        image_result and not image_result.get("error") and image_result.get("label")
    )

    if eligibility["can_run_cnn"]:
        combined = crop_doctor.combine_signals(image_result, symptom_result)
        # Explanation generation
        if combined.get("is_confident"):
            explanation = generate_description(image_result, symptom_result, cleaned_symptoms, combined)
        else:
            explanation = {
                "text": fallback_diagnosis(image_result, symptom_result, combined, cleaned_symptoms),
                "source": "offline-fallback",
                "used_ai": False,
                "model": None,
                "error": None,
                "prompt": None,
            }

        if image_prediction:
            rec = recommendation_for_image(image_result)
            if rec:
                recommendations.append(rec)
        if symptom_result and not symptom_result.get("error") and symptom_result.get("advice"):
            adv = symptom_result["advice"]
            if adv and adv not in recommendations:
                recommendations.append(adv)

    else:
        combined = {
            "combined_confidence": None,
            "is_confident": False,
            "threshold": None,
            "confidence_band": "Not evaluated",
            "message": None,
            "agreement": None,
            "disagreement_note": None,
            "severity": None,
            "signals_used": 0,
            "image_confidence": None,
            "symptom_confidence": None,
        }
        explanation = {
            "text": "This image category is not covered by the image diagnosis model.",
            "source": "preliminary-assessment",
            "used_ai": False,
            "model": None,
            "error": None,
            "prompt": None,
        }

    selected_crop = (
        crop.strip()
        if crop and "auto-detect" not in crop.lower() and "general crop" not in crop.lower()
        else None
    )
    crop_name = (
        selected_crop
        or (image_result.get("crop") if image_prediction else None)
        or (visual_review.get("crop") if visual_review else None)
    )
    symptom_description = cleaned_symptoms or None
    if image_prediction:
        assessment_type = "CNN diagnosis"
        visible_symptoms = None
        confidence = float(image_result["confidence"])
    elif image is not None:
        assessment_type = (
            "Preliminary visual assessment (AI-assisted)"
            if visual_review
            else (
                "Preliminary assessment (based on your description)"
                if symptom_description
                else "Image uploaded; visual symptoms not assessed automatically"
            )
        )
        observations = visual_review.get("observations", []) if visual_review else []
        if observations:
            visible_symptoms = "; ".join(observations)
        elif visual_review:
            visible_symptoms = "No clear visible symptoms were identified in the photo."
        elif symptom_description:
            visible_symptoms = None
        else:
            visible_symptoms = (
                "Visible symptoms are not automatically identified for this image category. "
                "Add a short description of what you can see for a more useful assessment."
            )
        confidence = None
    else:
        assessment_type = "Symptom description only"
        visible_symptoms = (
            None if symptom_description else "No image or symptom description was provided."
        )
        confidence = None

    possible_causes = (
        [f"CNN model prediction: {image_result.get('pretty_label') or image_result['label']}"]
        if image_prediction
        else []
    )
    cause_note = (
        "This is a model prediction, not a confirmed diagnosis."
        if image_prediction
        else (
            "The cause cannot be determined from this image alone. Similar marks can have "
            "different causes, and the affected fruit and foliage may need to be assessed separately."
            if image is not None
            else "There is not enough information to suggest a cause."
        )
    )
    next_steps = []
    if image_prediction and confidence >= crop_doctor.THRESHOLD:
        image_action = recommendation_for_image(image_result)
        if image_action:
            next_steps.append(image_action)
    next_steps.extend(
        [
            "Photograph affected areas clearly and check whether symptoms are spreading.",
            "Inspect nearby plants for similar changes and avoid treatment until the cause is clearer.",
        ]
    )
    assessment_report = {
        "crop": crop_name,
        "crop_basis": (
            "Selected by you"
            if selected_crop
            else "CNN prediction"
            if image_prediction and image_result.get("crop")
            else "AI visual estimate"
            if visual_review and crop_name
            else "Not identified"
        ),
        "plant_part": (
            "Not selected"
            if plant_part.strip().lower() == "select plant part"
            else plant_part.split(" ", 1)[-1]
            if " " in plant_part
            else plant_part
        ),
        "visible_symptoms": visible_symptoms,
        "reported_symptoms": symptom_description,
        "observed_plant_parts": visual_review.get("plant_parts", []) if visual_review else [],
        "assessment_type": assessment_type,
        "confidence": confidence,
        "possible_causes": possible_causes,
        "cause_note": cause_note,
        "next_steps": next_steps,
        "further_help": (
            "Share clear photos of both sides of affected leaves and the full fruit, including where "
            "each mark is located. Note when symptoms began, how quickly they are changing, and recent "
            "rain or watering. Ask a local agricultural extension officer or plant pathologist if the "
            "cause remains uncertain."
        ),
        "preliminary_note": (
            (
                "These image observations are preliminary and are not a confirmed or laboratory diagnosis."
                if visual_review
                else "This assessment is preliminary and is not a confirmed or laboratory diagnosis."
                if symptom_description
                else "No confirmed diagnosis was made from this image."
            )
            if image is not None and not image_prediction
            else None
        ),
        "visual_review_error": visual_review_error,
    }

    return {
        "image_result": image_result,
        "symptom_result": symptom_result,
        "combined": combined,
        "explanation": explanation,
        "recommendations": recommendations,
        "leaf_warning": leaf_warning,
        "eligibility": eligibility,
        "assessment_report": assessment_report,
    }


def generate_gradcam_explanation(
    image: Image.Image,
    target_label: Optional[str] = None,
    alpha: float = 0.45,
) -> Dict[str, Any]:
    """Generate Grad-CAM activation heatmap overlay for visual explainability on supported vision model."""
    try:
        from utils.gradcam import gradcam_overlay
        model, class_names, weights_path = get_cached_vision_model()
        scaled_img = resize_thumbnail(image, max_dim=800)
        tensor = crop_doctor.preprocess_image(scaled_img, device=crop_doctor.get_device())
        result = gradcam_overlay(
            model=model,
            input_tensor=tensor,
            class_names=class_names,
            target_label=target_label,
            alpha=alpha,
        )
        result["model_used"] = weights_path.name
        result["error"] = None
        return result
    except Exception as exc:
        return {"error": f"Grad-CAM generation failed: {type(exc).__name__}: {exc}"}
