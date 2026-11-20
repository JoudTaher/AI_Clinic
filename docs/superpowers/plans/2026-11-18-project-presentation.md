# Outgoing MTA Project Presentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and validate a 12-slide PowerPoint presentation that tells the outgoing MTA automation project story.

**Architecture:** Author the deck with editable PowerPoint text and native process diagrams using `@oai/artifact-tool`. Embed existing project screenshots and the Innovation Partnerships logo, then finalize and visually inspect every slide.

**Tech Stack:** JavaScript ES modules, `@oai/artifact-tool`, bundled presentation finalizer, PowerPoint PPTX.

**Spec:** `docs/superpowers/specs/2026-11-18-project-presentation-design.md`

## Global Constraints

- Exactly 12 slides in 16:9 format.
- U-M colors with readable contrast and no decorative template clutter.
- Editable flow diagrams and accurate project screenshots.
- No unsupported impact numbers or production-readiness claims.
- Private demo URL appears only as a labeled placeholder.

## Review Focus

- Current automated routing must show biological materials using UBMTA and animal-derived materials using the AUTM biological agreement.
- BART must appear as bounded evidence support, not autonomous approval.
- Provider-side signature and recipient-side SignNow invitations must not be conflated.
- Database and signed-document retrieval must be labeled future work.
- Screenshots, diagrams, and slide text must remain legible when projected.

---

### Task 1: Author the deck

**Files:**
- Create: `scripts/build_project_presentation.mjs`
- Create: `docs/presentation/Outgoing_MTA_Automation_Presentation_Deck.pptx`

**Interfaces:**
- Consumes: project guide, README, logo, user-supplied interface screenshots.
- Produces: editable 12-slide PowerPoint presentation.

- [x] Build the 12-slide narrative in the approved order.
- [x] Create editable workflow, decision, routing, and signing diagrams.
- [x] Embed the two clearest interface screenshots and the project logo.
- [x] Export a draft and finalize it with the bundled validation tool.

### Task 2: Validate and repair

**Files:**
- Verify: `docs/presentation/Outgoing_MTA_Automation_Presentation_Deck.pptx`

**Interfaces:**
- Consumes: finalized presentation.
- Produces: verified slide renders and validation evidence.

- [x] Render all 12 slides.
- [x] Inspect every slide at full size for overflow, overlap, clipping, and readability.
- [x] Repair and refinalize any affected slides.
- [x] Confirm content coverage against the design before delivery.
