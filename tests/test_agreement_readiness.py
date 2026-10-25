from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from tests.fixtures import ids, plasmid_request, request_for


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


def test_erpm_intake_and_agreement_population_fields_are_both_required():
    request = request_for("biological")
    request["erpm_intake"] = {
        "project_title": "Synthetic plasmid transfer",
        "paying_um_for_material": False,
        "duration_years": 0,
        "duration_months": 1,
        "copy_from_existing_ufa": False,
        "contact_pi_name": "Example PI",
        "primary_research_administrator_name": "Example RA",
        "measurable_personnel_effort": False,
        "material_types": ["Plasmid/vector (DNA or RNA)"],
        "material_description": "Synthetic plasmid",
        "radioactive": False,
        "dangerous_to_handle_store_or_use": False,
        "hazardous_chemical_capacity_constraint": False,
        "project_administrative_home": "Example department",
        "will_deposit_in_repository": False,
        "recipient_entity": "Example recipient",
        "recipient_scientist_name": "Example scientist",
        "recipient_scientist_email": "scientist@example.org",
        "leaving_country": False,
        "export_controlled": False,
        "reimbursement_cost_or_fee": "Shipping costs",
        "recipient_experimental_plan": "Non-commercial research",
        "return_required": False,
        "previously_invention_report_or_licensed": False,
        "external_funding_supported_development": False,
        "managed_affiliate_work": False,
        "made_using_third_party_materials": False,
        "clinical_health_data_shared": False,
    }

    result = evaluate_agreement_readiness(request)

    assert result == {"status": "ready", "missing_fields": [], "review_reasons": []}


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


def test_ubmta_scientist_certifier_does_not_require_separate_official():
    request = plasmid_request()
    information = request["agreement_information"]
    information["recipient_scientist_can_certify_organization"] = True
    information["recipient_authorized_official_name"] = ""
    information["recipient_authorized_official_title"] = ""
    information["recipient_authorized_official_email"] = ""

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "ready"


def test_erpm_intake_reports_a_missing_recipient_email():
    request = plasmid_request()
    request["erpm_intake"] = {
        "project_title": "Synthetic plasmid transfer",
        "material_types": ["Plasmid/vector (DNA or RNA)"],
    }

    result = evaluate_agreement_readiness(request)

    assert result["status"] == "missing_information"
    assert "recipient_scientist_email" in result["missing_fields"]
