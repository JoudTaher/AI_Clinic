# Agreement Template Naming Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every template filename and internal template ID match Chemical, Biological, Animal, or Device material without changing legal content or workflow behavior.

**Architecture:** The catalog is the source of truth for category-to-template selection. Runtime adapters consume the catalog's stable material-oriented IDs, while renderer-specific functions continue handling each legal document structure.

**Tech Stack:** Python, Streamlit, pytest, DOCX/OOXML, JSON

**Spec:** `docs/superpowers/specs/2026-11-05-template-naming-design.md`

## Global Constraints

- Use the exact four IDs and filenames in the spec.
- Preserve eligibility behavior, populated fields, signing roles, and signing order.
- Do not modify the supplied legal text.
- Do not commit unrelated existing worktree changes.

## Review Focus

- A category selects exactly one correctly named agreement.
- Every catalog path exists and points to the intended DOCX.
- Each renderer still populates its supplied template structure.
- SignNow tagging and signer planning accept all four new IDs.
- No stale IDs or filenames survive in runtime code, tests, or reference metadata.

---

### Task 1: Establish canonical catalog and reference filenames

**Files:**
- Modify: `tests/test_template_catalog.py`
- Modify: `tests/test_template_selector.py`
- Modify: `tests/test_reference_files.py`
- Modify: `src/templates/catalog.json`
- Rename: `reference_files/Template_AUTM_Animaldocx` to `reference_files/Template_AUTM_Animal.docx`

**Interfaces:**
- Produces: four canonical template IDs and paths consumed by all later tasks.

- [ ] Write expectations for the four canonical IDs, filenames, and selection outcomes.
- [ ] Run focused tests and confirm failure on old catalog values.
- [ ] Rename the Animal file and update the catalog minimally.
- [ ] Run focused tests and confirm catalog/selector behavior passes.

### Task 2: Migrate runtime adapters and form branches

**Files:**
- Modify: `app.py`
- Modify: `src/adapters/docx_renderer.py`
- Modify: `src/adapters/signnow_api_sender.py`
- Modify: `src/agreements/data.py`
- Modify: `src/agreement_readiness.py`
- Modify: `src/signing/plan.py`
- Modify: affected unit tests under `tests/`

**Interfaces:**
- Consumes: canonical IDs from Task 1.
- Produces: unchanged population and signing behavior under the new IDs.

- [ ] Change tests to use the four canonical IDs and run them to observe failures.
- [ ] Replace runtime branches and constants with the canonical IDs.
- [ ] Run renderer, readiness, signing, pipeline, and app tests to green.

### Task 3: Synchronize reference metadata and verify generated agreements

**Files:**
- Modify: `reference_files/manifest.json`
- Modify: `reference_files/README.md`
- Modify: remaining tests containing old names.

**Interfaces:**
- Consumes: final reference filenames and runtime IDs.
- Produces: reproducible reference hashes and verified generated agreements.

- [ ] Update reference-file expectations and confirm they fail against stale metadata.
- [ ] Recompute SHA-256 hashes and update the manifest and README.
- [ ] Run the full test suite and a repository-wide stale-name search.
- [ ] Generate all four agreements, render each to PNG, and inspect every page.
