from __future__ import annotations

import pytest

from src.signing.plan import SignerPlanError, build_signer_plan
from tests.fixtures import COMPLETE_AGREEMENT_INFORMATION


def information(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = dict(COMPLETE_AGREEMENT_INFORMATION)
    values.update(overrides)
    return values


@pytest.mark.parametrize("template_id", ["chemical_material_agreement", "animal_material_agreement"])
def test_autm_plan_uses_recipient_official_then_provider(template_id: str):
    plan = build_signer_plan(template_id, information())

    assert [(signer.party, signer.order, signer.roles) for signer in plan.signers] == [
        ("recipient_authorized_official", 1, ("recipient_authorized_signatory",)),
        ("provider_scientist", 2, ("provider_authorized_signatory",)),
    ]
    assert plan.signers[0].email == "recipient.official@example.org"
    assert plan.signers[1].email == "provider.scientist@umich.edu"


def test_ubmta_plan_combines_recipient_roles_when_scientist_can_certify():
    plan = build_signer_plan(
        "biological_material_agreement",
        information(recipient_scientist_can_certify_organization=True),
    )

    assert [(signer.party, signer.order, signer.roles) for signer in plan.signers] == [
        (
            "recipient_scientist",
            1,
            ("recipient_scientist", "recipient_organization_certifier"),
        ),
        ("provider_scientist", 2, ("provider_organization_certifier",)),
    ]


def test_ubmta_plan_requires_official_when_scientist_cannot_certify():
    plan = build_signer_plan(
        "biological_material_agreement",
        information(recipient_scientist_can_certify_organization=False),
    )

    assert [(signer.party, signer.order, signer.roles) for signer in plan.signers] == [
        ("recipient_scientist", 1, ("recipient_scientist",)),
        (
            "recipient_authorized_official",
            1,
            ("recipient_organization_certifier",),
        ),
        ("provider_scientist", 2, ("provider_organization_certifier",)),
    ]


def test_simple_letter_plan_matches_visible_signature_roles():
    plan = build_signer_plan("device_material_agreement", information())

    assert [(signer.party, signer.order, signer.roles) for signer in plan.signers] == [
        ("recipient_scientist", 1, ("recipient_scientist",)),
        (
            "recipient_authorized_official",
            1,
            ("recipient_authorized_signatory",),
        ),
        ("provider_scientist", 2, ("provider_authorized_signatory",)),
    ]
    assert plan.signers[0].title == ""


def test_strict_plan_reports_all_missing_fields_before_delivery():
    with pytest.raises(SignerPlanError) as caught:
        build_signer_plan(
            "chemical_material_agreement",
            information(
                recipient_authorized_official_email="",
                provider_scientist_name="",
            ),
        )

    assert caught.value.missing_fields == (
        "recipient_authorized_official_email",
        "provider_scientist_name",
    )


def test_preview_plan_keeps_roles_visible_with_incomplete_identity_data():
    plan = build_signer_plan(
        "biological_material_agreement",
        information(
            recipient_scientist_can_certify_organization=None,
            recipient_scientist_email="",
        ),
        strict=False,
    )

    assert plan.decision_required == "recipient_scientist_can_certify_organization"
    assert plan.missing_fields == (
        "recipient_scientist_can_certify_organization",
        "recipient_scientist_email",
    )
    assert [signer.party for signer in plan.signers] == [
        "recipient_scientist",
        "provider_scientist",
    ]


def test_signer_source_metadata_is_canonical():
    plan = build_signer_plan("device_material_agreement", information())

    assert plan.signers[0].source_summary == "from Outgoing Material Details"
    assert plan.signers[-1].source_summary == (
        "name from Contact PI; signing email from Agreement and Signing Information"
    )
