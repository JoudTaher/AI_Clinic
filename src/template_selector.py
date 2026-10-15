from __future__ import annotations

from collections.abc import Mapping
from typing import Any


TEMPLATE_ORDER = (
    "autm_chemical",
    "autm_biological",
    "simple_letter_agreement",
    "ubmta_implementing_letter",
)


def evaluate_template_selection(
    request: Mapping[str, Any], eligibility_result: Mapping[str, Any]
) -> dict[str, Any]:
    if eligibility_result.get("status") != "eligible":
        return {
            "status": "not_applicable",
            "selected_template": None,
            "candidate_templates": [],
            "review_reasons": [
                "Template review begins only after streamlined eligibility is established."
            ],
        }

    raw_categories = request.get("material_categories", [])
    categories = raw_categories if isinstance(raw_categories, list) else []
    candidate_set: set[str] = set()

    if "chemical" in categories:
        candidate_set.add("autm_chemical")
    if "biological" in categories:
        candidate_set.update(
            {
                "autm_biological",
                "simple_letter_agreement",
                "ubmta_implementing_letter",
            }
        )

    candidates = [template for template in TEMPLATE_ORDER if template in candidate_set]
    reasons = [
        "The supplied documents do not contain a confirmed rule that authorizes automatic template selection."
    ]
    if len(categories) > 1:
        reasons.append("The request includes multiple material categories.")
    if not candidates:
        reasons.append("No supplied template is confirmed for the selected material category.")
    if "biological" in categories:
        reasons.append(
            "UM must distinguish AUTM Biological, the Simple Letter Agreement, and UBMTA."
        )

    return {
        "status": "template_selection_requires_review",
        "selected_template": None,
        "candidate_templates": candidates,
        "review_reasons": reasons,
    }
