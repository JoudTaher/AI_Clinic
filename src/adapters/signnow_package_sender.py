from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.adapters.paths import safe_identifier
from src.pipeline.models import DeliveryReceipt, RenderedAgreement
from src.pipeline.ports import DeliveryError
from src.signing.config import EMAIL_PATTERN, SigningConfiguration


class SignNowPackageSender:
    """Builds a local SignNow-ready manifest without making a network request."""

    _AUTM_TEMPLATES = {"autm_chemical", "autm_biological"}

    def __init__(self, output_dir: Path, configuration: SigningConfiguration) -> None:
        self.output_dir = output_dir
        self.configuration = configuration

    @staticmethod
    def _required_text(data: Mapping[str, Any], field_id: str) -> str:
        value = data.get(field_id)
        if not isinstance(value, str) or not value.strip():
            raise DeliveryError(f"Missing required signer field: {field_id}")
        return value.strip()

    @classmethod
    def _required_email(cls, data: Mapping[str, Any], field_id: str) -> str:
        value = cls._required_text(data, field_id)
        if not EMAIL_PATTERN.fullmatch(value):
            raise DeliveryError(f"Signer field must be a valid email: {field_id}")
        return value

    @classmethod
    def _person(
        cls,
        data: Mapping[str, Any],
        prefix: str,
        roles: list[str],
        order: int,
    ) -> dict[str, object]:
        return {
            "email": cls._required_email(data, f"{prefix}_email"),
            "name": cls._required_text(data, f"{prefix}_name"),
            "order": order,
            "roles": roles,
            "title": cls._required_text(data, f"{prefix}_title"),
        }

    def _provider_official(self, role: str) -> dict[str, object]:
        return {
            "email": self.configuration.um_signer_email,
            "name": self.configuration.um_signer_name,
            "order": 2,
            "roles": [role],
            "title": self.configuration.um_signer_title,
        }

    def _signers(
        self, template_id: str, information: Mapping[str, Any]
    ) -> list[dict[str, object]]:
        if template_id in self._AUTM_TEMPLATES:
            return [
                self._person(
                    information,
                    "recipient_authorized_official",
                    ["recipient_authorized_signatory"],
                    1,
                ),
                self._provider_official("provider_authorized_signatory"),
            ]

        if template_id == "ubmta_implementing_letter":
            can_certify = information.get(
                "recipient_scientist_can_certify_organization"
            )
            if not isinstance(can_certify, bool):
                raise DeliveryError(
                    "Missing required signer field: "
                    "recipient_scientist_can_certify_organization"
                )
            scientist_roles = ["recipient_scientist"]
            if can_certify:
                scientist_roles.append("recipient_organization_certifier")
            signers = [
                self._person(
                    information, "recipient_scientist", scientist_roles, 1
                )
            ]
            if not can_certify:
                signers.append(
                    self._person(
                        information,
                        "recipient_authorized_official",
                        ["recipient_organization_certifier"],
                        1,
                    )
                )
            signers.append(self._provider_official("provider_organization_certifier"))
            return signers

        raise DeliveryError(f"Unsupported signing workflow: {template_id}")

    def send(
        self,
        request_id: str,
        request: Mapping[str, Any],
        artifact: RenderedAgreement,
    ) -> DeliveryReceipt:
        if not artifact.path.is_file():
            raise DeliveryError(f"Agreement artifact does not exist: {artifact.path}")
        raw_information = request.get("agreement_information", {})
        if not isinstance(raw_information, Mapping):
            raise DeliveryError("agreement_information must be an object")
        signers = self._signers(artifact.template_id, raw_information)

        manifest = {
            "audit_events": [
                "auto_approved:standard_rules",
                "agreement_rendered",
                "signing_package_prepared",
            ],
            "delivery_mode": "signnow_package",
            "document": {
                "path": str(artifact.path.resolve()),
                "sha256": hashlib.sha256(artifact.path.read_bytes()).hexdigest(),
            },
            "live_submission": False,
            "provider": "U-M SignNow",
            "request_id": request_id,
            "schema_version": 1,
            "signers": signers,
            "template_id": artifact.template_id,
        }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        destination = self.output_dir / f"{safe_identifier(request_id)}.signing.json"
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.output_dir, prefix=".signing-", suffix=".json"
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            temporary.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

        return DeliveryReceipt(
            status="prepared_for_signature",
            mode="signnow_package",
            reference=str(destination),
        )
