from __future__ import annotations

from src.models import Criterion, SemanticLabels


HUMAN_USE_LABELS = SemanticLabels(
    satisfied=(
        "research not involving administration or application of the material "
        "to human subjects"
    ),
    violated=(
        "research involving administration or application of the material to "
        "human subjects"
    ),
    unknown=(
        "insufficient information to determine whether the material is used in "
        "human subjects"
    ),
)

ANIMAL_DERIVATIVE_LABELS = SemanticLabels(
    satisfied=(
        "non-living animal-derived material such as fixed tissue, organs, "
        "samples, derivatives, or cell lines"
    ),
    violated="live animal or whole living animal use",
    unknown=(
        "insufficient information to determine whether the material is a "
        "non-living animal derivative"
    ),
)


SECTION_CRITERIA: dict[str, tuple[Criterion, ...]] = {
    "A": (
        Criterion(
            "recipient_is_us_nonprofit",
            "Material is being sent from UM to a U.S. non-profit institution (e.g., university, college, non-profit, or research organization)",
            "A",
            ("recipient_entity", "related_details"),
        ),
        Criterion(
            "um_owned_without_third_party_restrictions",
            "Material is owned by UM and not subject to third-party restrictions",
            "A",
            ("related_details", "material_description"),
        ),
        Criterion(
            "internal_noncommercial_research_only",
            "Use is limited to internal, non-commercial research (e.g., the research is not intended to inform a product, service, or company decision)",
            "A",
            (
                "project_title",
                "recipient_experimental_plan",
                "related_details",
            ),
            validate_semantics=True,
        ),
        Criterion(
            "not_invention_report_patented_or_encumbered",
            "The materials are not appropriately the subject of an invention report with Innovation Partnerships, whether or not yet filed, and are not patented or otherwise encumbered",
            "A",
            ("related_details", "material_description"),
        ),
        Criterion(
            "no_funding_restrictions",
            "No funding restrictions affect the transfer (e.g., a funding agreement did not pay for generation of the materials and include terms that follow the material)",
            "A",
            ("related_details",),
        ),
        Criterion(
            "no_human_subjects_materials_or_data",
            "No human subjects-derived materials or data will be included in the transfer",
            "A",
            (
                "human_derived_description",
                "human_data_classification",
                "protocol_consent_transfer_sections",
                "material_description",
                "related_details",
            ),
        ),
        Criterion(
            "not_controlled_beyond_ear99",
            "Material is not a controlled substance beyond EAR99 (e.g., DEA-regulated)",
            "A",
            ("material_description", "related_details"),
        ),
        Criterion(
            "return_not_required",
            "Material does not require return",
            "A",
            ("related_details",),
        ),
    ),
    "B": (
        Criterion(
            "chemical_no_heightened_ehs_risk",
            "Material does not pose heightened EHS risks beyond standard laboratory handling",
            "B",
            ("material_description", "related_details"),
        ),
        Criterion(
            "chemical_not_used_in_humans",
            "Material will not be used in humans",
            "B",
            ("recipient_experimental_plan", "related_details"),
            HUMAN_USE_LABELS,
        ),
    ),
    "C": (
        Criterion(
            "biological_nonradioactive",
            "Materials are non-radioactive",
            "C",
            ("material_description", "related_details"),
        ),
        Criterion(
            "biological_material_definition_met",
            "Materials consist of living organisms or contain biological molecules, such as cell lines, bacteria, fungi, viruses, and plasmids/vectors (rDNA or synthetic nucleic acids)",
            "C",
            ("material_description",),
        ),
        Criterion(
            "biological_safe_handling_storage_use",
            "Materials are safe for handling, storage, and use",
            "C",
            ("material_description", "related_details"),
        ),
    ),
    "D": (
        Criterion(
            "device_not_clinical_or_diagnostic",
            "Device will not be used for clinical or diagnostic use",
            "D",
            (
                "recipient_experimental_plan",
                "material_description",
                "related_details",
            ),
        ),
        Criterion(
            "device_not_used_in_humans",
            "Device will not be used in humans",
            "D",
            ("recipient_experimental_plan", "related_details"),
            HUMAN_USE_LABELS,
        ),
        Criterion(
            "device_no_embedded_third_party_ip",
            "No embedded software, firmware, or components are subject to third-party IP restrictions",
            "D",
            ("material_description", "related_details"),
        ),
    ),
    "E": (
        Criterion(
            "animal_no_live_animals",
            "Material does not involve live animals",
            "E",
            ("material_description", "related_details"),
        ),
        Criterion(
            "animal_no_restricted_species_or_permits",
            "Material does not require restricted species or special permits",
            "E",
            ("material_description", "related_details"),
        ),
        Criterion(
            "animal_nonliving_derivative_definition_met",
            "Materials consist of non-living animal derivatives, such as mouse cell lines, animal tissues or organs, fixed samples, or derivatives",
            "E",
            ("material_description", "related_details"),
            ANIMAL_DERIVATIVE_LABELS,
        ),
    ),
}

CATEGORY_TO_SECTION = {
    "chemical": "B",
    "biological": "C",
    "device": "D",
    "animal_derived": "E",
}


def all_criteria() -> tuple[Criterion, ...]:
    return tuple(
        criterion
        for section in ("A", "B", "C", "D", "E")
        for criterion in SECTION_CRITERIA[section]
    )
