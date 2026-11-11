# Chemical Structure Confidentiality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the source-form chemical structure confidentiality question without turning it into an eligibility rule.

**Architecture:** The Streamlit form conditionally captures a boolean in `erpm_intake`. Intake readiness owns its conditional requiredness, while the input-usage registry records it only as request/audit context; eligibility and template modules remain unchanged.

**Tech Stack:** Python, Streamlit, pytest, `st.testing.v1.AppTest`

**Spec:** `docs/superpowers/specs/2026-11-11-chemical-structure-confidentiality-design.md`

## Global Constraints

- The field is required only when `Chemical compound` is selected.
- The field must never affect eligibility, template selection, agreement population, or signing.
- Use the canonical field ID `chemical_structure_confidential`.

## Review Focus

- Chemical-only request shows the question and requires an answer.
- Non-chemical request does not show or require the question.
- Mixed material selection including chemical still shows and requires it.
- The submitted value has an explicit backend use and is not an eligibility input.
- Existing chemical eligibility results do not change when the confidentiality answer changes.

---

### Task 1: Conditional questionnaire field

**Files:**
- Modify: `app.py`
- Modify: `src/intake.py`
- Modify: `src/input_usage.py`
- Modify: `tests/test_app.py`
- Modify: `tests/test_intake.py`
- Modify: `tests/test_input_usage.py`
- Modify: `tests/test_eligibility.py`

**Interfaces:**
- Consumes: `erpm_intake.material_types: list[str]`
- Produces: `erpm_intake.chemical_structure_confidential: bool` for chemical requests

- [ ] **Step 1: Add failing UI, readiness, usage, and eligibility-independence tests.**
- [ ] **Step 2: Run the focused tests and verify they fail because the field is absent.**
- [ ] **Step 3: Add the conditional Streamlit input, conditional readiness validation, payload field, error copy, and audit/context usage mapping.**
- [ ] **Step 4: Run focused tests, then the broader non-semantic regression suite.**
- [ ] **Step 5: Review the diff for any eligibility or template-selection dependency on the new field.**

