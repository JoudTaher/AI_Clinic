from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from src.pipeline.models import DeliveryReceipt, PipelineResult, RenderedAgreement
from src.templates.catalog import TemplateDefinition


class AgreementRenderer(Protocol):
    def render(
        self,
        request_id: str,
        template: TemplateDefinition,
        request: Mapping[str, Any],
    ) -> RenderedAgreement: ...


class AgreementSender(Protocol):
    def send(
        self,
        request_id: str,
        request: Mapping[str, Any],
        artifact: RenderedAgreement,
    ) -> DeliveryReceipt: ...


class PipelineStore(Protocol):
    def get(self, request_id: str) -> PipelineResult | None: ...

    def save(self, result: PipelineResult) -> None: ...
