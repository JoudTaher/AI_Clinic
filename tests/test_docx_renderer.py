from pathlib import Path
from zipfile import ZipFile

import pytest
from docx import Document
from lxml import etree

from src.adapters.docx_renderer import DocxAgreementRenderer, UnsupportedTemplateError
from src.agreements.data import AgreementDataError
from src.templates.catalog import load_template_catalog
from tests.fixtures import request_for


def template(template_id: str):
    return next(
        definition
        for definition in load_template_catalog()
        if definition.template_id == template_id
    )


def document_text(path: Path) -> str:
    document = Document(path)
    values = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            values.extend(cell.text for cell in row.cells)
    return "\n".join(values)


@pytest.mark.parametrize(
    ("category", "template_id", "expected_material"),
    [
        ("chemical", "autm_chemical", "Synthetic plasmid pExample"),
        (
            "animal_derived",
            "autm_biological",
            "Fixed, non-living mouse tissue samples",
        ),
    ],
)
def test_autm_renderer_populates_parties_scientists_material_and_shipping(
    tmp_path: Path, category: str, template_id: str, expected_material: str
):
    renderer = DocxAgreementRenderer(tmp_path)

    artifact = renderer.render("REQ-100", template(template_id), request_for(category))

    assert artifact.path.suffix == ".docx"
    text = document_text(artifact.path)
    for expected in (
        "The Regents of the University of Michigan",
            "Example U.S. Non-Profit University",
        "Dr. Provider",
        "Professor",
        "Dr. Recipient",
        "Associate Professor",
        expected_material,
        "100 Research Way, Example, MI 48100",
    ):
        assert expected in text
    assert "Expression is faulty" not in text
    with ZipFile(artifact.path) as package:
        root = etree.fromstring(package.read("word/document.xml"))
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    signature_table = root.xpath(".//w:tbl", namespaces=namespace)[3]
    assert signature_table.xpath(".//w:instrText", namespaces=namespace) == []
    populated_provider = root.xpath(".//w:tbl", namespaces=namespace)[0].xpath(
        "./w:tr", namespaces=namespace
    )[1].xpath("./w:tc", namespaces=namespace)[1]
    assert populated_provider.xpath(".//w:highlight", namespaces=namespace) == []
    assert set(
        populated_provider.xpath(".//w:rPr/w:sz/@w:val", namespaces=namespace)
    ) == {"18"}


def test_ubmta_renderer_populates_request_data_and_transmittal_fee(tmp_path: Path):
    renderer = DocxAgreementRenderer(tmp_path)

    artifact = renderer.render(
        "REQ-101", template("ubmta_implementing_letter"), request_for("biological")
    )

    text = document_text(artifact.path)
    assert "Organization:\tExample U.S. Non-Profit University" in text
    assert "Dr. Provider" in text
    assert "Professor" in text
    assert "Dr. Recipient" in text
    assert "Associate Professor" in text
    assert "PROVIDER ORGANIZATION CERTIFICATION" in text
    assert "Authorized Official:\tAlex Official" in text
    assert "Address:\t100 Research Way, Example, MI 48100" in text
    assert "Synthetic plasmid pExample" in text
    assert "$125.00" in text
    assert "[enter amount]" not in text
    assert "FACULTY MEMBER" not in text
    assert "FACULTY TITLE" not in text
    assert "$125.00This Implementing Letter" not in text
    with ZipFile(artifact.path) as package:
        document_xml = package.read("word/document.xml")
    assert b'w:type="page"' in document_xml


def test_ubmta_uses_recipient_scientist_as_certifier_when_authorized(tmp_path: Path):
    request = request_for("biological")
    information = request["agreement_information"]
    information["recipient_scientist_can_certify_organization"] = True
    information["recipient_authorized_official_name"] = ""
    information["recipient_authorized_official_title"] = ""
    information["recipient_authorized_official_email"] = ""

    artifact = DocxAgreementRenderer(tmp_path).render(
        "REQ-101-CERTIFIER", template("ubmta_implementing_letter"), request
    )

    text = document_text(artifact.path)
    assert "Authorized Official:\tDr. Recipient" in text
    assert "Alex Official" not in text


def test_renderer_allows_blank_optional_scientist_titles(tmp_path: Path):
    request = request_for("chemical")
    request["agreement_information"]["recipient_scientist_title"] = ""
    request["agreement_information"]["provider_scientist_title"] = ""
    renderer = DocxAgreementRenderer(tmp_path)

    artifact = renderer.render("REQ-102", template("autm_chemical"), request)

    assert artifact.path.is_file()


def test_renderer_rejects_missing_template_specific_authorized_official(
    tmp_path: Path,
):
    request = request_for("device")
    request["agreement_information"]["recipient_authorized_official_name"] = ""

    with pytest.raises(
        AgreementDataError, match="recipient_authorized_official_name"
    ):
        DocxAgreementRenderer(tmp_path).render(
            "REQ-102-OFFICIAL", template("simple_letter_agreement"), request
        )

    assert list(tmp_path.iterdir()) == []


def test_simple_letter_renderer_populates_material_parties_and_fee(tmp_path: Path):
    renderer = DocxAgreementRenderer(tmp_path)

    artifact = renderer.render(
        "REQ-103", template("simple_letter_agreement"), request_for("device")
    )

    text = document_text(artifact.path)
    for expected in (
        "Synthetic plasmid pExample",
        "$125.00",
        "Dr. Provider",
        "Professor",
        "Dr. Recipient",
        "Example U.S. Non-Profit University",
        "100 Research Way, Example, MI 48100",
        "Alex Official",
        "Director of Research Agreements",
    ):
        assert expected in text
    assert "[insert description]" not in text
    assert "[insert fee here]" not in text
