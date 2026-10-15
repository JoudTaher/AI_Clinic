from __future__ import annotations

from collections.abc import Mapping
from typing import Any


TEXT_FIELDS = (
    "recipient_institution_name",
    "recipient_institution_address",
    "recipient_scientist_name",
    "provider_scientist_name",
    "material_description",
    "recipient_research_purpose",
    "requested_duration",
)

SHIPPING_COST_PAYERS = {"recipient", "provider", "other"}


def evaluate_agreement_readiness(request: Mapping[str, Any]) -> dict[str, Any]:
    raw_information = request.get("agreement_information", {})
    information = raw_information if isinstance(raw_information, Mapping) else {}

    missing_fields = [
        field_id
        for field_id in TEXT_FIELDS
        if not isinstance(information.get(field_id), str)
        or not information[field_id].strip()
    ]

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
        "missing_fields": missing_fields,
        "review_reasons": review_reasons,
    }
