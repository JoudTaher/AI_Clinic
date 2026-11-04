from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pytest

from src.adapters.docx_renderer import DocxAgreementRenderer
from src.adapters.signnow_api_sender import (
    SignNowApiSender,
    SignNowSettings,
)
from src.pipeline.ports import DeliveryError
from src.templates.catalog import load_template_catalog
from tests.fixtures import request_for


ROLE_NAMES = {
    "provider_authorized_signatory": "Provider Authorized Signatory",
    "recipient_authorized_signatory": "Recipient Authorized Signatory",
    "provider_organization_certifier": "Provider Organization Certifier",
    "recipient_scientist": "Recipient Scientist",
    "recipient_organization_certifier": "Recipient Organization Certifier",
}


class RecordingTransport:
    def __init__(self, roles: list[str]) -> None:
        self.roles = roles
        self.uploads: list[dict[str, Any]] = []
        self.requests: list[dict[str, Any]] = []

    def upload(
        self,
        path: str,
        file_path: Path,
        fields: Mapping[str, str],
    ) -> Mapping[str, Any]:
        with ZipFile(file_path) as archive:
            document_xml = archive.read("word/document.xml").decode("utf-8")
        self.uploads.append(
            {
                "path": path,
                "filename": file_path.name,
                "fields": dict(fields),
                "document_xml": document_xml,
            }
        )
        return {"id": "document-123"}

    def request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        self.requests.append(
            {"method": method, "path": path, "payload": dict(payload or {})}
        )
        if method == "GET":
            return {
                "roles": [
                    {"name": role, "unique_id": f"role-{index}"}
                    for index, role in enumerate(self.roles, start=1)
                ]
            }
        return {"status": "success"}


def rendered_agreement(tmp_path: Path, category: str):
    request = request_for(category)
    template_by_category = {
        "chemical": "autm_chemical",
        "biological": "ubmta_implementing_letter",
        "device": "simple_letter_agreement",
    }
    template_id = template_by_category[category]
    template = next(
        item for item in load_template_catalog() if item.template_id == template_id
    )
    artifact = DocxAgreementRenderer(tmp_path / "agreements").render(
        "REQ-API", template, request
    )
    return request, artifact


def settings(**overrides: Any) -> SignNowSettings:
    values = {
        "enabled": True,
        "api_key": "development-secret",
        "account_email": "mta-sender@umich.edu",
        "base_url": "https://api.signnow.test",
    }
    values.update(overrides)
    return SignNowSettings(**values)


def test_disabled_sender_refuses_network_delivery(tmp_path: Path):
    request, artifact = rendered_agreement(tmp_path, "chemical")
    transport = RecordingTransport(list(ROLE_NAMES.values()))
    sender = SignNowApiSender(settings(enabled=False), transport)

    with pytest.raises(DeliveryError, match="not enabled"):
        sender.send("REQ-DISABLED", request, artifact)

    assert transport.uploads == []
    assert transport.requests == []


@pytest.mark.parametrize("missing_field", ["api_key", "account_email"])
def test_missing_credentials_fail_before_upload(tmp_path: Path, missing_field: str):
    request, artifact = rendered_agreement(tmp_path, "chemical")
    transport = RecordingTransport(list(ROLE_NAMES.values()))
    sender = SignNowApiSender(settings(**{missing_field: ""}), transport)

    with pytest.raises(DeliveryError, match=missing_field):
        sender.send("REQ-MISSING", request, artifact)

    assert transport.uploads == []


def test_autm_uploads_tagged_copy_and_sends_ordered_field_invite(tmp_path: Path):
    request, artifact = rendered_agreement(tmp_path, "chemical")
    roles = [
        ROLE_NAMES["recipient_authorized_signatory"],
        ROLE_NAMES["provider_authorized_signatory"],
    ]
    transport = RecordingTransport(roles)
    sender = SignNowApiSender(settings(), transport)

    receipt = sender.send("REQ-AUTM", request, artifact)

    assert receipt.status == "sent_for_signature"
    assert receipt.mode == "signnow_development"
    assert receipt.reference == "document-123"
    assert artifact.path.is_file()
    original_xml = ZipFile(artifact.path).read("word/document.xml").decode("utf-8")
    assert "{{provider_authorized_signatory_signature}}" not in original_xml

    upload = transport.uploads[0]
    assert upload["path"] == "/document/fieldextract"
    assert "{{provider_authorized_signatory_signature}}" in upload["document_xml"]
    assert "{{recipient_authorized_signatory_date}}" in upload["document_xml"]
    tag_definitions = json.loads(upload["fields"]["Tags"])
    assert {item["role"] for item in tag_definitions} == set(roles)
    assert {item["type"] for item in tag_definitions} == {"signature", "text"}

    assert transport.requests[0] == {
        "method": "GET",
        "path": "/document/document-123",
        "payload": {},
    }
    invite = transport.requests[1]
    assert invite["method"] == "POST"
    assert invite["path"] == "/document/document-123/invite"
    assert invite["payload"]["from"] == "mta-sender@umich.edu"
    assert [item["email"] for item in invite["payload"]["to"]] == [
        "recipient.official@example.org",
        "provider.scientist@umich.edu",
    ]
    assert [item["order"] for item in invite["payload"]["to"]] == [1, 2]
    assert [item["role_id"] for item in invite["payload"]["to"]] == [
        "role-1",
        "role-2",
    ]


@pytest.mark.parametrize(
    ("category", "expected_roles"),
    [
        (
            "biological",
            [
                "Recipient Scientist",
                "Recipient Organization Certifier",
                "Provider Organization Certifier",
            ],
        ),
        (
            "device",
            [
                "Recipient Scientist",
                "Recipient Authorized Signatory",
                "Provider Authorized Signatory",
            ],
        ),
    ],
)
def test_each_template_uses_its_own_signature_roles(
    tmp_path: Path, category: str, expected_roles: list[str]
):
    request, artifact = rendered_agreement(tmp_path, category)
    transport = RecordingTransport(expected_roles)
    sender = SignNowApiSender(settings(), transport)

    sender.send(f"REQ-{category}", request, artifact)

    tags = json.loads(transport.uploads[0]["fields"]["Tags"])
    assert {item["role"] for item in tags} == set(expected_roles)
    if category == "device":
        assert "Signature of Authorized" in transport.uploads[0]["document_xml"]
    invite_roles = [item["role"] for item in transport.requests[-1]["payload"]["to"]]
    assert invite_roles == expected_roles


def test_missing_signnow_role_stops_before_invitation(tmp_path: Path):
    request, artifact = rendered_agreement(tmp_path, "chemical")
    transport = RecordingTransport(["Recipient Authorized Signatory"])
    sender = SignNowApiSender(settings(), transport)

    with pytest.raises(DeliveryError, match="Provider Authorized Signatory"):
        sender.send("REQ-ROLE-MISSING", request, artifact)

    assert not any(item["method"] == "POST" for item in transport.requests)


def test_settings_read_secrets_without_exposing_key():
    result = SignNowSettings.from_sources(
        {
            "enabled": "true",
            "api_key": "top-secret",
            "account_email": "sender@umich.edu",
            "base_url": "https://api.signnow.com/",
        },
        {},
    )

    assert result.enabled is True
    assert result.api_key == "top-secret"
    assert result.base_url == "https://api.signnow.com"
    assert "top-secret" not in repr(result)
