# Required Titles, Searchable Reference, and Termination Period Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Require every title used by an applicable agreement, give each request one readable reference used across review/delivery artifacts, and populate the existing AUTM termination option with the project period measured from the last signature.

**Architecture:** Keep the full SHA-256 submission ID as the immutable idempotency key and derive a separate `MTA-YYYY-XXXXXXXX` tracking reference from it. Inject that reference into the normalized downstream request only after hashing so rendering, reporting, local delivery, and SignNow share one value without changing eligibility. Agreement readiness and population own template-specific title requirements; the DOCX renderer owns the existing-template termination text.

**Tech Stack:** Python 3.11, Streamlit, python-docx/lxml DOCX processing, pytest, SignNow REST adapter.

**Spec:** `docs/requirements.md`

## Global Constraints

- Provider Scientist academic/job title is required for every automatically generated agreement.
- Recipient Scientist academic/job title is required for every supported agreement. The Simple Letter Agreement prints it beneath the scientist's name in the existing information cell.
- Recipient Authorized Official title remains required.
- The final review is unavailable until every applicable required title is present.
- The readable reference format is `MTA-YYYY-XXXXXXXX`; the full SHA submission ID remains internal.
- The same readable reference appears in final review, generated filenames, SignNow upload names, screening reports, and delivery results.
- Existing AUTM termination options are populated as the requested project period after the date of the last signature; templates without such a clause are not altered.
- UBMTA is the active biological-material route; authoritative organization and signer verification remain future production work.

## Review Focus

- Device agreements must require both scientist titles and print the recipient title beneath the Recipient Scientist's name.
- A request must keep the same reference through preview and confirmed delivery.
- SignNow upload names must be searchable but filesystem-safe generated filenames must remain portable.
- A zero or missing duration must continue to block readiness before termination population.
- AUTM termination population must activate the existing optional term without changing unrelated legal text.

---

### Task 1: Applicable title validation

**Files:**
- Modify: `app.py`
- Modify: `src/agreement_readiness.py`
- Modify: `src/agreements/data.py`
- Test: `tests/test_app.py`
- Test: `tests/test_agreement_readiness.py`
- Test: `tests/test_docx_renderer.py`

**Interfaces:**
- Produces: template-aware required title fields consumed by review and rendering.

- [x] Add failing tests for required labels, readiness blocking, and renderer rejection.
- [x] Run targeted tests and confirm failure.
- [x] Require provider title globally and recipient title for AUTM/UBMTA templates; remove “if known” labels.
- [x] Run targeted tests and confirm pass.

### Task 2: Stable searchable tracking reference

**Files:**
- Create: `src/request_identity.py`
- Modify: `src/pipeline/models.py`
- Modify: `src/pipeline/outgoing_mta.py`
- Modify: `src/adapters/docx_renderer.py`
- Modify: `src/adapters/signnow_api_sender.py`
- Modify: `src/adapters/signnow_package_sender.py`
- Modify: `src/screening_report.py`
- Modify: `app.py`
- Test: `tests/test_outgoing_mta_pipeline.py`
- Test: `tests/test_docx_renderer.py`
- Test: `tests/test_signnow_api_sender.py`
- Test: `tests/test_signnow_package_sender.py`
- Test: `tests/test_screening_report.py`

**Interfaces:**
- Produces: `submission_identity(request, verified_facts, now=None) -> SubmissionIdentity` with `submission_id` and `tracking_reference`.
- Produces: `PipelineResult.tracking_reference: str`.

- [x] Add failing format, consistency, filename, report, UI, and SignNow upload-name tests.
- [x] Run targeted tests and confirm failure.
- [x] Centralize identity generation and thread the readable reference through downstream request data and results.
- [x] Use the reference in generated filenames, local manifests, SignNow upload names, reports, and UI results.
- [x] Run targeted tests and confirm pass.

### Task 3: Existing AUTM termination option

**Files:**
- Modify: `src/agreements/data.py`
- Modify: `src/adapters/docx_renderer.py`
- Test: `tests/test_docx_renderer.py`

**Interfaces:**
- Consumes: canonical `requested_duration` from `normalize_request()`.
- Produces: checked AUTM Exhibit B text, “This Agreement shall terminate [duration] after the date of the last signature.”

- [x] Add failing renderer tests for chemical and animal templates and a non-AUTM preservation test.
- [x] Run targeted tests and confirm failure.
- [x] Populate and check only the existing AUTM termination option.
- [x] Run targeted tests and confirm pass.

### Task 4: Product documentation and full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/requirements.md`
- Modify: `docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx`

**Interfaces:**
- Consumes: implemented behavior from Tasks 1–3.

- [x] Update concise technical and product documentation, including future database use of the reference and the active UBMTA route.
- [x] Render the Word document and inspect every page.
- [x] Run the complete pytest suite.
- [x] Review the final diff for stale labels, long user-facing IDs, and inconsistent termination/reference wording.
