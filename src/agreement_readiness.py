from __future__ import annotations

from collections.abc import Mapping
from typing import Any


TEXT_FIELDS = (
    "recipient_institution_name",
    "recipient_institution_address",
    "recipient_scientist_name",
    "recipient_scientist_title",
    "provider_scientist_name",
    "provider_scientist_title",
    "material_description",
    "recipient_research_purpose",
    "requested_duration",
    "shipping_recipient_name",
    "shipping_address",
)

AUTOMATED_CATEGORIES = {"biological", "chemical", "animal_derived"}
RECIPIENT_OFFICIAL_FIELDS = (
    "recipient_authorized_official_name",
    "recipient_authorized_official_title",
    "recipient_authorized_official_email",
)

SHIPPING_COST_PAYERS = {"recipient", "provider", "other"}

ERPM_TEXT_FIELDS = (
    "project_title",
    "contact_pi_name",
    "primary_research_administrator_name",
    "material_description",
    "project_administrative_home",
    "recipient_entity",
    "recipient_scientist_name",
    "recipient_scientist_email",
    "reimbursement_cost_or_fee",
    "recipient_experimental_plan",
)

ERPM_BOOLEAN_FIELDS = (
    "paying_um_for_material",
    "copy_from_existing_ufa",
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


def _evaluate_erpm_readiness(information: Mapping[str, Any]) -> dict[str, Any]:
    missing_fields = [
        field_id
        for field_id in ERPM_TEXT_FIELDS
        if not isinstance(information.get(field_id), str)
        or not information[field_id].strip()
    ]

    material_types = information.get("material_types")
    if not isinstance(material_types, list) or not material_types:
        missing_fields.append("material_types")

    for field_id in ERPM_BOOLEAN_FIELDS:
        if not isinstance(information.get(field_id), bool):
            missing_fields.append(field_id)

    years = information.get("duration_years")
    months = information.get("duration_months")
    valid_years = isinstance(years, int) and not isinstance(years, bool) and years >= 0
    valid_months = (
        isinstance(months, int) and not isinstance(months, bool) and months >= 0
    )
    if not valid_years or not valid_months or years + months <= 0:
        missing_fields.append("expected_duration")

    return {
        "status": "missing_information" if missing_fields else "ready",
        "missing_fields": missing_fields,
        "review_reasons": [],
    }


def _evaluate_agreement_fields(request: Mapping[str, Any]) -> dict[str, Any]:
    raw_information = request.get("agreement_information", {})
    information = raw_information if isinstance(raw_information, Mapping) else {}

    missing_fields = [
        field_id
        for field_id in TEXT_FIELDS
        if not isinstance(information.get(field_id), str)
        or not information[field_id].strip()
    ]

    categories = request.get("material_categories")
    category = (
        categories[0]
        if isinstance(categories, list) and len(categories) == 1
        else None
    )
    if category in {"chemical", "animal_derived"}:
        signer_fields = RECIPIENT_OFFICIAL_FIELDS
    elif category == "biological":
        signer_fields = ("recipient_scientist_email",)
        can_certify = information.get("recipient_scientist_can_certify_organization")
        if not isinstance(can_certify, bool):
            missing_fields.append("recipient_scientist_can_certify_organization")
        if can_certify is False:
            signer_fields += RECIPIENT_OFFICIAL_FIELDS
    else:
        signer_fields = ()
    missing_fields.extend(
        field_id
        for field_id in signer_fields
        if not isinstance(information.get(field_id), str)
        or not information[field_id].strip()
    )

    if information.get("shipping_cost_payer") not in SHIPPING_COST_PAYERS:
        missing_fields.append("shipping_cost_payer")

    no_cost = information.get("material_provided_at_no_cost")
    review_reasons: list[dict[str, str]] = []
    if no_cost is not True and no_cost is not False:
        missing_fields.append("material_provided_at_no_cost")
    elif no_cost is False:
        review_reasons.append(
            {
                "field_id": "cost_terms_require_review",
                "label": (
                    "UM review is required because material cost and transmittal fee "
                    "are not mapped by the supplied checklist and templates."
                ),
            }
        )

    if missing_fields:
        status = "missing_information"
    elif review_reasons:
        status = "needs_review"
    else:
        status = "ready"

    return {
        "status": status,
        "missing_fields": list(dict.fromkeys(missing_fields)),
        "review_reasons": review_reasons,
    }


def evaluate_agreement_readiness(request: Mapping[str, Any]) -> dict[str, Any]:
    raw_categories = request.get("material_categories")
    automatic_request = (
        isinstance(raw_categories, list)
        and len(raw_categories) == 1
        and raw_categories[0] in AUTOMATED_CATEGORIES
    )
    raw_erpm_intake = request.get("erpm_intake")
    erpm_result = (
        _evaluate_erpm_readiness(raw_erpm_intake)
        if isinstance(raw_erpm_intake, Mapping)
        else None
    )
    agreement_result = (
        _evaluate_agreement_fields(request) if automatic_request else None
    )

    if erpm_result is None:
        return agreement_result or {
            "status": "ready",
            "missing_fields": [],
            "review_reasons": [],
        }
    if agreement_result is None:
        return erpm_result

    missing_fields = list(
        dict.fromkeys(
            erpm_result["missing_fields"] + agreement_result["missing_fields"]
        )
    )
    review_reasons = erpm_result["review_reasons"] + agreement_result["review_reasons"]
    status = (
        "missing_information"
        if missing_fields
        else "needs_review"
        if review_reasons
        else "ready"
    )
    return {
        "status": status,
        "missing_fields": missing_fields,
        "review_reasons": review_reasons,
    }
