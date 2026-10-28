from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from src.pipeline.models import DeliveryReceipt, PipelineResult, RenderedAgreement
from src.templates.catalog import TemplateDefinition


class DeliveryError(ValueError):
    """Expected delivery-adapter failure that the pipeline can report safely."""


class AgreementRenderError(ValueError):
    """Expected agreement-generation failure that the pipeline can report safely."""


class AgreementRenderer(Protocol):
    def render(
        self,
        submission_id: str,
        template: TemplateDefinition,
        request: Mapping[str, Any],
    ) -> RenderedAgreement: ...


class AgreementSender(Protocol):
    def send(
        self,
        submission_id: str,
        request: Mapping[str, Any],
        artifact: RenderedAgreement,
    ) -> DeliveryReceipt: ...


class PipelineStore(Protocol):
    def get(self, submission_id: str) -> PipelineResult | None: ...

    def save(self, result: PipelineResult) -> None: ...
