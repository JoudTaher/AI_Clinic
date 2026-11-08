from __future__ import annotations

import json
import mimetypes
import os
import re
import tempfile
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

from src.adapters.signnow_package_sender import SignNowPackageSender
from src.pipeline.models import DeliveryReceipt, RenderedAgreement
from src.pipeline.ports import DeliveryError
from src.request_normalization import normalize_request


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}
ROLE_NAMES = {
    "provider_authorized_signatory": "Provider Authorized Signatory",
    "recipient_authorized_signatory": "Recipient Authorized Signatory",
    "provider_organization_certifier": "Provider Organization Certifier",
    "recipient_scientist": "Recipient Scientist",
    "recipient_organization_certifier": "Recipient Organization Certifier",
}
TAG_PATTERN = re.compile(r"^[a-z0-9_]+$")


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class SignNowSettings:
    enabled: bool = False
    api_key: str = field(default="", repr=False)
    account_email: str = ""
    base_url: str = "https://api.signnow.com"
    timeout_seconds: float = 30.0

    @classmethod
    def from_sources(
        cls,
        secrets: Mapping[str, Any] | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> SignNowSettings:
        secret_values = secrets or {}
        env = environment if environment is not None else os.environ

        def value(secret_key: str, environment_key: str, default: object = "") -> object:
            candidate = secret_values.get(secret_key)
            if candidate is not None and str(candidate).strip():
                return candidate
            return env.get(environment_key, default)

        raw_timeout = value("timeout_seconds", "SIGNNOW_TIMEOUT_SECONDS", 30)
        try:
            timeout = float(raw_timeout)
        except (TypeError, ValueError):
            timeout = 30.0
        base_url = str(
            value("base_url", "SIGNNOW_BASE_URL", "https://api.signnow.com")
        ).strip().rstrip("/")
        return cls(
            enabled=_truthy(value("enabled", "SIGNNOW_SEND_ENABLED", False)),
            api_key=str(value("api_key", "SIGNNOW_API_KEY")).strip(),
            account_email=str(
                value("account_email", "SIGNNOW_ACCOUNT_EMAIL")
            ).strip(),
            base_url=base_url or "https://api.signnow.com",
            timeout_seconds=timeout if timeout > 0 else 30.0,
        )


class SignNowTransport(Protocol):
    def upload(
        self,
        path: str,
        file_path: Path,
        fields: Mapping[str, str],
    ) -> Mapping[str, Any]: ...

    def request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]: ...


def _signnow_error_detail(error: HTTPError) -> str:
    try:
        payload = json.loads(error.read().decode("utf-8"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return ""
    if not isinstance(payload, Mapping):
        return ""

    candidates: list[Mapping[str, Any]] = []
    raw_errors = payload.get("errors")
    if isinstance(raw_errors, list):
        candidates.extend(item for item in raw_errors if isinstance(item, Mapping))
    candidates.append(payload)

    for candidate in candidates:
        message = next(
            (
                str(candidate[key]).strip()
                for key in ("message", "error", "description")
                if candidate.get(key) is not None and str(candidate[key]).strip()
            ),
            "",
        )
        if not message:
            continue
        code = candidate.get("code")
        code_text = f" (code {code})" if code is not None else ""
        return f"{message[:300]}{code_text}."
    return ""


class UrllibSignNowTransport:
    def __init__(self, settings: SignNowSettings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.settings.api_key}",
        }

    def _execute(self, request: Request) -> Mapping[str, Any]:
        try:
            with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                payload = response.read()
        except HTTPError as error:
            method = request.get_method()
            path = urlsplit(request.full_url).path
            detail = _signnow_error_detail(error)
            suffix = f" {detail}" if detail else ""
            raise DeliveryError(
                f"SignNow rejected {method} {path} with HTTP {error.code}.{suffix}"
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise DeliveryError("SignNow could not be reached.") from error
        if not payload:
            return {}
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise DeliveryError("SignNow returned an unreadable response.") from error
        if not isinstance(decoded, Mapping):
            raise DeliveryError("SignNow returned an unexpected response.")
        return decoded

    def upload(
        self,
        path: str,
        file_path: Path,
        fields: Mapping[str, str],
    ) -> Mapping[str, Any]:
        boundary = f"signnow-{uuid.uuid4().hex}"
        chunks: list[bytes] = []
        for name, value in fields.items():
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode(),
                    (
                        f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                    ).encode(),
                    value.encode("utf-8"),
                    b"\r\n",
                ]
            )
        content_type = mimetypes.guess_type(file_path.name)[0] or (
            "application/octet-stream"
        )
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    'Content-Disposition: form-data; name="file"; '
                    f'filename="{file_path.name}"\r\n'
                ).encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                file_path.read_bytes(),
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )
        headers = self._headers()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        request = Request(
            f"{self.settings.base_url}{path}",
            data=b"".join(chunks),
            headers=headers,
            method="POST",
        )
        return self._execute(request)

    def request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        headers = self._headers()
        data = None
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self.settings.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        return self._execute(request)


def _paragraph_text(paragraph: etree._Element) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


def _set_paragraph_text(paragraph: etree._Element, text: str) -> None:
    nodes = paragraph.xpath(".//w:t", namespaces=NS)
    if nodes:
        nodes[0].text = text
        for node in nodes[1:]:
            node.text = ""
        return
    run = etree.SubElement(paragraph, f"{{{WORD_NS}}}r")
    node = etree.SubElement(run, f"{{{WORD_NS}}}t")
    node.text = text


def _tag(role: str, field_type: str) -> str:
    name = f"{role}_{field_type}"
    if not TAG_PATTERN.fullmatch(name):
        raise DeliveryError("The SignNow tag name is invalid.")
    return f"{{{{{name}}}}}"


class TaggedAgreementBuilder:
    def build(
        self,
        artifact: RenderedAgreement,
        destination: Path,
        role_aliases: Mapping[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        aliases = role_aliases or {}
        with ZipFile(artifact.path) as source:
            root = etree.fromstring(source.read("word/document.xml"))
            roles = self._insert_tags(root, artifact.template_id)
            document_xml = etree.tostring(
                root, xml_declaration=True, encoding="UTF-8", standalone=True
            )
            with ZipFile(destination, "w", compression=ZIP_DEFLATED) as target:
                for item in source.infolist():
                    target.writestr(
                        item,
                        document_xml
                        if item.filename == "word/document.xml"
                        else source.read(item.filename),
                    )
        definitions: list[dict[str, Any]] = []
        for role in roles:
            display_role = ROLE_NAMES[aliases.get(role, role)]
            definitions.extend(
                [
                    {
                        "tag_name": f"{role}_signature",
                        "role": display_role,
                        "required": True,
                        "type": "signature",
                        "height": 30,
                        "width": 180,
                    },
                    {
                        "tag_name": f"{role}_date",
                        "role": display_role,
                        "label": "Date",
                        "required": True,
                        "type": "text",
                        "height": 20,
                        "width": 90,
                    },
                ]
            )
        return definitions

    def _insert_tags(self, root: etree._Element, template_id: str) -> list[str]:
        if template_id in {"chemical_material_agreement", "animal_material_agreement"}:
            return self._insert_autm(root)
        if template_id == "biological_material_agreement":
            return self._insert_ubmta(root)
        if template_id == "device_material_agreement":
            return self._insert_simple_letter(root)
        raise DeliveryError(f"Unsupported SignNow template: {template_id}")

    @staticmethod
    def _insert_autm(root: etree._Element) -> list[str]:
        for table in root.xpath(".//w:tbl", namespaces=NS):
            table_text = " ".join(
                table.xpath(".//w:t/text()", namespaces=NS)
            )
            if "Provider Authorized Signatory" not in table_text:
                continue
            rows = table.xpath("./w:tr", namespaces=NS)
            for column, role in enumerate(
                ("provider_authorized_signatory", "recipient_authorized_signatory")
            ):
                for row_index, field_type in ((1, "signature"), (4, "date")):
                    cells = rows[row_index].xpath("./w:tc", namespaces=NS)
                    paragraphs = cells[column].xpath("./w:p", namespaces=NS)
                    target = paragraphs[0]
                    _set_paragraph_text(target, _tag(role, field_type))
            return [
                "provider_authorized_signatory",
                "recipient_authorized_signatory",
            ]
        raise DeliveryError("The AUTM signing table could not be located.")

    @staticmethod
    def _insert_ubmta(root: etree._Element) -> list[str]:
        roles = [
            "provider_organization_certifier",
            "recipient_scientist",
            "recipient_organization_certifier",
        ]
        active_role: str | None = None
        seen: set[tuple[str, str]] = set()
        for paragraph in root.xpath(".//w:body/w:p", namespaces=NS):
            text = _paragraph_text(paragraph).strip()
            upper = text.upper()
            if upper == "PROVIDER ORGANIZATION CERTIFICATION":
                active_role = roles[0]
            elif upper == "RECIPIENT SCIENTIST":
                active_role = roles[1]
            elif upper == "RECIPIENT ORGANIZATION CERTIFICATION":
                active_role = roles[2]
            elif active_role and text.startswith("Signature:"):
                _set_paragraph_text(
                    paragraph, f"   Signature:\t{_tag(active_role, 'signature')}"
                )
                seen.add((active_role, "signature"))
            elif active_role and text.startswith("Date:"):
                _set_paragraph_text(paragraph, f"   Date:\t\t{_tag(active_role, 'date')}")
                seen.add((active_role, "date"))
        expected = {(role, kind) for role in roles for kind in ("signature", "date")}
        if seen != expected:
            raise DeliveryError("The UBMTA signing lines could not be located.")
        return roles

    @staticmethod
    def _insert_simple_letter(root: etree._Element) -> list[str]:
        provider_role = "provider_authorized_signatory"
        scientist_role = "recipient_scientist"
        line_paragraphs = [
            paragraph
            for paragraph in root.xpath(".//w:body/w:p", namespaces=NS)
            if "______________________________________" in _paragraph_text(paragraph)
        ]
        if len(line_paragraphs) != 2:
            raise DeliveryError("The Simple Letter signature lines could not be located.")
        for paragraph, role in zip(
            line_paragraphs, (provider_role, scientist_role), strict=True
        ):
            _set_paragraph_text(
                paragraph,
                f"        {_tag(role, 'signature')}\t\t{_tag(role, 'date')}",
            )

        official_role = "recipient_authorized_signatory"
        official_found = False
        for row in root.xpath(".//w:tr", namespaces=NS):
            cells = row.xpath("./w:tc", namespaces=NS)
            if len(cells) < 2 or "Signature of Authorized" not in " ".join(
                row.xpath(".//w:t/text()", namespaces=NS)
            ):
                continue
            paragraphs = cells[-1].xpath("./w:p", namespaces=NS)
            if paragraphs:
                _set_paragraph_text(
                    paragraphs[0],
                    f"{_tag(official_role, 'signature')}  {_tag(official_role, 'date')}",
                )
                official_found = True
                break
        if not official_found:
            raise DeliveryError(
                "The Simple Letter authorized-official signing line could not be located."
            )
        return [provider_role, official_role, scientist_role]


def _document_id(payload: Mapping[str, Any]) -> str:
    for key in ("id", "document_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise DeliveryError("SignNow did not return a document ID.")


def _role_ids(payload: Mapping[str, Any]) -> dict[str, str]:
    raw_roles = payload.get("roles", payload.get("document_roles", []))
    if not isinstance(raw_roles, list):
        return {}
    result: dict[str, str] = {}
    for raw_role in raw_roles:
        if not isinstance(raw_role, Mapping):
            continue
        name = raw_role.get("name", raw_role.get("role"))
        identifier = raw_role.get(
            "unique_id", raw_role.get("id", raw_role.get("role_id"))
        )
        if isinstance(name, str) and isinstance(identifier, str):
            result[name] = identifier
    return result


class SignNowApiSender:
    def __init__(
        self,
        settings: SignNowSettings,
        transport: SignNowTransport | None = None,
        builder: TaggedAgreementBuilder | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport or UrllibSignNowTransport(settings)
        self.builder = builder or TaggedAgreementBuilder()

    def _validate_configuration(self) -> None:
        if not self.settings.enabled:
            raise DeliveryError("SignNow API sending is not enabled.")
        if not self.settings.api_key:
            raise DeliveryError("SignNow configuration is missing api_key.")
        if not self.settings.account_email:
            raise DeliveryError("SignNow configuration is missing account_email.")

    def send(
        self,
        submission_id: str,
        request: Mapping[str, Any],
        artifact: RenderedAgreement,
    ) -> DeliveryReceipt:
        del submission_id
        self._validate_configuration()
        if not artifact.path.is_file():
            raise DeliveryError(f"Agreement artifact does not exist: {artifact.path}")
        normalized = normalize_request(request)
        information = normalized.get("agreement_information", {})
        if not isinstance(information, Mapping):
            raise DeliveryError("agreement_information must be an object")
        signers = SignNowPackageSender(Path(".")).signers_for(
            artifact.template_id, information
        )
        role_aliases: dict[str, str] = {}
        for signer in signers:
            raw_roles = signer.get("roles", [])
            if not isinstance(raw_roles, list) or not raw_roles:
                raise DeliveryError("The signer plan contains invalid roles.")
            if any(
                not isinstance(role, str) or role not in ROLE_NAMES
                for role in raw_roles
            ):
                raise DeliveryError("The signer plan contains an unknown role.")
            primary_role = raw_roles[0]
            role_aliases.update(
                {logical_role: primary_role for logical_role in raw_roles}
            )

        descriptor, temporary_name = tempfile.mkstemp(suffix=".docx")
        os.close(descriptor)
        tagged_path = Path(temporary_name)
        try:
            tag_definitions = self.builder.build(
                artifact, tagged_path, role_aliases=role_aliases
            )
            uploaded = self.transport.upload(
                "/document/fieldextract",
                tagged_path,
                {"Tags": json.dumps(tag_definitions, separators=(",", ":"))},
            )
        finally:
            tagged_path.unlink(missing_ok=True)

        document_id = _document_id(uploaded)
        document = self.transport.request_json(
            "GET", f"/document/{document_id}"
        )
        role_ids = _role_ids(document)

        invitees: list[dict[str, object]] = []
        for signer in signers:
            raw_roles = signer.get("roles", [])
            if not isinstance(raw_roles, list) or not raw_roles:
                raise DeliveryError("The signer plan contains invalid roles.")
            logical_role = raw_roles[0]
            if not isinstance(logical_role, str) or logical_role not in ROLE_NAMES:
                raise DeliveryError("The signer plan contains an unknown role.")
            role = ROLE_NAMES[logical_role]
            role_id = role_ids.get(role)
            if not role_id:
                raise DeliveryError(
                    f"SignNow did not create the required role: {role}."
                )
            invitees.append(
                {
                    "email": signer["email"],
                    "role": role,
                    "role_id": role_id,
                    "order": signer["order"],
                    "reassign": "0",
                    "decline_by_signature": "0",
                    "reminder": 0,
                    "expiration_days": 30,
                }
            )

        self.transport.request_json(
            "POST",
            f"/document/{document_id}/invite",
            {
                "document_id": document_id,
                "to": invitees,
                "from": self.settings.account_email,
                "cc": [],
            },
        )
        return DeliveryReceipt(
            status="sent_for_signature",
            mode="signnow_development",
            reference=document_id,
        )
