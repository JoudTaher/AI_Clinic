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
from src.pipeline.ports import AgreementRenderError
from src.request_normalization import normalize_request
from src.templates.catalog import TemplateDefinition


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": WORD_NS}


class UnsupportedTemplateError(AgreementRenderError):
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


def _set_cell_text(
    cell: etree._Element,
    value: str,
    *,
    preserve_run_formatting: bool = True,
    font_size_half_points: int | None = None,
) -> None:
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
            run_properties = (
                deepcopy(existing_rpr)
                if preserve_run_formatting and existing_rpr is not None
                else None
            )

    for child in list(cell):
        if child.tag != _word("tcPr"):
            cell.remove(child)

    paragraph = etree.SubElement(cell, _word("p"))
    if paragraph_properties is not None:
        if font_size_half_points is not None:
            paragraph_run_properties = paragraph_properties.find(_word("rPr"))
            if paragraph_run_properties is not None:
                for tag in (_word("sz"), _word("szCs")):
                    for existing_size in paragraph_run_properties.findall(tag):
                        paragraph_run_properties.remove(existing_size)
                    size = etree.SubElement(paragraph_run_properties, tag)
                    size.set(_word("val"), str(font_size_half_points))
        paragraph.append(paragraph_properties)
    run = etree.SubElement(paragraph, _word("r"))
    if run_properties is not None:
        run.append(run_properties)
    elif not preserve_run_formatting:
        run_properties = etree.SubElement(run, _word("rPr"))
        size = etree.SubElement(run_properties, _word("sz"))
        size.set(_word("val"), "22")
        complex_size = etree.SubElement(run_properties, _word("szCs"))
        complex_size.set(_word("val"), "22")
    if font_size_half_points is not None:
        run_properties = run.find(_word("rPr"))
        if run_properties is None:
            run_properties = etree.Element(_word("rPr"))
            run.insert(0, run_properties)
        for tag in (_word("sz"), _word("szCs")):
            for existing_size in run_properties.findall(tag):
                run_properties.remove(existing_size)
            size = etree.SubElement(run_properties, tag)
            size.set(_word("val"), str(font_size_half_points))
    parts = value.split("\n")
    for index, part in enumerate(parts):
        if index:
            etree.SubElement(run, _word("br"))
        node = etree.SubElement(run, _word("t"))
        _set_text_node(node, part)


class DocxAgreementRenderer:
    _AUTM_TEMPLATE_IDS = {
        "chemical_material_agreement",
        "animal_material_agreement",
    }

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def render(
        self,
        submission_id: str,
        template: TemplateDefinition,
        request: Mapping[str, Any],
    ) -> RenderedAgreement:
        supported = self._AUTM_TEMPLATE_IDS | {
            "biological_material_agreement",
            "device_material_agreement",
        }
        if not template.automation_enabled or template.template_id not in supported:
            raise UnsupportedTemplateError(
                f"No automatic population strategy for {template.template_id}"
            )
        if template.source_path.suffix.lower() != ".docx":
            raise UnsupportedTemplateError(
                f"Automatic population requires DOCX: {template.template_id}"
            )

        request = normalize_request(request)
        data = AgreementData.from_request(request, template.template_id)
        with ZipFile(template.source_path) as source:
            root = etree.fromstring(source.read("word/document.xml"))
            if template.template_id in self._AUTM_TEMPLATE_IDS:
                self._populate_autm(root, data)
            elif template.template_id == "biological_material_agreement":
                self._populate_ubmta(root, data)
            else:
                self._populate_simple_letter(root, data)
            populated_xml = etree.tostring(
                root, xml_declaration=True, encoding="UTF-8", standalone=True
            )

            self.output_dir.mkdir(parents=True, exist_ok=True)
            destination = self.output_dir / (
                f"{safe_identifier(submission_id)}-"
                f"{safe_identifier(template.template_id)}.docx"
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
                _set_cell_text(
                    cls._cell(tables, table, row, column),
                    value,
                    font_size_half_points=18,
                )
            normalized_fee = data.transmittal_fee.casefold().replace(" ", "")
            if normalized_fee not in {
                "",
                "n/a",
                "na",
                "none",
                "no",
                "0",
                "0.00",
                "$0",
                "$0.00",
            }:
                exhibit_notice = cls._paragraph_containing(
                    root, "If checked, this Agreement"
                )
                fee_term = cls._paragraph_containing(root, "A transmittal fee of")
                cls._set_plain_checkbox(exhibit_notice, checked=True)
                cls._set_plain_checkbox(fee_term, checked=True)
                cls._replace_between(
                    fee_term,
                    "A transmittal fee of ",
                    " shall be paid",
                    data.transmittal_fee,
                )
            signer_values = (
                (2, 0, data.provider_scientist_name, "Print Name"),
                (3, 0, data.provider_scientist_title, "Title"),
                (2, 1, data.recipient_authorized_official_name, "Print Name"),
                (3, 1, data.recipient_authorized_official_title, "Title"),
            )
            for row, column, value, label in signer_values:
                signer_cell = cls._cell(tables, 3, row, column)
                _set_cell_text(
                    signer_cell,
                    f"{value}\n{label}",
                    font_size_half_points=18,
                )
        except IndexError as error:
            raise UnsupportedTemplateError(
                "The AUTM template structure does not match the approved slot map"
            ) from error

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
    def _paragraph_containing(
        cls, root: etree._Element, marker: str
    ) -> etree._Element:
        matches = [
            paragraph
            for paragraph in cls._paragraphs(root)
            if marker in _text(paragraph)
        ]
        if len(matches) != 1:
            raise UnsupportedTemplateError(
                f"Expected exactly one template line containing: {marker}"
            )
        return matches[0]

    @classmethod
    def _paragraph_after_heading_prefix(
        cls, root: etree._Element, heading_prefix: str
    ) -> etree._Element:
        paragraphs = cls._paragraphs(root)
        heading_index = next(
            (
                index
                for index, paragraph in enumerate(paragraphs)
                if _text(paragraph).strip().startswith(heading_prefix)
            ),
            None,
        )
        if heading_index is None or heading_index + 1 >= len(paragraphs):
            raise UnsupportedTemplateError(
                f"Expected template heading is missing: {heading_prefix}"
            )
        return paragraphs[heading_index + 1]

    @staticmethod
    def _set_plain_checkbox(paragraph: etree._Element, *, checked: bool) -> None:
        value = _text(paragraph)
        stripped = value.lstrip()
        if not stripped.startswith(("☐", "☒")):
            raise UnsupportedTemplateError("Expected plain checkbox is missing")
        indentation = value[: len(value) - len(stripped)]
        symbol = "☒" if checked else "☐"
        _replace_paragraph_text(paragraph, indentation + symbol + stripped[1:])

    @staticmethod
    def _replace_between(
        paragraph: etree._Element,
        start_marker: str,
        end_marker: str,
        value: str,
    ) -> None:
        current = _text(paragraph)
        start = current.find(start_marker)
        if start < 0:
            raise UnsupportedTemplateError(
                f"Expected template marker is missing: {start_marker}"
            )
        value_start = start + len(start_marker)
        end = current.find(end_marker, value_start)
        if end < 0:
            raise UnsupportedTemplateError(
                f"Expected template marker is missing: {end_marker}"
            )
        _replace_paragraph_text(
            paragraph,
            current[:value_start] + value + current[end:],
        )

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
    def _line_after_heading_containing(
        cls, root: etree._Element, heading: str, marker: str
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
            if marker in _text(paragraph):
                return paragraph
        raise UnsupportedTemplateError(
            f"Expected {marker} line after template heading {heading}"
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

        material = cls._paragraph_after_heading_prefix(root, "3.ORIGINAL MATERIAL")
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
        _replace_paragraph_text(
            provider_name, f"Name:\t\t{data.provider_scientist_name}"
        )
        provider_title = cls._line_after_heading(root, "PROVIDER SCIENTIST", "Title:")
        _replace_paragraph_text(
            provider_title, f"Title:\t\t{data.provider_scientist_title}"
        )

        recipient_name = cls._line_after_heading(root, "RECIPIENT SCIENTIST", "Name:")
        _replace_paragraph_text(
            recipient_name, f"   Name:\t\t{data.recipient_scientist_name}"
        )
        recipient_title = cls._line_after_heading(root, "RECIPIENT SCIENTIST", "Title:")
        _replace_paragraph_text(
            recipient_title, f"   Title:\t\t{data.recipient_scientist_title}"
        )

        provider_cert_name = cls._line_after_heading(
            root, "PROVIDER ORGANIZATION CERTIFICATION", "Name:"
        )
        _replace_paragraph_text(
            provider_cert_name, f"Name:\t\t{data.provider_scientist_name}"
        )
        provider_cert_title = cls._line_after_heading(
            root, "PROVIDER ORGANIZATION CERTIFICATION", "Title:"
        )
        _replace_paragraph_text(
            provider_cert_title, f"   Title:\t\t{data.provider_scientist_title}"
        )
        provider_cert_address = cls._line_after_heading(
            root, "PROVIDER ORGANIZATION CERTIFICATION", "Address:"
        )
        _replace_paragraph_text(
            provider_cert_address, f"  Address:\t{data.provider_address}"
        )

        recipient_certifier_name = (
            data.recipient_scientist_name
            if data.recipient_scientist_can_certify_organization
            else data.recipient_authorized_official_name
        )
        recipient_certifier_title = (
            data.recipient_scientist_title
            if data.recipient_scientist_can_certify_organization
            else data.recipient_authorized_official_title
        )
        recipient_certifier = cls._line_after_heading_containing(
            root, "RECIPIENT ORGANIZATION CERTIFICATION", "Authorized"
        )
        leftover_official_label = cls._line_after_heading(
            root, "RECIPIENT ORGANIZATION CERTIFICATION", "Official:"
        )
        _replace_paragraph_text(
            recipient_certifier, f"   Authorized Official:\t{recipient_certifier_name}"
        )
        _replace_paragraph_text(leftover_official_label, "")
        recipient_certifier_title_line = cls._line_after_heading(
            root, "RECIPIENT ORGANIZATION CERTIFICATION", "Title:"
        )
        _replace_paragraph_text(
            recipient_certifier_title_line,
            f"   Title:\t\t{recipient_certifier_title}",
        )
        recipient_certifier_address = cls._line_after_heading(
            root, "RECIPIENT ORGANIZATION CERTIFICATION", "Address:"
        )
        _replace_paragraph_text(
            recipient_certifier_address, f"  Address:\t{data.recipient_address}"
        )

    @classmethod
    def _populate_simple_letter(
        cls, root: etree._Element, data: AgreementData
    ) -> None:
        material = cls._paragraph_after_heading_prefix(
            root,
            "In response to the RECIPIENT's request for the MATERIAL:",
        )
        _replace_paragraph_text(material, data.material_description)

        paragraphs = cls._paragraphs(root)
        fee = next(
            (paragraph for paragraph in paragraphs if "[insert fee here]" in _text(paragraph)),
            None,
        )
        if fee is None:
            raise UnsupportedTemplateError("Expected Simple Letter fee marker is missing")
        _replace_marker(fee, "[insert fee here]", data.transmittal_fee)

        tables = root.xpath(".//w:tbl", namespaces=NS)
        try:
            _set_cell_text(
                cls._cell(tables, 0, 0, 1),
                data.provider_scientist_name,
                preserve_run_formatting=False,
            )
            _set_cell_text(
                cls._cell(tables, 0, 4, 1),
                data.provider_scientist_name,
                preserve_run_formatting=False,
            )
            _set_cell_text(
                cls._cell(tables, 0, 5, 1),
                data.provider_scientist_title,
                preserve_run_formatting=False,
            )
            _set_cell_text(
                cls._cell(tables, 1, 0, 1),
                data.recipient_scientist_name,
                preserve_run_formatting=False,
            )
            _set_cell_text(
                cls._cell(tables, 1, 1, 1),
                data.recipient_organization,
                preserve_run_formatting=False,
            )
            _set_cell_text(
                cls._cell(tables, 1, 2, 1),
                data.recipient_address,
                preserve_run_formatting=False,
            )
            _set_cell_text(
                cls._cell(tables, 1, 4, 1),
                data.recipient_authorized_official_name,
                preserve_run_formatting=False,
            )
            _set_cell_text(
                cls._cell(tables, 1, 5, 1),
                data.recipient_authorized_official_title,
                preserve_run_formatting=False,
            )
        except IndexError as error:
            raise UnsupportedTemplateError(
                "The Simple Letter template structure does not match the approved slot map"
            ) from error
