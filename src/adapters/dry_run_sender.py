from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.adapters.paths import safe_identifier
from src.pipeline.models import DeliveryReceipt, RenderedAgreement


class DryRunSender:
    """Writes an inspectable email package locally and never sends a message."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def send(
        self,
        request_id: str,
        request: Mapping[str, Any],
        artifact: RenderedAgreement,
    ) -> DeliveryReceipt:
        raw_intake = request.get("erpm_intake", {})
        intake = raw_intake if isinstance(raw_intake, Mapping) else {}
        recipient = intake.get("recipient_scientist_email")
        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError("recipient_scientist_email is required for delivery")
        if not artifact.path.is_file():
            raise ValueError(f"Agreement artifact does not exist: {artifact.path}")

        raw_title = intake.get("project_title")
        project_title = (
            raw_title.strip()
            if isinstance(raw_title, str) and raw_title.strip()
            else request_id
        )
        package = {
            "attachment": str(artifact.path),
            "delivery_mode": "dry_run",
            "request_id": request_id,
            "sent": False,
            "subject": f"Outgoing MTA: {project_title}",
            "template_id": artifact.template_id,
            "to": recipient.strip(),
        }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        package_path = self.output_dir / f"{safe_identifier(request_id)}.email.json"
        package_path.write_text(
            json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return DeliveryReceipt(
            status="prepared_for_delivery",
            mode="dry_run",
            reference=str(package_path),
        )
