from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from src.pipeline.models import PipelineResult
from src.pipeline.ports import AgreementRenderer, AgreementSender, PipelineStore
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
        approved_template_id: str | None = None,
        approved_by: str | None = None,
    ) -> PipelineResult:
        existing = self.store.get(request_id)
        if existing is not None:
            return existing

        readiness = evaluate_agreement_readiness(request)
        if readiness["status"] == "missing_information":
            return PipelineResult(
                request_id=request_id,
                status="intake_incomplete",
                reasons=tuple(readiness["missing_fields"]),
                audit_events=("intake_checked",),
            )

        eligibility = evaluate_eligibility(request)
        selection = select_template(request, eligibility, self.catalog)
        recommendation = selection["recommended_template"]
        audit = ("intake_checked", "eligibility_screened", "template_evaluated")

        if selection["status"] != "recommendation_ready":
            return PipelineResult(
                request_id=request_id,
                status="manual_review_required",
                recommended_template=recommendation,
                reasons=tuple(selection["review_reasons"]),
                audit_events=audit,
            )

        if not approved_template_id or not isinstance(approved_by, str) or not approved_by.strip():
            return PipelineResult(
                request_id=request_id,
                status="approval_required",
                recommended_template=recommendation,
                reasons=("A named approver must approve the recommended template.",),
                audit_events=audit,
            )

        if approved_template_id != recommendation:
            return PipelineResult(
                request_id=request_id,
                status="approval_mismatch",
                recommended_template=recommendation,
                reasons=("The approved template does not match the recommendation.",),
                audit_events=audit,
            )

        template = next(
            definition
            for definition in self.catalog
            if definition.template_id == recommendation
        )
        approved_audit = audit + (f"approved:{approved_by.strip()}",)
        artifact = self.renderer.render(request_id, template, request)
        receipt = self.sender.send(request_id, request, artifact)
        result = PipelineResult(
            request_id=request_id,
            status=receipt.status,
            recommended_template=recommendation,
            artifact_path=str(artifact.path),
            delivery_reference=receipt.reference,
            audit_events=approved_audit + ("agreement_rendered", "delivery_prepared"),
        )
        self.store.save(result)
        return result
