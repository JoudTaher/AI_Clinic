from src.eligibility import evaluate_eligibility
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


def test_questionnaire_only_facts_do_not_silently_pass_unverifiable_rules():
    result = evaluate_eligibility(plasmid_request())

    assert result["status"] == "needs_review"
    assert result["evaluated_sections"] == ["A", "C"]
    assert result["failed_checks"] == []
    assert "recipient_is_us_nonprofit" in ids(result["missing_information"])
    assert "um_owned_without_third_party_restrictions" in ids(
        result["missing_information"]
    )
    assert "internal_noncommercial_research_only" in ids(
        result["missing_information"]
    )


def test_human_derived_material_is_ineligible():
    result = evaluate_eligibility(human_samples_request())
    assert result["status"] == "ineligible"
    assert "no_human_subjects_materials_or_data" in ids(result["failed_checks"])


def test_third_party_material_answer_cannot_be_treated_as_um_ownership_proof():
    request = plasmid_request()
    request["erpm_intake"]["made_using_third_party_materials"] = True
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
