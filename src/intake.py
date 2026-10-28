from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.materials import HUMAN_MATERIAL_TYPE, valid_material_type_selection
from src.request_normalization import normalize_request


REQUIRED_TEXT_FIELDS = (
    "project_title",
    "contact_pi_name",
    "primary_research_administrator_name",
    "project_administrative_home",
    "recipient_entity",
    "recipient_scientist_name",
    "recipient_scientist_email",
    "reimbursement_cost_or_fee",
    "recipient_experimental_plan",
)

REQUIRED_BOOLEAN_FIELDS = (
    "paying_for_material_as_product_or_service",
    "measurable_personnel_effort",
    "radioactive",
    "dangerous_to_handle_store_or_use",
    "hazardous_chemical_capacity_constraint",
    "will_deposit_in_repository",
    "leaving_country",
    "export_controlled",
    "return_required",
    "previously_invention_report_or_licensed",
    "external_funding_supported_development",
    "managed_affiliate_work",
    "made_using_third_party_materials",
    "clinical_health_data_shared",
)

HUMAN_REQUIRED_FIELDS = (
    "human_derived_description",
    "human_data_classification",
    "irb_study_number",
    "protocol_consent_transfer_sections",
)


def _missing_text(information: Mapping[str, Any], field_id: str) -> bool:
    value = information.get(field_id)
    return not isinstance(value, str) or not value.strip()


def evaluate_intake_readiness(request: Mapping[str, Any]) -> dict[str, Any]:
    raw_erpm_intake = request.get("erpm_intake", {})
    raw_material_types = (
        raw_erpm_intake.get("material_types")
        if isinstance(raw_erpm_intake, Mapping)
        else None
    )
    request = normalize_request(request)
    raw_intake = request.get("erpm_intake", {})
    intake = raw_intake if isinstance(raw_intake, Mapping) else {}
    missing_fields = [
        field_id
        for field_id in REQUIRED_TEXT_FIELDS
        if _missing_text(intake, field_id)
    ]
    missing_fields.extend(
        field_id
        for field_id in REQUIRED_BOOLEAN_FIELDS
        if not isinstance(intake.get(field_id), bool)
    )

    material_types = intake.get("material_types")
    if not valid_material_type_selection(raw_material_types):
        missing_fields.append("material_types")
        if not isinstance(material_types, list):
            material_types = []

    years = intake.get("duration_years")
    months = intake.get("duration_months")
    valid_years = isinstance(years, int) and not isinstance(years, bool) and years >= 0
    valid_months = (
        isinstance(months, int) and not isinstance(months, bool) and months >= 0
    )
    if not valid_years or not valid_months or years + months <= 0:
        missing_fields.append("expected_duration")

    if HUMAN_MATERIAL_TYPE in material_types:
        missing_fields.extend(
            field_id
            for field_id in HUMAN_REQUIRED_FIELDS
            if _missing_text(intake, field_id)
        )

    if intake.get("previously_invention_report_or_licensed") is True and _missing_text(
        intake, "innovation_partnerships_file_number"
    ):
        missing_fields.append("innovation_partnerships_file_number")

    unique_missing = list(dict.fromkeys(missing_fields))
    return {
        "status": "missing_information" if unique_missing else "ready",
        "missing_fields": unique_missing,
    }
