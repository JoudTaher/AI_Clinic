import json

from src.screening_report import build_screening_report, serialize_screening_report
from tests.fixtures import human_samples_request, plasmid_request


def test_report_contains_separate_decisions():
    report = build_screening_report(plasmid_request())
    assert report["proof_of_concept"] is True
    assert set(report) == {
        "proof_of_concept",
        "disclaimer",
        "eligibility",
        "agreement_readiness",
        "template_selection",
    }
    assert report["eligibility"]["status"] == "eligible"
    assert report["template_selection"]["selected_template"] is None


def test_human_samples_failure_is_preserved():
    report = build_screening_report(human_samples_request())
    failed = [entry["field_id"] for entry in report["eligibility"]["failed_checks"]]
    assert report["eligibility"]["status"] == "ineligible"
    assert "no_human_subjects_materials_or_data" in failed


def test_serialized_report_is_valid_deterministic_json():
    report = build_screening_report(plasmid_request())
    serialized = serialize_screening_report(report)
    assert json.loads(serialized) == report
    assert serialized.endswith("\n")
    assert "signed agreement" not in serialized.lower()
    assert "legal approval" in serialized.lower()
