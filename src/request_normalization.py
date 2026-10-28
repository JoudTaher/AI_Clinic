from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.materials import canonical_material_types, derive_material_categories


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        return {
            key: _normalize_value(item)
            for key, item in value.items()
            if isinstance(key, str)
        }
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    return value


def format_requested_duration(years: Any, months: Any, comments: Any) -> str:
    parts: list[str] = []
    if isinstance(years, int) and not isinstance(years, bool) and years > 0:
        parts.append(f"{years} year(s)")
    if isinstance(months, int) and not isinstance(months, bool) and months > 0:
        parts.append(f"{months} month(s)")
    duration = ", ".join(parts)
    normalized_comments = comments.strip() if isinstance(comments, str) else ""
    return " — ".join(
        part for part in (duration, normalized_comments) if part
    )


def normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Return the canonical request used by every backend decision.

    Questionnaire values are authoritative for identities and material types. Fields
    reused by agreement generation are derived here rather than trusted as duplicates.
    """

    normalized = _normalize_value(request)
    if not isinstance(normalized, dict):
        normalized = {}

    raw_intake = normalized.get("erpm_intake")
    intake = raw_intake if isinstance(raw_intake, dict) else {}
    material_types = canonical_material_types(intake.get("material_types"))
    if "material_types" in intake:
        intake["material_types"] = material_types

    document_names = intake.get("related_document_names")
    if isinstance(document_names, list):
        intake["related_document_names"] = sorted(
            dict.fromkeys(
                name for name in document_names if isinstance(name, str) and name
            ),
            key=str.casefold,
        )

    normalized["erpm_intake"] = intake
    normalized["material_categories"] = derive_material_categories(material_types)

    raw_agreement = normalized.get("agreement_information")
    agreement = raw_agreement if isinstance(raw_agreement, dict) else {}
    agreement.update(
        {
            "recipient_institution_name": intake.get("recipient_entity", ""),
            "recipient_scientist_name": intake.get("recipient_scientist_name", ""),
            "recipient_scientist_email": intake.get("recipient_scientist_email", ""),
            "provider_scientist_name": intake.get("contact_pi_name", ""),
            "recipient_research_purpose": intake.get(
                "recipient_experimental_plan", ""
            ),
            "requested_duration": format_requested_duration(
                intake.get("duration_years"),
                intake.get("duration_months"),
                intake.get("duration_comments"),
            ),
            "transmittal_fee": intake.get("reimbursement_cost_or_fee", ""),
        }
    )
    normalized["agreement_information"] = agreement
    return normalized
