from src.intake import evaluate_intake_readiness
from tests.fixtures import request_for


def test_complete_requester_questionnaire_is_ready():
    result = evaluate_intake_readiness(request_for("biological"))

    assert result == {"status": "ready", "missing_fields": []}


def test_requester_questionnaire_requires_source_form_fields():
    request = request_for("biological")
    request["erpm_intake"]["project_administrative_home"] = ""

    result = evaluate_intake_readiness(request)

    assert result["status"] == "missing_information"
    assert "project_administrative_home" in result["missing_fields"]


def test_human_material_requires_human_specific_source_form_fields():
    request = request_for("biological")
    request["erpm_intake"]["material_types"] = [
        "Human derived materials (isolated tissue, samples, specimens, cells, etc.)"
    ]

    result = evaluate_intake_readiness(request)

    assert result["status"] == "missing_information"
    assert result["missing_fields"] == [
        "human_derived_description",
        "human_data_classification",
        "irb_study_number",
        "protocol_consent_transfer_sections",
    ]


def test_innovation_partnerships_file_number_is_conditional():
    request = request_for("chemical")
    request["erpm_intake"]["previously_invention_report_or_licensed"] = True

    result = evaluate_intake_readiness(request)

    assert result["status"] == "missing_information"
    assert result["missing_fields"] == ["innovation_partnerships_file_number"]
