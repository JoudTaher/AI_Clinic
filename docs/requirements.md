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

- A single eligible chemical request selects AUTM Chemical.
- A single eligible biological request selects the UBMTA Implementing Letter.
- A single eligible non-living animal-derived request selects AUTM Biological.
- Device, mixed, missing, unsupported, or failed-eligibility requests route to eRPM.
- The Simple Letter Agreement is not selected until Innovation Partnerships confirms its rule.

No internal template-approval step exists on the documented standard path.

## Pipeline

The modular backend follows `intake -> completeness -> eligibility -> automatic selection -> DOCX population -> signing package`. A completed request ID is idempotent and cannot prepare a duplicate package within the pipeline store. Each supported agreement has an explicit slot map; standard legal text is not rewritten.

The local package contains only the populated document reference and hash, request/template identifiers, audit events, and required signer roles, identities, and order. U-M institutional signer identity comes from `MTA_UM_SIGNER_NAME`, `MTA_UM_SIGNER_TITLE`, and `MTA_UM_SIGNER_EMAIL`. Missing or invalid signer data stops package preparation.

## Scope

This local application does not connect to eRPM or SignNow and makes no network request. It creates a SignNow-ready manifest for later adapter integration. Authentication, production persistence, live e-signature submission, and eRPM integration remain outside this version.
