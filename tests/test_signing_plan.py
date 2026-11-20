from __future__ import annotations

import pytest

from src.signing.plan import SignerPlanError, build_signer_plan
from tests.fixtures import COMPLETE_AGREEMENT_INFORMATION


def information(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = dict(COMPLETE_AGREEMENT_INFORMATION)
    values.update(overrides)
    return values


@pytest.mark.parametrize("template_id", ["chemical_material_agreement", "animal_material_agreement"])
def test_autm_plan_invites_only_recipient_official(template_id: str):
    plan = build_signer_plan(template_id, information())

    assert [(signer.party, signer.order, signer.roles) for signer in plan.signers] == [
        ("recipient_authorized_official", 1, ("recipient_authorized_signatory",)),
    ]
    assert plan.signers[0].email == "recipient.official@example.org"


def test_ubmta_plan_requires_scientist_and_separate_official():
    plan = build_signer_plan("biological_material_agreement", information())

    assert [(signer.party, signer.order, signer.roles) for signer in plan.signers] == [
        ("recipient_scientist", 1, ("recipient_scientist",)),
        (
            "recipient_authorized_official",
            1,
            ("recipient_organization_certifier",),
        ),
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
    ]
    assert plan.signers[0].title == "Associate Professor"


def test_simple_letter_plan_requires_recipient_scientist_title():
    plan = build_signer_plan(
        "device_material_agreement",
        information(recipient_scientist_title=""),
        strict=False,
    )

    assert plan.missing_fields == ("recipient_scientist_title",)


def test_strict_plan_reports_all_missing_fields_before_delivery():
    with pytest.raises(SignerPlanError) as caught:
        build_signer_plan(
            "chemical_material_agreement",
            information(
                recipient_authorized_official_email="",
            ),
        )

    assert caught.value.missing_fields == ("recipient_authorized_official_email",)


def test_ubmta_preview_never_requires_a_certification_decision():
    plan = build_signer_plan(
        "biological_material_agreement",
        information(
            recipient_scientist_email="",
        ),
        strict=False,
    )

    assert not hasattr(plan, "decision_required")
    assert plan.missing_fields == ("recipient_scientist_email",)
    assert [signer.party for signer in plan.signers] == [
        "recipient_scientist",
        "recipient_authorized_official",
    ]


def test_signer_source_metadata_is_canonical():
    plan = build_signer_plan("device_material_agreement", information())

    assert plan.signers[0].source_summary == "from Outgoing Material Details"
    assert plan.signers[-1].source_summary == "from Agreement and Signing Information"
