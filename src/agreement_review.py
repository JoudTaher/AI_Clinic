from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from spellchecker import SpellChecker

from src.agreements.data import AgreementData
from src.pipeline.models import RenderedAgreement
from src.request_normalization import normalize_request
from src.signing.plan import Signer, build_signer_plan


@dataclass(frozen=True)
class ReviewField:
    field_id: str
    label: str
    value: str
    section: str


@dataclass(frozen=True)
class ReviewWarning:
    code: str
    field_id: str
    message: str


@dataclass(frozen=True)
class AgreementReview:
    template_id: str
    reference: str
    fields: tuple[ReviewField, ...]
    signers: tuple[Signer, ...]
    warnings: tuple[ReviewWarning, ...]


@dataclass(frozen=True)
class AgreementConfirmation:
    reference: str
    template_id: str
    artifact_path: Path


FIELD_LABELS = {
    "provider_organization": "Provider organization",
    "provider_address": "Provider organization address",
    "provider_scientist_name": "Provider Scientist full name",
    "provider_scientist_title": "Provider Scientist academic or job title",
    "recipient_organization": "Recipient organization",
    "recipient_address": "Recipient organization address",
    "recipient_scientist_name": "Recipient Scientist full name",
    "recipient_scientist_title": "Recipient Scientist academic or job title",
    "recipient_authorized_official_name": "Recipient Authorized Official full name",
    "recipient_authorized_official_title": "Recipient Authorized Official title",
    "material_description": "Material description",
    "requested_duration": "Agreement period after the last signature",
    "shipping_recipient_name": "Shipping recipient name",
    "shipping_address": "Shipping address",
    "transmittal_fee": "Transmittal or reimbursement fee",
}

IDENTITY_FIELDS = {
    "provider_scientist_name",
    "provider_scientist_title",
    "recipient_scientist_name",
    "recipient_scientist_title",
    "recipient_authorized_official_name",
    "recipient_authorized_official_title",
}


@lru_cache(maxsize=1)
def _spellchecker() -> SpellChecker:
    """Load the local dictionary once for repeated Streamlit reruns."""

    return SpellChecker(distance=1)


def _section(field_id: str) -> str:
    if field_id in IDENTITY_FIELDS:
        return "Agreement parties"
    if field_id in {"material_description", "transmittal_fee"}:
        return "Material and fee"
    if field_id == "requested_duration":
        return "Agreement term"
    if field_id in {"shipping_recipient_name", "shipping_address"}:
        return "Shipping"
    return "Organizations"


def _review_fields(data: AgreementData, template_id: str) -> tuple[ReviewField, ...]:
    raw = asdict(data)
    fields: list[ReviewField] = []
    for field_id, label in FIELD_LABELS.items():
        value = raw[field_id]
        if not isinstance(value, str) or not value:
            continue
        fields.append(
            ReviewField(
                field_id=field_id,
                label=label,
                value=value,
                section=_section(field_id),
            )
        )
    return tuple(fields)


def _possible_spelling_warning(field_id: str, value: str) -> ReviewWarning | None:
    tokens = {
        token.casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", value)
        if not token.isupper() and not any(character.isupper() for character in token[1:])
    }
    unknown = sorted(_spellchecker().unknown(tokens))[:8]
    if not unknown:
        return None
    return ReviewWarning(
        code="possible_spelling",
        field_id=field_id,
        message=(
            "Review possible spelling errors: "
            + ", ".join(unknown)
            + ". Scientific terms may be correct and are never changed automatically."
        ),
    )


def _text_warnings(field_id: str, value: str) -> list[ReviewWarning]:
    warnings: list[ReviewWarning] = []
    repeated = re.search(r"\b([A-Za-z][A-Za-z'-]*)\s+\1\b", value, re.IGNORECASE)
    if repeated:
        warnings.append(
            ReviewWarning(
                code="repeated_word",
                field_id=field_id,
                message=f'Review repeated word "{repeated.group(1)}".',
            )
        )
    if re.search(r"[^\n] {2,}[^\n]", value):
        warnings.append(
            ReviewWarning(
                code="repeated_whitespace",
                field_id=field_id,
                message="Review repeated spaces in this value.",
            )
        )
    spelling = _possible_spelling_warning(field_id, value)
    if spelling is not None:
        warnings.append(spelling)
    return warnings


def _address_warning(field_id: str, value: str) -> ReviewWarning | None:
    has_street_number = re.search(r"\b\d+[A-Za-z-]*\b", value) is not None
    has_us_postal_code = re.search(r"\b\d{5}(?:-\d{4})?\b", value) is not None
    if has_street_number and has_us_postal_code:
        return None
    return ReviewWarning(
        code="incomplete_address",
        field_id=field_id,
        message=(
            "Review this address; it does not appear to include both a street number "
            "and a U.S. ZIP code."
        ),
    )


def _identity_warnings(signers: tuple[Signer, ...]) -> list[ReviewWarning]:
    warnings: list[ReviewWarning] = []
    names_by_email: dict[str, set[str]] = defaultdict(set)
    emails_by_name: dict[str, set[str]] = defaultdict(set)
    for signer in signers:
        names_by_email[signer.email.casefold()].add(signer.name.casefold())
        emails_by_name[signer.name.casefold()].add(signer.email.casefold())
    for email, names in names_by_email.items():
        if email and len(names) > 1:
            warnings.append(
                ReviewWarning(
                    code="inconsistent_signer_identity",
                    field_id="signers",
                    message=(
                        f"The signing email {email} is associated with more than one "
                        "signer name. Confirm the intended signer identities."
                    ),
                )
            )
    for name, emails in emails_by_name.items():
        if name and len(emails) > 1:
            warnings.append(
                ReviewWarning(
                    code="inconsistent_signer_identity",
                    field_id="signers",
                    message=(
                        f"The signer name {name} is associated with more than one signing "
                        "email. Confirm the intended signer identities."
                    ),
                )
            )
    return warnings


def _reference(
    request: Mapping[str, Any], template_id: str, artifact_path: Path
) -> str:
    document_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    normalized_request = normalize_request(request)
    normalized_request.pop("tracking_reference", None)
    payload = {
        "document_sha256": document_hash,
        "request": normalized_request,
        "template_id": template_id,
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_agreement_review(
    request: Mapping[str, Any],
    template_id: str,
    artifact: RenderedAgreement,
) -> AgreementReview:
    if artifact.template_id != template_id:
        raise ValueError("The rendered agreement does not match the selected template.")
    if not artifact.path.is_file():
        raise ValueError(f"The rendered agreement does not exist: {artifact.path}")

    normalized = normalize_request(request)
    data = AgreementData.from_request(normalized, template_id)
    information = normalized.get("agreement_information", {})
    if not isinstance(information, Mapping):
        raise ValueError("agreement_information must be an object")
    signers = build_signer_plan(template_id, information).signers
    fields = _review_fields(data, template_id)

    warnings: list[ReviewWarning] = []
    for field in fields:
        if field.field_id == "material_description":
            warnings.extend(_text_warnings(field.field_id, field.value))
        if field.field_id in {"recipient_address", "shipping_address"}:
            warning = _address_warning(field.field_id, field.value)
            if warning is not None:
                warnings.append(warning)
    warnings.extend(_identity_warnings(signers))

    return AgreementReview(
        template_id=template_id,
        reference=_reference(normalized, template_id, artifact.path),
        fields=fields,
        signers=signers,
        warnings=tuple(warnings),
    )
