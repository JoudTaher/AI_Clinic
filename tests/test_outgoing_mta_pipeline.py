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


def test_mixed_material_request_routes_to_erpm_before_rendering():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("biological", "chemical")

    result = pipeline.run("REQ-1", request)

    assert result.status == "routed_to_erpm"
    assert renderer.calls == 0
    assert sender.calls == 0


def test_empty_request_id_is_rejected_before_processing():
    pipeline, renderer, sender = pipeline_with_recorders()

    result = pipeline.run("   ", request_for("chemical"))

    assert result.status == "invalid_request"
    assert "request_id" in result.reasons
    assert renderer.calls == 0
    assert sender.calls == 0


def test_standard_request_is_auto_approved_and_prepared():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    result = pipeline.run("REQ-2", request)

    assert result.status == "prepared_for_delivery"
    assert result.selected_template == "autm_chemical"
    assert "auto_approved:standard_rules" in result.audit_events
    assert renderer.calls == 1
    assert sender.calls == 1


def test_agreement_readiness_review_stops_before_rendering():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")
    request["agreement_information"]["material_provided_at_no_cost"] = False

    result = pipeline.run("REQ-REVIEW", request)

    assert result.status == "routed_to_erpm"
    assert any("cost_terms_require_review" in reason for reason in result.reasons)
    assert renderer.calls == 0
    assert sender.calls == 0


def test_auto_selected_request_is_rendered_and_prepared_for_delivery():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    result = pipeline.run("REQ-4", request)

    assert result.status == "prepared_for_delivery"
    assert result.artifact_path == "/tmp/REQ-4-autm_chemical.docx"
    assert result.delivery_reference == "dry-run:REQ-4"
    assert "auto_approved:standard_rules" in result.audit_events
    assert renderer.calls == 1
    assert sender.calls == 1


def test_completed_request_id_is_idempotent():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    first = pipeline.run("REQ-5", request)
    second = pipeline.run("REQ-5", request)

    assert second == first
    assert renderer.calls == 1
    assert sender.calls == 1


def test_reused_request_id_with_changed_data_is_rejected():
    pipeline, renderer, sender = pipeline_with_recorders()
    original = request_for("chemical")
    changed = request_for("chemical")
    changed["agreement_information"]["material_description"] = "Different material"
    pipeline.run("REQ-6", original)

    result = pipeline.run("REQ-6", changed)

    assert result.status == "idempotency_conflict"
    assert renderer.calls == 1
    assert sender.calls == 1


def test_delivery_adapter_failure_is_reported_without_marking_complete():
    renderer = RecordingRenderer()
    sender = FailingSender()
    pipeline = OutgoingMTAPipeline(renderer, sender)

    result = pipeline.run("REQ-FAIL", request_for("chemical"))

    assert result.status == "delivery_failed"
    assert result.reasons == ("delivery provider unavailable",)
    assert "delivery_failed" in result.audit_events
    assert renderer.calls == 1
    assert sender.calls == 1
