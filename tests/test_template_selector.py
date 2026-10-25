from src.template_selector import evaluate_template_selection
from tests.fixtures import request_for


def test_ineligible_request_has_no_template_selection():
    result = evaluate_template_selection(request_for("biological"), {"status": "ineligible"})
    assert result["status"] == "not_applicable"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == []


def test_eligible_chemical_request_reports_candidate_without_selecting():
    result = evaluate_template_selection(request_for("chemical"), {"status": "eligible"})
    assert result["status"] == "recommendation_ready"
    assert result["selected_template"] is None
    assert result["recommended_template"] == "autm_chemical"
    assert result["candidate_templates"] == ["autm_chemical"]
    assert "source_path" not in result["candidate_details"][0]
    assert result["candidate_details"][0]["source_file"] == (
        "Template_AUTM_MTA_for_Chemical_Materials.docx"
    )


def test_eligible_biological_request_reports_three_candidates():
    result = evaluate_template_selection(request_for("biological"), {"status": "eligible"})
    assert result["status"] == "template_selection_requires_review"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == [
        "autm_biological",
        "simple_letter_agreement",
        "ubmta_implementing_letter",
    ]


def test_biological_request_recommends_ubmta_for_a_signatory():
    request = request_for("biological")
    request["template_context"] = {
        "recipient_ubmta_signatory": True,
        "simple_letter_authorized": False,
    }

    result = evaluate_template_selection(request, {"status": "eligible"})

    assert result["status"] == "recommendation_ready"
    assert result["recommended_template"] == "ubmta_implementing_letter"
    assert result["candidate_templates"] == ["ubmta_implementing_letter"]


def test_biological_request_recommends_simple_letter_when_authorized():
    request = request_for("biological")
    request["template_context"] = {
        "recipient_ubmta_signatory": False,
        "simple_letter_authorized": True,
    }

    result = evaluate_template_selection(request, {"status": "eligible"})

    assert result["status"] == "recommendation_ready"
    assert result["recommended_template"] == "simple_letter_agreement"


def test_biological_request_recommends_autm_when_both_qualifiers_are_false():
    request = request_for("biological")
    request["template_context"] = {
        "recipient_ubmta_signatory": False,
        "simple_letter_authorized": False,
    }

    result = evaluate_template_selection(request, {"status": "eligible"})

    assert result["status"] == "recommendation_ready"
    assert result["recommended_template"] == "autm_biological"


def test_conflicting_biological_qualifiers_require_manual_review():
    request = request_for("biological")
    request["template_context"] = {
        "recipient_ubmta_signatory": True,
        "simple_letter_authorized": True,
    }

    result = evaluate_template_selection(request, {"status": "eligible"})

    assert result["status"] == "template_selection_requires_review"
    assert result["recommended_template"] is None
    assert result["candidate_templates"] == [
        "simple_letter_agreement",
        "ubmta_implementing_letter",
    ]
    assert any("conflicting" in reason.lower() for reason in result["review_reasons"])


def test_device_only_request_reports_no_candidate():
    result = evaluate_template_selection(request_for("device"), {"status": "eligible"})
    assert result["status"] == "template_selection_requires_review"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == []
    assert result["recommended_template"] is None


def test_mixed_request_never_selects_candidate():
    result = evaluate_template_selection(
        request_for("chemical", "biological"), {"status": "eligible"}
    )
    assert result["status"] == "template_selection_requires_review"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == [
        "autm_chemical",
        "autm_biological",
        "simple_letter_agreement",
        "ubmta_implementing_letter",
    ]


def test_malformed_material_categories_fail_closed_instead_of_crashing():
    request = request_for("chemical")
    request["material_categories"] = [{"invalid": True}]

    result = evaluate_template_selection(request, {"status": "eligible"})

    assert result["status"] == "template_selection_requires_review"
    assert result["recommended_template"] is None
    assert result["candidate_templates"] == []
    assert any("non-empty strings" in reason for reason in result["review_reasons"])
