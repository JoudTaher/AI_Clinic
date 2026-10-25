import json
from pathlib import Path

from src.adapters.dry_run_sender import DryRunSender
from src.adapters.reference_renderer import ReferenceTemplateRenderer
from src.pipeline.models import RenderedAgreement
from src.templates.catalog import TemplateDefinition


def template_definition(source: Path) -> TemplateDefinition:
    return TemplateDefinition(
        template_id="example_template",
        display_name="Example Template",
        source_path=source,
        material_categories=("chemical",),
        required_context={},
    )


def test_renderer_copies_exact_template_bytes_with_a_safe_name(tmp_path: Path):
    source = tmp_path / "source.docx"
    source.write_bytes(b"exact-template-bytes")
    output_dir = tmp_path / "rendered"
    renderer = ReferenceTemplateRenderer(output_dir)

    artifact = renderer.render(
        "../../REQ 7", template_definition(source), {"material_categories": ["chemical"]}
    )

    assert artifact.path.parent == output_dir
    assert artifact.path.name == "REQ_7-example_template.docx"
    assert artifact.path.read_bytes() == source.read_bytes()


def test_dry_run_sender_writes_a_local_unsent_email_package(tmp_path: Path):
    agreement = tmp_path / "agreement.docx"
    agreement.write_bytes(b"agreement")
    sender = DryRunSender(tmp_path / "delivery")
    request = {
        "erpm_intake": {
            "project_title": "Synthetic transfer",
            "recipient_scientist_email": "recipient@example.org",
        }
    }

    receipt = sender.send(
        "REQ-8",
        request,
        RenderedAgreement(template_id="example_template", path=agreement),
    )

    package_path = Path(receipt.reference)
    package = json.loads(package_path.read_text(encoding="utf-8"))
    assert receipt.status == "prepared_for_delivery"
    assert receipt.mode == "dry_run"
    assert package == {
        "attachment": str(agreement),
        "delivery_mode": "dry_run",
        "request_id": "REQ-8",
        "sent": False,
        "subject": "Outgoing MTA: Synthetic transfer",
        "template_id": "example_template",
        "to": "recipient@example.org",
    }


def test_dry_run_sender_rejects_a_missing_recipient_email(tmp_path: Path):
    sender = DryRunSender(tmp_path / "delivery")
    artifact = RenderedAgreement(
        template_id="example_template", path=tmp_path / "agreement.docx"
    )

    try:
        sender.send("REQ-9", {}, artifact)
    except ValueError as error:
        assert "recipient_scientist_email" in str(error)
    else:
        raise AssertionError("Missing recipient email must stop delivery preparation")
