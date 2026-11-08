from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from tests.fixtures import plasmid_request, request_for, verified_facts_for


def test_complete_information_is_ready():
    result = evaluate_agreement_readiness(plasmid_request())
    assert result == {
        "status": "ready",
        "missing_fields": [],
        "validation_errors": {},
        "review_reasons": [],
    }


def test_missing_agreement_data_does_not_change_eligibility():
    request = plasmid_request()
    request["erpm_intake"]["recipient_experimental_plan"] = ""
    assert (
        evaluate_eligibility(request, verified_facts_for("biological"))["status"]
        == "eligible"
    )
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "missing_information"
    assert "recipient_research_purpose" in result["missing_fields"]


def test_whitespace_only_value_is_missing():
    request = plasmid_request()
    request["agreement_information"]["material_description"] = "   "
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "missing_information"
    assert "material_description" in result["missing_fields"]


def test_ubmta_does_not_require_shipping_address():
    request = plasmid_request()
    request["agreement_information"].pop("shipping_address", None)

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "ready"


def test_autm_request_requires_recipient_authorized_official():
    request = request_for("chemical")
    request["agreement_information"]["recipient_authorized_official_email"] = ""

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "recipient_authorized_official_email" in result["missing_fields"]


def test_template_specific_readiness_does_not_treat_non_signer_email_as_agreement_data():
    request = request_for("chemical")
    request["erpm_intake"]["recipient_scientist_email"] = ""

    result = evaluate_agreement_readiness(request, template_id="chemical_material_agreement")

    assert result["status"] == "ready"
    assert "recipient_scientist_email" not in result["missing_fields"]


def test_simple_letter_requires_recipient_authorized_official():
    request = request_for("device")
    request["agreement_information"]["recipient_authorized_official_name"] = ""

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "recipient_authorized_official_name" in result["missing_fields"]


def test_ubmta_scientist_certifier_does_not_require_separate_official():
    request = plasmid_request()
    information = request["agreement_information"]
    information["recipient_scientist_can_certify_organization"] = True
    information["recipient_authorized_official_name"] = ""
    information["recipient_authorized_official_title"] = ""
    information["recipient_authorized_official_email"] = ""

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "ready"


def test_ubmta_scientist_certifier_ignores_stale_official_email():
    request = plasmid_request()
    information = request["agreement_information"]
    information["recipient_scientist_can_certify_organization"] = True
    information["recipient_authorized_official_email"] = "stale invalid email"

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "ready"
    assert result["validation_errors"] == {}


def test_ubmta_does_not_require_autm_shipping_slots():
    request = plasmid_request()
    information = request["agreement_information"]
    information.pop("shipping_recipient_name", None)
    information.pop("shipping_address", None)

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "ready"


def test_simple_letter_does_not_require_unprinted_recipient_title_or_shipping():
    request = request_for("device")
    information = request["agreement_information"]
    information.pop("recipient_scientist_title", None)
    information.pop("shipping_recipient_name", None)
    information.pop("shipping_address", None)

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "ready"


def test_scientist_academic_titles_are_optional_for_all_templates():
    for category in ("chemical", "animal_derived", "biological", "device"):
        request = request_for(category)
        information = request["agreement_information"]
        information["provider_scientist_title"] = ""
        information["recipient_scientist_title"] = ""

        result = evaluate_agreement_readiness(request)

        assert result["status"] == "ready", category


def test_autm_still_requires_template_shipping_slots():
    request = request_for("chemical")
    request["agreement_information"].pop("shipping_address")

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "shipping_address" in result["missing_fields"]


def test_agreement_readiness_is_not_applicable_without_one_supported_template():
    request = request_for("chemical", "biological")

    result = evaluate_agreement_readiness(request)

    assert result == {
        "status": "not_applicable",
        "missing_fields": [],
        "validation_errors": {},
        "review_reasons": [
            "Agreement fields apply only after one supported material category is selected."
        ],
    }


def test_checklist_required_shipping_and_no_cost_answers_are_required():
    request = plasmid_request()
    request["agreement_information"].pop("recipient_pays_shipping")

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "recipient_pays_shipping" in result["missing_fields"]


def test_recipient_not_paying_shipping_is_still_complete_standard_information():
    request = plasmid_request()
    request["agreement_information"]["recipient_pays_shipping"] = False

    result = evaluate_agreement_readiness(request)

    assert result == {
        "status": "ready",
        "missing_fields": [],
        "validation_errors": {},
        "review_reasons": [],
    }


def test_invalid_signing_email_stops_agreement_preparation_with_specific_error():
    request = plasmid_request()
    request["agreement_information"]["provider_scientist_email"] = "provider-at-umich"

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "provider_scientist_email" not in result["missing_fields"]
    assert result["validation_errors"] == {
        "provider_scientist_email": "Enter a valid Provider Scientist signing email."
    }


def test_special_case_cost_term_requires_manual_review():
    request = plasmid_request()
    request["agreement_information"]["material_provided_at_no_cost"] = False

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "needs_review"
    assert "Provider material is not supplied at no cost." in result["review_reasons"]
