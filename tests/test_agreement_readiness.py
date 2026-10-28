from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from tests.fixtures import plasmid_request, request_for


def test_complete_information_is_ready():
    result = evaluate_agreement_readiness(plasmid_request())
    assert result == {"status": "ready", "missing_fields": [], "review_reasons": []}


def test_missing_agreement_data_does_not_change_eligibility():
    request = plasmid_request()
    request["erpm_intake"]["recipient_experimental_plan"] = ""
    assert evaluate_eligibility(request)["status"] == "eligible"
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "missing_information"
    assert "recipient_research_purpose" in result["missing_fields"]


def test_whitespace_only_value_is_missing():
    request = plasmid_request()
    request["agreement_information"]["material_description"] = "   "
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "missing_information"
    assert "material_description" in result["missing_fields"]


def test_no_cost_answer_is_required_information_not_an_eligibility_rule():
    request = plasmid_request()
    request["agreement_information"]["material_provided_at_no_cost"] = False
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "ready"
    assert result["review_reasons"] == []


def test_recipient_shipping_payment_answer_must_be_boolean():
    request = plasmid_request()
    request["agreement_information"]["recipient_pays_shipping"] = "unspecified"
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "missing_information"
    assert "recipient_pays_shipping" in result["missing_fields"]


def test_missing_renderer_field_is_reported_before_generation():
    request = plasmid_request()
    request["agreement_information"].pop("shipping_address")

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "shipping_address" in result["missing_fields"]


def test_autm_request_requires_recipient_authorized_official():
    request = request_for("chemical")
    request["agreement_information"]["recipient_authorized_official_email"] = ""

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "recipient_authorized_official_email" in result["missing_fields"]


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
