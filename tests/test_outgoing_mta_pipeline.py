from pathlib import Path

from src.pipeline.models import DeliveryReceipt, RenderedAgreement
from src.pipeline.outgoing_mta import OutgoingMTAPipeline
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
