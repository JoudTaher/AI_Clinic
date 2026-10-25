from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.templates.catalog import TemplateDefinition, load_template_catalog


def _base_result(
    status: str,
    candidates: list[TemplateDefinition],
    reasons: list[str],
    *,
    recommended_template: str | None = None,
    selected_template: str | None = None,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "selected_template": selected_template,
        "recommended_template": recommended_template,
        "candidate_templates": [item.template_id for item in candidates],
        "candidate_details": [item.as_dict() for item in candidates],
        "missing_context": missing_context or [],
        "review_reasons": reasons,
    }


def select_template(
    request: Mapping[str, Any],
    eligibility_result: Mapping[str, Any],
    catalog: Sequence[TemplateDefinition] | None = None,
) -> dict[str, Any]:
    definitions = tuple(catalog or load_template_catalog())
    if eligibility_result.get("status") != "eligible":
        return _base_result(
            "not_applicable",
            [],
            ["Template review begins only after streamlined eligibility is established."],
        )

    raw_categories = request.get("material_categories", [])
    if not isinstance(raw_categories, list) or not all(
        isinstance(value, str) and value.strip() for value in raw_categories
    ):
        return _base_result(
            "route_to_erpm",
            [],
            ["Material categories must be a list of non-empty strings."],
        )
    categories = list(dict.fromkeys(raw_categories))
    relevant = [
        definition
        for definition in definitions
        if definition.automation_enabled
        and any(category in definition.material_categories for category in categories)
    ]

    if len(categories) != 1:
        reason = (
            "A material category is required for template matching."
            if not categories
            else "Mixed material categories require manual template review."
        )
        return _base_result("route_to_erpm", relevant, [reason])

    if len(relevant) == 1:
        selected = relevant[0].template_id
        return _base_result(
            "template_selected",
            relevant,
            ["Selected automatically from the approved material-type rule."],
            selected_template=selected,
        )

    reasons = (
        ["No automation-enabled template matches this request; route to eRPM."]
        if not relevant
        else ["More than one automation-enabled template matches; route to eRPM."]
    )
    return _base_result(
        "route_to_erpm",
        relevant,
        reasons,
    )
