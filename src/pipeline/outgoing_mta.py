from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from src.pipeline.models import PipelineResult
from src.pipeline.ports import (
    AgreementRenderer,
    AgreementSender,
    DeliveryError,
    PipelineStore,
)
from src.templates.catalog import TemplateDefinition, load_template_catalog
from src.templates.selector import select_template


class InMemoryPipelineStore:
    def __init__(self) -> None:
        self._results: dict[str, PipelineResult] = {}

    def get(self, request_id: str) -> PipelineResult | None:
        return self._results.get(request_id)

    def save(self, result: PipelineResult) -> None:
        self._results[result.request_id] = result


class OutgoingMTAPipeline:
    def __init__(
        self,
        renderer: AgreementRenderer,
        sender: AgreementSender,
        store: PipelineStore | None = None,
        catalog: Sequence[TemplateDefinition] | None = None,
    ) -> None:
        self.renderer = renderer
        self.sender = sender
        self.store = store or InMemoryPipelineStore()
        self.catalog = tuple(catalog or load_template_catalog())

    def run(
        self,
        request_id: str,
        request: Mapping[str, Any],
    ) -> PipelineResult:
        if not isinstance(request_id, str) or not request_id.strip():
            return PipelineResult(
                request_id=request_id if isinstance(request_id, str) else "",
                status="invalid_request",
                reasons=("request_id",),
                audit_events=("request_rejected",),
            )
        serialized_request = json.dumps(
            request,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        request_fingerprint = hashlib.sha256(
            serialized_request.encode("utf-8")
        ).hexdigest()
        existing = self.store.get(request_id)
        if existing is not None:
            if existing.request_fingerprint == request_fingerprint:
                return existing
            return PipelineResult(
                request_id=request_id,
                status="idempotency_conflict",
                request_fingerprint=request_fingerprint,
                reasons=(
                    "This request ID was already completed with different request data.",
                ),
                audit_events=("idempotency_conflict",),
            )

        readiness = evaluate_agreement_readiness(request)
        if readiness["status"] == "missing_information":
            return PipelineResult(
                request_id=request_id,
                status="intake_incomplete",
                reasons=tuple(readiness["missing_fields"]),
                audit_events=("intake_checked",),
            )
        if readiness["status"] != "ready":
            review_reasons = tuple(
                reason.get("field_id", str(reason))
                if isinstance(reason, Mapping)
                else str(reason)
                for reason in readiness["review_reasons"]
            )
            return PipelineResult(
                request_id=request_id,
                status="routed_to_erpm",
                reasons=review_reasons,
                audit_events=("intake_checked", "agreement_review_required"),
            )

        eligibility = evaluate_eligibility(request)
        selection = select_template(request, eligibility, self.catalog)
        selected_template = selection["selected_template"]
        audit = ("intake_checked", "eligibility_screened", "template_evaluated")

        if selection["status"] != "template_selected":
            return PipelineResult(
                request_id=request_id,
                status="routed_to_erpm",
                reasons=tuple(selection["review_reasons"]),
                audit_events=audit + ("routed_to_erpm",),
            )

        template = next(
            definition
            for definition in self.catalog
            if definition.template_id == selected_template
        )
        approved_audit = audit + ("auto_approved:standard_rules",)
        artifact = self.renderer.render(request_id, template, request)
        try:
            receipt = self.sender.send(request_id, request, artifact)
        except DeliveryError as error:
            return PipelineResult(
                request_id=request_id,
                status="delivery_failed",
                selected_template=selected_template,
                artifact_path=str(artifact.path),
                request_fingerprint=request_fingerprint,
                reasons=(str(error),),
                audit_events=approved_audit
                + ("agreement_rendered", "delivery_failed"),
            )
        result = PipelineResult(
            request_id=request_id,
            status=receipt.status,
            selected_template=selected_template,
            artifact_path=str(artifact.path),
            delivery_reference=receipt.reference,
            request_fingerprint=request_fingerprint,
            audit_events=approved_audit + ("agreement_rendered", "delivery_prepared"),
        )
        self.store.save(result)
        return result
