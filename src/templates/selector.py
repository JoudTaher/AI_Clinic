from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.materials import valid_material_type_selection
from src.request_normalization import normalize_request
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
    raw_intake = request.get("erpm_intake", {})
    raw_material_types = (
        raw_intake.get("material_types") if isinstance(raw_intake, Mapping) else None
    )
    request = normalize_request(request)
    definitions = tuple(catalog or load_template_catalog())
    if eligibility_result.get("status") != "eligible":
        return _base_result(
            "manual_special_case_review",
            [],
            [
                "Automatic template selection begins only after Standard MTA "
                "eligibility is established."
            ],
        )

    if not valid_material_type_selection(raw_material_types):
        return _base_result(
            "manual_special_case_review",
            [],
            ["Material types must be a non-empty list of approved questionnaire values."],
        )

    raw_categories = request.get("material_categories", [])
    if not isinstance(raw_categories, list) or not all(
        isinstance(value, str) and value.strip() for value in raw_categories
    ):
        return _base_result(
            "manual_special_case_review",
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
            else "Mixed material categories require manual special-case review."
        )
        return _base_result("manual_special_case_review", relevant, [reason])

    if len(relevant) == 1:
        selected = relevant[0].template_id
        return _base_result(
            "template_selected",
            relevant,
            ["Selected automatically from the approved material-type rule."],
            selected_template=selected,
        )

    reasons = (
        [
            "No automation-enabled template matches this request; manual "
            "special-case review in eRPM is required."
        ]
        if not relevant
        else [
            "More than one automation-enabled template matches; manual "
            "special-case review in eRPM is required."
        ]
    )
    return _base_result(
        "manual_special_case_review",
        relevant,
        reasons,
    )
