from pathlib import Path

import pytest

from src.adapters.docx_renderer import DocxAgreementRenderer
from src.adapters.signnow_package_sender import SignNowPackageSender
from src.pipeline.outgoing_mta import OutgoingMTAPipeline
from tests.fixtures import request_for, verified_facts_for


@pytest.mark.parametrize(
    ("category", "template_id"),
    [
        ("chemical", "autm_chemical"),
        ("biological", "ubmta_implementing_letter"),
        ("animal_derived", "autm_biological"),
        ("device", "simple_letter_agreement"),
    ],
)
def test_real_standard_workflow_creates_agreement_and_signing_package(
    tmp_path: Path, category: str, template_id: str
):
    pipeline = OutgoingMTAPipeline(
        renderer=DocxAgreementRenderer(tmp_path / "agreements"),
        sender=SignNowPackageSender(tmp_path / "signing"),
        verified_facts=verified_facts_for(category),
    )

    result = pipeline.run(request_for(category))

    assert result.status == "prepared_for_signature"
    assert result.selected_template == template_id
    assert result.delivery_mode == "signnow_package"
    assert Path(result.artifact_path or "").is_file()
    assert Path(result.delivery_reference or "").is_file()
