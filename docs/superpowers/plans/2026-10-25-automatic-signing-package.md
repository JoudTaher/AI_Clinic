# Automatic MTA Signing Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically route eligible standard requests, populate the correct agreement, and produce a safe U-M SignNow-ready package without an internal approval step.

**Architecture:** Keep the rules engine, document renderer, and signature delivery adapter separate. The pipeline automatically advances only deterministic standard requests and routes everything else to eRPM. A local SignNow package adapter preserves the production boundary without making network calls.

**Tech Stack:** Python, Streamlit, python-docx, pytest, U-M SignNow adapter interface

**Spec:** `docs/superpowers/specs/2026-10-25-automatic-signing-package-design.md`

## Global Constraints

- Use the exact approved material-type mapping in the spec.
- Never select the Simple Letter Agreement or a device agreement automatically in this version.
- Do not send network requests or store credentials in the repository.
- Populate only mapped agreement slots and preserve legal terms.
- Use test-first development and visually inspect every generated DOCX.

## Review Focus

- Missing or malformed categories must route to eRPM without rendering.
- Mixed categories must never select a template.
- Missing institutional or recipient signer data must not produce a sendable package.
- Reused request IDs with changed data must remain rejected.
- Generated agreements must contain the request data without altering standard legal text or layout.

---

### Task 1: Automatic selection and routing

**Files:**
- Modify: `src/templates/catalog.json`
- Modify: `src/templates/catalog.py`
- Modify: `src/templates/selector.py`
- Modify: `src/pipeline/outgoing_mta.py`
- Modify: `src/pipeline/models.py`
- Test: `tests/test_template_catalog.py`
- Test: `tests/test_template_selector.py`
- Test: `tests/test_outgoing_mta_pipeline.py`

**Interfaces:**
- Produces: deterministic `selected_template` or `routed_to_erpm` result.
- Consumes: existing eligibility and readiness results.

- [ ] Write failing tests for the three automatic mappings, disabled Simple Letter, device fallback, and approval-free pipeline.
- [ ] Run focused tests and confirm expected failures.
- [ ] Add automation metadata to the catalog and replace recommendation logic with exact material-type selection.
- [ ] Remove the named approval arguments and gate; add automatic-rule audit events and eRPM routing statuses.
- [ ] Run focused and full tests; commit.

### Task 2: Populated agreement renderer

**Files:**
- Create: `src/agreements/data.py`
- Create: `src/adapters/docx_renderer.py`
- Add: `reference_files/Template_AUTM_MTA_for_Biological_Materials.docx`
- Modify: `requirements.txt`
- Modify: `src/adapters/__init__.py`
- Test: `tests/test_docx_renderer.py`
- Test: `tests/fixtures.py`

**Interfaces:**
- Consumes: `TemplateDefinition` and normalized request data.
- Produces: `RenderedAgreement` containing a populated DOCX for the selected template.

- [ ] Write failing tests asserting populated recipient, scientist, material, address, title, shipping, and fee fields for each automated template.
- [ ] Run focused tests and confirm expected failures.
- [ ] Normalize the legacy biological source to DOCX and visually compare it with the retained source.
- [ ] Implement explicit per-template population strategies; fail on missing data or unsupported templates.
- [ ] Run focused/full tests and render every sample output to PNG for visual inspection; commit.

### Task 3: SignNow-ready package and app flow

**Files:**
- Create: `src/signing/config.py`
- Create: `src/adapters/signnow_package_sender.py`
- Modify: `src/pipeline/ports.py`
- Modify: `src/pipeline/models.py`
- Modify: `src/screening_report.py`
- Modify: `app.py`
- Modify: `README.md`
- Modify: `docs/requirements.md`
- Test: `tests/test_signnow_package_sender.py`
- Test: `tests/test_screening_report.py`
- Test: `tests/test_app_smoke.py`

**Interfaces:**
- Consumes: populated agreement, request signer data, and deployment-owned U-M signer configuration.
- Produces: local `.signing.json` manifest and `prepared_for_signature` receipt; future live SignNow sender can implement the same port.

- [ ] Write failing tests for signer roles/order, configuration failures, manifest safety, and UI/report wording.
- [ ] Run focused tests and confirm expected failures.
- [ ] Implement environment-backed U-M signer configuration and the local signing-package adapter.
- [ ] Wire the app to process eligible requests automatically and remove manual template-qualification questions.
- [ ] Run focused/full tests, compile checks, Streamlit health check, and final local review; commit.

