import json
from pathlib import Path

import pytest

from src.adapters.signnow_package_sender import SignNowPackageSender
from src.pipeline.models import RenderedAgreement
from src.pipeline.ports import DeliveryError
from tests.fixtures import request_for


def artifact(tmp_path: Path, template_id: str) -> RenderedAgreement:
    path = tmp_path / f"{template_id}.docx"
    path.write_bytes(b"populated agreement")
    return RenderedAgreement(template_id=template_id, path=path)


@pytest.mark.parametrize("template_id", ["chemical_material_agreement", "animal_material_agreement"])
def test_autm_package_has_only_recipient_side_signer(
    tmp_path: Path, template_id: str
):
    sender = SignNowPackageSender(tmp_path / "signing")
    category = "chemical" if template_id == "chemical_material_agreement" else "animal_derived"

    request = request_for(category)
    request["tracking_reference"] = "MTA-2026-7F3A91C2"
    receipt = sender.send("REQ/AUTM", request, artifact(tmp_path, template_id))

    manifest_path = Path(receipt.reference)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert receipt.status == "prepared_for_signature"
    assert receipt.mode == "signnow_package"
    assert manifest_path.name == "MTA-2026-7F3A91C2.signing.json"
    assert manifest["tracking_reference"] == "MTA-2026-7F3A91C2"
    assert manifest["document"]["name"].startswith("MTA-2026-7F3A91C2 — ")
    assert manifest["live_submission"] is False
    assert manifest["audit_events"] == [
        "auto_approved:standard_rules",
        "agreement_rendered",
        "signing_package_prepared",
    ]
    assert [signer["order"] for signer in manifest["signers"]] == [1]
    assert [signer["roles"] for signer in manifest["signers"]] == [
        ["recipient_authorized_signatory"],
    ]
    assert manifest["signers"][0]["email"] == "recipient.official@example.org"
    assert manifest["document"]["sha256"]
    assert "agreement_information" not in json.dumps(manifest)


def test_ubmta_package_assigns_visible_signature_roles_and_order(tmp_path: Path):
    sender = SignNowPackageSender(tmp_path / "signing")

    receipt = sender.send(
        "REQ-UBMTA",
        request_for("biological"),
        artifact(tmp_path, "biological_material_agreement"),
    )

    manifest = json.loads(Path(receipt.reference).read_text(encoding="utf-8"))
    assert [signer["roles"] for signer in manifest["signers"]] == [
        ["recipient_scientist"],
        ["recipient_organization_certifier"],
    ]
    assert [signer["order"] for signer in manifest["signers"]] == [1, 1]


def test_ubmta_package_excludes_prefilled_provider_side_signer(tmp_path: Path):
    request = request_for("biological")
    sender = SignNowPackageSender(tmp_path / "signing")

    receipt = sender.send(
        "REQ-RECIPIENT-SIGNERS",
        request,
        artifact(tmp_path, "biological_material_agreement"),
    )

    manifest = json.loads(Path(receipt.reference).read_text(encoding="utf-8"))
    assert manifest["signers"][0]["title"] == "Associate Professor"
    assert manifest["signers"][1]["title"] == "Director of Research Agreements"
    assert all(
        "provider" not in role
        for signer in manifest["signers"]
        for role in signer["roles"]
    )


def test_missing_recipient_signer_data_does_not_write_manifest(tmp_path: Path):
    request = request_for("chemical")
    request["agreement_information"]["recipient_authorized_official_email"] = ""
    output_dir = tmp_path / "signing"
    sender = SignNowPackageSender(output_dir)

    with pytest.raises(DeliveryError, match="recipient_authorized_official_email"):
        sender.send("REQ-NO-SIGNER", request, artifact(tmp_path, "chemical_material_agreement"))

    assert not output_dir.exists()


def test_missing_signer_error_reports_every_missing_identity_field(tmp_path: Path):
    request = request_for("chemical")
    information = request["agreement_information"]
    information["recipient_authorized_official_email"] = ""
    sender = SignNowPackageSender(tmp_path / "signing")

    with pytest.raises(DeliveryError) as caught:
        sender.send("REQ-MISSING-SIGNERS", request, artifact(tmp_path, "chemical_material_agreement"))

    assert "recipient_authorized_official_email" in str(caught.value)


def test_simple_letter_package_matches_visible_signature_roles(tmp_path: Path):
    sender = SignNowPackageSender(tmp_path / "signing")

    receipt = sender.send(
        "REQ-SIMPLE",
        request_for("device"),
        artifact(tmp_path, "device_material_agreement"),
    )

    manifest = json.loads(Path(receipt.reference).read_text(encoding="utf-8"))
    assert [signer["roles"] for signer in manifest["signers"]] == [
        ["recipient_scientist"],
        ["recipient_authorized_signatory"],
    ]
    assert [signer["order"] for signer in manifest["signers"]] == [1, 1]


def test_simple_letter_ignores_stale_recipient_scientist_title(tmp_path: Path):
    request = request_for("device")
    request["agreement_information"]["recipient_scientist_title"] = "Stale title"
    sender = SignNowPackageSender(tmp_path / "signing")

    receipt = sender.send(
        "REQ-SIMPLE-STALE",
        request,
        artifact(tmp_path, "device_material_agreement"),
    )

    manifest = json.loads(Path(receipt.reference).read_text(encoding="utf-8"))
    assert manifest["signers"][0]["title"] == ""


def test_unsupported_template_does_not_write_manifest(tmp_path: Path):
    output_dir = tmp_path / "signing"
    sender = SignNowPackageSender(output_dir)

    with pytest.raises(DeliveryError, match="Unsupported signing workflow"):
        sender.send(
            "REQ-SIMPLE",
            request_for("biological"),
            artifact(tmp_path, "unknown_template"),
        )

    assert not output_dir.exists()
