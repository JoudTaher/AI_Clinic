from datetime import date
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
    definition = next(
        definition
        for definition in load_template_catalog()
        if definition.template_id == template_id
    )
    return definition


def document_text(path: Path) -> str:
    document = Document(path)
    values = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            values.extend(cell.text for cell in row.cells)
    return "\n".join(values)


def signature_field_codes(path: Path) -> list[str]:
    with ZipFile(path) as package:
        root = etree.fromstring(package.read("word/document.xml"))
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    signature_table = root.xpath(".//w:tbl", namespaces=namespace)[3]
    return [
        (node.text or "").strip()
        for node in signature_table.xpath(".//w:instrText", namespaces=namespace)
    ]


def drawing_count(path: Path) -> int:
    with ZipFile(path) as package:
        root = etree.fromstring(package.read("word/document.xml"))
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return len(root.xpath(".//w:drawing | .//w:pict", namespaces=namespace))


def paragraph_containing(root: etree._Element, marker: str) -> etree._Element:
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return next(
        paragraph
        for paragraph in root.xpath(".//w:body/w:p", namespaces=namespace)
        if marker in "".join(
            paragraph.xpath(".//w:t/text()", namespaces=namespace)
        )
    )


@pytest.mark.parametrize(
    ("category", "template_id", "expected_material"),
    [
        ("chemical", "chemical_material_agreement", "Synthetic research compound C-101"),
        (
            "animal_derived",
            "animal_material_agreement",
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
    assert artifact.path.name.startswith("MTA-")
    assert "chemical_material_agreement" in artifact.path.name or "animal_material_agreement" in artifact.path.name
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
    assert signature_field_codes(template(template_id).source_path) == []
    assert signature_field_codes(artifact.path) == []
    with ZipFile(artifact.path) as package:
        root = etree.fromstring(package.read("word/document.xml"))
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    populated_provider = root.xpath(".//w:tbl", namespaces=namespace)[0].xpath(
        "./w:tr", namespaces=namespace
    )[1].xpath("./w:tc", namespaces=namespace)[1]
    assert populated_provider.xpath(".//w:highlight", namespaces=namespace) == []
    assert set(
        populated_provider.xpath(".//w:rPr/w:sz/@w:val", namespaces=namespace)
    ) == {"18"}


def test_renderer_uses_supplied_tracking_reference_in_generated_filename(
    tmp_path: Path,
):
    request = request_for("chemical")
    request["tracking_reference"] = "MTA-2026-7F3A91C2"

    artifact = DocxAgreementRenderer(tmp_path).render(
        "mta-" + "7f3a91c2" + "0" * 56,
        template("chemical_material_agreement"),
        request,
    )

    assert artifact.path.name == (
        "MTA-2026-7F3A91C2-chemical_material_agreement.docx"
    )


@pytest.mark.parametrize(
    ("category", "template_id"),
    [
        ("chemical", "chemical_material_agreement"),
        ("animal_derived", "animal_material_agreement"),
    ],
)
def test_autm_renderer_populates_and_activates_transmittal_fee_term(
    tmp_path: Path, category: str, template_id: str
):
    artifact = DocxAgreementRenderer(tmp_path).render(
        "REQ-AUTM-FEE", template(template_id), request_for(category)
    )

    with ZipFile(artifact.path) as package:
        root = etree.fromstring(package.read("word/document.xml"))
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    exhibit_notice = paragraph_containing(root, "If checked, this Agreement")
    fee_term = paragraph_containing(root, "A transmittal fee of")

    exhibit_text = "".join(
        exhibit_notice.xpath(".//w:t/text()", namespaces=namespace)
    )
    fee_text = "".join(fee_term.xpath(".//w:t/text()", namespaces=namespace))
    assert exhibit_text.strip().startswith("☒")
    assert fee_text.strip().startswith("☒")
    assert "$125.00" in fee_text


@pytest.mark.parametrize(
    ("category", "template_id"),
    [
        ("chemical", "chemical_material_agreement"),
        ("animal_derived", "animal_material_agreement"),
    ],
)
def test_autm_renderer_activates_relative_termination_period_from_last_signature(
    tmp_path: Path, category: str, template_id: str
):
    artifact = DocxAgreementRenderer(tmp_path).render(
        "REQ-AUTM-TERM", template(template_id), request_for(category)
    )

    with ZipFile(artifact.path) as package:
        root = etree.fromstring(package.read("word/document.xml"))
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    term = paragraph_containing(root, "This Agreement shall terminate")
    term_text = "".join(term.xpath(".//w:t/text()", namespaces=namespace))

    assert term_text.strip().startswith("☒")
    assert (
        "This Agreement shall terminate 3 years after the date of the last signature."
        in term_text
    )
    assert "This Agreement shall terminate on" not in term_text


def test_simple_letter_does_not_gain_an_autm_termination_clause(tmp_path: Path):
    artifact = DocxAgreementRenderer(tmp_path).render(
        "REQ-DEVICE-NO-TERM",
        template("device_material_agreement"),
        request_for("device"),
    )

    assert "after the date of the last signature" not in document_text(artifact.path)


@pytest.mark.parametrize(
    ("category", "template_id"),
    [
        ("chemical", "chemical_material_agreement"),
        ("animal_derived", "animal_material_agreement"),
    ],
)
def test_autm_renderer_populates_authorized_signatory_names_and_titles(
    tmp_path: Path, category: str, template_id: str
):
    artifact = DocxAgreementRenderer(
        tmp_path, signed_on=date(2026, 11, 15)
    ).render(
        "REQ-AUTM-SIGNERS", template(template_id), request_for(category)
    )

    signing_table = Document(artifact.path).tables[3]

    assert "Maggie Swift" in signing_table.cell(2, 0).text
    assert "Technology Transfer Associate Director" in signing_table.cell(3, 0).text
    assert "November 15, 2026" in signing_table.cell(4, 0).text
    assert "Alex Official" in signing_table.cell(2, 1).text
    assert "Director of Research Agreements" in signing_table.cell(3, 1).text


@pytest.mark.parametrize(
    ("category", "template_id"),
    [
        ("chemical", "chemical_material_agreement"),
        ("animal_derived", "animal_material_agreement"),
    ],
)
def test_autm_population_preserves_embedded_provider_signature(
    tmp_path: Path, category: str, template_id: str
):
    definition = template(template_id)
    artifact = DocxAgreementRenderer(tmp_path).render(
        "REQ-AUTM-SIGNATURE", definition, request_for(category)
    )

    assert drawing_count(definition.source_path) > 0
    assert drawing_count(artifact.path) == drawing_count(definition.source_path)


@pytest.mark.parametrize(
    ("category", "template_id"),
    [
        ("chemical", "chemical_material_agreement"),
        ("animal_derived", "animal_material_agreement"),
        ("biological", "biological_material_agreement"),
        ("device", "device_material_agreement"),
    ],
)
def test_every_agreement_keeps_provider_scientist_separate_from_fixed_signer(
    tmp_path: Path, category: str, template_id: str
):
    artifact = DocxAgreementRenderer(
        tmp_path, signed_on=date(2026, 11, 15)
    ).render("REQ-PRESIGNED", template(template_id), request_for(category))

    text = document_text(artifact.path)
    assert "Dr. Provider" in text
    assert "Maggie Swift" in text
    assert "Technology Transfer Associate Director" in text
    assert "November 15, 2026" in text


def test_ubmta_renderer_populates_request_data_and_transmittal_fee(tmp_path: Path):
    renderer = DocxAgreementRenderer(tmp_path)

    artifact = renderer.render(
        "REQ-101", template("biological_material_agreement"), request_for("biological")
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


@pytest.mark.parametrize(
    ("category", "template_id", "missing_field"),
    [
        ("chemical", "chemical_material_agreement", "provider_scientist_title"),
        ("chemical", "chemical_material_agreement", "recipient_scientist_title"),
        ("animal_derived", "animal_material_agreement", "provider_scientist_title"),
        ("animal_derived", "animal_material_agreement", "recipient_scientist_title"),
        ("biological", "biological_material_agreement", "provider_scientist_title"),
        ("biological", "biological_material_agreement", "recipient_scientist_title"),
        ("device", "device_material_agreement", "provider_scientist_title"),
    ],
)
def test_renderer_rejects_missing_applicable_scientist_title(
    tmp_path: Path, category: str, template_id: str, missing_field: str
):
    request = request_for(category)
    request["agreement_information"][missing_field] = ""

    with pytest.raises(AgreementDataError, match=missing_field):
        DocxAgreementRenderer(tmp_path).render(
            "REQ-102", template(template_id), request
        )


def test_device_renderer_does_not_require_unprinted_recipient_scientist_title(
    tmp_path: Path,
):
    request = request_for("device")
    request["agreement_information"]["recipient_scientist_title"] = ""

    artifact = DocxAgreementRenderer(tmp_path).render(
        "REQ-DEVICE-TITLE", template("device_material_agreement"), request
    )

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
            "REQ-102-OFFICIAL", template("device_material_agreement"), request
        )

    assert list(tmp_path.iterdir()) == []


def test_simple_letter_renderer_populates_material_parties_and_fee(tmp_path: Path):
    renderer = DocxAgreementRenderer(tmp_path)

    artifact = renderer.render(
        "REQ-103", template("device_material_agreement"), request_for("device")
    )

    text = document_text(artifact.path)
    for expected in (
        "Prototype benchtop research device",
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
