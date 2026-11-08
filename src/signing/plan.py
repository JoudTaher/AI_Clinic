from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
TitleMode = Literal["required", "optional", "omit"]


class SignerPlanError(ValueError):
    def __init__(
        self,
        missing_fields: tuple[str, ...] = (),
        invalid_fields: tuple[str, ...] = (),
    ) -> None:
        self.missing_fields = missing_fields
        self.invalid_fields = invalid_fields
        details = [*(f"missing {field}" for field in missing_fields)]
        details.extend(f"invalid {field}" for field in invalid_fields)
        super().__init__("Signer plan is incomplete: " + ", ".join(details))


@dataclass(frozen=True)
class Signer:
    party: str
    label: str
    name: str
    email: str
    title: str
    order: int
    roles: tuple[str, ...]
    source_summary: str

    def as_dict(self) -> dict[str, object]:
        return {
            "email": self.email,
            "name": self.name,
            "order": self.order,
            "roles": list(self.roles),
            "title": self.title,
        }


@dataclass(frozen=True)
class SignerPlan:
    template_id: str
    signers: tuple[Signer, ...]
    missing_fields: tuple[str, ...] = ()
    invalid_fields: tuple[str, ...] = ()
    decision_required: str | None = None


@dataclass(frozen=True)
class _SignerDefinition:
    party: str
    label: str
    roles: tuple[str, ...]
    order: int
    title_mode: TitleMode
    source_summary: str


PROVIDER_SOURCE = (
    "name from Contact PI; signing email from Agreement and Signing Information"
)
RECIPIENT_SCIENTIST_SOURCE = "from Outgoing Material Details"
RECIPIENT_OFFICIAL_SOURCE = "from Agreement and Signing Information"


def _text(information: Mapping[str, Any], field_id: str) -> str:
    value = information.get(field_id, "")
    return value.strip() if isinstance(value, str) else ""


def _build_signer(
    definition: _SignerDefinition,
    information: Mapping[str, Any],
) -> tuple[Signer, tuple[str, ...], tuple[str, ...]]:
    name_field = f"{definition.party}_name"
    email_field = f"{definition.party}_email"
    title_field = f"{definition.party}_title"
    name = _text(information, name_field)
    email = _text(information, email_field)
    title = "" if definition.title_mode == "omit" else _text(information, title_field)

    missing: list[str] = []
    if not name:
        missing.append(name_field)
    if not email:
        missing.append(email_field)
    if definition.title_mode == "required" and not title:
        missing.append(title_field)

    invalid = (
        (email_field,)
        if email and not EMAIL_PATTERN.fullmatch(email)
        else ()
    )
    signer = Signer(
        party=definition.party,
        label=definition.label,
        name=name,
        email=email,
        title=title,
        order=definition.order,
        roles=definition.roles,
        source_summary=definition.source_summary,
    )
    return signer, tuple(missing), invalid


def _provider(role: str) -> _SignerDefinition:
    return _SignerDefinition(
        party="provider_scientist",
        label="Provider Scientist",
        roles=(role,),
        order=2,
        title_mode="optional",
        source_summary=PROVIDER_SOURCE,
    )


def _recipient_scientist(
    roles: tuple[str, ...], *, title_mode: TitleMode = "optional"
) -> _SignerDefinition:
    return _SignerDefinition(
        party="recipient_scientist",
        label="Recipient Scientist",
        roles=roles,
        order=1,
        title_mode=title_mode,
        source_summary=RECIPIENT_SCIENTIST_SOURCE,
    )


def _recipient_official(
    label: str, role: str
) -> _SignerDefinition:
    return _SignerDefinition(
        party="recipient_authorized_official",
        label=label,
        roles=(role,),
        order=1,
        title_mode="required",
        source_summary=RECIPIENT_OFFICIAL_SOURCE,
    )


def build_signer_plan(
    template_id: str,
    information: Mapping[str, Any],
    strict: bool = True,
) -> SignerPlan:
    decision_required: str | None = None
    if template_id in {"chemical_material_agreement", "animal_material_agreement"}:
        definitions = (
            _recipient_official(
                "Recipient Authorized Signatory",
                "recipient_authorized_signatory",
            ),
            _provider("provider_authorized_signatory"),
        )
    elif template_id == "biological_material_agreement":
        can_certify = information.get(
            "recipient_scientist_can_certify_organization"
        )
        if not isinstance(can_certify, bool):
            decision_required = "recipient_scientist_can_certify_organization"
            definitions = (
                _recipient_scientist(("recipient_scientist",)),
                _provider("provider_organization_certifier"),
            )
        elif can_certify:
            definitions = (
                _recipient_scientist(
                    ("recipient_scientist", "recipient_organization_certifier")
                ),
                _provider("provider_organization_certifier"),
            )
        else:
            definitions = (
                _recipient_scientist(("recipient_scientist",)),
                _recipient_official(
                    "Recipient Authorized Official",
                    "recipient_organization_certifier",
                ),
                _provider("provider_organization_certifier"),
            )
    elif template_id == "device_material_agreement":
        definitions = (
            _recipient_scientist(("recipient_scientist",), title_mode="omit"),
            _recipient_official(
                "Recipient Authorized Official",
                "recipient_authorized_signatory",
            ),
            _provider("provider_authorized_signatory"),
        )
    else:
        raise ValueError(f"Unsupported signing workflow: {template_id}")

    signers: list[Signer] = []
    missing_fields: list[str] = []
    invalid_fields: list[str] = []
    if decision_required:
        missing_fields.append(decision_required)
    for definition in definitions:
        signer, missing, invalid = _build_signer(definition, information)
        signers.append(signer)
        missing_fields.extend(missing)
        invalid_fields.extend(invalid)

    plan = SignerPlan(
        template_id=template_id,
        signers=tuple(signers),
        missing_fields=tuple(dict.fromkeys(missing_fields)),
        invalid_fields=tuple(dict.fromkeys(invalid_fields)),
        decision_required=decision_required,
    )
    if strict and (plan.missing_fields or plan.invalid_fields):
        raise SignerPlanError(plan.missing_fields, plan.invalid_fields)
    return plan
