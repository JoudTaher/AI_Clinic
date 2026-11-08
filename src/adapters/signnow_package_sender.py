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
from src.request_normalization import normalize_request
from src.signing.plan import SignerPlanError, build_signer_plan


class SignNowPackageSender:
    """Builds a local SignNow-ready manifest without making a network request."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def signers_for(
        self, template_id: str, information: Mapping[str, Any]
    ) -> list[dict[str, object]]:
        try:
            plan = build_signer_plan(template_id, information)
        except SignerPlanError as error:
            details: list[str] = []
            if error.missing_fields:
                details.append(
                    "Missing required signer fields: "
                    + ", ".join(error.missing_fields)
                )
            if error.invalid_fields:
                details.append(
                    "Signer fields must contain valid emails: "
                    + ", ".join(error.invalid_fields)
                )
            raise DeliveryError("; ".join(details)) from error
        except ValueError as error:
            raise DeliveryError(str(error)) from error
        return [signer.as_dict() for signer in plan.signers]

    def send(
        self,
        submission_id: str,
        request: Mapping[str, Any],
        artifact: RenderedAgreement,
    ) -> DeliveryReceipt:
        request = normalize_request(request)
        if not artifact.path.is_file():
            raise DeliveryError(f"Agreement artifact does not exist: {artifact.path}")
        raw_information = request.get("agreement_information", {})
        if not isinstance(raw_information, Mapping):
            raise DeliveryError("agreement_information must be an object")
        signers = self.signers_for(artifact.template_id, raw_information)

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
            "submission_id": submission_id,
            "schema_version": 1,
            "signers": signers,
            "template_id": artifact.template_id,
        }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        destination = self.output_dir / (
            f"{safe_identifier(submission_id)}.signing.json"
        )
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
