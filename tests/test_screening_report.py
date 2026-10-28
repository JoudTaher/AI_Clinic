import json

from src.screening_report import build_screening_report, serialize_screening_report
from tests.fixtures import human_samples_request, plasmid_request, verified_facts_for


def test_report_contains_separate_decisions():
    request = plasmid_request()
    request["erpm_intake"] = {"project_title": "Synthetic plasmid transfer"}
    report = build_screening_report(request)
    assert report["proof_of_concept"] is True
    assert set(report) == {
        "proof_of_concept",
        "disclaimer",
        "delivery_policy",
        "erpm_intake",
        "agreement_information",
        "intake_readiness",
        "eligibility",
        "agreement_readiness",
        "input_usage",
        "template_selection",
    }
    assert report["erpm_intake"] == {"project_title": "Synthetic plasmid transfer"}
    assert "recipient_institution_name" in report["agreement_information"]
    assert report["intake_readiness"]["status"] == "missing_information"
    assert report["delivery_policy"] == {
        "internal_approval_required": False,
        "delivery_mode": "signnow_package",
        "live_delivery_enabled": False,
        "manual_special_case_route": "eRPM",
    }
    assert report["eligibility"]["status"] == "needs_review"
    assert report["template_selection"]["status"] == "manual_special_case_review"
    assert report["template_selection"]["selected_template"] is None


def test_human_samples_failure_is_preserved():
    report = build_screening_report(human_samples_request())
    failed = [entry["field_id"] for entry in report["eligibility"]["failed_checks"]]
    assert report["eligibility"]["status"] == "ineligible"
    assert "no_human_subjects_materials_or_data" in failed


def test_report_uses_the_same_trusted_backend_facts_as_the_pipeline():
    report = build_screening_report(
        plasmid_request(), verified_facts=verified_facts_for("biological")
    )

    assert report["eligibility"]["status"] == "eligible"
    assert report["template_selection"]["selected_template"] == (
        "ubmta_implementing_letter"
    )


def test_serialized_report_is_valid_deterministic_json():
    report = build_screening_report(plasmid_request())
    serialized = serialize_screening_report(report)
    assert json.loads(serialized) == report
    assert serialized.endswith("\n")
    assert "live submission" in serialized.lower()
    assert "legal approval" not in serialized.lower()
