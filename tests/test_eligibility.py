from src.eligibility import evaluate_eligibility
from tests.fixtures import ids, human_samples_request, plasmid_request, request_for


def test_complete_plasmid_request_is_eligible():
    result = evaluate_eligibility(plasmid_request())
    assert result["status"] == "eligible"
    assert result["evaluated_sections"] == ["A", "C"]
    assert result["failed_checks"] == []
    assert result["missing_information"] == []


def test_human_derived_material_is_ineligible():
    result = evaluate_eligibility(human_samples_request())
    assert result["status"] == "ineligible"
    assert "no_human_subjects_materials_or_data" in ids(result["failed_checks"])


def test_missing_answer_needs_review():
    request = plasmid_request()
    request["eligibility_answers"].pop("no_funding_restrictions")
    result = evaluate_eligibility(request)
    assert result["status"] == "needs_review"
    assert "no_funding_restrictions" in ids(result["missing_information"])


def test_commercial_recipient_is_ineligible():
    request = plasmid_request()
    request["eligibility_answers"]["recipient_is_us_nonprofit"] = False
    result = evaluate_eligibility(request)
    assert result["status"] == "ineligible"
    assert "recipient_is_us_nonprofit" in ids(result["failed_checks"])


def test_third_party_restriction_is_ineligible():
    request = plasmid_request()
    request["eligibility_answers"]["um_owned_without_third_party_restrictions"] = False
    result = evaluate_eligibility(request)
    assert result["status"] == "ineligible"
    assert "um_owned_without_third_party_restrictions" in ids(result["failed_checks"])


def test_failed_chemical_condition_is_ineligible():
    request = request_for("chemical")
    request["eligibility_answers"]["chemical_no_heightened_ehs_risk"] = False
    result = evaluate_eligibility(request)
    assert result["status"] == "ineligible"
    assert result["evaluated_sections"] == ["A", "B"]
    assert "chemical_no_heightened_ehs_risk" in ids(result["failed_checks"])


def test_multiple_material_categories_are_all_evaluated():
    result = evaluate_eligibility(request_for("chemical", "biological"))
    assert result["status"] == "eligible"
    assert result["evaluated_sections"] == ["A", "B", "C"]


def test_unsupported_category_needs_review():
    request = request_for("other")
    result = evaluate_eligibility(request)
    assert result["status"] == "needs_review"
    assert result["evaluated_sections"] == ["A"]
    assert "material_categories" in ids(result["missing_information"])


def test_failed_general_condition_takes_precedence_over_missing_category():
    request = request_for()
    request["eligibility_answers"]["return_not_required"] = False
    result = evaluate_eligibility(request)
    assert result["status"] == "ineligible"
    assert "return_not_required" in ids(result["failed_checks"])


def test_truthy_string_is_missing_not_passing():
    request = plasmid_request()
    request["eligibility_answers"]["no_funding_restrictions"] = "yes"
    result = evaluate_eligibility(request)
    assert result["status"] == "needs_review"
    assert "no_funding_restrictions" in ids(result["missing_information"])
