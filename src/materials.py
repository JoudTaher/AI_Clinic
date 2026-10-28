from __future__ import annotations

from typing import Any


HUMAN_MATERIAL_TYPE = (
    "Human derived materials (isolated tissue, samples, specimens, cells, etc.)"
)

MATERIAL_TYPES = (
    HUMAN_MATERIAL_TYPE,
    "Cells (other than those derived from human subjects or patients)",
    "Plasmid/Vector (rDNA or SNA)",
    "Mouse/Rat",
    "Other Model Organism (yeast, drosophila, zebrafish)",
    "Custom Antibody",
    "Protein",
    "Chemical compound",
    "Software/code",
    "Device",
    "Other material",
)

MATERIAL_TYPE_TO_CATEGORY = {
    MATERIAL_TYPES[0]: "biological",
    MATERIAL_TYPES[1]: "biological",
    MATERIAL_TYPES[2]: "biological",
    MATERIAL_TYPES[3]: "animal_derived",
    MATERIAL_TYPES[4]: "other",
    MATERIAL_TYPES[5]: "biological",
    MATERIAL_TYPES[6]: "biological",
    MATERIAL_TYPES[7]: "chemical",
    MATERIAL_TYPES[8]: "other",
    MATERIAL_TYPES[9]: "device",
    MATERIAL_TYPES[10]: "other",
}


def canonical_material_types(raw_material_types: Any) -> list[str]:
    if not isinstance(raw_material_types, list):
        return []
    cleaned = {
        value.strip()
        for value in raw_material_types
        if isinstance(value, str) and value.strip()
    }
    known = [material_type for material_type in MATERIAL_TYPES if material_type in cleaned]
    unknown = sorted(cleaned.difference(MATERIAL_TYPE_TO_CATEGORY), key=str.casefold)
    return known + unknown


def derive_material_categories(raw_material_types: Any) -> list[str]:
    return list(
        dict.fromkeys(
            MATERIAL_TYPE_TO_CATEGORY.get(material_type, "other")
            for material_type in canonical_material_types(raw_material_types)
        )
    )


def valid_material_type_selection(raw_material_types: Any) -> bool:
    return (
        isinstance(raw_material_types, list)
        and bool(raw_material_types)
        and all(
            isinstance(value, str)
            and value.strip() in MATERIAL_TYPE_TO_CATEGORY
            for value in raw_material_types
        )
    )
