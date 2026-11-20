# Concise Project Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current 25-page report with a minimal, accurate, no-table project overview and handoff guide of no more than 10 pages.

**Architecture:** Rebuild the DOCX from scratch using the repository and verified tests as the authority. Use a simple black-and-white Word style with headings, paragraphs, numbered workflow steps, and short bullet lists.

**Tech Stack:** python-docx, bundled document renderer, pytest evidence.

**Spec:** `docs/superpowers/specs/2026-11-18-concise-project-guide-design.md`

## Global Constraints

- Maximum 10 pages.
- No tables, colors, code snippets, comparison matrix, decorative blocks, or duplicated explanations.
- Clearly label current behavior and future recommendations.
- Preserve the requested termination-date explanation and UBMTA handoff warning.

## Review Focus

- Do not present database, signed-document retrieval, authentication, or UBMTA automation as implemented.
- Keep the one-sided provider-signature flow distinct from recipient-side SignNow invitations.
- Explain BART as supporting open-text checklist evidence, not replacing the rules engine.
- Explain the manual-review example as unresolved evidence, not an automatic rejection.
- Keep the rendered document within 10 pages without cramped text.

---

### Task 1: Rebuild the guide

**Files:**
- Modify: `docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx`
- Create: `scripts/build_concise_project_guide.py`

**Interfaces:**
- Consumes: current repository behavior, verified tests, and the approved design.
- Produces: a concise Word handoff guide.

- [x] Replace the existing content with the approved section order.
- [x] Apply a minimal black-and-white style with no tables.
- [x] Include current workflow, technology rationale, rejection example, handoff risks, research, and future recommendations.

### Task 2: Verify the guide

**Files:**
- Verify: `docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx`

**Interfaces:**
- Consumes: Task 1 DOCX.
- Produces: verified page count and visual quality evidence.

- [x] Render the DOCX using the bundled renderer.
- [x] Confirm the page count is no more than 10.
- [x] Inspect every rendered page for clipping, overlap, broken lists, and unnecessary whitespace.
- [x] Revise and rerender until clean.
