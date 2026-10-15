from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.models import Criterion


SECTION_CRITERIA: dict[str, tuple[Criterion, ...]] = {
    "A": (
        Criterion(
            "recipient_is_us_nonprofit",
            "Material is being sent from UM to a U.S. non-profit institution",
            "A",
        ),
        Criterion(
            "um_owned_without_third_party_restrictions",
            "Material is owned by UM and not subject to third-party restrictions",
            "A",
        ),
        Criterion(
            "internal_noncommercial_research_only",
            "Use is limited to internal, non-commercial research",
            "A",
        ),
        Criterion(
            "not_invention_report_patented_or_encumbered",
            "Material is not appropriately the subject of an invention report and is not patented or otherwise encumbered",
            "A",
        ),
        Criterion(
            "no_funding_restrictions",
            "No funding restrictions affect the transfer",
            "A",
        ),
        Criterion(
            "no_human_subjects_materials_or_data",
            "No human subjects-derived materials or data will be included in the transfer",
            "A",
        ),
        Criterion(
            "not_controlled_beyond_ear99",
            "Material is not a controlled substance beyond EAR99",
            "A",
        ),
        Criterion(
            "return_not_required",
            "Material does not require return",
            "A",
        ),
    ),
    "B": (
        Criterion(
            "chemical_no_heightened_ehs_risk",
            "Material does not pose heightened EHS risks beyond standard laboratory handling",
            "B",
        ),
        Criterion(
            "chemical_not_used_in_humans",
            "Material will not be used in humans",
            "B",
        ),
    ),
    "C": (
        Criterion(
            "biological_nonradioactive",
            "Materials are non-radioactive",
            "C",
        ),
        Criterion(
            "biological_material_definition_met",
            "Materials consist of living organisms or contain biological molecules as described in the checklist",
            "C",
        ),
        Criterion(
            "biological_safe_handling_storage_use",
            "Materials are safe for handling, storage, and use",
            "C",
        ),
    ),
    "D": (
        Criterion(
            "device_not_clinical_or_diagnostic",
            "Device will not be used for clinical or diagnostic use",
            "D",
        ),
        Criterion(
            "device_not_used_in_humans",
            "Device will not be used in humans",
            "D",
        ),
        Criterion(
            "device_no_embedded_third_party_ip",
            "No embedded software, firmware, or components are subject to third-party IP restrictions",
            "D",
        ),
    ),
    "E": (
        Criterion(
            "animal_no_live_animals",
            "Material does not involve live animals",
            "E",
        ),
        Criterion(
            "animal_no_restricted_species_or_permits",
            "Material does not require restricted species or special permits",
            "E",
        ),
        Criterion(
            "animal_nonliving_derivative_definition_met",
            "Materials consist of non-living animal derivatives as described in the checklist",
            "E",
        ),
    ),
}

CATEGORY_TO_SECTION = {
    "chemical": "B",
    "biological": "C",
    "device": "D",
    "animal_derived": "E",
}


def _scope_issue(message: str) -> dict[str, str]:
    return {
        "field_id": "material_categories",
        "label": message,
        "section": "Scope",
    }


def evaluate_eligibility(request: Mapping[str, Any]) -> dict[str, Any]:
    raw_categories = request.get("material_categories", [])
    categories = raw_categories if isinstance(raw_categories, list) else []
    raw_answers = request.get("eligibility_answers", {})
    answers = raw_answers if isinstance(raw_answers, Mapping) else {}

    requested_sections = {
        CATEGORY_TO_SECTION[category]
        for category in categories
        if category in CATEGORY_TO_SECTION
    }
    evaluated_sections = ["A"] + [
        section for section in ("B", "C", "D", "E") if section in requested_sections
    ]

    passed_checks: list[dict[str, str]] = []
    failed_checks: list[dict[str, str]] = []
    missing_information: list[dict[str, str]] = []

    for section in evaluated_sections:
        for criterion in SECTION_CRITERIA[section]:
            value = answers.get(criterion.field_id)
            if value is True:
                passed_checks.append(criterion.as_dict())
            elif value is False:
                failed_checks.append(criterion.as_dict())
            else:
                missing_information.append(criterion.as_dict())

    unsupported = [category for category in categories if category not in CATEGORY_TO_SECTION]
    if not categories:
        missing_information.append(
            _scope_issue("At least one material category is required")
        )
    elif unsupported:
        missing_information.append(
            _scope_issue(
                "Material category is outside the documented checklist scope: "
                + ", ".join(str(value) for value in unsupported)
            )
        )

    if failed_checks:
        status = "ineligible"
        explanation = (
            "Not eligible for the Streamlined Template Process because one or more "
            "applicable checklist conditions were not satisfied."
        )
    elif missing_information:
        status = "needs_review"
        explanation = (
            "Manual review is required because one or more applicable checklist "
            "answers or material-category details are missing or outside scope."
        )
    else:
        status = "eligible"
        explanation = (
            "Eligible for the Streamlined Template Process because every condition "
            "in each applicable checklist section was satisfied."
        )

    return {
        "status": status,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "missing_information": missing_information,
        "evaluated_sections": evaluated_sections,
        "explanation": explanation,
    }
