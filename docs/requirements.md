# Outgoing MTA Proof of Concept Requirements

## Source boundaries

The supplied eRPM PDF defines requester questionnaire fields. The supplied eligibility checklist alone defines whether a request qualifies for automatic approval. The supplied agreement templates define agreement population and signature fields. Data from one layer must not be presented as if it came from another.

## Requester questionnaire

The questionnaire follows the source form's Introduction, Personnel, Material Details, Material Safety, and Outgoing Material Details sections. The eRPM-only “copy an existing UFA record” action is omitted because this standalone app has no eRPM record source. There is no requester-entered request identifier.

Missing questionnaire information is reported separately and does not alter checklist rules.

## Automatic approval

The checklist is never displayed as requester input. The backend derives every checklist fact that the questionnaire proves directly. Facts that require institutional data are accepted only through a separate trusted backend verification input, never from the requester payload.

Every request evaluates checklist Section A. Chemical, biological, device, and animal-material requests also evaluate Sections B, C, D, and E respectively.

- Every applicable statement is true: eligible for automatic approval.
- Any applicable statement is false: route to the Standard MTA Process.
- Any statement is unanswered or the material category is unsupported or ambiguous: route to the Standard MTA Process.

The checklist refers to Sections B through F, but the supplied checklist contains no Section F.

The standalone questionnaire does not prove every checklist fact, including recipient non-profit status, U-M ownership and restrictions, and internal non-commercial use. Those facts remain unresolved and route to eRPM until an institutional verification source is connected.

## Agreement mapping

- Animal materials → AUTM MTA for Biological Materials
- Biological materials → UBMTA Implementing Letter
- Chemical materials → AUTM MTA for Chemical Materials
- Devices → Simple Letter Agreement

Mixed material categories never select an agreement automatically. Standard legal terms are unchanged; each template has an explicit tested population strategy.

The combined “Other Model Organism (yeast, drosophila, zebrafish)” questionnaire option is routed to eRPM because it does not identify one unambiguous checklist section.

## Pipeline

The backend follows `questionnaire completeness -> derive checklist facts -> apply trusted system verifications -> checklist decision -> template selection -> agreement-data completeness -> DOCX population -> signing package`.

The pipeline derives an internal deterministic submission identifier from the normalized submission. It is not a requester input and is not displayed as a form field. Identical submissions do not prepare duplicate packages within one pipeline store.

The local signing manifest contains the populated document path and hash, internal submission and template identifiers, audit events, and required signer identities, roles, and order. The relevant PI is the provider signer under the delegation stated in the checklist. Missing or invalid signer data stops package preparation.

## Current boundary

The app does not connect to eRPM or SignNow and makes no network requests. Authentication, persistent production storage, live e-signature submission, and eRPM integration remain outside this proof of concept.
