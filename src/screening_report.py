from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from src.intake import evaluate_intake_readiness
from src.input_usage import build_input_usage
from src.request_normalization import normalize_request
from src.templates.selector import select_template


DISCLAIMER = (
    "This proof of concept automatically processes only documented standard "
    "requests. It creates a local signing package and performs no live submission."
)

DELIVERY_POLICY = {
    "internal_approval_required": False,
    "delivery_mode": "signnow_package",
    "live_delivery_enabled": False,
    "nonstandard_route": "eRPM",
}


def build_screening_report(
    request: Mapping[str, Any],
    verified_facts: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request = normalize_request(request)
    eligibility = evaluate_eligibility(request, verified_facts)
    raw_intake = request.get("erpm_intake", {})
    erpm_intake = dict(raw_intake) if isinstance(raw_intake, Mapping) else {}
    raw_agreement = request.get("agreement_information", {})
    agreement_information = (
        dict(raw_agreement) if isinstance(raw_agreement, Mapping) else {}
    )
    return {
        "proof_of_concept": True,
        "disclaimer": DISCLAIMER,
        "delivery_policy": dict(DELIVERY_POLICY),
        "erpm_intake": erpm_intake,
        "agreement_information": agreement_information,
        "intake_readiness": evaluate_intake_readiness(request),
        "eligibility": eligibility,
        "agreement_readiness": evaluate_agreement_readiness(request),
        "input_usage": build_input_usage(request),
        "template_selection": select_template(request, eligibility),
    }


def serialize_screening_report(report: Mapping[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
