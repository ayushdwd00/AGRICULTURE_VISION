"""
training/build_symptom_dataset.py

Builds ``data/symptoms.csv`` - the small labelled dataset behind the Crop
Doctor's symptom classifier (Module 1, part 7).

Design

For every symptom class we authored realistic farmer sentences.  The binary
symptom features required by the brief (leaf colour change, spot pattern,
wilting, leaf curling, stunted growth) are then derived **from the text** with
:func:`modules.symptom_model.extract_symptom_flags`, so the CSV, the training
features and the live inference path are guaranteed to use exactly the same
definition.  Rows whose derived flags would all be zero are dropped and a
summary is printed so the dataset stays auditable.

Usage

    python training/build_symptom_dataset.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from modules.symptom_model import (  # noqa: E402
    CSV_COLUMNS,
    FLAG_COLUMNS,
    SYMPTOM_LABELS,
    TEXT_COLUMN,
    extract_symptom_flags,
)
from utils.helpers import SYMPTOMS_CSV_PATH, ensure_directories  # noqa: E402

# Neutral follow-up phrases - deliberately free of symptom keywords so they do
# not change the derived features.
MODIFIERS: List[str] = [
    "this started about a week ago",
    "it is spreading to nearby plants",
    "I noticed it after two days of rain",
    "it looks worse in the afternoon",
    "around half of the field is affected",
    "the neighbouring field looks fine",
]

#: ``{label: {"core": [...], "extra": [...]}}``
SYMPTOM_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "Nitrogen Deficiency": {
        "core": [
            "the older leaves are turning pale yellow from the bottom of the plant",
            "lower leaves look yellow while the veins stay green",
            "the leaves are pale and the colour is fading from the older foliage",
            "new leaves are light green and the older leaves are yellow",
            "the leaf colour is going from green to pale yellow",
            "the bottom leaves have turned yellow and the plant is weak",
        ],
        "extra": [
            "the plant is small and growing slowly",
            "the whole plant looks thin and the growth is poor",
            "the leaves look limp and drooping",
        ],
    },
    "Phosphorus Deficiency": {
        "core": [
            "the leaves are turning dark purple and the plant is not growing",
            "older leaves have a purple colour and growth has stopped",
            "the leaf undersides look dark purple",
            "the plant is short and the leaves are dark and dull",
            "leaves are turning purple with slow growth",
            "the plant is dwarf and the older leaves look purple",
        ],
        "extra": [
            "the leaves are small and the plant is short",
            "the leaf tips look brown and dry",
            "the plant is stunted and not growing",
        ],
    },
    "Potassium Deficiency": {
        "core": [
            "the leaf edges are turning brown and drying from the margins",
            "the edges of older leaves are scorched and brown",
            "leaf margins look brown and the leaves are drying at the border",
            "old leaves have brown edges and the plant is weak",
            "the leaf border is turning brown and burning at the edges",
            "the leaves have brown margins and are drying from the sides",
        ],
        "extra": [
            "there are small brown patches on the older leaves",
            "the plant looks weak and slow growing",
            "the leaves are small with brown margins",
        ],
    },
    "Fungal Leaf Spot / Blight": {
        "core": [
            "there are round brown spots on the leaves with dark rings",
            "the leaves show brown lesions with a target like pattern",
            "small dark spots are appearing on the lower leaves",
            "the leaf surface has grey patches with mould like powder",
            "the plants have rusty pustules and damaged leaves",
            "the leaves are showing concentric rings and brown rot",
        ],
        "extra": [
            "the spots are spreading and the leaves are wilting",
            "the lower leaves have lesions and dry up",
            "the plants are stunted with rot on the leaf stalk",
        ],
    },
    "Bacterial Infection": {
        "core": [
            "leaves have dark water soaked spots and the plant is wilting",
            "the leaf spots are dark and the leaves are collapsing",
            "small black lesions are spreading over the leaves",
            "there are dark spots with a halo on the leaves",
            "the leaves look greasy with dark spots and they are drying",
            "dark lesions appear on the leaves and the plant is drooping",
        ],
        "extra": [
            "small black lesions are spreading after the rain",
            "the plant looks stunted with spots on the fruit",
            "the leaves are wilting and the spots have merged",
        ],
    },
}


EXTRA_CORE_SENTENCES: Dict[str, List[str]] = {
    "Nitrogen Deficiency": [
        "the entire plant is pale green with the oldest leaves most affected",
        "the lower foliage is yellow while the plant keeps growing taller",
        "growth is slow and the colour is fading from the bottom leaves upward",
    ],
    "Phosphorus Deficiency": [
        "the plant stays short and the leaves have a dark purple tint",
        "the foliage is dull dark green with purple leaf margins",
        "the plant is not developing and the older leaves are purple",
    ],
    "Potassium Deficiency": [
        "the older leaves are brown and dry along the margins",
        "the leaf border is scorched and the plant is weak",
        "large brown drying patches appear at the leaf edges",
    ],
    "Fungal Leaf Spot / Blight": [
        "concentric rings and target shaped lesions are visible on the leaves",
        "grey powdery mould is spreading on the leaf surface",
        "rusty pustules with dark borders are showing on the underside of the leaves",
    ],
    "Bacterial Infection": [
        "water soaked greasy areas and angular lesions appear on the leaves",
        "the spots have a yellow halo and the leaf stalk is dark",
        "black lesions are spreading quickly after the rain",
    ],
    "Viral Infection": [
        "the mosaic pattern of light and dark green is spreading to the whole plant",
        "curling of the new growth and stiff cupped leaves are visible",
        "the plant is dwarf and the foliage is mottled and distorted",
    ],
    "Pest Attack (mites / insects)": [
        "fine webbing and moving mites are visible under the leaves",
        "the leaves are speckled, silvery and many small insects are present",
        "the underside of the leaves is dusty with speckle damage and webbing",
    ],
    "Water Stress (over/under watering)": [
        "the plants are wilting while the soil is either dry or waterlogged",
        "the leaves are limp and the whole plant is drooping at midday",
        "yellowing leaves dropped off after the field was waterlogged",
    ],
    "Heat & Sunlight Stress": [
        "the leaves are scorched and dry on the side facing the sun",
        "the foliage burns and the leaves dry up at noon",
        "the leaves curl and dry in strong sunlight, the shade side is fine",
    ],
    "Healthy Crop": [
        "the foliage is evenly green and the plants are upright and strong",
        "the crop is uniform and growth is even across the field",
        "the plants look strong with full green foliage",
    ],
}


def _add_more_sentences() -> None:
    """Extend every label's 'core' pool for a richer, more separable dataset."""
    for label, sentences in EXTRA_CORE_SENTENCES.items():
        SYMPTOM_TEMPLATES[label]["core"].extend(sentences)


def _add_more_labels() -> None:
    """Labels added in a second block (kept separate for readability)."""
    SYMPTOM_TEMPLATES.update(
        {
            "Viral Infection": {
                "core": [
                    "leaves are curling and distorted with a light green mosaic pattern",
                    "the new leaves are curled and the plant looks puckered",
                    "the leaves are rolled and show a mosaic colour pattern",
                    "the plant has crinkled leaves with a green and light green mosaic",
                    "the new growth is twisted and the leaves are distorted",
                    "leaf curling is visible and the surface looks wrinkled",
                ],
                "extra": [
                    "the plant is stunted and new leaves are small",
                    "the leaves look crinkled and rolled",
                    "the plant is not growing and the leaves are cupped",
                ],
            },
            "Pest Attack (mites / insects)": {
                "core": [
                    "leaves are pale yellow with tiny speckles and fine webbing under the leaf",
                    "the leaf surface looks silver with speckle damage and small mites",
                    "the underside of the leaves has webbing and tiny insects",
                    "the leaves are speckled and there are holes from the insects",
                    "the upper leaves have a patch of speckled damage and webbing",
                    "small mites are visible and the leaves are turning bronze",
                ],
                "extra": [
                    "the plant is stunted and leaves are curled",
                    "there are small holes and insects on the leaves",
                    "the leaves are curling with heavy speckle damage",
                ],
            },
            "Water Stress (over/under watering)": {
                "core": [
                    "the plant is wilting and the leaves are drooping even after watering",
                    "the leaves are limp and the plant is sagging in the morning",
                    "the lower leaves are yellow and falling after heavy watering",
                    "the plant is collapsed and the soil stays wet for days",
                    "the leaves are turning yellow with the plant sitting in water",
                    "the plant looks wilted and the leaves have turned yellow",
                ],
                "extra": [
                    "the leaves turned yellow and fell off after waterlogging",
                    "the lower leaves are yellow and the plant is not growing",
                    "the plant is drooping and growth has slowed down",
                ],
            },
            "Heat & Sunlight Stress": {
                "core": [
                    "the leaves are scorched and pale in the afternoon sun",
                    "leaf edges are dry and brown and the plant looks wilted at midday",
                    "the leaves are pale and burning in strong sunlight",
                    "the upper leaves are scorched and drying at noon",
                    "the plant is wilting in the hot part of the day",
                    "the leaves look bleached and dry where the sun is strongest",
                ],
                "extra": [
                    "the plant is small and the leaves curl in strong sunlight",
                    "the leaves dry out and the plant looks tired at midday",
                    "growth is slow and the leaves are pale",
                ],
            },
            "Healthy Crop": {
                "core": [
                    "the leaves are a healthy even green colour and the plant is growing well",
                    "the crop looks normal, the leaves are firm and upright",
                    "growth is even and the foliage has a full green colour",
                    "the plants are tall and strong with full green leaves",
                    "the field has uniform green plants with even growth",
                    "the leaves are firm, upright and evenly green",
                ],
                "extra": [
                    "the crop is growing as expected",
                    "the plants look strong and upright",
                    "growth is even across the field",
                ],
            },
        }
    )


def build_rows() -> pd.DataFrame:
    """Create the labelled symptom rows (``2 * len(core)`` rows per label)."""
    _add_more_labels()
    _add_more_sentences()
    records: List[Dict[str, object]] = []
    for label in SYMPTOM_LABELS:
        template = SYMPTOM_TEMPLATES.get(label)
        if not template:
            raise KeyError(f"No symptom template authored for label: {label}")
        core = template["core"]
        extra = template["extra"]
        for index, sentence in enumerate(core):
            # Row A: core symptom description + a neutral follow-up.
            records.append(
                {"text": f"{sentence}, {MODIFIERS[index % len(MODIFIERS)]}", "label": label}
            )
            # Row B: core description joined with an additional observation.
            records.append(
                {
                    "text": (
                        f"{sentence} and {extra[index % len(extra)]}, "
                        f"{MODIFIERS[(index + 3) % len(MODIFIERS)]}"
                    ),
                    "label": label,
                }
            )

    rows: List[Dict[str, object]] = []
    zero_flag_rows: Dict[str, int] = {}
    for record in records:
        text = str(record["text"]).strip()
        flags = extract_symptom_flags(text)
        if not any(flags.values()):
            # All-zero flags are the *expected and informative* pattern for a
            # healthy crop, so these rows are kept - but they are counted and
            # reported, because for a diseased label they would signal an
            # authoring mistake in the template sentences.
            label = str(record["label"])
            zero_flag_rows[label] = zero_flag_rows.get(label, 0) + 1
        rows.append({**{TEXT_COLUMN: text}, **flags, "label": record["label"]})

    for label, count in sorted(zero_flag_rows.items()):
        if label != "Healthy Crop":
            print(
                f"[warn] {count} row(s) of '{label}' have no keyword-derived symptom "
                "feature - check the template sentences"
            )
    if "Healthy Crop" in zero_flag_rows:
        print(
            f"[info] Healthy Crop uses the all-zero symptom pattern for "
            f"{zero_flag_rows['Healthy Crop']} rows (expected)."
        )
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build data/symptoms.csv for AgriVision.")
    parser.add_argument(
        "--out", default=str(SYMPTOMS_CSV_PATH), help="output CSV path"
    )
    args = parser.parse_args()

    ensure_directories()
    frame = build_rows()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_path, index=False)

    print(f"[ok] wrote {out_path}")
    print(f"[info] rows={len(frame)} columns={list(frame.columns)}")
    print("[info] rows per label:")
    for label, count in frame["label"].value_counts().sort_index().items():
        print(f"       {label:<38s} {count}")
    print("[info] symptom feature prevalence:")
    for column in FLAG_COLUMNS:
        print(f"       {column:<20s} {int(frame[column].sum())}/{len(frame)} rows = 1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
