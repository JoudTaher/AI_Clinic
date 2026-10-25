# Outgoing MTA Proof of Concept Requirements

## Eligibility

All requests evaluate Section A. Chemical, biological, device, and animal-derived selections additionally evaluate Sections B, C, D, and E respectively. Multiple selections evaluate every applicable section.

- Every applicable answer is confirmed true: `eligible`.
- Any applicable answer is false: `ineligible` for the Streamlined Template Process.
- An answer is missing, the category is missing, or the request is outside documented scope: `needs_review`.

The checklist refers to Sections B through F, but no Section F is present.

## eRPM-Aligned Intake

The form follows the submitted worksheet's Introduction, Personnel, Material Details, Material Safety, and Outgoing Material Details sections. It includes the worksheet's material-type choices, recipient contacts, safety and export questions, experimental plan, relevant details, document upload, and sponsor field. Missing intake information is reported separately and never changes checklist eligibility.

## Template Selection

Template definitions live in a validated JSON catalog. Adding a template must not require selector-code changes.

- A single eligible chemical request recommends AUTM Chemical.
- A single eligible biological request recommends UBMTA only when the recipient is explicitly confirmed as a UBMTA signatory and Simple Letter authorization is false.
- A single eligible biological request recommends the Simple Letter Agreement only when that agreement is explicitly authorized and UBMTA signatory status is false.
- A single eligible biological request recommends AUTM Biological when both qualification answers are explicitly false.
- Missing answers, conflicting answers, mixed categories, and unsupported categories require manual review.

A recommendation is not final selection or legal approval. Generation or delivery preparation requires a named approver and an exact match between the approved and recommended template IDs.

## Pipeline

The modular backend follows `screen -> recommend -> approve -> copy source template -> prepare dry-run email`. A completed request ID is idempotent and cannot prepare a duplicate delivery within the pipeline store. Rendering preserves the supplied source template bytes; it does not alter legal language. The sender writes an inspectable local JSON package and performs no network action.

## Scope

This local application is not connected to eRPM, does not provide legal approval, does not automate signatures, and does not send email. Use synthetic data only. Production storage, Outlook or Microsoft Graph, e-signature, SSO, and eRPM integrations are outside this version.
