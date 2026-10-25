from pathlib import Path

from src.pipeline.models import DeliveryReceipt, RenderedAgreement
from src.pipeline.outgoing_mta import OutgoingMTAPipeline
from src.pipeline.ports import DeliveryError
from tests.fixtures import request_for


class RecordingRenderer:
    def __init__(self) -> None:
        self.calls = 0

    def render(self, request_id, template, request):
        self.calls += 1
        return RenderedAgreement(
            template_id=template.template_id,
            path=Path(f"/tmp/{request_id}-{template.template_id}.docx"),
        )


class RecordingSender:
    def __init__(self) -> None:
        self.calls = 0

    def send(self, request_id, request, artifact):
        self.calls += 1
        return DeliveryReceipt(
            status="prepared_for_delivery",
            mode="dry_run",
            reference=f"dry-run:{request_id}",
        )


class FailingSender:
    def __init__(self) -> None:
        self.calls = 0

    def send(self, request_id, request, artifact):
        self.calls += 1
        raise DeliveryError("delivery provider unavailable")


def pipeline_with_recorders():
    renderer = RecordingRenderer()
    sender = RecordingSender()
    return OutgoingMTAPipeline(renderer, sender), renderer, sender


def test_ambiguous_template_stops_before_rendering():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("biological")

    result = pipeline.run("REQ-1", request)

    assert result.status == "manual_review_required"
    assert renderer.calls == 0
    assert sender.calls == 0


def test_empty_request_id_is_rejected_before_processing():
    pipeline, renderer, sender = pipeline_with_recorders()

    result = pipeline.run("   ", request_for("chemical"))

    assert result.status == "invalid_request"
    assert "request_id" in result.reasons
    assert renderer.calls == 0
    assert sender.calls == 0


def test_recommendation_requires_a_named_approver():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    result = pipeline.run("REQ-2", request)

    assert result.status == "approval_required"
    assert result.recommended_template == "autm_chemical"
    assert renderer.calls == 0
    assert sender.calls == 0


def test_approval_must_match_the_recommendation():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    result = pipeline.run(
        "REQ-3",
        request,
        approved_template_id="autm_biological",
        approved_by="Example Approver",
    )

    assert result.status == "approval_mismatch"
    assert renderer.calls == 0
    assert sender.calls == 0


def test_agreement_readiness_review_stops_before_rendering():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")
    request["agreement_information"]["material_provided_at_no_cost"] = False

    result = pipeline.run(
        "REQ-REVIEW",
        request,
        approved_template_id="autm_chemical",
        approved_by="Example Approver",
    )

    assert result.status == "manual_review_required"
    assert any("cost_terms_require_review" in reason for reason in result.reasons)
    assert renderer.calls == 0
    assert sender.calls == 0


def test_approved_request_is_rendered_and_prepared_for_delivery():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    result = pipeline.run(
        "REQ-4",
        request,
        approved_template_id="autm_chemical",
        approved_by="Example Approver",
    )

    assert result.status == "prepared_for_delivery"
    assert result.artifact_path == "/tmp/REQ-4-autm_chemical.docx"
    assert result.delivery_reference == "dry-run:REQ-4"
    assert "approved:Example Approver" in result.audit_events
    assert renderer.calls == 1
    assert sender.calls == 1


def test_completed_request_id_is_idempotent():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    first = pipeline.run(
        "REQ-5",
        request,
        approved_template_id="autm_chemical",
        approved_by="Example Approver",
    )
    second = pipeline.run(
        "REQ-5",
        request,
        approved_template_id="autm_chemical",
        approved_by="Example Approver",
    )

    assert second == first
    assert renderer.calls == 1
    assert sender.calls == 1


def test_reused_request_id_with_changed_data_is_rejected():
    pipeline, renderer, sender = pipeline_with_recorders()
    original = request_for("chemical")
    changed = request_for("chemical")
    changed["agreement_information"]["material_description"] = "Different material"
    pipeline.run(
        "REQ-6",
        original,
        approved_template_id="autm_chemical",
        approved_by="Example Approver",
    )

    result = pipeline.run(
        "REQ-6",
        changed,
        approved_template_id="autm_chemical",
        approved_by="Example Approver",
    )

    assert result.status == "idempotency_conflict"
    assert renderer.calls == 1
    assert sender.calls == 1


def test_delivery_adapter_failure_is_reported_without_marking_complete():
    renderer = RecordingRenderer()
    sender = FailingSender()
    pipeline = OutgoingMTAPipeline(renderer, sender)

    result = pipeline.run(
        "REQ-FAIL",
        request_for("chemical"),
        approved_template_id="autm_chemical",
        approved_by="Example Approver",
    )

    assert result.status == "delivery_failed"
    assert result.reasons == ("delivery provider unavailable",)
    assert "delivery_failed" in result.audit_events
    assert renderer.calls == 1
    assert sender.calls == 1
