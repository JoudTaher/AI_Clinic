from __future__ import annotations

from copy import deepcopy


GENERAL_ANSWERS = {
    "recipient_is_us_nonprofit": True,
    "um_owned_without_third_party_restrictions": True,
    "internal_noncommercial_research_only": True,
    "not_invention_report_patented_or_encumbered": True,
    "no_funding_restrictions": True,
    "no_human_subjects_materials_or_data": True,
    "not_controlled_beyond_ear99": True,
    "return_not_required": True,
}

BIOLOGICAL_ANSWERS = {
    "biological_nonradioactive": True,
    "biological_material_definition_met": True,
    "biological_safe_handling_storage_use": True,
}

CHEMICAL_ANSWERS = {
    "chemical_no_heightened_ehs_risk": True,
    "chemical_not_used_in_humans": True,
}

DEVICE_ANSWERS = {
    "device_not_clinical_or_diagnostic": True,
    "device_not_used_in_humans": True,
    "device_no_embedded_third_party_ip": True,
}

ANIMAL_ANSWERS = {
    "animal_no_live_animals": True,
    "animal_no_restricted_species_or_permits": True,
    "animal_nonliving_derivative_definition_met": True,
}

COMPLETE_AGREEMENT_INFORMATION = {
    "recipient_institution_name": "Example University",
    "recipient_institution_address": "100 Research Way, Example, MI 48100",
    "recipient_scientist_name": "Dr. Recipient",
    "recipient_scientist_title": "Associate Professor",
    "provider_scientist_name": "Dr. Provider",
    "provider_scientist_title": "Professor",
    "material_description": "Synthetic plasmid pExample",
    "recipient_research_purpose": "Non-commercial laboratory research",
    "requested_duration": "3 years",
    "shipping_cost_payer": "recipient",
    "material_provided_at_no_cost": True,
    "shipping_recipient_name": "Dr. Recipient",
    "shipping_address": "100 Research Way, Example, MI 48100",
    "transmittal_fee": "$125.00",
}


def request_for(*categories: str) -> dict:
    answers = dict(GENERAL_ANSWERS)
    if "biological" in categories:
        answers.update(BIOLOGICAL_ANSWERS)
    if "chemical" in categories:
        answers.update(CHEMICAL_ANSWERS)
    if "device" in categories:
        answers.update(DEVICE_ANSWERS)
    if "animal_derived" in categories:
        answers.update(ANIMAL_ANSWERS)
    return {
        "material_categories": list(categories),
        "eligibility_answers": answers,
        "agreement_information": deepcopy(COMPLETE_AGREEMENT_INFORMATION),
    }


def plasmid_request() -> dict:
    return request_for("biological")


def human_samples_request() -> dict:
    request = request_for("biological")
    request["eligibility_answers"]["no_human_subjects_materials_or_data"] = False
    return request


def ids(entries: list[dict]) -> list[str]:
    return [entry["field_id"] for entry in entries]
