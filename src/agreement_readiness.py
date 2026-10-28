from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.request_normalization import normalize_request

COMMON_REQUIRED_TEXT_FIELDS = (
    "recipient_institution_name",
    "recipient_institution_address",
    "recipient_scientist_name",
    "recipient_scientist_email",
    "provider_scientist_name",
    "provider_scientist_email",
    "material_description",
    "recipient_research_purpose",
    "requested_duration",
)

AUTM_REQUIRED_TEXT_FIELDS = (
    "shipping_recipient_name",
    "shipping_address",
)

RECIPIENT_OFFICIAL_FIELDS = (
    "recipient_authorized_official_name",
    "recipient_authorized_official_title",
    "recipient_authorized_official_email",
)


def _missing_text(information: Mapping[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [
        field_id
        for field_id in fields
        if not isinstance(information.get(field_id), str)
        or not information[field_id].strip()
    ]


def evaluate_agreement_readiness(request: Mapping[str, Any]) -> dict[str, Any]:
    """Check data needed to prepare and sign the selected agreement.

    Requester-questionnaire completeness and Standard MTA eligibility are evaluated
    separately. This function intentionally contains no eRPM or eligibility rules.
    """

    request = normalize_request(request)
    raw_information = request.get("agreement_information", {})
    information = raw_information if isinstance(raw_information, Mapping) else {}

    categories = request.get("material_categories")
    category = (
        categories[0]
        if isinstance(categories, list) and len(categories) == 1
        else None
    )

    if category not in {"chemical", "animal_derived", "biological", "device"}:
        return {
            "status": "not_applicable",
            "missing_fields": [],
            "review_reasons": [
                "Agreement fields apply only after one supported material category is selected."
            ],
        }

    missing_fields = _missing_text(information, COMMON_REQUIRED_TEXT_FIELDS)

    if category in {"chemical", "animal_derived"}:
        missing_fields.extend(_missing_text(information, AUTM_REQUIRED_TEXT_FIELDS))
        missing_fields.extend(_missing_text(information, RECIPIENT_OFFICIAL_FIELDS))
    elif category == "device":
        missing_fields.extend(_missing_text(information, RECIPIENT_OFFICIAL_FIELDS))
    elif category == "biological":
        can_certify = information.get("recipient_scientist_can_certify_organization")
        if not isinstance(can_certify, bool):
            missing_fields.append("recipient_scientist_can_certify_organization")
        elif not can_certify:
            missing_fields.extend(_missing_text(information, RECIPIENT_OFFICIAL_FIELDS))

    for field_id in ("recipient_pays_shipping", "material_provided_at_no_cost"):
        if not isinstance(information.get(field_id), bool):
            missing_fields.append(field_id)

    review_reasons: list[str] = []
    if information.get("recipient_pays_shipping") is False:
        review_reasons.append("Recipient Scientist will not pay shipping costs.")
    if information.get("material_provided_at_no_cost") is False:
        review_reasons.append("Provider material is not supplied at no cost.")

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
