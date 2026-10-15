from src.template_selector import evaluate_template_selection
from tests.fixtures import request_for


def test_ineligible_request_has_no_template_selection():
    result = evaluate_template_selection(request_for("biological"), {"status": "ineligible"})
    assert result["status"] == "not_applicable"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == []


def test_eligible_chemical_request_reports_candidate_without_selecting():
    result = evaluate_template_selection(request_for("chemical"), {"status": "eligible"})
    assert result["status"] == "template_selection_requires_review"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == ["autm_chemical"]


def test_eligible_biological_request_reports_three_candidates():
    result = evaluate_template_selection(request_for("biological"), {"status": "eligible"})
    assert result["status"] == "template_selection_requires_review"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == [
        "autm_biological",
        "simple_letter_agreement",
        "ubmta_implementing_letter",
    ]


def test_device_only_request_reports_no_candidate():
    result = evaluate_template_selection(request_for("device"), {"status": "eligible"})
    assert result["status"] == "template_selection_requires_review"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == []


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
