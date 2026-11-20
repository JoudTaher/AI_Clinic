from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml import OxmlElement


DOCUMENT = Path("docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx")


def replace_paragraph(document: Document, old: str, new: str) -> None:
    matches = [paragraph for paragraph in document.paragraphs if paragraph.text == old]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one paragraph: {old[:80]}")
    paragraph = matches[0]
    if not paragraph.runs:
        paragraph.add_run(new)
        return
    paragraph.runs[0].text = new
    for run in paragraph.runs[1:]:
        run.text = ""


def add_paragraph_after(paragraph: Paragraph, text: str) -> Paragraph:
    element = OxmlElement("w:p")
    paragraph._p.addnext(element)
    created = Paragraph(element, paragraph._parent)
    created.style = paragraph.style
    created.add_run(text)
    return created


def set_cell(document: Document, table_index: int, row: int, column: int, value: str) -> None:
    document.tables[table_index].cell(row, column).text = value


def main() -> None:
    document = Document(DOCUMENT)

    replace_paragraph(
        document,
        "The system reuses questionnaire data rather than asking for the same identity twice. Contact PI becomes the provider scientist name. Recipient entity and recipient scientist fields populate the recipient party. Duration, research purpose, and reimbursement are retained as agreement context and are inserted only where the approved template exposes a supported slot. Signing emails are delivery data and are not printed in the agreement.",
        "The system reuses questionnaire data rather than asking for the same identity twice. Contact PI becomes the provider scientist name. Recipient entity and recipient scientist fields populate the recipient party. Provider Scientist academic or job title is required for every generated agreement. Recipient Scientist title is required only when the selected template prints it, and Recipient Authorized Official title remains required. Research purpose and reimbursement are inserted only where an approved template exposes a supported slot. The AUTM chemical and animal renderers activate the existing Exhibit B termination option and express the entered project period relative to the date of the last signature. Signing emails are delivery data and are not printed in the agreement.",
    )
    replace_paragraph(
        document,
        "The review displays provider and recipient organizations and addresses, scientist and authorized-official names and titles, material and fee details, shipping details, and every planned signer's name, email, role, and signing order. Empty optional fields are not presented as populated values. The exact DOCX is downloadable before confirmation.",
        "The review displays the readable MTA reference, provider and recipient organizations and addresses, every applicable required title, material and fee details, the agreement period, shipping details, and every planned signer's name, email, role, and signing order. The exact DOCX is downloadable before confirmation. Final review remains blocked until all applicable scientist and authorized-official titles are present.",
    )
    replace_paragraph(
        document,
        "AgreementConfirmation contains the review reference, selected template, and artifact path. Before delivery, the pipeline reopens the artifact and rebuilds the reference. A changed request, template, or file cannot reuse the old confirmation. Successful delivery adds agreement_review_confirmed to the audit events; the unconfirmed state records agreement_rendered and final_review_required.",
        "AgreementConfirmation contains the immutable review reference, selected template, and artifact path. That review reference protects a specific request and DOCX snapshot; it is separate from the shorter staff-facing MTA reference. Before delivery, the pipeline reopens the artifact and rebuilds the review reference. A changed request, template, or file cannot reuse the old confirmation. Successful delivery adds agreement_review_confirmed to the audit events; the unconfirmed state records agreement_rendered and final_review_required.",
    )
    replace_paragraph(
        document,
        "The current proof of concept stops after a confirmed local package or a successful SignNow invitation. src/adapters/signnow_api_sender.py returns the SignNow document ID as the delivery reference, but the current code has no webhook endpoint, no durable transaction database, no completion-status worker, no final PDF or completion-certificate download, and no institutional archive. Files under outputs and the in-memory pipeline cache are development artifacts, not an official records system.",
        "The current proof of concept stops after a confirmed local package or a successful SignNow invitation. The generated agreement, screening report, local manifest, final review, and SignNow document name share a readable reference in the form MTA-YYYY-XXXXXXXX. src/adapters/signnow_api_sender.py also returns the SignNow document ID as the external delivery reference. The current code has no webhook endpoint, no durable transaction database, no completion-status worker, no final PDF or completion-certificate download, and no institutional archive. Files under outputs and the in-memory pipeline cache are development artifacts, not an official records system.",
    )
    replace_paragraph(
        document,
        "1. Create a persistent request record before rendering. Store the institutional case ID, internal transaction ID, requester identity, normalized request, checklist version, and template version.",
        "1. Create a persistent request record before rendering. Store the readable MTA reference, full internal SHA-256 submission identifier, institutional case ID, requester identity, normalized request, checklist version, and template version as separate indexed values.",
    )
    replace_paragraph(
        document,
        "A production integration should treat the SignNow document ID returned by the existing sender as the stable external correlation key. The internal request or institutional case ID remains the business key. The database record must connect both identifiers before the invitation is considered operationally complete.",
        "A production integration should treat the SignNow document ID returned by the existing sender as the stable external correlation key. The readable MTA-YYYY-XXXXXXXX reference is the staff-facing search key; the institutional case ID remains the authoritative business key, and the full SHA-256 submission identifier remains the idempotency key. The database record must connect all four identifiers before the invitation is considered operationally complete.",
    )
    replace_paragraph(
        document,
        "No production database, durable queue, object store, or shared record search",
        "No production database, durable queue, object store, or cross-system record search; the readable MTA reference currently supports local filenames and SignNow document search only",
    )

    set_cell(document, 0, 4, 1, "18 November 2026")
    set_cell(document, 0, 5, 1, "Current repository and automated verification suite")

    set_cell(
        document,
        3,
        5,
        1,
        "Full content hash prevents duplicate processing; MTA-YYYY-XXXXXXXX is the staff-facing search reference",
    )
    set_cell(
        document,
        3,
        5,
        2,
        "Use the institutional record ID as the business key and index the readable MTA reference, full submission hash, and SignNow document ID",
    )

    set_cell(document, 8, 1, 0, "Provider scientist name and title")
    set_cell(document, 8, 1, 1, "Contact PI; Agreement and Signing Information")
    set_cell(document, 8, 1, 2, "Required agreement population fields")
    set_cell(document, 8, 4, 0, "Recipient scientist name, email, and applicable title")
    set_cell(document, 8, 4, 2, "Agreement population and recipient signing plan; title is required only when printed")
    set_cell(document, 8, 5, 0, "Recipient authorized official name, title, and email")
    set_cell(document, 8, 8, 2, "AUTM Exhibit B termination period measured from the date of the last signature")

    set_cell(
        document,
        10,
        1,
        1,
        "After confirmation, creates the populated DOCX and JSON manifest named with the readable MTA reference and containing roles, order, hash, internal ID, and audit events. Sends no email.",
    )
    set_cell(
        document,
        10,
        2,
        1,
        "After confirmation, uploads a temporary tagged DOCX named MTA-YYYY-XXXXXXXX — Project Title, verifies returned roles, sends ordered invitations, and records the SignNow document ID.",
    )

    module_row = document.tables[12].add_row().cells
    module_row[0].text = "src/request_identity.py"
    module_row[1].text = "Full idempotency hash, readable MTA reference, and searchable document-name construction"

    set_cell(document, 13, 3, 2, "Populated immutable artifact, readable MTA reference, searchable filename, and hash")
    set_cell(document, 13, 4, 2, "Displayed MTA reference, review fields and warnings, downloadable DOCX, immutable review reference, and explicit confirmation")
    set_cell(document, 13, 5, 2, "Readable MTA reference, SignNow document ID, invitation status, and audit event")

    heading = next(
        paragraph for paragraph in document.paragraphs if paragraph.text == "Near term product work"
    )
    add_paragraph_after(
        heading,
        "Persist the readable MTA reference as a unique indexed field when a database is introduced. Store it beside the institutional case ID, full submission hash, SignNow document ID, template version, and final-document repository location so staff can search one value across the application, SignNow, screening reports, and the records system.",
    )

    document.save(DOCUMENT)


if __name__ == "__main__":
    main()
