import unittest
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from services import crop_diagnosis
from utils import gemini
from utils.image_processing import assess_image_quality, load_image_safely


class CropDiagnosisReportTests(unittest.TestCase):
    def test_tomato_fruit_uses_preliminary_report_without_cnn(self):
        image = Image.new("RGB", (128, 128), "red")

        with patch.object(crop_diagnosis, "get_cached_vision_model") as get_model:
            result = crop_diagnosis.run_crop_diagnosis(
                image=image,
                plant_part="🍎 Fruit",
                crop="Tomato",
            )

        get_model.assert_not_called()
        report = result["assessment_report"]
        self.assertIsNone(result["image_result"])
        self.assertEqual(report["crop"], "Tomato")
        self.assertEqual(report["plant_part"], "Fruit")
        self.assertEqual(
            report["assessment_type"],
            "Image uploaded; visual symptoms not assessed automatically",
        )
        self.assertIsNone(report["model_score"])
        self.assertEqual(report["possible_causes"], [])
        self.assertIn("cannot be determined", report["cause_note"])
        self.assertTrue(report["preliminary_note"])

    def test_other_unsupported_parts_and_crops_never_call_leaf_cnn(self):
        image = Image.new("RGB", (128, 128), "green")
        unsupported_inputs = (
            ("Select plant part", "Tomato"),
            ("🍎 Fruit", "Tomato"),
            ("🥔 Vegetable / Tuber", "Potato"),
            ("🪴 Whole Plant / Stem", "Tomato"),
            ("🌾 Field Crop", "Rice"),
            ("🌱 Root", "Tomato"),
            ("🌼 Flower", "Tomato"),
            ("🌱 Seedling", "Tomato"),
            ("🍃 Leaf / Foliage", "Mango"),
        )
        with patch.object(crop_diagnosis, "get_cached_vision_model") as get_model:
            for part, crop in unsupported_inputs:
                with self.subTest(part=part, crop=crop):
                    result = crop_diagnosis.run_crop_diagnosis(
                        image=image,
                        plant_part=part,
                        crop=crop,
                    )
                    self.assertIsNone(result["image_result"])
                    self.assertIsNone(result["assessment_report"]["model_score"])
        get_model.assert_not_called()

    def test_unsupported_image_reports_only_user_described_symptoms(self):
        image = Image.new("RGB", (128, 128), "red")
        description = "Dark sunken fruit lesions and damaged foliage"
        symptom_result = {
            "label": "fungal",
            "pretty_label": "Fungal condition",
            "confidence": 0.73,
            "advice": "Review the symptoms with an adviser.",
        }

        with (
            patch.object(crop_diagnosis, "predict_symptoms", return_value=symptom_result),
            patch.object(crop_diagnosis, "get_cached_vision_model") as get_model,
        ):
            result = crop_diagnosis.run_crop_diagnosis(
                image=image,
                symptom_text=description,
                plant_part="🍎 Fruit",
                crop="Tomato",
            )

        get_model.assert_not_called()
        self.assertIsNone(result["assessment_report"]["model_score"])
        self.assertEqual(result["assessment_report"]["reported_symptoms"], description)
        self.assertEqual(result["symptom_result"]["confidence"], 0.73)
        self.assertEqual(result["assessment_report"]["possible_causes"], [])

    def test_opted_in_visual_review_is_preliminary_without_confidence(self):
        image = Image.new("RGB", (128, 128), "red")
        observations = {
            "crop": "Tomato",
            "plant_parts": ["fruit", "foliage"],
            "observations": [
                "Dark, sunken-looking marks are visible on the fruit.",
                "Some foliage appears damaged.",
            ],
        }
        with patch.object(
            crop_diagnosis,
            "generate_visual_observations",
            return_value=observations,
        ) as review:
            result = crop_diagnosis.run_crop_diagnosis(
                image=image,
                plant_part="🍎 Fruit",
                crop="Auto-detect from supported crops",
                use_ai_visual_review=True,
            )

        review.assert_called_once()
        report = result["assessment_report"]
        self.assertEqual(report["crop"], "Tomato")
        self.assertEqual(report["crop_basis"], "AI visual estimate")
        self.assertEqual(report["assessment_type"], "Preliminary visual assessment (AI-assisted)")
        self.assertEqual(
            report["visible_symptoms"],
            "Dark, sunken-looking marks are visible on the fruit.; Some foliage appears damaged.",
        )
        self.assertEqual(report["observed_plant_parts"], ["fruit", "foliage"])
        self.assertIsNone(report["model_score"])
        self.assertEqual(report["possible_causes"], [])

    def test_supported_leaf_still_uses_cnn_prediction_and_confidence(self):
        image = Image.new("RGB", (128, 128), "green")
        prediction = {
            "label": "Tomato___Early_blight",
            "pretty_label": "Tomato Early Blight",
            "confidence": 0.62,
            "category": "fungal",
            "error": None,
        }

        with (
            patch.object(
                crop_diagnosis,
                "get_cached_vision_model",
                return_value=(object(), ["Tomato___Early_blight"], Path("weights.pth")),
            ),
            patch.object(
                crop_diagnosis.crop_doctor,
                "predict_from_image",
                return_value=prediction,
            ),
        ):
            result = crop_diagnosis.run_crop_diagnosis(
                image=image,
                plant_part="🍃 Leaf / Foliage",
                crop="Tomato",
            )

        self.assertIs(result["image_result"], prediction)
        self.assertEqual(result["assessment_report"]["assessment_type"], "CNN diagnosis")
        self.assertEqual(result["assessment_report"]["model_score"], 0.62)
        self.assertEqual(result["assessment_report"]["status"], "Supported model assessment")

    def test_selected_crop_mismatch_does_not_count_as_supported_diagnosis(self):
        image = Image.new("RGB", (128, 128), "green")
        prediction = {
            "label": "Potato___Late_blight",
            "pretty_label": "Potato - Late blight",
            "crop": "Potato",
            "confidence": 0.91,
            "category": "fungal",
            "error": None,
        }

        with (
            patch.object(
                crop_diagnosis,
                "get_cached_vision_model",
                return_value=(object(), ["Potato___Late_blight"], Path("weights.pth")),
            ),
            patch.object(
                crop_diagnosis.crop_doctor,
                "predict_from_image",
                return_value=prediction,
            ),
        ):
            result = crop_diagnosis.run_crop_diagnosis(
                image=image,
                plant_part="🍃 Leaf / Foliage",
                crop="Tomato",
            )

        report = result["assessment_report"]
        self.assertEqual(report["status"], "More information needed")
        self.assertEqual(report["crop"], "Tomato")
        self.assertIsNone(report["model_score"])
        self.assertEqual(report["model_findings"]["score"], 0.91)
        self.assertIn("different crop", report["cause_note"])

    def test_photo_quality_and_corrupt_image_handling(self):
        tiny_dark_image = Image.new("RGB", (32, 48), "black")
        quality = assess_image_quality(tiny_dark_image)
        self.assertFalse(quality["is_suitable"])
        self.assertTrue(any("small" in issue for issue in quality["issues"]))
        self.assertTrue(any("dark" in issue for issue in quality["issues"]))

        decoded, error = load_image_safely(b"not an image")
        self.assertIsNone(decoded)
        self.assertIn("could not be decoded", error)

    def test_too_small_leaf_photo_is_not_sent_to_the_cnn(self):
        image = Image.new("RGB", (48, 48), "green")
        with patch.object(crop_diagnosis, "get_cached_vision_model") as get_model:
            result = crop_diagnosis.run_crop_diagnosis(
                image=image,
                plant_part="🍃 Leaf / Foliage",
                crop="Tomato",
            )

        get_model.assert_not_called()
        self.assertIsNone(result["image_result"])
        self.assertEqual(result["assessment_report"]["status"], "More information needed")

    def test_visual_review_accepts_visible_observations_but_rejects_diagnoses(self):
        image = Image.new("RGB", (128, 128), "red")
        with (
            patch.object(gemini, "get_api_key", return_value="test-key"),
            patch("google.generativeai.configure"),
            patch("google.generativeai.GenerativeModel") as make_model,
        ):
            model = make_model.return_value
            model.generate_content.return_value = SimpleNamespace(
                text=json.dumps(
                    {
                        "crop": "Tomato",
                        "plant_parts": ["fruit", "foliage"],
                        "observations": ["Dark, sunken-looking marks are visible on fruit."],
                    }
                )
            )
            report = gemini.generate_visual_observations(image)
            self.assertEqual(report["crop"], "Tomato")
            self.assertEqual(report["plant_parts"], ["fruit", "foliage"])
            self.assertIn("sunken-looking", report["observations"][0])

            model.generate_content.return_value = SimpleNamespace(
                text=json.dumps(
                    {
                        "crop": "Tomato",
                        "plant_parts": ["fruit"],
                        "observations": ["The fruit has anthracnose."],
                    }
                )
            )
            with self.assertRaises(gemini.GeminiError):
                gemini.generate_visual_observations(image)

    def test_visual_review_without_provider_reports_limitation(self):
        image = Image.new("RGB", (128, 128), "red")
        with patch.object(
            crop_diagnosis,
            "generate_visual_observations",
            side_effect=gemini.GeminiError("Photo review unavailable."),
        ):
            result = crop_diagnosis.run_crop_diagnosis(
                image=image,
                plant_part="🍎 Fruit",
                crop="Tomato",
                use_ai_visual_review=True,
            )

        report = result["assessment_report"]
        self.assertEqual(report["status"], "More information needed")
        self.assertEqual(report["visible_symptoms"], (
            "Visible symptoms are not automatically identified for this image category. "
            "Add a short description of what you can see for a more useful assessment."
        ))
        self.assertIn("Photo review unavailable", report["visual_review_error"])
        self.assertEqual(report["possible_causes"], [])


if __name__ == "__main__":
    unittest.main()
