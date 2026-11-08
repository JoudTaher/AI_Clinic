# Template Workflow Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize template-specific signer requirements and ordering so validation,
UI explanation, local packages, and SignNow delivery cannot disagree.

**Architecture:** A new pure workflow module builds a canonical signer plan from the
selected template and normalized agreement information. Existing layers consume that
plan rather than reproducing template branches.

**Tech Stack:** Python, dataclasses, pytest, Streamlit

**Spec:** `docs/superpowers/specs/2026-11-05-template-workflow-design.md`

## Global Constraints

- Eligibility and template selection remain unchanged.
- Administrative contacts never gain signing authority implicitly.
- Signer emails are invitation destinations and are not printed in agreements.
- Missing or invalid signer data must fail before upload or invitation.

## Review Focus

- UBMTA Recipient Scientist can certify: one recipient identity fills two roles.
- UBMTA Recipient Scientist cannot certify: a separate authorized official is required.
- AUTM uses Recipient Authorized Signatory then Provider Scientist.
- Simple Letter uses Recipient Scientist and Recipient Authorized Signatory before Provider Scientist.
- Incomplete preview data remains displayable while strict delivery fails closed.

---

### Task 1: Canonical signer plan

**Files:**
- Create: `src/signing/plan.py`
- Test: `tests/test_signing_plan.py`

**Interfaces:**
- Produces: `build_signer_plan(template_id, information, strict=True) -> SignerPlan`

- [ ] Write failing tests for every template, both UBMTA certification branches, and missing data.
- [ ] Run the tests and confirm they fail because the module does not exist.
- [ ] Implement immutable signer/role plan objects and the plan builder.
- [ ] Run the signer-plan tests.

### Task 2: Backend consumers

**Files:**
- Modify: `src/adapters/signnow_package_sender.py`
- Modify: `src/agreement_readiness.py`
- Test: `tests/test_signnow_package_sender.py`
- Test: `tests/test_agreement_readiness.py`

**Interfaces:**
- Consumes: `build_signer_plan(...)`

- [ ] Add failing tests proving both consumers use the canonical plan.
- [ ] Replace duplicated signer branches and signer-field validation.
- [ ] Run package and readiness tests.

### Task 3: UI preview

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: non-strict `build_signer_plan(...)`

- [ ] Add failing tests for exact identity sources and signing order.
- [ ] Replace UI template branching with the canonical preview plan.
- [ ] Run Streamlit app tests.

### Task 4: Verification

**Files:**
- No production changes expected.

- [ ] Run the focused signing, readiness, API, pipeline, and app suites.
- [ ] Run the complete pytest suite.
- [ ] Review the diff for duplicated signer-routing rules.
