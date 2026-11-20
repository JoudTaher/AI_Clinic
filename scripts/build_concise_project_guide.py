from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUTPUT = Path("docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx")
FONT = "Arial"
BLACK = RGBColor(0, 0, 0)


def set_run_font(run, size: float | None = None, bold: bool | None = None) -> None:
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
    run.font.color.rgb = BLACK
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def configure_styles(document: Document) -> None:
    normal = document.styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:ascii"), FONT)
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
    normal.font.size = Pt(10.2)
    normal.font.color.rgb = BLACK
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.04

    styles = {
        "Title": (24, 0, 12),
        "Subtitle": (12, 0, 16),
        "Heading 1": (16, 14, 6),
        "Heading 2": (12, 9, 3),
    }
    for name, (size, before, after) in styles.items():
        style = document.styles[name]
        style.font.name = FONT
        style._element.rPr.rFonts.set(qn("w:ascii"), FONT)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
        style.font.size = Pt(size)
        style.font.bold = name != "Subtitle"
        style.font.color.rgb = BLACK
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for name in ("List Bullet", "List Number"):
        style = document.styles[name]
        style.font.name = FONT
        style._element.rPr.rFonts.set(qn("w:ascii"), FONT)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
        style.font.size = Pt(10.2)
        style.font.color.rgb = BLACK
        style.paragraph_format.space_after = Pt(2.5)
        style.paragraph_format.line_spacing = 1.03


def add_body(document: Document, text: str, *, bold_lead: str | None = None):
    paragraph = document.add_paragraph()
    if bold_lead and text.startswith(bold_lead):
        lead = paragraph.add_run(bold_lead)
        set_run_font(lead, bold=True)
        body = paragraph.add_run(text[len(bold_lead) :])
        set_run_font(body)
    else:
        run = paragraph.add_run(text)
        set_run_font(run)
    return paragraph


def add_bullet(document: Document, text: str, *, bold_lead: str | None = None):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.22)
    paragraph.paragraph_format.first_line_indent = Inches(-0.16)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.05
    paragraph.paragraph_format.keep_together = True
    bullet = paragraph.add_run("•  ")
    set_run_font(bullet)
    if bold_lead and text.startswith(bold_lead):
        lead = paragraph.add_run(bold_lead)
        set_run_font(lead, bold=True)
        body = paragraph.add_run(text[len(bold_lead) :])
        set_run_font(body)
    else:
        run = paragraph.add_run(text)
        set_run_font(run)
    return paragraph


def add_number(
    document: Document,
    number: int,
    text: str,
    *,
    bold_lead: str | None = None,
) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.3)
    paragraph.paragraph_format.first_line_indent = Inches(-0.3)
    paragraph.paragraph_format.space_before = Pt(1.5)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.06
    paragraph.paragraph_format.keep_together = True
    prefix = paragraph.add_run(f"{number}.  ")
    set_run_font(prefix)
    if bold_lead and text.startswith(bold_lead):
        lead = paragraph.add_run(bold_lead)
        set_run_font(lead, bold=True)
        body = paragraph.add_run(text[len(bold_lead) :])
        set_run_font(body)
    else:
        run = paragraph.add_run(text)
        set_run_font(run)


def add_heading(document: Document, text: str, level: int = 1) -> None:
    document.add_heading(text, level=level)


def build_document() -> Document:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    configure_styles(document)

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(10)
    title.paragraph_format.keep_with_next = True
    set_run_font(title.add_run("Outgoing MTA Automation Guide"), 24, True)
    subtitle = document.add_paragraph(style="Subtitle")
    set_run_font(
        subtitle.add_run("Client workflow, current capability, and production handoff"),
        12,
        False,
    )
    add_body(
        document,
        "This guide explains the outgoing Material Transfer Agreement automation service developed for University of Michigan Innovation Partnerships. It gives department staff, U-M IT, and the next development team one shared view of the problem, the current solution, the verified workflow, and the work required for production use.",
    )
    add_body(
        document,
        "The current system is a working standalone Streamlit application with a Python backend. It turns one requester submission into an eligibility decision, the correct populated agreement, a final review step, and a recipient-side SignNow request. It reduces repeated staff handling while keeping policy decisions explainable and exceptions in a staff-review path. It is ready for controlled demonstration and testing; institutional authentication, durable records, and production operations still need to be added.",
    )

    add_heading(document, "Guide map")
    for item in (
        "Problem and starting materials",
        "Solution and workflow",
        "Design and technology decisions",
        "Current verification and staff-review example",
        "Deployment and operational boundary",
        "Production decisions and handoff",
        "Research completed",
        "Future product development",
    ):
        add_bullet(document, item)

    add_heading(document, "1 Problem and starting point")
    add_body(
        document,
        "Innovation Partnerships staff currently perform several repeatable steps manually for standard outgoing MTA requests: review a submitted form against an eligibility checklist, decide whether the request can use a standard agreement, select the correct agreement, transfer information into the document, check the result, and coordinate signatures. This creates avoidable handling time and increases the chance of inconsistent routing, copied values, and document errors.",
    )
    add_body(document, "The project began with four main sources:")
    add_bullet(document, "The existing outgoing request form, which defines what the requester supplies.")
    add_bullet(document, "The outgoing MTA eligibility checklist, which defines the automatic standard path.")
    add_bullet(document, "The approved chemical, animal, biological, and device agreement files, including the Uniform Biological Material Transfer Agreement (UBMTA), which define the legal wording, population locations, and signature blocks.")
    add_bullet(document, "A SignNow developer account for testing document upload and signature invitations.")
    add_body(
        document,
        "The supplied agreements do not share one standard layout. They use different labels, optional terms, and signature blocks, so each approved template requires its own controlled population logic. The biological UBMTA route also needs organization and authorized-official information that the other agreements do not use in the same way. The current form collects those values; a production service should verify them against an authoritative institutional source. Production ownership for identity, hosting, records, security, and platform integration also remains to be assigned.",
    )

    add_heading(document, "2 Solution developed")
    add_body(
        document,
        "The proof of concept separates the requester form, eligibility policy, agreement generation, document review, and signature delivery. This separation is intentional: a requester question is not automatically an eligibility rule, and an agreement field is not automatically a policy condition.",
    )
    add_heading(document, "End to end workflow", 2)
    steps = (
        ("Questionnaire intake. ", "The requester completes one form based on the supplied outgoing request form. Required fields and email formats are validated before processing."),
        ("Eligibility assessment. ", "The backend translates the checklist into explicit rules and evaluates every applicable general and material-specific condition."),
        ("Open-text evidence. ", "Only unresolved or potentially contradictory checklist evidence is sent to the local language model. Structured answers remain primary."),
        ("Routing. ", "A request that satisfies every applicable condition enters the automated standard MTA process. Failed, unresolved, mixed, unsupported, or out-of-scope cases move to staff review."),
        ("Template selection. ", "The material category selects one approved, automation-enabled agreement. The system does not choose the closest agreement when the category is ambiguous."),
        ("Agreement population. ", "The backend reuses form data, checks template-specific requirements, and creates a new populated Word agreement without modifying the approved source template."),
        ("Document review. ", "The requester sees the values entering the agreement, the signer plan, warnings, and the exact generated Word agreement. Delivery is blocked until the current document is confirmed."),
        ("Signing. ", "After confirmation, SignNow Development Mode uploads a temporary signing copy and sends invitations only to the recipient-side signer or signers required by that agreement."),
        ("Traceability. ", "The system assigns a readable MTA reference and records the selected template, artifact, review reference, delivery result, and audit events."),
    )
    for number, (lead, body) in enumerate(steps, start=1):
        add_number(document, number, lead + body, bold_lead=lead)

    add_heading(document, "Current agreement routing", 2)
    add_bullet(document, "Chemical material requests use the chemical agreement when all checklist conditions pass.")
    add_bullet(document, "Animal-derived material requests use the AUTM biological agreement for animal materials when all checklist conditions pass.")
    add_bullet(document, "Device requests use the simple device agreement when all checklist conditions pass.")
    add_bullet(document, "Biological material requests use the UBMTA agreement when all checklist conditions pass.")
    add_body(
        document,
        "This is the current proof-of-concept mapping: material category determines the agreement family after checklist eligibility is established. A production version should add an organization-verification step before using UBMTA. It should confirm that the recipient organization is eligible for the UBMTA process and obtain authorized-official information from a trusted institutional source. If those checks cannot be completed, the request should move to staff review or another approved biological agreement.",
    )

    add_heading(document, "3 Design rationale")
    add_heading(document, "Rules before AI", 2)
    add_body(
        document,
        "The eligibility checklist is legal and operational policy, so the main decision must remain deterministic and explainable. Each checklist statement resolves to true, false, or unresolved. Automatic approval requires true for every applicable statement. The system does not ask a model to make the final eligibility decision and does not treat missing evidence as approval.",
    )
    add_heading(document, "Local language model for open text", 2)
    model_overview = add_body(
        document,
        "Some checklist conditions rely on narrative answers, such as the recipient's research purpose or whether a chemical will be used in humans. The system uses a free local natural-language model (facebook/bart-large-mnli through Hugging Face Transformers) to compare the submitted wording with one specific checklist statement. It records support, contradiction, and neutral scores. Structured answers remain authoritative; the model only interprets text that the checklist permits as evidence. Clear support can resolve the condition, clear contradiction blocks it, and uncertain wording moves to staff review. After the model is downloaded, form text is processed locally rather than sent to a hosted inference service.",
    )
    model_overview.paragraph_format.keep_together = True
    add_heading(document, "Model risk and controls", 2)
    model_risk = add_body(
        document,
        "The language model can still make classification errors. A false positive could treat weak wording as sufficient evidence and contribute to an incorrect approval. A false negative could miss valid wording and send a standard request to staff review. Because the first error is more serious, the current thresholds are conservative and uncertain results remain unresolved. Before production, the department should evaluate the model on approved examples, measure both error types for each checklist condition, and re-test every model or threshold change.",
    )
    model_risk.paragraph_format.keep_together = True
    add_heading(document, "Template-specific population", 2)
    add_body(
        document,
        "The legal files are not standardized, so one generic merge routine would be unsafe. Each enabled agreement has a tested population strategy that knows where its organization, scientist, material, shipping, title, date, and signature information belongs. The system stops if an expected marker is missing instead of writing into an uncertain location.",
    )
    add_heading(document, "Final document review", 2)
    add_body(
        document,
        "The review step was added to prevent typos and incorrect signer information from reaching SignNow. It shows all agreement-bound values, validates required titles and emails, flags possible spelling, address, spacing, and identity problems, and provides the exact populated Word agreement for inspection. Warnings never change eligibility or silently edit legal content. Any form or document change invalidates the earlier confirmation.",
    )
    add_heading(document, "One-sided signature flow", 2)
    add_body(
        document,
        "The approved templates already contain Maggie Swift's provider-side signature, name, and title. The active SignNow flow therefore creates only the recipient-side invitation or invitations required by the selected agreement. The configured SignNow account is the sender, not an additional signer. Recipient signer emails come from the submitted form.",
    )
    add_heading(document, "Searchable references", 2)
    add_body(
        document,
        "Each request receives a readable reference such as MTA-2026-7F3A91C2. The same value is used in the final review, generated filename, screening report, local signing manifest, SignNow document name, and delivery result. The full SHA-256 identifier remains the internal idempotency key.",
    )
    add_heading(document, "Department outcome", 2)
    add_body(
        document,
        "For a standard request, staff no longer need to repeat the same checklist comparison, select an agreement by hand, copy the same values into Word, and build the signature package separately. The system prepares one traceable package and gives staff and requesters a clear review point before delivery. Exceptions remain visible and follow the department's existing staff-review process rather than being forced into an automated agreement.",
    )

    add_heading(document, "4 Current verification")
    add_body(
        document,
        "The repository has automated tests for intake, checklist rules, language-model decision handling through controlled test doubles, template selection, population, review confirmation, signer planning, SignNow payloads, references, termination wording, and the Streamlit interface.",
    )
    add_body(document, "Representative end-to-end mock cases verify that:")
    add_bullet(document, "Chemical, animal-derived, biological, and device requests that meet the checklist produce the mapped agreement, stop for document review, and create the expected recipient-side signing package after confirmation.")
    add_bullet(document, "Biological requests select the UBMTA agreement; animal-derived requests select the AUTM biological agreement for animal materials.")
    add_bullet(document, "Mixed or unsupported material categories do not receive an automatic template.")
    add_bullet(document, "Missing agreement or signer information blocks preparation instead of producing an incomplete agreement.")

    add_heading(document, "Example that requires staff review", 2)
    review_example = add_body(
        document,
        "A requester selects Chemical compound and answers the structured safety questions correctly, but writes only 'research in the chemistry class' as the purpose. The chemical checklist requires evidence that the material will not be used in humans. That sentence does not establish the condition, so the request moves to staff review. The system does not invent the missing statement or approve the request because the wording sounds generally research-related. A clear answer such as 'laboratory research only; the material will not be used in humans' provides the relevant evidence.",
    )
    review_example.paragraph_format.keep_together = True

    add_heading(document, "5 Termination wording")
    add_body(
        document,
        "Every request must state the intended project period. Eligibility for automatic processing and agreement duration are separate decisions: the checklist determines whether the request may use a standard agreement, while the entered period describes how long the recipient may use the material. The chemical and animal AUTM templates contain an existing optional termination field. In those templates, the generated agreement uses the relative phrase: 'This Agreement shall terminate [project period] after the date of the last signature.' A specific calendar date is not inserted before signing because the date of the last signature is not yet known.",
    )
    add_body(
        document,
        "The UBMTA and simple device agreements do not contain the same termination-date field, so the system does not invent a new legal term in those documents. The same rule should continue: populate the relative phrase only where the approved agreement already provides a supported field.",
    )
    add_body(
        document,
        "Store the calculated date after signing. A future webhook and database can calculate and record the date after SignNow completion, but that value would be operational metadata rather than text inside the already signed agreement.",
    )

    add_heading(document, "6 Deployment and current operational boundary")
    add_body(
        document,
        "The application runs locally or as a private Streamlit deployment. A private hosted link can be shared with approved testers after their email addresses are granted access. The deployment owner must keep the exact URL, access list, deployment branch, and secret ownership in an internal handoff record rather than in the public repository. A shareable link makes the proof of concept easier to demonstrate; it does not make the service production-ready.",
    )
    add_body(document, "The current proof of concept includes:")
    add_bullet(document, "Standalone requester interface and backend pipeline.")
    add_bullet(document, "Eligibility rules and local language-model support for permitted open-text evidence.")
    add_bullet(document, "Automatic selection and population for chemical, animal-derived, biological UBMTA, and device agreements.")
    add_bullet(document, "Final Word agreement review and immutable confirmation before delivery.")
    add_bullet(document, "One-sided recipient signature delivery through SignNow Development Mode.")
    add_bullet(document, "Readable request references and downloadable screening evidence.")
    not_included_intro = add_body(document, "The current proof of concept does not include:")
    not_included_items = [
        add_bullet(document, "U-M authentication or institutional role authorization."),
        add_bullet(document, "A production database, document repository, durable job queue, or staff administration view."),
        add_bullet(document, "Automatic retrieval and storage of the final signed PDF and SignNow completion certificate."),
        add_bullet(document, "A verified SignNow webhook receiver, status reconciliation, retry handling, or cancellation administration."),
        add_bullet(document, "Integration with U-M's electronic research administration system (eRPM) or another institutional platform."),
        add_bullet(document, "Production SignNow approval, records-retention controls, or a completed security and accessibility review."),
    ]
    not_included_intro.paragraph_format.keep_with_next = True
    for paragraph in not_included_items[:-1]:
        paragraph.paragraph_format.keep_with_next = True

    add_heading(document, "7 Production decisions and handoff")
    add_bullet(document, "Agreement formats are not standardized. Treat each approved template as versioned legal source material and maintain a template-specific renderer and regression case.")
    add_bullet(document, "The proof of concept maps biological materials directly to UBMTA, but production routing needs an additional organization-verification service. It must confirm UBMTA participation, maintain recipient-organization records, and obtain authorized-official data from a trusted source. A model may help match organization names, but it must not decide eligibility or signer authority.")
    add_bullet(document, "Agreement eligibility and agreement duration are different. The checklist controls the automatic route; the entered project period controls contract wording only where the approved template contains a duration or termination field. A future records system should calculate the final calendar date from the last signature when the business process needs it.")
    add_bullet(document, "Open-text interpretation can produce false positives and false negatives. Maintain a labeled evaluation set, report performance by checklist condition, favor thresholds that prevent false approvals, and keep an unresolved route for language the model cannot support confidently.")
    add_bullet(document, "Production ownership for authentication, hosting, database design, website integration, and operational support remains to be assigned. Name those owners before setting a production schedule.")
    add_bullet(document, "Not all production stakeholders were available during the proof of concept. The next phase should confirm the checklist, template ownership, delegated signature policy, staff-review route, records retention, and support model with the responsible offices.")
    add_bullet(document, "The application is backend-intensive. The next team should include backend and architecture capability, API and security integration experience, document-generation testing, and enough AI expertise to evaluate the local model. Legal and process owners should approve every rule or template change.")
    add_bullet(document, "Correct data population does not guarantee a polished Word layout. Normalize the approved source templates and make page-by-page visual review a release requirement.")
    add_bullet(document, "Do not place API keys in source control. Hosted secrets, access rights, logs, and deployment ownership need a controlled U-M operating model.")

    add_heading(document, "8 Research completed")
    add_bullet(document, "Compared the requester form, eligibility checklist, and agreement templates to separate intake fields, policy rules, and agreement fields.")
    add_bullet(document, "Translated each supplied checklist statement into a structured rule and defined which form fields may provide evidence for it.")
    add_bullet(document, "Evaluated a local Hugging Face natural-language inference approach for open-ended evidence, including conservative confidence thresholds and an unresolved fallback.")
    add_bullet(document, "Studied each agreement's population locations, signature blocks, optional terms, and template-specific data requirements.")
    add_bullet(document, "Implemented and tested SignNow Development Mode upload, recipient roles, one-sided invitation flow, document naming, and error handling.")
    add_bullet(document, "Researched Streamlit private hosting as a way to create a controlled demonstration link.")
    add_bullet(document, "Designed the future completed-document lifecycle: SignNow completion event, verified retrieval, checksum, database metadata, approved document storage, and institutional record linkage.")
    add_bullet(document, "Added a final review service to reduce typo, identity, and stale-document risk before SignNow delivery.")

    add_heading(document, "9 Future product development")
    add_body(
        document,
        "The recommended product direction is to mature the current standalone MTA service with U-M authentication, a persistent database, approved document storage, and completed-document retrieval from SignNow. The goal is a reliable, searchable, supportable, and auditable service that preserves the workflow already verified in this proof of concept.",
    )
    add_heading(document, "Recommended order", 2)
    future_steps = (
        ("Confirm ownership and policy. ", "Name the Innovation Partnerships process owner, template owners, U-M IT hosting and identity owner, records owner, security contact, and operational support team."),
        ("Normalize and approve templates. ", "Create controlled versions with stable population markers, consistent formatting, approved signature blocks, and a recorded template version."),
        ("Add U-M authentication. ", "Require institutional login and define requester, staff, administrator, and service permissions."),
        ("Add a production database. ", "Store the readable MTA reference, full internal identifier, normalized request, checklist evidence, rule and template versions, review confirmation, SignNow document ID, signer status, errors, and timestamps."),
        ("Connect signed documents. ", "Receive verified SignNow completion events, retrieve the final signed PDF and completion certificate, calculate checksums, store them in an approved document repository, and link their locations to the database record."),
        ("Add reconciliation and staff tools. ", "Provide search by MTA reference or SignNow document ID, show request and signing status, retry failed jobs safely, and reconcile missed webhook events."),
        ("Stabilize hosting and the link. ", "Move from an individual demonstration deployment to U-M-owned hosting with managed secrets, monitoring, backups, an agreed URL, and documented support."),
        ("Strengthen the UBMTA route. ", "Keep the current biological-to-UBMTA mapping, then add authoritative organization participation, recipient-official identity, signer authority, and staff-exception checks before production use."),
        ("Maintain representative cases. ", "Keep chemical, animal-derived, biological UBMTA, device, staff-review, boundary-length, and failure cases in the regression suite. Require all cases and visual agreement checks to pass before release."),
    )
    for number, (lead, body) in enumerate(future_steps, start=1):
        add_number(document, number, lead + body, bold_lead=lead)

    add_heading(document, "AI recommendations", 2)
    add_body(
        document,
        "Keep AI limited to evidence support, quality checks, and staff assistance. Do not use a model to replace the checklist, verify UBMTA participation, choose legal terms, approve exceptions, redline agreements, or infer missing facts. Any model change should be versioned, evaluated against approved cases, measured for false positives and false negatives, and reviewed by policy owners.",
    )
    add_body(
        document,
        "Useful additions include highlighting the sentences used as checklist evidence; detecting contradictions across answers and attachments; suggesting spelling, name, organization, and address corrections during final review; summarizing staff-review cases; and flagging missing values or broken formatting in generated documents. After a permission-controlled records database exists, semantic search could help staff find related agreements. Every suggestion must cite its source evidence, preserve the original submission, and require confirmation before changing a record or document.",
    )

    for paragraph in document.paragraphs:
        if paragraph.style.name.startswith("Heading"):
            paragraph.paragraph_format.keep_with_next = True
        for run in paragraph.runs:
            if run.font.color.rgb is None:
                run.font.color.rgb = BLACK

    return document


def main() -> None:
    document = build_document()
    document.save(OUTPUT)


if __name__ == "__main__":
    main()
