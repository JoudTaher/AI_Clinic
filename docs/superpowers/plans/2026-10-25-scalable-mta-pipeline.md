# Scalable MTA Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a clear modular backend with an extensible template catalog, deterministic conservative matching, approval gating, and a local dry-run delivery pipeline.

**Architecture:** Keep a modular Python monolith. New template, pipeline, and adapter packages expose small typed interfaces; the current selector remains a compatibility facade for the Streamlit app.

**Tech Stack:** Python standard library, pytest, Streamlit.

**Spec:** `docs/superpowers/specs/2026-10-25-scalable-mta-pipeline-design.md`

## Global Constraints

- Never claim a recommendation is legal approval.
- Never select when criteria are incomplete, conflicting, or mixed-category.
- Never contact a real recipient in this version.
- Preserve the existing application and report interfaces where practical.
- Add production behavior only after a failing test demonstrates it.

## Review Focus

- Missing catalog fields fail closed with a clear validation error.
- Unknown biological qualification answers return manual review.
- Conflicting biological qualification answers return manual review.
- Approval of a different template cannot render or deliver anything.
- Reusing a completed request ID cannot prepare a duplicate delivery.

---

### Task 1: Configurable template catalog and deterministic matcher

**Files:**
- Create: `src/templates/__init__.py`
- Create: `src/templates/catalog.py`
- Create: `src/templates/selector.py`
- Create: `src/templates/catalog.json`
- Modify: `src/template_selector.py`
- Test: `tests/test_template_catalog.py`
- Modify: `tests/test_template_selector.py`

**Interfaces:**
- Produces: `load_template_catalog(path: Path | None = None) -> tuple[TemplateDefinition, ...]`
- Produces: `select_template(request, eligibility_result, catalog=None) -> dict[str, Any]`
- Preserves: `evaluate_template_selection(request, eligibility_result) -> dict[str, Any]`

- [ ] Write failing catalog validation and selector behavior tests.
- [ ] Run the focused tests and confirm failures are caused by missing modules/behavior.
- [ ] Implement immutable catalog models, JSON validation, and conservative rule matching.
- [ ] Make the legacy selector delegate to the new selector.
- [ ] Run focused and full test suites.
- [ ] Commit Task 1.

### Task 2: Approval-gated idempotent pipeline

**Files:**
- Create: `src/pipeline/__init__.py`
- Create: `src/pipeline/models.py`
- Create: `src/pipeline/ports.py`
- Create: `src/pipeline/outgoing_mta.py`
- Test: `tests/test_outgoing_mta_pipeline.py`

**Interfaces:**
- Consumes: `select_template(...)`
- Produces: `OutgoingMTAPipeline.run(request_id, request, approved_template_id=None, approved_by=None) -> PipelineResult`
- Produces: renderer, sender, and idempotency-store protocols.

- [ ] Write failing tests for review blocking, approval mismatch, successful preparation, and idempotency.
- [ ] Run focused tests and confirm the expected failures.
- [ ] Implement pipeline states and approval/idempotency guards.
- [ ] Run focused and full test suites.
- [ ] Commit Task 2.

### Task 3: Reference-template renderer and dry-run sender

**Files:**
- Create: `src/adapters/__init__.py`
- Create: `src/adapters/reference_renderer.py`
- Create: `src/adapters/dry_run_sender.py`
- Test: `tests/test_delivery_adapters.py`

**Interfaces:**
- Consumes: catalog `source_file`, pipeline renderer/sender protocols.
- Produces: copied agreement artifact and local JSON email package.

- [ ] Write failing tests for safe filenames, exact template bytes, and local-only email packages.
- [ ] Run focused tests and confirm expected failures.
- [ ] Implement the adapters using `pathlib`, `shutil`, and `json` only.
- [ ] Run focused and full test suites.
- [ ] Commit Task 3.

### Task 4: Report and Streamlit integration

**Files:**
- Modify: `app.py`
- Modify: `src/screening_report.py`
- Modify: `tests/test_app.py`
- Modify: `tests/test_screening_report.py`

**Interfaces:**
- Consumes: template qualification answers and selector result.
- Produces: visible recommendation/manual-review reasons and report data.

- [ ] Write failing app/report tests for the two qualification questions and recommended template output.
- [ ] Run focused tests and confirm expected failures.
- [ ] Add the two inputs, request mapping, and clearer result rendering.
- [ ] Run focused and full test suites.
- [ ] Commit Task 4.

### Task 5: Documentation and final verification

**Files:**
- Modify: `README.md`
- Modify: `docs/requirements.md`

**Interfaces:**
- Documents catalog extension, dry-run pipeline, and live-integration boundaries.

- [ ] Document the new structure and how to add a template.
- [ ] Run the complete tests, syntax compilation, diff check, and Streamlit startup smoke test.
- [ ] Request whole-branch code review and resolve critical/important findings with TDD.
- [ ] Commit Task 5 and finish the branch.
