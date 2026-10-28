from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from src.intake import evaluate_intake_readiness
from src.pipeline.models import PipelineResult
from src.pipeline.ports import (
    AgreementRenderError,
    AgreementRenderer,
    AgreementSender,
    DeliveryError,
    PipelineStore,
)
from src.request_normalization import normalize_request
from src.templates.catalog import TemplateDefinition, load_template_catalog
from src.templates.selector import select_template


class InMemoryPipelineStore:
    def __init__(self) -> None:
        self._results: dict[str, PipelineResult] = {}

    def get(self, submission_id: str) -> PipelineResult | None:
        return self._results.get(submission_id)

    def save(self, result: PipelineResult) -> None:
        self._results[result.submission_id] = result


class OutgoingMTAPipeline:
    def __init__(
        self,
        renderer: AgreementRenderer,
        sender: AgreementSender,
        store: PipelineStore | None = None,
        catalog: Sequence[TemplateDefinition] | None = None,
        verified_facts: Mapping[str, Any] | None = None,
    ) -> None:
        self.renderer = renderer
        self.sender = sender
        self.store = store or InMemoryPipelineStore()
        self.catalog = tuple(catalog or load_template_catalog())
        self.verified_facts = {
            key: value
            for key, value in (verified_facts or {}).items()
            if isinstance(key, str) and isinstance(value, bool)
        }

    def run(
        self,
        request: Mapping[str, Any],
    ) -> PipelineResult:
        request = normalize_request(request)
        submission_basis = {
            "request": request,
            "verified_facts": self.verified_facts,
        }
        serialized_request = json.dumps(
            submission_basis,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        request_fingerprint = hashlib.sha256(
            serialized_request.encode("utf-8")
        ).hexdigest()
        submission_id = f"mta-{request_fingerprint}"
        existing = self.store.get(submission_id)
        if existing is not None:
            return existing

        intake_readiness = evaluate_intake_readiness(request)
        if intake_readiness["status"] == "missing_information":
            return PipelineResult(
                submission_id=submission_id,
                status="intake_incomplete",
                reasons=tuple(intake_readiness["missing_fields"]),
                audit_events=("intake_checked",),
            )

        eligibility = evaluate_eligibility(request, self.verified_facts)
        selection = select_template(request, eligibility, self.catalog)
        selected_template = selection["selected_template"]
        audit = ("intake_checked", "eligibility_screened", "template_evaluated")

        if selection["status"] != "template_selected":
            return PipelineResult(
                submission_id=submission_id,
                status="routed_to_erpm",
                reasons=tuple(selection["review_reasons"]),
                audit_events=audit + ("routed_to_erpm",),
            )

        agreement_readiness = evaluate_agreement_readiness(request)
        if agreement_readiness["status"] == "missing_information":
            return PipelineResult(
                submission_id=submission_id,
                status="agreement_incomplete",
                selected_template=selected_template,
                reasons=tuple(agreement_readiness["missing_fields"]),
                audit_events=audit + ("agreement_information_checked",),
            )

        template = next(
            definition
            for definition in self.catalog
            if definition.template_id == selected_template
        )
        approved_audit = audit + ("auto_approved:standard_rules",)
        try:
            artifact = self.renderer.render(submission_id, template, request)
        except AgreementRenderError as error:
            return PipelineResult(
                submission_id=submission_id,
                status="generation_failed",
                selected_template=selected_template,
                reasons=(str(error),),
                audit_events=approved_audit + ("agreement_generation_failed",),
            )
        try:
            receipt = self.sender.send(submission_id, request, artifact)
        except DeliveryError as error:
            return PipelineResult(
                submission_id=submission_id,
                status="delivery_failed",
                selected_template=selected_template,
                artifact_path=str(artifact.path),
                reasons=(str(error),),
                audit_events=approved_audit
                + ("agreement_rendered", "delivery_failed"),
            )
        result = PipelineResult(
            submission_id=submission_id,
            status=receipt.status,
            selected_template=selected_template,
            artifact_path=str(artifact.path),
            delivery_reference=receipt.reference,
            delivery_mode=receipt.mode,
            audit_events=approved_audit
            + ("agreement_rendered", "signing_package_prepared"),
        )
        self.store.save(result)
        return result
