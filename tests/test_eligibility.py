from src.checklist import SECTION_CRITERIA, all_criteria
from src.eligibility import derive_checklist_facts, evaluate_eligibility
from tests.fixtures import (
    ids,
    human_samples_request,
    plasmid_request,
    request_for,
    verified_facts_for,
)


def test_checklist_is_evaluated_from_questionnaire_not_caller_answers():
    request = plasmid_request()
    request["erpm_intake"]["return_required"] = True
    request["eligibility_answers"] = {"return_not_required": True}

    result = evaluate_eligibility(request, verified_facts_for("biological"))

    assert "return_not_required" in ids(result["failed_checks"])


def test_every_documented_checklist_criterion_has_one_derived_fact():
    criterion_ids = {
        criterion.field_id
        for criteria in SECTION_CRITERIA.values()
        for criterion in criteria
    }

    assert set(derive_checklist_facts(plasmid_request())) == criterion_ids
    assert [criterion.field_id for criterion in all_criteria()] == [
        criterion.field_id
        for section in ("A", "B", "C", "D", "E")
        for criterion in SECTION_CRITERIA[section]
    ]
    assert all(criterion.semantic_sources for criterion in all_criteria())


def test_trusted_backend_facts_can_complete_unverifiable_checklist_rules():
    result = evaluate_eligibility(
        plasmid_request(), verified_facts_for("biological")
    )

    assert result["status"] == "eligible"
    assert result["missing_information"] == []


def test_questionnaire_proxy_cannot_override_verified_invention_restriction():
    facts = verified_facts_for("biological")
    facts["not_invention_report_patented_or_encumbered"] = False

    result = evaluate_eligibility(plasmid_request(), facts)

    assert "not_invention_report_patented_or_encumbered" in ids(
        result["failed_checks"]
    )


def test_questionnaire_proxy_cannot_override_verified_funding_restriction():
    facts = verified_facts_for("biological")
    facts["no_funding_restrictions"] = False

    result = evaluate_eligibility(plasmid_request(), facts)

    assert "no_funding_restrictions" in ids(result["failed_checks"])


def test_verified_blocker_overrides_less_restrictive_questionnaire_signal():
    facts = verified_facts_for("biological")
    facts["biological_safe_handling_storage_use"] = False

    result = evaluate_eligibility(plasmid_request(), facts)

    assert "biological_safe_handling_storage_use" in ids(result["failed_checks"])


def test_complete_questionnaire_with_explicit_text_can_auto_approve():
    result = evaluate_eligibility(plasmid_request())

    assert result["status"] == "eligible"
    assert result["evaluated_sections"] == ["A", "C"]
    assert result["failed_checks"] == []
    assert result["missing_information"] == []


def test_human_derived_material_is_ineligible():
    result = evaluate_eligibility(human_samples_request())
    assert result["status"] == "ineligible"
    assert "no_human_subjects_materials_or_data" in ids(result["failed_checks"])


def test_third_party_material_answer_routes_ownership_rule_for_review():
    request = plasmid_request()
    request["erpm_intake"]["made_using_third_party_materials"] = True
    request["erpm_intake"]["related_details"] = ""
    result = evaluate_eligibility(request)
    assert result["status"] == "needs_review"
    assert "um_owned_without_third_party_restrictions" in ids(
        result["missing_information"]
    )


def test_failed_chemical_condition_is_ineligible():
    request = request_for("chemical")
    request["erpm_intake"]["dangerous_to_handle_store_or_use"] = True
    result = evaluate_eligibility(request)
    assert result["status"] == "ineligible"
    assert result["evaluated_sections"] == ["A", "B"]
    assert "chemical_no_heightened_ehs_risk" in ids(result["failed_checks"])


def test_commercial_experimental_plan_overrides_noncommercial_proxy():
    request = request_for("chemical")
    request["erpm_intake"]["paying_for_material_as_product_or_service"] = False
    request["erpm_intake"]["recipient_experimental_plan"] = (
        "Commercial product development for a company decision."
    )

    result = evaluate_eligibility(request)

    assert result["status"] == "ineligible"
    assert "internal_noncommercial_research_only" in ids(
        result["failed_checks"]
    )


def test_material_name_does_not_override_structured_export_answer():
    request = request_for("chemical")
    request["erpm_intake"]["export_controlled"] = False
    request["agreement_information"]["material_description"] = (
        "Synthetic research compound C-101"
    )

    result = evaluate_eligibility(request)

    assert "not_controlled_beyond_ear99" in ids(result["passed_checks"])
    assert "not_controlled_beyond_ear99" not in ids(result["failed_checks"])


def test_multiple_material_categories_are_all_evaluated():
    result = evaluate_eligibility(request_for("chemical", "biological"))
    assert result["status"] == "needs_review"
    assert result["evaluated_sections"] == ["A", "B", "C"]


def test_unsupported_category_needs_review():
    request = request_for("other")
    result = evaluate_eligibility(request)
    assert result["status"] == "needs_review"
    assert result["evaluated_sections"] == ["A"]
    assert "material_categories" in ids(result["missing_information"])


def test_failed_general_condition_takes_precedence_over_missing_category():
    request = request_for()
    request["erpm_intake"]["return_required"] = True
    result = evaluate_eligibility(request)
    assert result["status"] == "ineligible"
    assert "return_not_required" in ids(result["failed_checks"])


def test_questionnaire_and_explicit_text_can_satisfy_documented_rules():
    request = request_for("chemical")
    request["erpm_intake"].update(
        {
            "recipient_entity": "Example U.S. Non-Profit University",
            "leaving_country": False,
            "recipient_experimental_plan": (
                "Internal, non-commercial laboratory research only. "
                "Not for use in humans."
            ),
            "made_using_third_party_materials": False,
            "previously_invention_report_or_licensed": False,
            "external_funding_supported_development": False,
        }
    )

    result = evaluate_eligibility(request)

    assert result["status"] == "eligible"
    assert result["missing_information"] == []
    assert result["semantic_assessment"]["method"] == (
        "local_huggingface_semantic_classification"
    )


def test_chemical_classroom_research_establishes_no_human_use():
    request = request_for("chemical")
    request["erpm_intake"]["project_title"] = "For test purposes only"
    request["erpm_intake"]["recipient_experimental_plan"] = (
        "Research in the chemistry class"
    )
    request["agreement_information"]["material_description"] = "Chemistry NaCl"

    result = evaluate_eligibility(request)

    assert result["status"] == "eligible"
    assert "chemical_not_used_in_humans" in ids(result["passed_checks"])
    assert result["missing_information"] == []


def test_ambiguous_device_use_text_keeps_device_rules_unresolved():
    request = request_for("device")
    request["erpm_intake"]["recipient_experimental_plan"] = "Study performance."

    result = evaluate_eligibility(request)

    assert result["status"] == "needs_review"
    assert "internal_noncommercial_research_only" in ids(result["passed_checks"])
    assert "device_not_used_in_humans" in ids(result["missing_information"])


def test_third_party_material_answer_does_not_claim_a_restriction_without_evidence():
    request = plasmid_request()
    request["erpm_intake"]["made_using_third_party_materials"] = True
    request["erpm_intake"]["related_details"] = ""

    result = evaluate_eligibility(request)

    assert result["status"] == "needs_review"
    assert "um_owned_without_third_party_restrictions" in ids(result["missing_information"])


def test_disqualifying_narrative_overrides_structured_proxy_answers():
    request = plasmid_request()
    request["erpm_intake"]["related_details"] = (
        "The material is patented and encumbered, owned by another party subject "
        "to third-party restrictions, and is a DEA Schedule II controlled substance."
    )

    result = evaluate_eligibility(request)

    failed = ids(result["failed_checks"])
    assert result["status"] == "ineligible"
    assert "not_invention_report_patented_or_encumbered" in failed
    assert "um_owned_without_third_party_restrictions" in failed
    assert "not_controlled_beyond_ear99" in failed


def test_domestic_university_name_satisfies_nonprofit_institution_rule():
    request = plasmid_request()
    request["erpm_intake"]["recipient_entity"] = "Example University"
    request["erpm_intake"]["leaving_country"] = False

    result = evaluate_eligibility(request)

    assert "recipient_is_us_nonprofit" in ids(result["passed_checks"])


def test_research_department_request_passes_without_email_domain_inference():
    request = plasmid_request()
    request["erpm_intake"].update(
        {
            "recipient_entity": "Research and medicine department",
            "recipient_scientist_email": "scientist@example.com",
            "recipient_administrative_contact_email": "admin@example.com",
            "leaving_country": False,
            "paying_for_material_as_product_or_service": False,
            "recipient_experimental_plan": "Research in the medicine department",
            "related_details": "",
        }
    )

    result = evaluate_eligibility(request)

    assert result["status"] == "eligible"
    assert result["missing_information"] == []
    passed = ids(result["passed_checks"])
    assert "recipient_is_us_nonprofit" in passed
    assert "internal_noncommercial_research_only" in passed


def test_domestic_noncommercial_nih_chemical_request_passes_eligibility():
    request = request_for("chemical")
    request["erpm_intake"].update(
        {
            "recipient_entity": "NIH",
            "leaving_country": False,
            "paying_for_material_as_product_or_service": False,
            "recipient_experimental_plan": "Experiments for chemistry students.",
            "radioactive": False,
            "dangerous_to_handle_store_or_use": False,
            "hazardous_chemical_capacity_constraint": False,
            "related_details": "",
        }
    )
    request["agreement_information"]["material_description"] = (
        "Chemical compounds such as NaCl"
    )

    result = evaluate_eligibility(request)

    assert result["status"] == "eligible"
    assert result["failed_checks"] == []
    assert result["missing_information"] == []


def test_email_domain_alone_does_not_establish_nonprofit_status():
    request = plasmid_request()
    request["erpm_intake"].update(
        {
            "recipient_entity": "Unspecified recipient",
            "recipient_scientist_email": "scientist@nih.gov",
            "recipient_administrative_contact_email": "admin@nih.gov",
            "leaving_country": False,
            "paying_for_material_as_product_or_service": False,
            "recipient_experimental_plan": "Research",
            "related_details": "",
        }
    )

    result = evaluate_eligibility(request)

    assert result["status"] == "needs_review"
    assert "recipient_is_us_nonprofit" in ids(result["missing_information"])


def test_completed_original_form_style_plasmid_request_is_eligible():
    request = plasmid_request()
    request["erpm_intake"].update(
        {
            "recipient_entity": "Michigan State University",
            "leaving_country": False,
            "paying_for_material_as_product_or_service": False,
            "recipient_experimental_plan": (
                "The recipient will study plasmid expression in laboratory cells."
            ),
            "made_using_third_party_materials": False,
            "previously_invention_report_or_licensed": False,
            "related_details": "",
        }
    )
    request["agreement_information"]["material_description"] = ""

    result = evaluate_eligibility(request)

    assert result["status"] == "eligible"
    assert result["failed_checks"] == []
    assert result["missing_information"] == []


def test_no_third_party_materials_satisfies_device_ip_rule():
    request = request_for("device")
    request["erpm_intake"]["made_using_third_party_materials"] = False
    request["erpm_intake"]["related_details"] = ""

    result = evaluate_eligibility(request)

    assert "device_no_embedded_third_party_ip" in ids(result["passed_checks"])


def test_eligible_request_is_identified_as_standard_automatic_mta():
    result = evaluate_eligibility(plasmid_request())

    assert "Standard MTA automatic approval" in result["explanation"]


def test_nonqualifying_request_is_identified_as_manual_special_case():
    request = plasmid_request()
    request["erpm_intake"]["return_required"] = True

    result = evaluate_eligibility(request)

    assert "Manual special-case MTA review" in result["explanation"]
