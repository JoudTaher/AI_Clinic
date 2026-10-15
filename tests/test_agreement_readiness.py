from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from tests.fixtures import ids, plasmid_request


def test_complete_information_is_ready():
    result = evaluate_agreement_readiness(plasmid_request())
    assert result == {"status": "ready", "missing_fields": [], "review_reasons": []}


def test_missing_agreement_data_does_not_change_eligibility():
    request = plasmid_request()
    request["agreement_information"].pop("recipient_research_purpose")
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


def test_false_no_cost_answer_requires_review():
    request = plasmid_request()
    request["agreement_information"]["material_provided_at_no_cost"] = False
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "needs_review"
    assert "cost_terms_require_review" in ids(result["review_reasons"])


def test_invalid_shipping_cost_payer_is_missing():
    request = plasmid_request()
    request["agreement_information"]["shipping_cost_payer"] = "unspecified"
    result = evaluate_agreement_readiness(request)
    assert result["status"] == "missing_information"
    assert "shipping_cost_payer" in result["missing_fields"]
