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


@pytest.mark.parametrize("template_id", ["autm_chemical", "autm_biological"])
def test_autm_package_has_recipient_then_delegated_pi_signers(
    tmp_path: Path, template_id: str
):
    sender = SignNowPackageSender(tmp_path / "signing")
    category = "chemical" if template_id == "autm_chemical" else "animal_derived"

    receipt = sender.send(
        "REQ/AUTM", request_for(category), artifact(tmp_path, template_id)
    )

    manifest_path = Path(receipt.reference)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert receipt.status == "prepared_for_signature"
    assert receipt.mode == "signnow_package"
    assert manifest_path.name == "REQ_AUTM.signing.json"
    assert manifest["live_submission"] is False
    assert manifest["audit_events"] == [
        "auto_approved:standard_rules",
        "agreement_rendered",
        "signing_package_prepared",
    ]
    assert [signer["order"] for signer in manifest["signers"]] == [1, 2]
    assert [signer["roles"] for signer in manifest["signers"]] == [
        ["recipient_authorized_signatory"],
        ["provider_authorized_signatory"],
    ]
    assert manifest["signers"][1]["email"] == "provider.scientist@umich.edu"
    assert manifest["document"]["sha256"]
    assert "agreement_information" not in json.dumps(manifest)


def test_ubmta_package_assigns_visible_signature_roles_and_order(tmp_path: Path):
    sender = SignNowPackageSender(tmp_path / "signing")

    receipt = sender.send(
        "REQ-UBMTA",
        request_for("biological"),
        artifact(tmp_path, "ubmta_implementing_letter"),
    )

    manifest = json.loads(Path(receipt.reference).read_text(encoding="utf-8"))
    assert [signer["roles"] for signer in manifest["signers"]] == [
        ["recipient_scientist"],
        ["recipient_organization_certifier"],
        ["provider_organization_certifier"],
    ]
    assert [signer["order"] for signer in manifest["signers"]] == [1, 1, 2]


def test_ubmta_combines_recipient_roles_when_scientist_can_certify(tmp_path: Path):
    request = request_for("biological")
    request["agreement_information"][
        "recipient_scientist_can_certify_organization"
    ] = True
    sender = SignNowPackageSender(tmp_path / "signing")

    receipt = sender.send(
        "REQ-UBMTA-ONE",
        request,
        artifact(tmp_path, "ubmta_implementing_letter"),
    )

    manifest = json.loads(Path(receipt.reference).read_text(encoding="utf-8"))
    assert manifest["signers"][0]["roles"] == [
        "recipient_scientist",
        "recipient_organization_certifier",
    ]
    assert manifest["signers"][0]["email"] == "recipient.scientist@example.org"
    assert len(manifest["signers"]) == 2


def test_missing_recipient_signer_data_does_not_write_manifest(tmp_path: Path):
    request = request_for("chemical")
    request["agreement_information"]["recipient_authorized_official_email"] = ""
    output_dir = tmp_path / "signing"
    sender = SignNowPackageSender(output_dir)

    with pytest.raises(DeliveryError, match="recipient_authorized_official_email"):
        sender.send("REQ-NO-SIGNER", request, artifact(tmp_path, "autm_chemical"))

    assert not output_dir.exists()


def test_simple_letter_package_matches_visible_signature_roles(tmp_path: Path):
    sender = SignNowPackageSender(tmp_path / "signing")

    receipt = sender.send(
        "REQ-SIMPLE",
        request_for("device"),
        artifact(tmp_path, "simple_letter_agreement"),
    )

    manifest = json.loads(Path(receipt.reference).read_text(encoding="utf-8"))
    assert [signer["roles"] for signer in manifest["signers"]] == [
        ["recipient_scientist"],
        ["recipient_authorized_signatory"],
        ["provider_authorized_signatory"],
    ]
    assert [signer["order"] for signer in manifest["signers"]] == [1, 1, 2]


def test_simple_letter_ignores_stale_recipient_scientist_title(tmp_path: Path):
    request = request_for("device")
    request["agreement_information"]["recipient_scientist_title"] = "Stale title"
    sender = SignNowPackageSender(tmp_path / "signing")

    receipt = sender.send(
        "REQ-SIMPLE-STALE",
        request,
        artifact(tmp_path, "simple_letter_agreement"),
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
