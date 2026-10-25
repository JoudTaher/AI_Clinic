# Scalable MTA Pipeline Design

## Intent

Turn the working local PoC into a clear modular backend that can grow to many
agreement templates and eventually deliver approved agreements without hiding
legal or operational uncertainty.

## Safety and scope

- Template matching is deterministic and explainable.
- A match is a recommendation, never legal approval.
- Ambiguous, incomplete, mixed-category, or unsupported requests stop for
  manual review.
- Delivery always requires an explicit approver and an exact match between the
  approved template and the recommendation.
- This version provides a dry-run delivery adapter only. It writes an email
  package locally and never contacts a real recipient.
- The four supplied agreements are the initial catalog. More templates are
  added through catalog data and a source file, without changing selector code.

## Architecture

Use a modular Python monolith. `src/templates/` owns catalog loading and rule
matching. `src/pipeline/` owns workflow states and approval/idempotency rules.
`src/adapters/` owns file rendering and dry-run delivery. The existing
`src/template_selector.py` remains a compatibility facade for the Streamlit app
and existing callers.

For a single eligible chemical category, recommend the AUTM chemical template.
For a single eligible biological category, require two explicit qualification
answers: recipient UBMTA signatory status and whether a Simple Letter Agreement
has been authorized. Recommend UBMTA when only its condition is true, Simple
Letter when only its authorization is true, and AUTM Biological when both are
explicitly false. Unknown or conflicting answers require manual review.

## Initial pipeline

`screen -> recommend -> approve -> copy source template -> prepare dry-run email`

Every result includes a status and reasons. A request ID is idempotent: a
successfully prepared request is returned rather than prepared a second time.

## Non-goals

- No invented UM legal rules beyond the explicit conservative qualification
  inputs above.
- No live email, eRPM, e-signature, SSO, database, or production deployment.
- No automatic filling or editing of the legal template text in this phase.

## Approaches considered

1. Keep adding conditions to `template_selector.py`: smallest diff, but brittle
   and difficult to extend or audit.
2. Configurable catalog plus modular pipeline (chosen): clear, testable, and
   expandable while staying small.
3. Microservices and a workflow engine: unnecessary operational complexity for
   this PoC.
