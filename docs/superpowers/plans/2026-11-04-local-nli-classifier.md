# Local NLI Classifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace regex phrase matching with a clean, local Hugging Face NLI classifier for open-ended checklist evidence.

**Architecture:** Move checklist definitions into one authoritative module. Keep structured rules deterministic and isolate model loading, batched inference, confidence policy, and evidence in `src/semantic_classifier.py`.

**Tech Stack:** Python, Transformers, PyTorch, Hugging Face `facebook/bart-large-mnli`, pytest, Streamlit resource caching through process-level lazy loading.

**Spec:** `docs/superpowers/specs/2026-11-04-local-nli-design.md`

## Global Constraints

- No pass/fail phrase lists or regex semantic fallback.
- Only confident entailment or contradiction produces a boolean result.
- Neutral, low-confidence, or unavailable-model results stay unresolved.
- Structured Yes/No questionnaire rules remain deterministic.
- Checklist statements exist in exactly one production module.

## Review Focus

- Paraphrases that do not reuse checklist wording.
- Negated and contradictory statements.
- Conflicting statements across different open-text fields.
- Empty text and unavailable model behavior.
- Model loading and inference do not repeat on every Streamlit rerun.

---

### Task 1: Authoritative checklist catalog

**Files:** Create `src/checklist.py`; modify `src/eligibility.py`; test `tests/test_eligibility.py`.

**Interfaces:** Produces `SECTION_CRITERIA`, `CATEGORY_TO_SECTION`, and `all_criteria()`.

- [ ] Add a failing test proving every eligibility fact comes from the shared checklist catalog.
- [ ] Move the existing checklist definitions without changing their text or IDs.
- [ ] Run the focused and full eligibility tests.

### Task 2: Local NLI classifier

**Files:** Create `src/semantic_classifier.py`; delete `src/semantic_rules.py`; replace `tests/test_semantic_rules.py` with `tests/test_semantic_classifier.py`; modify `requirements.txt`.

**Interfaces:** Produces `analyze_open_text(values, criteria, classifier=None)` and a cached local classifier implementing `predict(pairs)`.

- [ ] Add failing tests for paraphrase, contradiction, conflict, neutral, and model-unavailable behavior.
- [ ] Implement batched NLI inference and conservative aggregation.
- [ ] Install dependencies, download the model, and run the focused tests.

### Task 3: Eligibility integration and cleanup

**Files:** Modify `src/eligibility.py`, `tests/test_eligibility.py`, and `README.md`.

**Interfaces:** Eligibility passes applicable checklist criteria to the semantic classifier and exposes auditable assessment metadata.

- [ ] Add a failing end-to-end test for the submitted chemical-classroom case.
- [ ] Wire the classifier into eligibility and remove all old method names and regex references.
- [ ] Run the complete test suite and search for obsolete semantic-rule remnants.
