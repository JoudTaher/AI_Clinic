# Final Agreement Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Require review and confirmation of an immutable populated agreement before any SignNow or local signing delivery.

**Architecture:** A focused review module builds the exact review model and snapshot reference from normalized agreement data, signer data, and rendered bytes. The pipeline adds a prepare-before-send gate, and Streamlit presents the resulting values, warnings, DOCX, and confirmation control.

**Tech Stack:** Python, Streamlit, python-docx/OOXML renderer, pytest, Streamlit AppTest, python-docx documentation editing

**Spec:** `docs/superpowers/specs/2026-11-11-final-agreement-review-design.md`

## Global Constraints

- SignNow and local delivery must not run without confirmation of the current generated snapshot.
- Confirmation must become invalid when questionnaire data, template content, or rendered output changes.
- Warnings must never silently edit user or legal text.
- Documentation must describe verified code, not proposed behavior.

## Review Focus

- Confirmation missing: render once, sender never called.
- Stale confirmation: changed request or DOCX cannot be sent.
- Invalid email: existing validation remains blocking before review.
- Technical terminology: spelling warnings remain non-blocking and never mutate text.
- Streamlit reruns: the current review persists only for its snapshot and is replaced after edits.

---

### Task 1: Review snapshot and warnings

**Files:**
- Create: `src/agreement_review.py`
- Test: `tests/test_agreement_review.py`

**Interfaces:**
- Produces: `build_agreement_review(request, template_id, artifact) -> AgreementReview`

- [ ] Write failing tests for exact fields, signer identities, warnings, and stable/change-sensitive snapshot references.
- [ ] Run the tests and verify the expected failures.
- [ ] Implement the minimal review model and warning rules.
- [ ] Run the tests and verify they pass.

### Task 2: Pipeline confirmation gate

**Files:**
- Modify: `src/pipeline/models.py`
- Modify: `src/pipeline/outgoing_mta.py`
- Modify: `tests/test_outgoing_mta_pipeline.py`

**Interfaces:**
- Produces: `OutgoingMTAPipeline.run(request, confirmed_review_reference=None)` and `PipelineResult.review_reference`.

- [ ] Write failing tests proving render-before-review, no delivery without confirmation, successful confirmed delivery, and stale-reference rejection.
- [ ] Run the tests and verify the expected failures.
- [ ] Add the review-required pipeline state and enforce exact-reference confirmation.
- [ ] Run pipeline tests and verify they pass.

### Task 3: Streamlit final review interaction

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: pipeline review-required state and agreement review fields/warnings.

- [ ] Write failing AppTest assertions for preparing a review, displaying the DOCX and values, requiring confirmation, and preventing an unconfirmed send.
- [ ] Run the tests and verify the expected failures.
- [ ] Implement the final review container, correction guidance, confirmation checkbox, and confirmed delivery action.
- [ ] Run AppTest and verify it passes.

### Task 4: Product and technical documentation

**Files:**
- Modify: `docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx`
- Modify: `README.md`

**Interfaces:**
- Documents only verified Task 1-3 behavior and existing semantic-classifier code.

- [ ] Update the Word documentation with the review service, typo-control workflow, pipeline state, and detailed local NLP section.
- [ ] Update the README workflow summary.
- [ ] Render the DOCX to PNG, inspect every page, and correct layout defects.
- [ ] Run the full test suite and verify all tests pass.

