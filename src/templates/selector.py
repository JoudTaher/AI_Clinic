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
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "selected_template": None,
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
    categories = (
        list(dict.fromkeys(raw_categories))
        if isinstance(raw_categories, list)
        else []
    )
    relevant = [
        definition
        for definition in definitions
        if any(category in definition.material_categories for category in categories)
    ]

    if len(categories) != 1:
        reason = (
            "A material category is required for template matching."
            if not categories
            else "Mixed material categories require manual template review."
        )
        return _base_result("template_selection_requires_review", relevant, [reason])

    raw_context = request.get("template_context", {})
    context = raw_context if isinstance(raw_context, Mapping) else {}
    exact_ids: set[str] = set()
    possible_ids: set[str] = set()
    missing_fields: set[str] = set()

    for definition in relevant:
        mismatched = False
        unresolved: list[str] = []
        for field_id, expected in definition.required_context.items():
            value = context.get(field_id)
            if not isinstance(value, bool):
                unresolved.append(field_id)
            elif value is not expected:
                mismatched = True
                break
        if mismatched:
            continue
        if unresolved:
            possible_ids.add(definition.template_id)
            missing_fields.update(unresolved)
        else:
            exact_ids.add(definition.template_id)

    candidate_ids = exact_ids | possible_ids
    candidates = [
        definition
        for definition in relevant
        if definition.template_id in candidate_ids
    ]

    if len(exact_ids) == 1 and not possible_ids:
        recommendation = next(iter(exact_ids))
        return _base_result(
            "recommendation_ready",
            candidates,
            ["A human approver must confirm the recommendation before delivery."],
            recommended_template=recommendation,
        )

    reasons: list[str] = []
    if len(exact_ids) > 1:
        reasons.append("Template criteria are conflicting; manual review is required.")
    if missing_fields:
        reasons.append(
            "Template qualification information is missing: "
            + ", ".join(sorted(missing_fields))
        )
    if not candidates:
        reasons.append("No configured template matches this request.")
    if not reasons:
        reasons.append("Template selection requires manual review.")
    return _base_result(
        "template_selection_requires_review",
        candidates,
        reasons,
        missing_context=sorted(missing_fields),
    )
