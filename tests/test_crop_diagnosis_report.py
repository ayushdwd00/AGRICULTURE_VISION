import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from services import crop_diagnosis


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
        self.assertIsNone(report["confidence"])
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
                    self.assertIsNone(result["assessment_report"]["confidence"])
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
        self.assertIsNone(result["assessment_report"]["confidence"])
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
        self.assertIsNone(report["confidence"])
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
        self.assertEqual(result["assessment_report"]["confidence"], 0.62)


if __name__ == "__main__":
    unittest.main()
