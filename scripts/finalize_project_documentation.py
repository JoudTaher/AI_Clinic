from __future__ import annotations

from pathlib import Path

from docx import Document


DOCUMENT = Path("docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx")


def replace_paragraph(document: Document, old: str, new: str) -> None:
    matches = [paragraph for paragraph in document.paragraphs if paragraph.text == old]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one paragraph: {old[:80]}")
    paragraph = matches[0]
    paragraph.runs[0].text = new
    for run in paragraph.runs[1:]:
        run.text = ""


def main() -> None:
    document = Document(DOCUMENT)

    replace_paragraph(
        document,
        "11. The result records the internal submission ID, selected template, artifact path, immutable review reference, delivery reference, status, reasons, and audit events. A production extension must continue the record through completed-document collection and retention.",
        "11. The result records the readable MTA reference, full internal submission ID, selected template, artifact path, immutable review reference, delivery reference, status, reasons, and audit events. A production extension must continue the record through completed-document collection and retention.",
    )
    replace_paragraph(
        document,
        "Request and identity: institutional_case_id, internal_submission_id, authenticated requester, responsible PI, administrative home, created and updated timestamps.",
        "Request and identity: mta_reference, institutional_case_id, internal_submission_id, authenticated requester, responsible PI, administrative home, created and updated timestamps.",
    )
    replace_paragraph(
        document,
        "The repository currently has 175 passing automated tests. Tests cover intake, eligibility, semantic behavior through controlled classifier doubles, material mapping, template selection, agreement readiness, review warnings and immutable confirmation references, stale-confirmation rejection, DOCX population, signer planning, local package generation, SignNow payload construction, pipeline outcomes, screening reports, and the Streamlit form. Test success demonstrates current code behavior; it does not replace legal approval, platform integration testing, security review, accessibility review, or production acceptance testing.",
        "The repository maintains an automated test suite covering intake, eligibility, semantic behavior through controlled classifier doubles, material mapping, template selection, agreement readiness, review warnings and immutable confirmation references, stale-confirmation rejection, DOCX population, signer planning, local package generation, SignNow payload construction, pipeline outcomes, screening reports, readable reference propagation, termination-clause rendering, and the Streamlit form. Test success demonstrates current code behavior; it does not replace legal approval, platform integration testing, security review, accessibility review, or production acceptance testing.",
    )

    future_text = (
        "Persist the readable MTA reference as a unique indexed field when a database is introduced. "
        "Store it beside the institutional case ID, full submission hash, SignNow document ID, template "
        "version, and final-document repository location so staff can search one value across the "
        "application, SignNow, screening reports, and the records system."
    )
    future_matches = [paragraph for paragraph in document.paragraphs if paragraph.text == future_text]
    if len(future_matches) != 1:
        raise RuntimeError("Expected one readable-reference future-work paragraph")
    future_matches[0].style = document.styles["Normal"]

    history_matches = []
    for table in document.tables:
        for row in table.rows:
            if row.cells[0].text.strip() == "Remove record-system artifacts":
                history_matches.append(row)
    if len(history_matches) != 1:
        raise RuntimeError("Expected one development-history row")
    history_matches[0].cells[2].text = (
        "A full SHA-256 submission ID supports idempotency without becoming user input; "
        "a separate MTA-YYYY-XXXXXXXX reference supports staff search."
    )

    request_rows = []
    for table in document.tables:
        for row in table.rows:
            if row.cells[0].text.strip() == "Request" and len(row.cells) >= 3:
                if "Institutional ID" in row.cells[1].text:
                    request_rows.append(row)
    if len(request_rows) != 1:
        raise RuntimeError("Expected one Appendix C request row")
    request_rows[0].cells[1].text = (
        "Readable MTA reference, institutional ID, full internal ID, requester, timestamps, "
        "normalized questionnaire, version, and status"
    )

    document.save(DOCUMENT)


if __name__ == "__main__":
    main()
