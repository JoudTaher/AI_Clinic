from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderedAgreement:
    template_id: str
    path: Path


@dataclass(frozen=True)
class DeliveryReceipt:
    status: str
    mode: str
    reference: str


@dataclass(frozen=True)
class PipelineResult:
    request_id: str
    status: str
    recommended_template: str | None = None
    artifact_path: str | None = None
    delivery_reference: str | None = None
    request_fingerprint: str | None = None
    reasons: tuple[str, ...] = ()
    audit_events: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "recommended_template": self.recommended_template,
            "artifact_path": self.artifact_path,
            "delivery_reference": self.delivery_reference,
            "request_fingerprint": self.request_fingerprint,
            "reasons": list(self.reasons),
            "audit_events": list(self.audit_events),
        }
