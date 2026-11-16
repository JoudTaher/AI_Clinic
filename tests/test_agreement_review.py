from copy import deepcopy
from pathlib import Path

from src.agreement_review import build_agreement_review
from src.pipeline.models import RenderedAgreement
from tests.fixtures import request_for


def artifact(tmp_path: Path, contents: bytes = b"reviewed agreement") -> RenderedAgreement:
    path = tmp_path / "agreement.docx"
    path.write_bytes(contents)
    return RenderedAgreement(template_id="chemical_material_agreement", path=path)


def test_review_uses_renderer_data_and_signnow_signer_data(tmp_path):
    request = request_for("chemical")

    review = build_agreement_review(
        request,
        "chemical_material_agreement",
        artifact(tmp_path),
    )

    values = {field.field_id: field.value for field in review.fields}
    assert values["provider_organization"] == "The Regents of the University of Michigan"
    assert values["provider_scientist_name"] == "Dr. Provider"
    assert values["recipient_organization"] == "Example U.S. Non-Profit University"
    assert values["material_description"] == "Synthetic research compound C-101"
    assert values["shipping_address"] == "100 Research Way, Example, MI 48100"
    assert [signer.email for signer in review.signers] == [
        "recipient.official@example.org",
    ]


def test_review_reference_changes_with_request_or_rendered_bytes(tmp_path):
    request = request_for("chemical")
    original = build_agreement_review(
        request,
        "chemical_material_agreement",
        artifact(tmp_path, b"version one"),
    )
    same = build_agreement_review(
        deepcopy(request),
        "chemical_material_agreement",
        artifact(tmp_path, b"version one"),
    )
    changed_request = deepcopy(request)
    changed_request["agreement_information"]["material_description"] = "Version two"
    request_change = build_agreement_review(
        changed_request,
        "chemical_material_agreement",
        artifact(tmp_path, b"version one"),
    )
    document_change = build_agreement_review(
        request,
        "chemical_material_agreement",
        artifact(tmp_path, b"version two"),
    )

    assert original.reference == same.reference
    assert request_change.reference != original.reference
    assert document_change.reference != original.reference


def test_review_flags_suspicious_text_address_and_signer_identity_without_editing(tmp_path):
    request = request_for("biological")
    request["agreement_information"]["material_description"] = (
        "Reseach reseach compund"
    )
    request["agreement_information"]["recipient_institution_address"] = "Ann Arbor"
    request["agreement_information"]["recipient_authorized_official_email"] = (
        request["agreement_information"]["recipient_scientist_email"]
    )
    original_description = request["agreement_information"]["material_description"]

    review = build_agreement_review(
        request,
        "biological_material_agreement",
        RenderedAgreement(
            template_id="biological_material_agreement",
            path=artifact(tmp_path).path,
        ),
    )

    warning_codes = {warning.code for warning in review.warnings}
    assert "repeated_word" in warning_codes
    assert "possible_spelling" in warning_codes
    assert "incomplete_address" in warning_codes
    assert "inconsistent_signer_identity" in warning_codes
    assert request["agreement_information"]["material_description"] == original_description
