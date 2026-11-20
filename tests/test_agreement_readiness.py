from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from tests.fixtures import plasmid_request, request_for, verified_facts_for


def test_complete_information_is_ready():
    result = evaluate_agreement_readiness(request_for("chemical"))
    assert result == {
        "status": "ready",
        "missing_fields": [],
        "validation_errors": {},
        "review_reasons": [],
    }


def test_missing_agreement_data_does_not_change_eligibility():
    request = request_for("chemical")
    request["erpm_intake"]["recipient_experimental_plan"] = ""
    assert (
        evaluate_eligibility(request, verified_facts_for("chemical"))["status"]
        == "eligible"
    )
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "missing_information"
    assert "recipient_research_purpose" in result["missing_fields"]


def test_whitespace_only_value_is_missing():
    request = request_for("chemical")
    request["agreement_information"]["material_description"] = "   "
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "missing_information"
    assert "material_description" in result["missing_fields"]


def test_ubmta_does_not_require_shipping_address():
    request = plasmid_request()
    request["agreement_information"].pop("shipping_address", None)

    result = evaluate_agreement_readiness(
        request, template_id="biological_material_agreement"
    )

    assert result["status"] == "ready"


def test_autm_request_requires_recipient_authorized_official():
    request = request_for("chemical")
    request["agreement_information"]["recipient_authorized_official_email"] = ""

    result = evaluate_agreement_readiness(
        request, template_id="biological_material_agreement"
    )

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


def test_ubmta_requires_separate_recipient_official():
    request = plasmid_request()
    information = request["agreement_information"]
    information["recipient_authorized_official_name"] = ""
    information["recipient_authorized_official_title"] = ""
    information["recipient_authorized_official_email"] = ""

    result = evaluate_agreement_readiness(
        request, template_id="biological_material_agreement"
    )

    assert result["status"] == "missing_information"
    assert "recipient_authorized_official_name" in result["missing_fields"]
    assert "recipient_authorized_official_title" in result["missing_fields"]
    assert "recipient_authorized_official_email" in result["missing_fields"]


def test_ubmta_validates_separate_official_email():
    request = plasmid_request()
    information = request["agreement_information"]
    information["recipient_authorized_official_email"] = "stale invalid email"

    result = evaluate_agreement_readiness(
        request, template_id="biological_material_agreement"
    )

    assert result["status"] == "missing_information"
    assert "recipient_authorized_official_email" in result["validation_errors"]


def test_ubmta_does_not_require_autm_shipping_slots():
    request = plasmid_request()
    information = request["agreement_information"]
    information.pop("shipping_recipient_name", None)
    information.pop("shipping_address", None)

    result = evaluate_agreement_readiness(
        request, template_id="biological_material_agreement"
    )

    assert result["status"] == "ready"


def test_simple_letter_requires_recipient_title_but_not_autm_shipping():
    request = request_for("device")
    information = request["agreement_information"]
    information["recipient_scientist_title"] = ""
    information.pop("shipping_recipient_name", None)
    information.pop("shipping_address", None)

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "recipient_scientist_title" in result["missing_fields"]
    assert "shipping_recipient_name" not in result["missing_fields"]
    assert "shipping_address" not in result["missing_fields"]


def test_provider_scientist_title_is_required_for_every_template():
    for category in ("chemical", "animal_derived", "biological", "device"):
        request = request_for(category)
        request["agreement_information"]["provider_scientist_title"] = ""

        result = evaluate_agreement_readiness(
            request,
            template_id=(
                "biological_material_agreement"
                if category == "biological"
                else None
            ),
        )

        assert result["status"] == "missing_information", category
        assert "provider_scientist_title" in result["missing_fields"]


def test_recipient_scientist_title_is_required_for_every_template():
    for category in ("chemical", "animal_derived", "biological", "device"):
        request = request_for(category)
        request["agreement_information"]["recipient_scientist_title"] = ""

        result = evaluate_agreement_readiness(
            request,
            template_id=(
                "biological_material_agreement"
                if category == "biological"
                else None
            ),
        )

        assert result["status"] == "missing_information", category
        assert "recipient_scientist_title" in result["missing_fields"]


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
    request = request_for("chemical")
    request["agreement_information"].pop("recipient_pays_shipping")

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "recipient_pays_shipping" in result["missing_fields"]


def test_recipient_not_paying_shipping_is_still_complete_standard_information():
    request = request_for("chemical")
    request["agreement_information"]["recipient_pays_shipping"] = False

    result = evaluate_agreement_readiness(request)

    assert result == {
        "status": "ready",
        "missing_fields": [],
        "validation_errors": {},
        "review_reasons": [],
    }


def test_provider_scientist_signing_email_is_not_required_for_one_sided_delivery():
    request = request_for("chemical")
    request["agreement_information"].pop("provider_scientist_email", None)

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "ready"
    assert result["missing_fields"] == []
    assert result["validation_errors"] == {}


def test_special_case_cost_term_requires_manual_review():
    request = request_for("chemical")
    request["agreement_information"]["material_provided_at_no_cost"] = False

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "needs_review"
    assert "Provider material is not supplied at no cost." in result["review_reasons"]
