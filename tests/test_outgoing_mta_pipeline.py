from pathlib import Path

from src.pipeline.models import DeliveryReceipt, RenderedAgreement
from src.pipeline.outgoing_mta import OutgoingMTAPipeline
from src.pipeline.ports import AgreementRenderError, DeliveryError
from tests.fixtures import request_for, verified_facts_for


class RecordingRenderer:
    def __init__(self) -> None:
        self.calls = 0

    def render(self, submission_id, template, request):
        self.calls += 1
        return RenderedAgreement(
            template_id=template.template_id,
            path=Path(f"/tmp/{submission_id}-{template.template_id}.docx"),
        )


class RecordingSender:
    def __init__(self) -> None:
        self.calls = 0
        self.last_request = None

    def send(self, submission_id, request, artifact):
        self.calls += 1
        self.last_request = request
        return DeliveryReceipt(
            status="prepared_for_signature",
            mode="signnow_package",
            reference=f"dry-run:{submission_id}",
        )


class FailingSender:
    def __init__(self) -> None:
        self.calls = 0

    def send(self, submission_id, request, artifact):
        self.calls += 1
        raise DeliveryError("delivery provider unavailable")


class FailingRenderer:
    def render(self, submission_id, template, request):
        raise AgreementRenderError("recipient signer data is incomplete")


def pipeline_with_recorders():
    renderer = RecordingRenderer()
    sender = RecordingSender()
    return (
        OutgoingMTAPipeline(
            renderer,
            sender,
            verified_facts=verified_facts_for(
                "chemical", "biological", "animal_derived", "device"
            ),
        ),
        renderer,
        sender,
    )


def test_mixed_material_request_routes_to_erpm_before_rendering():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("biological", "chemical")

    result = pipeline.run(request)

    assert result.status == "routed_to_erpm"
    assert renderer.calls == 0
    assert sender.calls == 0


def test_standard_request_is_auto_approved_and_prepared():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    result = pipeline.run(request)

    assert result.status == "prepared_for_signature"
    assert result.selected_template == "autm_chemical"
    assert result.submission_id.startswith("mta-")
    assert "auto_approved:standard_rules" in result.audit_events
    assert renderer.calls == 1
    assert sender.calls == 1


def test_no_cost_answer_does_not_change_automatic_approval():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")
    request["agreement_information"]["material_provided_at_no_cost"] = False

    result = pipeline.run(request)

    assert result.status == "prepared_for_signature"
    assert renderer.calls == 1
    assert sender.calls == 1


def test_missing_agreement_information_stops_after_template_selection():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")
    request["agreement_information"]["material_description"] = ""

    result = pipeline.run(request)

    assert result.status == "agreement_incomplete"
    assert result.selected_template == "autm_chemical"
    assert "material_description" in result.reasons
    assert renderer.calls == 0
    assert sender.calls == 0


def test_incomplete_requester_questionnaire_stops_before_eligibility():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")
    request["erpm_intake"]["project_title"] = ""

    result = pipeline.run(request)

    assert result.status == "intake_incomplete"
    assert "project_title" in result.reasons
    assert renderer.calls == 0
    assert sender.calls == 0


def test_auto_selected_request_is_rendered_and_prepared_for_signature():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    result = pipeline.run(request)

    assert result.status == "prepared_for_signature"
    assert result.delivery_mode == "signnow_package"
    assert result.submission_id in (result.artifact_path or "")
    assert result.delivery_reference == f"dry-run:{result.submission_id}"
    assert "auto_approved:standard_rules" in result.audit_events
    assert renderer.calls == 1
    assert sender.calls == 1


def test_identical_questionnaire_is_idempotent():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")

    first = pipeline.run(request)
    second = pipeline.run(request)

    assert second == first
    assert renderer.calls == 1
    assert sender.calls == 1


def test_changed_questionnaire_gets_a_different_submission_id():
    pipeline, renderer, sender = pipeline_with_recorders()
    original = request_for("chemical")
    changed = request_for("chemical")
    changed["agreement_information"]["material_description"] = "Different material"
    first = pipeline.run(original)

    result = pipeline.run(changed)

    assert result.status == "prepared_for_signature"
    assert result.submission_id != first.submission_id
    assert renderer.calls == 2
    assert sender.calls == 2


def test_malformed_questionnaire_material_types_fail_closed_without_crashing():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")
    request["erpm_intake"]["material_types"] = [{"invalid": True}]

    result = pipeline.run(request)

    assert result.status == "intake_incomplete"
    assert "material_types" in result.reasons
    assert renderer.calls == 0
    assert sender.calls == 0


def test_questionnaire_material_type_overrides_contradictory_derived_category():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")
    request["material_categories"] = ["device"]

    result = pipeline.run(request)

    assert result.status == "prepared_for_signature"
    assert result.selected_template == "autm_chemical"


def test_mixed_questionnaire_cannot_be_disguised_as_one_category():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical", "device")
    request["material_categories"] = ["chemical"]

    result = pipeline.run(request)

    assert result.status == "routed_to_erpm"
    assert renderer.calls == 0
    assert sender.calls == 0


def test_ambiguous_other_model_organism_routes_to_erpm():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("biological")
    request["erpm_intake"]["material_types"] = [
        "Other Model Organism (yeast, drosophila, zebrafish)"
    ]

    result = pipeline.run(request)

    assert result.status == "routed_to_erpm"
    assert renderer.calls == 0
    assert sender.calls == 0


def test_transmittal_fee_is_derived_from_questionnaire_reimbursement_value():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("biological")
    request["erpm_intake"]["reimbursement_cost_or_fee"] = "$100.00"
    request["agreement_information"]["transmittal_fee"] = "$999.00"

    result = pipeline.run(request)

    assert result.status == "prepared_for_signature"
    assert (
        sender.last_request["agreement_information"]["transmittal_fee"]
        == "$100.00"
    )


def test_provider_signer_name_is_derived_from_contact_pi():
    pipeline, renderer, sender = pipeline_with_recorders()
    request = request_for("chemical")
    request["erpm_intake"]["contact_pi_name"] = "Relevant PI"
    request["agreement_information"]["provider_scientist_name"] = "Different Person"

    result = pipeline.run(request)

    assert result.status == "prepared_for_signature"
    assert sender.last_request["agreement_information"]["provider_scientist_name"] == (
        "Relevant PI"
    )


def test_semantically_identical_questionnaires_share_submission_id():
    pipeline, renderer, sender = pipeline_with_recorders()
    original = request_for("chemical")
    original["erpm_intake"]["related_document_names"] = ["a.pdf", "b.pdf"]
    equivalent = request_for("chemical")
    equivalent["erpm_intake"]["project_title"] = "  Synthetic plasmid transfer  "
    equivalent["erpm_intake"]["related_document_names"] = ["b.pdf", "a.pdf"]

    first = pipeline.run(original)
    second = pipeline.run(equivalent)

    assert second.submission_id == first.submission_id
    assert renderer.calls == 1
    assert sender.calls == 1


def test_delivery_adapter_failure_is_reported_without_marking_complete():
    renderer = RecordingRenderer()
    sender = FailingSender()
    pipeline = OutgoingMTAPipeline(
        renderer,
        sender,
        verified_facts=verified_facts_for("chemical"),
    )

    result = pipeline.run(request_for("chemical"))

    assert result.status == "delivery_failed"
    assert result.reasons == ("delivery provider unavailable",)
    assert "delivery_failed" in result.audit_events
    assert renderer.calls == 1
    assert sender.calls == 1


def test_rendering_failure_is_reported_without_calling_sender():
    sender = RecordingSender()
    pipeline = OutgoingMTAPipeline(
        FailingRenderer(),
        sender,
        verified_facts=verified_facts_for("chemical"),
    )

    result = pipeline.run(request_for("chemical"))

    assert result.status == "generation_failed"
    assert result.reasons == ("recipient signer data is incomplete",)
    assert "agreement_generation_failed" in result.audit_events
    assert sender.calls == 0
