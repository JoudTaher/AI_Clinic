from __future__ import annotations

from copy import deepcopy


VERIFIED_GENERAL_FACTS = {
    "recipient_is_us_nonprofit": True,
    "um_owned_without_third_party_restrictions": True,
    "internal_noncommercial_research_only": True,
    "not_invention_report_patented_or_encumbered": True,
    "no_funding_restrictions": True,
    "no_human_subjects_materials_or_data": True,
    "not_controlled_beyond_ear99": True,
    "return_not_required": True,
}

VERIFIED_BIOLOGICAL_FACTS = {
    "biological_nonradioactive": True,
    "biological_material_definition_met": True,
    "biological_safe_handling_storage_use": True,
}

VERIFIED_CHEMICAL_FACTS = {
    "chemical_no_heightened_ehs_risk": True,
    "chemical_not_used_in_humans": True,
}

VERIFIED_DEVICE_FACTS = {
    "device_not_clinical_or_diagnostic": True,
    "device_not_used_in_humans": True,
    "device_no_embedded_third_party_ip": True,
}

VERIFIED_ANIMAL_FACTS = {
    "animal_no_live_animals": True,
    "animal_no_restricted_species_or_permits": True,
    "animal_nonliving_derivative_definition_met": True,
}

COMPLETE_AGREEMENT_INFORMATION = {
    "recipient_institution_name": "Example University",
    "recipient_institution_address": "100 Research Way, Example, MI 48100",
    "recipient_scientist_name": "Dr. Recipient",
    "recipient_scientist_title": "Associate Professor",
    "recipient_scientist_email": "recipient.scientist@example.org",
    "recipient_scientist_can_certify_organization": False,
    "recipient_authorized_official_name": "Alex Official",
    "recipient_authorized_official_title": "Director of Research Agreements",
    "recipient_authorized_official_email": "recipient.official@example.org",
    "provider_scientist_name": "Dr. Provider",
    "provider_scientist_title": "Professor",
    "provider_scientist_email": "provider.scientist@umich.edu",
    "material_description": "Synthetic plasmid pExample",
    "recipient_research_purpose": "Non-commercial laboratory research",
    "requested_duration": "3 years",
    "recipient_pays_shipping": True,
    "material_provided_at_no_cost": True,
    "shipping_recipient_name": "Dr. Recipient",
    "shipping_address": "100 Research Way, Example, MI 48100",
}

COMPLETE_ERPM_INTAKE = {
    "project_title": "Synthetic plasmid transfer",
    "paying_for_material_as_product_or_service": False,
    "duration_years": 3,
    "duration_months": 0,
    "duration_comments": "",
    "contact_pi_name": "Dr. Provider",
    "primary_research_administrator_name": "Example Administrator",
    "measurable_personnel_effort": False,
    "material_types": ["Plasmid/Vector (rDNA or SNA)"],
    "radioactive": False,
    "dangerous_to_handle_store_or_use": False,
    "hazardous_chemical_capacity_constraint": False,
    "project_administrative_home": "Example Department",
    "will_deposit_in_repository": False,
    "recipient_entity": "Example U.S. Non-Profit University",
    "recipient_scientist_name": "Dr. Recipient",
    "recipient_scientist_email": "recipient.scientist@example.org",
    "recipient_administrative_contact_name": "",
    "recipient_administrative_contact_email": "",
    "recipient_administrative_contact_street_address": "",
    "recipient_administrative_contact_telephone": "",
    "recipient_administrative_contact_fax": "",
    "leaving_country": False,
    "export_controlled": False,
    "reimbursement_cost_or_fee": "$125.00",
    "recipient_experimental_plan": "Non-commercial laboratory research",
    "return_required": False,
    "previously_invention_report_or_licensed": False,
    "innovation_partnerships_file_number": "",
    "external_funding_supported_development": False,
    "managed_affiliate_work": False,
    "made_using_third_party_materials": False,
    "clinical_health_data_shared": False,
    "related_details": (
        "The material is owned by U-M with no third-party restrictions. "
        "No invention report, patent, license, or encumbrance applies."
    ),
    "related_document_names": [],
}


def request_for(*categories: str) -> dict:
    intake = deepcopy(COMPLETE_ERPM_INTAKE)
    if categories == ("chemical",):
        intake["material_types"] = ["Chemical compound"]
        intake["recipient_experimental_plan"] = (
            "Internal, non-commercial laboratory research only. "
            "The material will not be used in humans."
        )
    elif categories == ("animal_derived",):
        intake["material_types"] = ["Mouse/Rat"]
        intake["recipient_experimental_plan"] = (
            "Internal, non-commercial laboratory research only."
        )
    elif categories == ("device",):
        intake["material_types"] = ["Device"]
        intake["recipient_experimental_plan"] = (
            "Research use only. Not for use in humans or for clinical or diagnostic use."
        )
    elif categories == ("other",):
        intake["material_types"] = ["Other material"]
    elif len(categories) > 1:
        category_material = {
            "biological": "Plasmid/Vector (rDNA or SNA)",
            "chemical": "Chemical compound",
            "device": "Device",
            "animal_derived": "Mouse/Rat",
            "other": "Other material",
        }
        intake["material_types"] = [
            category_material[category]
            for category in categories
            if category in category_material
        ]
    agreement = deepcopy(COMPLETE_AGREEMENT_INFORMATION)
    if categories == ("animal_derived",):
        agreement["material_description"] = (
            "Fixed, non-living mouse tissue samples; no live animals, no restricted "
            "species, and no special permits are involved."
        )
    if categories == ("biological",):
        agreement.pop("shipping_recipient_name")
        agreement.pop("shipping_address")
    elif categories in {("chemical",), ("animal_derived",)}:
        agreement.pop("recipient_scientist_can_certify_organization")
    elif categories == ("device",):
        agreement.pop("recipient_scientist_title")
        agreement.pop("recipient_scientist_can_certify_organization")
        agreement.pop("shipping_recipient_name")
        agreement.pop("shipping_address")
    return {
        "erpm_intake": intake,
        "agreement_information": agreement,
    }


def verified_facts_for(*categories: str) -> dict[str, bool]:
    facts = dict(VERIFIED_GENERAL_FACTS)
    if "biological" in categories:
        facts.update(VERIFIED_BIOLOGICAL_FACTS)
    if "chemical" in categories:
        facts.update(VERIFIED_CHEMICAL_FACTS)
    if "device" in categories:
        facts.update(VERIFIED_DEVICE_FACTS)
    if "animal_derived" in categories:
        facts.update(VERIFIED_ANIMAL_FACTS)
    return facts


def plasmid_request() -> dict:
    return request_for("biological")


def human_samples_request() -> dict:
    request = request_for("biological")
    request["erpm_intake"]["material_types"] = [
        "Human derived materials (isolated tissue, samples, specimens, cells, etc.)"
    ]
    request["erpm_intake"].update(
        {
            "human_derived_description": "Skin tissue",
            "human_data_classification": "De-identified",
            "irb_study_number": "HUM00000001",
            "protocol_consent_transfer_sections": "Section 4 permits transfer",
        }
    )
    return request


def ids(entries: list[dict]) -> list[str]:
    return [entry["field_id"] for entry in entries]
