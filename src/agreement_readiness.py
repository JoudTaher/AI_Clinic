from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.field_validation import email_errors
from src.request_normalization import normalize_request
from src.signing.plan import build_signer_plan
from src.templates.catalog import load_template_catalog

COMMON_REQUIRED_TEXT_FIELDS = (
    "recipient_institution_name",
    "recipient_institution_address",
    "recipient_scientist_name",
    "provider_scientist_name",
    "material_description",
    "recipient_research_purpose",
    "requested_duration",
)

AUTM_REQUIRED_TEXT_FIELDS = (
    "shipping_recipient_name",
    "shipping_address",
)

def _missing_text(information: Mapping[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [
        field_id
        for field_id in fields
        if not isinstance(information.get(field_id), str)
        or not information[field_id].strip()
    ]


def evaluate_agreement_readiness(
    request: Mapping[str, Any], template_id: str | None = None
) -> dict[str, Any]:
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

    if template_id is None and isinstance(category, str):
        candidates = [
            definition.template_id
            for definition in load_template_catalog()
            if definition.automation_enabled
            and category in definition.material_categories
        ]
        template_id = candidates[0] if len(candidates) == 1 else None

    if template_id is None:
        return {
            "status": "not_applicable",
            "missing_fields": [],
            "validation_errors": {},
            "review_reasons": [
                "Agreement fields apply only after one supported material category is selected."
            ],
        }

    missing_fields = _missing_text(information, COMMON_REQUIRED_TEXT_FIELDS)
    if template_id in {"chemical_material_agreement", "animal_material_agreement"}:
        missing_fields.extend(_missing_text(information, AUTM_REQUIRED_TEXT_FIELDS))

    signer_plan = build_signer_plan(template_id, information, strict=False)
    missing_fields.extend(signer_plan.missing_fields)

    for field_id in ("recipient_pays_shipping", "material_provided_at_no_cost"):
        if not isinstance(information.get(field_id), bool):
            missing_fields.append(field_id)

    review_reasons: list[str] = []
    if information.get("material_provided_at_no_cost") is False:
        review_reasons.append("Provider material is not supplied at no cost.")

    email_field_labels: dict[str, str] = {}
    for signer in signer_plan.signers:
        field_id = f"{signer.party}_email"
        label = (
            "Recipient Scientist Email"
            if signer.party == "recipient_scientist"
            else f"{signer.label} signing email"
        )
        email_field_labels[field_id] = label
    validation_errors = email_errors(information, email_field_labels)

    if missing_fields or validation_errors:
        status = "missing_information"
    elif review_reasons:
        status = "needs_review"
    else:
        status = "ready"

    return {
        "status": status,
        "missing_fields": list(dict.fromkeys(missing_fields)),
        "validation_errors": validation_errors,
        "review_reasons": review_reasons,
    }
