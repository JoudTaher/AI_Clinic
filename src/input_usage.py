from __future__ import annotations

from collections.abc import Mapping
from typing import Any


ERPM_FIELD_USES: dict[str, tuple[str, ...]] = {
    "project_title": (
        "intake_completeness",
        "semantic_eligibility",
        "audit_record",
    ),
    "paying_for_material_as_product_or_service": (
        "intake_completeness",
        "eligibility_rule",
    ),
    "duration_years": ("intake_completeness", "agreement_population"),
    "duration_months": ("intake_completeness", "agreement_population"),
    "duration_comments": ("agreement_population",),
    "contact_pi_name": (
        "intake_completeness",
        "agreement_population",
        "signing_package",
    ),
    "primary_research_administrator_name": (
        "intake_completeness",
        "routing_record",
    ),
    "measurable_personnel_effort": ("intake_completeness", "audit_record"),
    "material_types": (
        "intake_completeness",
        "eligibility_rule",
        "template_selection",
    ),
    "human_derived_description": (
        "intake_completeness",
        "semantic_eligibility",
    ),
    "human_data_classification": (
        "intake_completeness",
        "semantic_eligibility",
    ),
    "irb_study_number": ("intake_completeness", "routing_record"),
    "protocol_consent_transfer_sections": (
        "intake_completeness",
        "semantic_eligibility",
        "routing_record",
    ),
    "radioactive": ("intake_completeness", "eligibility_rule"),
    "dangerous_to_handle_store_or_use": (
        "intake_completeness",
        "eligibility_rule",
    ),
    "hazardous_chemical_capacity_constraint": (
        "intake_completeness",
        "eligibility_rule",
    ),
    "project_administrative_home": ("intake_completeness", "routing_record"),
    "will_deposit_in_repository": ("intake_completeness", "audit_record"),
    "recipient_entity": (
        "intake_completeness",
        "eligibility_rule",
        "agreement_population",
    ),
    "recipient_scientist_name": (
        "intake_completeness",
        "agreement_population",
        "signing_package",
    ),
    "recipient_scientist_email": (
        "intake_completeness",
        "signing_package",
    ),
    "recipient_administrative_contact_name": ("contact_record",),
    "recipient_administrative_contact_email": ("contact_record",),
    "recipient_administrative_contact_street_address": ("contact_record",),
    "recipient_administrative_contact_telephone": ("contact_record",),
    "recipient_administrative_contact_fax": ("contact_record",),
    "leaving_country": ("intake_completeness", "eligibility_rule"),
    "export_controlled": ("intake_completeness", "eligibility_rule"),
    "reimbursement_cost_or_fee": (
        "intake_completeness",
        "agreement_population",
    ),
    "recipient_experimental_plan": (
        "intake_completeness",
        "semantic_eligibility",
        "agreement_population",
    ),
    "return_required": ("intake_completeness", "eligibility_rule"),
    "previously_invention_report_or_licensed": (
        "intake_completeness",
        "eligibility_rule",
    ),
    "innovation_partnerships_file_number": (
        "conditional_intake_completeness",
        "routing_record",
    ),
    "external_funding_supported_development": (
        "intake_completeness",
        "eligibility_rule",
    ),
    "managed_affiliate_work": ("intake_completeness", "routing_record"),
    "made_using_third_party_materials": (
        "intake_completeness",
        "eligibility_rule",
    ),
    "clinical_health_data_shared": (
        "intake_completeness",
        "eligibility_rule",
    ),
    "related_document_names": ("evidence_record",),
    "related_details": ("semantic_eligibility", "routing_record"),
}


AGREEMENT_FIELD_USES: dict[str, tuple[str, ...]] = {
    "recipient_institution_name": ("agreement_population",),
    "recipient_institution_address": ("agreement_population",),
    "recipient_scientist_name": ("agreement_population", "signing_package"),
    "recipient_scientist_title": ("agreement_population", "signing_package"),
    "recipient_scientist_email": ("signing_package",),
    "recipient_scientist_can_certify_organization": (
        "agreement_population",
        "signing_package",
    ),
    "recipient_authorized_official_name": (
        "agreement_population",
        "signing_package",
    ),
    "recipient_authorized_official_title": (
        "agreement_population",
        "signing_package",
    ),
    "recipient_authorized_official_email": ("signing_package",),
    "provider_scientist_name": ("agreement_population", "signing_package"),
    "provider_scientist_title": ("agreement_population", "signing_package"),
    "provider_scientist_email": ("signing_package",),
    "material_description": ("semantic_eligibility", "agreement_population"),
    "recipient_research_purpose": (
        "semantic_eligibility",
        "agreement_population_context",
    ),
    "requested_duration": ("agreement_population_context",),
    "shipping_recipient_name": ("agreement_population",),
    "shipping_address": ("agreement_population",),
    "transmittal_fee": ("agreement_population",),
    "recipient_pays_shipping": ("agreement_term_validation",),
    "material_provided_at_no_cost": ("agreement_term_validation",),
}

AGREEMENT_COMMON_FIELDS = {
    "recipient_institution_name",
    "recipient_institution_address",
    "recipient_scientist_name",
    "recipient_scientist_email",
    "provider_scientist_name",
    "provider_scientist_title",
    "provider_scientist_email",
    "material_description",
    "recipient_research_purpose",
    "requested_duration",
    "transmittal_fee",
    "recipient_pays_shipping",
    "material_provided_at_no_cost",
}

AGREEMENT_CATEGORY_FIELDS = {
    "chemical": {
        "recipient_scientist_title",
        "recipient_authorized_official_name",
        "recipient_authorized_official_title",
        "recipient_authorized_official_email",
        "shipping_recipient_name",
        "shipping_address",
    },
    "animal_derived": {
        "recipient_scientist_title",
        "recipient_authorized_official_name",
        "recipient_authorized_official_title",
        "recipient_authorized_official_email",
        "shipping_recipient_name",
        "shipping_address",
    },
    "biological": {
        "recipient_scientist_title",
        "recipient_scientist_can_certify_organization",
        "recipient_authorized_official_name",
        "recipient_authorized_official_title",
        "recipient_authorized_official_email",
    },
    "device": {
        "recipient_authorized_official_name",
        "recipient_authorized_official_title",
        "recipient_authorized_official_email",
    },
}


def _section_usage(
    values: Mapping[str, Any],
    catalog: Mapping[str, tuple[str, ...]],
    applicable_fields: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for field_id in values:
        uses = catalog.get(field_id)
        if uses is None:
            result[field_id] = {
                "uses": ["unmapped_input"],
                "warning": "No backend consumer is registered for this field.",
            }
        elif applicable_fields is not None and field_id not in applicable_fields:
            result[field_id] = {
                "uses": ["not_applicable_to_selected_template"],
                "warning": "This field is not used by the selected agreement template.",
            }
        else:
            result[field_id] = {"uses": list(uses)}
    return result


def build_input_usage(request: Mapping[str, Any]) -> dict[str, Any]:
    """Return an audit map showing the backend consumer for each submitted field."""

    raw_intake = request.get("erpm_intake", {})
    intake = raw_intake if isinstance(raw_intake, Mapping) else {}
    raw_agreement = request.get("agreement_information", {})
    agreement = raw_agreement if isinstance(raw_agreement, Mapping) else {}
    raw_categories = request.get("material_categories", [])
    category = (
        raw_categories[0]
        if isinstance(raw_categories, list) and len(raw_categories) == 1
        else None
    )
    applicable_agreement_fields = (
        AGREEMENT_COMMON_FIELDS | AGREEMENT_CATEGORY_FIELDS[category]
        if category in AGREEMENT_CATEGORY_FIELDS
        else set()
    )
    return {
        "erpm_intake": _section_usage(intake, ERPM_FIELD_USES),
        "agreement_information": _section_usage(
            agreement, AGREEMENT_FIELD_USES, applicable_agreement_fields
        ),
    }
