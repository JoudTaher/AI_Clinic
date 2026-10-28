from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.materials import HUMAN_MATERIAL_TYPE, MATERIAL_TYPE_TO_CATEGORY
from src.models import Criterion
from src.request_normalization import normalize_request
from src.semantic_rules import analyze_open_text


SECTION_CRITERIA: dict[str, tuple[Criterion, ...]] = {
    "A": (
        Criterion(
            "recipient_is_us_nonprofit",
            "Material is being sent from UM to a U.S. non-profit institution (e.g., university, college, non-profit, or research organization)",
            "A",
        ),
        Criterion(
            "um_owned_without_third_party_restrictions",
            "Material is owned by UM and not subject to third-party restrictions",
            "A",
        ),
        Criterion(
            "internal_noncommercial_research_only",
            "Use is limited to internal, non-commercial research (e.g., the research is not intended to inform a product, service, or company decision)",
            "A",
        ),
        Criterion(
            "not_invention_report_patented_or_encumbered",
            "The materials are not appropriately the subject of an invention report with Innovation Partnerships, whether or not yet filed, and are not patented or otherwise encumbered",
            "A",
        ),
        Criterion(
            "no_funding_restrictions",
            "No funding restrictions affect the transfer (e.g., a funding agreement did not pay for generation of the materials and include terms that follow the material)",
            "A",
        ),
        Criterion(
            "no_human_subjects_materials_or_data",
            "No human subjects-derived materials or data will be included in the transfer",
            "A",
        ),
        Criterion(
            "not_controlled_beyond_ear99",
            "Material is not a controlled substance beyond EAR99 (e.g., DEA-regulated)",
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
            "Materials consist of living organisms or contain biological molecules, such as cell lines, bacteria, fungi, viruses, and plasmids/vectors (rDNA or synthetic nucleic acids)",
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
            "Materials consist of non-living animal derivatives, such as mouse cell lines, animal tissues or organs, fixed samples, or derivatives",
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


def _inverse_boolean(value: Any) -> bool | None:
    return not value if isinstance(value, bool) else None


def _all_false(*values: Any) -> bool | None:
    if any(value is True for value in values):
        return False
    if all(value is False for value in values):
        return True
    return None


def _recipient_nonprofit_fact(intake: Mapping[str, Any]) -> bool | None:
    leaving_country = intake.get("leaving_country")
    if leaving_country is True:
        return False
    if leaving_country is not False:
        return None
    entity = intake.get("recipient_entity")
    if not isinstance(entity, str) or not entity.strip():
        return None
    normalized = entity.casefold()
    if any(
        marker in normalized
        for marker in (" inc", " llc", " ltd", " gmbh", " corporation", " company")
    ):
        return False
    if any(
        marker in normalized
        for marker in (
            "university",
            "college",
            "non-profit",
            "nonprofit",
            "research organization",
            "research institute",
        )
    ):
        return True
    for field_id in (
        "recipient_scientist_email",
        "recipient_administrative_contact_email",
    ):
        email = intake.get(field_id)
        if not isinstance(email, str):
            continue
        _, separator, domain = email.strip().casefold().rpartition("@")
        if separator and domain.endswith((".edu", ".gov")):
            return True
    return None


def _merge_fact(
    structured: bool | None, semantic: bool | None
) -> bool | None:
    if structured is False or semantic is False:
        return False
    if structured is True:
        return True
    return semantic


def _derive_checklist_assessment(
    request: Mapping[str, Any],
    verified_facts: Mapping[str, Any] | None = None,
) -> tuple[dict[str, bool | None], dict[str, Any]]:


    """Apply checklist criteria only when questionnaire data proves the result.

    Criteria that the requester questionnaire cannot establish remain unresolved.
    They must never be converted into requester-facing checklist questions or
    silently treated as passing.
    """

    raw_intake = request.get("erpm_intake", {})
    intake = raw_intake if isinstance(raw_intake, Mapping) else {}
    raw_material_types = intake.get("material_types", [])
    material_types = (
        raw_material_types if isinstance(raw_material_types, list) else []
    )

    no_human_materials: bool | None
    clinical_data_shared = intake.get("clinical_health_data_shared")
    if HUMAN_MATERIAL_TYPE in material_types or clinical_data_shared is True:
        no_human_materials = False
    elif material_types and clinical_data_shared is False:
        no_human_materials = True
    else:
        no_human_materials = None

    safe_handling = _all_false(
        intake.get("dangerous_to_handle_store_or_use"),
        intake.get("hazardous_chemical_capacity_constraint"),
    )
    no_heightened_ehs_risk = _all_false(
        intake.get("radioactive"),
        intake.get("dangerous_to_handle_store_or_use"),
        intake.get("hazardous_chemical_capacity_constraint"),
    )
    has_biological_material = any(
        isinstance(material_type, str)
        and MATERIAL_TYPE_TO_CATEGORY.get(material_type) == "biological"
        for material_type in material_types
    )

    raw_agreement = request.get("agreement_information", {})
    agreement = raw_agreement if isinstance(raw_agreement, Mapping) else {}
    semantic = analyze_open_text(
        {
            **{
                field_id: intake.get(field_id, "")
                for field_id in (
                    "recipient_experimental_plan",
                    "related_details",
                    "human_derived_description",
                    "human_data_classification",
                    "protocol_consent_transfer_sections",
                    "project_title",
                    "recipient_entity",
                )
            },
            "material_description": agreement.get("material_description", ""),
        }
    )
    semantic_facts = semantic["facts"]

    third_party_materials = intake.get("made_using_third_party_materials")
    ownership_fact = True if third_party_materials is False else None
    external_funding = intake.get("external_funding_supported_development")
    funding_fact = True if external_funding is False else None
    paying_as_product = intake.get("paying_for_material_as_product_or_service")
    commercial_fact = (
        False
        if paying_as_product is True
        else True
        if paying_as_product is False
        and _recipient_nonprofit_fact(intake) is True
        and isinstance(intake.get("recipient_experimental_plan"), str)
        and bool(intake["recipient_experimental_plan"].strip())
        else None
    )
    invention_or_license = intake.get("previously_invention_report_or_licensed")
    invention_fact = (
        False
        if invention_or_license is True
        else True
        if invention_or_license is False
        else None
    )
    device_ip_fact = True if third_party_materials is False else None

    facts: dict[str, bool | None] = {
        "recipient_is_us_nonprofit": _merge_fact(
            _recipient_nonprofit_fact(intake),
            semantic_facts["recipient_is_us_nonprofit"],
        ),
        "um_owned_without_third_party_restrictions": _merge_fact(
            ownership_fact,
            semantic_facts["um_owned_without_third_party_restrictions"],
        ),
        "internal_noncommercial_research_only": _merge_fact(
            commercial_fact,
            semantic_facts["internal_noncommercial_research_only"],
        ),
        "not_invention_report_patented_or_encumbered": _merge_fact(
            invention_fact,
            semantic_facts["not_invention_report_patented_or_encumbered"],
        ),
        "no_funding_restrictions": _merge_fact(
            funding_fact, semantic_facts["no_funding_restrictions"]
        ),
        "no_human_subjects_materials_or_data": _merge_fact(
            no_human_materials,
            semantic_facts["no_human_subjects_materials_or_data"],
        ),
        "not_controlled_beyond_ear99": _merge_fact(
            _inverse_boolean(intake.get("export_controlled")),
            semantic_facts["not_controlled_beyond_ear99"],
        ),
        "return_not_required": _merge_fact(
            _inverse_boolean(intake.get("return_required")),
            semantic_facts["return_not_required"],
        ),
        "chemical_no_heightened_ehs_risk": _merge_fact(
            no_heightened_ehs_risk,
            semantic_facts["chemical_no_heightened_ehs_risk"],
        ),
        "chemical_not_used_in_humans": semantic_facts[
            "chemical_not_used_in_humans"
        ],
        "biological_nonradioactive": _merge_fact(
            _inverse_boolean(intake.get("radioactive")),
            semantic_facts["biological_nonradioactive"],
        ),
        "biological_material_definition_met": _merge_fact(
            True if has_biological_material else None,
            semantic_facts["biological_material_definition_met"],
        ),
        "biological_safe_handling_storage_use": _merge_fact(
            safe_handling,
            semantic_facts["biological_safe_handling_storage_use"],
        ),
        "device_not_clinical_or_diagnostic": semantic_facts[
            "device_not_clinical_or_diagnostic"
        ],
        "device_not_used_in_humans": semantic_facts["device_not_used_in_humans"],
        "device_no_embedded_third_party_ip": _merge_fact(
            device_ip_fact,
            semantic_facts["device_no_embedded_third_party_ip"],
        ),
        "animal_no_live_animals": semantic_facts["animal_no_live_animals"],
        "animal_no_restricted_species_or_permits": semantic_facts[
            "animal_no_restricted_species_or_permits"
        ],
        "animal_nonliving_derivative_definition_met": semantic_facts[
            "animal_nonliving_derivative_definition_met"
        ],
    }
    trusted = verified_facts if isinstance(verified_facts, Mapping) else {}
    for field_id, value in facts.items():
        verified_value = trusted.get(field_id)
        if verified_value is False:
            facts[field_id] = False
        elif value is None and verified_value is True:
            facts[field_id] = verified_value
    return facts, semantic


def derive_checklist_facts(
    request: Mapping[str, Any],
    verified_facts: Mapping[str, Any] | None = None,
) -> dict[str, bool | None]:
    facts, _ = _derive_checklist_assessment(request, verified_facts)
    return facts


def evaluate_eligibility(
    request: Mapping[str, Any],
    verified_facts: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request = normalize_request(request)
    raw_categories = request.get("material_categories", [])
    categories = raw_categories if isinstance(raw_categories, list) else []
    answers, semantic = _derive_checklist_assessment(request, verified_facts)

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
            "Manual special-case MTA review is required because one or more "
            "applicable checklist conditions were not satisfied."
        )
    elif missing_information:
        status = "needs_review"
        explanation = (
            "Manual special-case MTA review is required because one or more "
            "applicable checklist answers or material-category details are missing "
            "or outside scope."
        )
    else:
        status = "eligible"
        explanation = (
            "Eligible for Standard MTA automatic approval because every condition "
            "in each applicable checklist section was satisfied."
        )

    return {
        "status": status,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "missing_information": missing_information,
        "evaluated_sections": evaluated_sections,
        "explanation": explanation,
        "semantic_assessment": semantic,
    }
