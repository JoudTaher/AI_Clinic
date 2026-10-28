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
    submission_id: str
    status: str
    selected_template: str | None = None
    recommended_template: str | None = None
    artifact_path: str | None = None
    delivery_reference: str | None = None
    delivery_mode: str | None = None
    reasons: tuple[str, ...] = ()
    audit_events: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "submission_id": self.submission_id,
            "status": self.status,
            "selected_template": self.selected_template,
            "recommended_template": self.recommended_template,
            "artifact_path": self.artifact_path,
            "delivery_reference": self.delivery_reference,
            "delivery_mode": self.delivery_mode,
            "reasons": list(self.reasons),
            "audit_events": list(self.audit_events),
        }
