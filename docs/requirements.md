# Outgoing MTA Proof of Concept Requirements

## Source boundaries

The supplied eRPM PDF defines requester questionnaire fields. The supplied eligibility checklist alone defines whether a request qualifies for automatic approval. The supplied agreement templates define agreement population and signature fields. Data from one layer must not be presented as if it came from another.

## Requester questionnaire

The questionnaire follows the source form's Introduction, Personnel, Material Details, Material Safety, and Outgoing Material Details sections. The eRPM-only “copy an existing UFA record” action is omitted because this standalone app has no eRPM record source. There is no requester-entered request identifier.

Required fields are marked in the interface. Missing or malformed questionnaire information is reported beside the relevant field and separately from eligibility; it does not alter checklist rules. Signing-email syntax is validated before agreement preparation. Eligibility failures remain checklist results rather than being presented as form-validation errors.

## Automatic approval

The checklist is never displayed as requester input. The backend derives each checklist fact from deterministic structured questionnaire answers and, only where the source form provides narrative evidence, local Hugging Face semantic classification. A trusted backend verification can supplement facts that institutional systems prove independently.

Every request evaluates checklist Section A. Chemical, biological, device, and animal-material requests also evaluate Sections B, C, D, and E respectively.

- Every applicable statement is true: eligible for Standard MTA automatic approval.
- Any applicable statement is false: require manual special-case MTA review.
- Any statement is unanswered or the material category is unsupported or ambiguous: require manual special-case MTA review.

The checklist refers to Sections B through F, but the supplied checklist contains no Section F.

The text analyzer uses the free `facebook/bart-large-mnli` model through Hugging Face Transformers. It performs direct natural-language inference and, where contextual inference is required, zero-shot semantic-category classification. It contains no regex pass/fail phrase dictionary. Only relevant form fields defined by the checklist catalog are evaluated. Low-confidence or neutral results remain unresolved and require manual special-case review. Every semantic decision records its source field, model scores, and decision method in the screening report. The model is downloaded once and then runs locally; form content is not sent to a hosted inference service.

Structured proxies are limited to the checklist comparison documented by the supplied sources: recipient organization type plus domestic-transfer answer, third-party-material answer, invention/licensing answer, funding answer, human-material/data answers, export-control answer, return answer, and category-specific safety answers. A negative or unresolved signal is never converted to a pass by text.

The general checklist rules use the submitted questionnaire as follows:

- A domestic destination plus a recipient name identifying a university, college, non-profit, research organization/institute, or research/medicine department satisfies the U.S. non-profit rule. A foreign destination or company/corporate entity fails it; an unrecognized entity remains unresolved. Email domains are not used for this eligibility decision; authentication and institutional verification are separate future concerns.
- “No” to materials made using another party's or commercially purchased materials satisfies the ownership/no-third-party-restrictions rule. “Yes” requires review unless other evidence explicitly resolves the restriction.
- “No” to purchasing a product/service, a qualifying non-profit recipient, and a completed recipient experimental plan satisfy the internal non-commercial-research rule. Explicit commercial or product-development language overrides that result and fails the rule.
- “No” to the prior U-M invention-report/licensing question satisfies the invention-report/patent/encumbrance rule. “Yes” fails it.
- The remaining general and material-specific rules use their corresponding funding, human-material/data, export-control, return, material-type, safety, and narrative-use answers. Deterministic structured answers are authoritative. An explicit contradiction in Other Relevant Details can override a structured pass; unrelated descriptive fields cannot.

Material description is required for agreement population and can provide semantic evidence for an otherwise unresolved material-category criterion. It is not treated as a standalone checklist rule and cannot override a directly answered structured export-control or safety question.

## Agreement mapping

- Animal materials → AUTM MTA for Biological Materials
- Biological materials → UBMTA Implementing Letter
- Chemical materials → AUTM MTA for Chemical Materials
- Devices → Simple Letter Agreement

Mixed material categories never select an agreement automatically. Standard legal terms are unchanged; each template has an explicit tested population strategy.

Agreement fields are conditional on the selected template:

- AUTM Chemical and AUTM Biological: recipient organization address, optional academic/job titles for the provider and recipient scientists, material description, shipping recipient/address, and recipient authorized signatory identity and signing email.
- UBMTA Implementing Letter: recipient organization address, optional academic/job titles for the provider and recipient scientists, original-material description, recipient scientist certification authority, and a separate recipient authorized official only when required.
- Simple Letter Agreement: recipient organization address, material description, recipient scientist signing email, and recipient authorized official identity and signing email. It does not request an unprinted recipient-scientist title or AUTM shipping slots.

Provider and recipient full names, organization, and transmittal fee are reused from the requester questionnaire. The agreement section displays the reused names instead of requesting duplicate name entries. A scientist title means an academic or job role (for example, Professor or Research Scientist); both scientist-title fields are optional and blank titles do not block Standard MTA processing. Research purpose and duration remain generation context unless the selected standard template has an approved population slot; the system does not silently activate optional legal terms. The checklist-sourced shipping-payment and no-cost answers are required agreement-term information. Either shipping-payment answer is valid; a transfer that is not provided at no cost requires review when it is incompatible with the supplied standard-template terms. Signing emails are delivery data and are not printed into the agreement.

The combined “Other Model Organism (yeast, drosophila, zebrafish)” questionnaire option requires manual special-case review in eRPM because it does not identify one unambiguous checklist section.

## Pipeline

The backend follows `questionnaire completeness -> structured and semantic checklist facts -> trusted system verifications -> checklist decision -> template selection -> template-specific agreement completeness -> DOCX population -> signing package`.

The downloadable screening report contains the normalized agreement information and an input-usage map. Every submitted field is assigned to intake validation, an eligibility rule, semantic analysis, agreement population, agreement-term validation, signing, routing/contact context, or the evidence/audit record. An unexpected field is marked `unmapped_input` instead of being silently ignored; a stale field that does not belong to the selected template is marked `not_applicable_to_selected_template`.

The pipeline derives an internal deterministic submission identifier from the normalized submission. It is not a requester input and is not displayed as a form field. Identical submissions do not prepare duplicate packages within one pipeline store.

The local signing manifest contains the populated document path and hash, internal submission and template identifiers, audit events, and required signer identities, roles, and order. The relevant PI is the provider signer under the delegation stated in the checklist. Missing or invalid signer data stops package preparation.

## Current boundary

The app does not connect to eRPM. SignNow Development Mode can be enabled explicitly for API integration testing; local package mode remains the default. Authentication, persistent production storage, production SignNow activation, webhook status tracking, and eRPM integration remain outside this proof of concept.
