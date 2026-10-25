from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

from src.adapters.paths import safe_identifier
from src.agreements.data import AgreementData
from src.pipeline.models import RenderedAgreement
from src.templates.catalog import TemplateDefinition


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": WORD_NS}


class UnsupportedTemplateError(ValueError):
    """Raised when no safe population strategy exists for a template."""


def _word(tag: str) -> str:
    return f"{{{WORD_NS}}}{tag}"


def _text(element: etree._Element) -> str:
    return "".join(element.xpath(".//w:t/text()", namespaces=NS))


def _set_text_node(node: etree._Element, value: str) -> None:
    node.text = value
    if value[:1].isspace() or value[-1:].isspace():
        node.set(f"{{{XML_NS}}}space", "preserve")
    else:
        node.attrib.pop(f"{{{XML_NS}}}space", None)


def _replace_marker(paragraph: etree._Element, old: str, new: str) -> None:
    for node in paragraph.xpath(".//w:t", namespaces=NS):
        value = node.text or ""
        if old in value:
            _set_text_node(node, value.replace(old, new, 1))
            return
    raise UnsupportedTemplateError(f"Expected template marker is missing: {old}")


def _replace_paragraph_text(paragraph: etree._Element, value: str) -> None:
    nodes = paragraph.xpath(".//w:t", namespaces=NS)
    if not nodes:
        run = etree.SubElement(paragraph, _word("r"))
        nodes = [etree.SubElement(run, _word("t"))]
    _set_text_node(nodes[0], value)
    for node in nodes[1:]:
        _set_text_node(node, "")


def _set_cell_text(cell: etree._Element, value: str) -> None:
    original_paragraph = next(iter(cell.xpath("./w:p", namespaces=NS)), None)
    paragraph_properties = None
    run_properties = None
    if original_paragraph is not None:
        existing_ppr = original_paragraph.find(_word("pPr"))
        paragraph_properties = deepcopy(existing_ppr) if existing_ppr is not None else None
        existing_run = next(
            iter(original_paragraph.xpath(".//w:r[w:t]", namespaces=NS)), None
        )
        if existing_run is not None:
            existing_rpr = existing_run.find(_word("rPr"))
            run_properties = deepcopy(existing_rpr) if existing_rpr is not None else None

    for child in list(cell):
        if child.tag != _word("tcPr"):
            cell.remove(child)

    paragraph = etree.SubElement(cell, _word("p"))
    if paragraph_properties is not None:
        paragraph.append(paragraph_properties)
    run = etree.SubElement(paragraph, _word("r"))
    if run_properties is not None:
        run.append(run_properties)
    parts = value.split("\n")
    for index, part in enumerate(parts):
        if index:
            etree.SubElement(run, _word("br"))
        node = etree.SubElement(run, _word("t"))
        _set_text_node(node, part)


class DocxAgreementRenderer:
    _AUTM_IDS = {"autm_chemical", "autm_biological"}

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def render(
        self,
        request_id: str,
        template: TemplateDefinition,
        request: Mapping[str, Any],
    ) -> RenderedAgreement:
        supported = self._AUTM_IDS | {"ubmta_implementing_letter"}
        if not template.automation_enabled or template.template_id not in supported:
            raise UnsupportedTemplateError(
                f"No automatic population strategy for {template.template_id}"
            )
        if template.source_path.suffix.lower() != ".docx":
            raise UnsupportedTemplateError(
                f"Automatic population requires DOCX: {template.template_id}"
            )

        data = AgreementData.from_request(request)
        with ZipFile(template.source_path) as source:
            root = etree.fromstring(source.read("word/document.xml"))
            if template.template_id in self._AUTM_IDS:
                self._populate_autm(root, data)
            else:
                self._populate_ubmta(root, data)
            populated_xml = etree.tostring(
                root, xml_declaration=True, encoding="UTF-8", standalone=True
            )

            self.output_dir.mkdir(parents=True, exist_ok=True)
            destination = self.output_dir / (
                f"{safe_identifier(request_id)}-{safe_identifier(template.template_id)}.docx"
            )
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self.output_dir, prefix=".agreement-", suffix=".docx"
            )
            os.close(descriptor)
            temporary = Path(temporary_name)
            try:
                with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as target:
                    for item in source.infolist():
                        payload = (
                            populated_xml
                            if item.filename == "word/document.xml"
                            else source.read(item.filename)
                        )
                        target.writestr(item, payload)
                temporary.replace(destination)
            finally:
                temporary.unlink(missing_ok=True)

        return RenderedAgreement(template_id=template.template_id, path=destination)

    @staticmethod
    def _cell(
        tables: list[etree._Element], table: int, row: int, column: int
    ) -> etree._Element:
        rows = tables[table].xpath("./w:tr", namespaces=NS)
        cells = rows[row].xpath("./w:tc", namespaces=NS)
        return cells[column]

    @classmethod
    def _populate_autm(cls, root: etree._Element, data: AgreementData) -> None:
        tables = root.xpath(".//w:tbl", namespaces=NS)
        values = (
            (0, 1, 1, data.provider_organization),
            (0, 1, 3, data.recipient_organization),
            (0, 2, 1, data.provider_address),
            (0, 2, 3, data.recipient_address),
            (1, 1, 1, data.provider_scientist_name),
            (1, 1, 3, data.recipient_scientist_name),
            (1, 2, 1, data.provider_scientist_title),
            (1, 2, 3, data.recipient_scientist_title),
            (2, 1, 0, data.material_description),
            (2, 1, 2, data.shipping_recipient_name),
            (2, 2, 2, data.shipping_address),
        )
        try:
            for table, row, column, value in values:
                _set_cell_text(cls._cell(tables, table, row, column), value)
            cls._clear_form_fields(tables[3])
        except IndexError as error:
            raise UnsupportedTemplateError(
                "The AUTM template structure does not match the approved slot map"
            ) from error

    @staticmethod
    def _clear_form_fields(container: etree._Element) -> None:
        paragraphs = container.xpath(".//w:p[.//w:instrText]", namespaces=NS)
        for paragraph in paragraphs:
            for child in list(paragraph):
                if child.tag != _word("pPr"):
                    paragraph.remove(child)

    @staticmethod
    def _paragraphs(root: etree._Element) -> list[etree._Element]:
        body = root.find("w:body", namespaces=NS)
        if body is None:
            raise UnsupportedTemplateError("The DOCX template has no document body")
        return body.xpath("./w:p", namespaces=NS)

    @classmethod
    def _nth_starting(
        cls, root: etree._Element, prefix: str, occurrence: int
    ) -> etree._Element:
        matches = [
            paragraph
            for paragraph in cls._paragraphs(root)
            if _text(paragraph).strip().startswith(prefix)
        ]
        try:
            return matches[occurrence]
        except IndexError as error:
            raise UnsupportedTemplateError(
                f"Expected template line is missing: {prefix} occurrence {occurrence + 1}"
            ) from error

    @classmethod
    def _line_after_heading(
        cls, root: etree._Element, heading: str, prefix: str
    ) -> etree._Element:
        paragraphs = cls._paragraphs(root)
        heading_index = next(
            (
                index
                for index, paragraph in enumerate(paragraphs)
                if _text(paragraph).strip() == heading
            ),
            None,
        )
        if heading_index is None:
            raise UnsupportedTemplateError(f"Expected template heading is missing: {heading}")
        for paragraph in paragraphs[heading_index + 1 :]:
            if _text(paragraph).strip().startswith(prefix):
                return paragraph
        raise UnsupportedTemplateError(
            f"Expected {prefix} line after template heading {heading}"
        )

    @classmethod
    def _populate_ubmta(cls, root: etree._Element, data: AgreementData) -> None:
        recipient_org = cls._nth_starting(root, "Organization:", 1)
        _replace_paragraph_text(
            recipient_org, f"Organization:\t{data.recipient_organization}"
        )

        recipient_address = cls._nth_starting(root, "Address:", 1)
        _replace_paragraph_text(
            recipient_address, f"Address:\t\t{data.recipient_address}"
        )

        material = next(
            (
                paragraph
                for paragraph in cls._paragraphs(root)
                if "MATERIAL (UM Technology Transfer File #XXXX)" in _text(paragraph)
            ),
            None,
        )
        if material is None:
            raise UnsupportedTemplateError("Expected UBMTA material marker is missing")
        _replace_paragraph_text(material, data.material_description)

        fee = next(
            (
                paragraph
                for paragraph in cls._paragraphs(root)
                if "[enter amount]" in _text(paragraph)
            ),
            None,
        )
        if fee is None:
            raise UnsupportedTemplateError("Expected UBMTA fee marker is missing")
        _replace_marker(fee, "[enter amount]", data.transmittal_fee + " ")

        provider_name = cls._line_after_heading(root, "PROVIDER SCIENTIST", "Name:")
        _replace_marker(provider_name, "FACULTY MEMBER", data.provider_scientist_name)
        provider_title = cls._line_after_heading(root, "PROVIDER SCIENTIST", "Title:")
        _replace_marker(provider_title, "FACULTY TITLE", data.provider_scientist_title)

        recipient_name = cls._line_after_heading(root, "RECIPIENT SCIENTIST", "Name:")
        _replace_paragraph_text(
            recipient_name, f"   Name:\t\t{data.recipient_scientist_name}"
        )
        recipient_title = cls._line_after_heading(root, "RECIPIENT SCIENTIST", "Title:")
        _replace_paragraph_text(
            recipient_title, f"   Title:\t\t{data.recipient_scientist_title}"
        )
