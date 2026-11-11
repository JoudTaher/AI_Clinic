# Chemical Structure Confidentiality Field Design

## Intent

Match the supplied outgoing MTA requester form by asking whether a chemical compound's structure is confidential whenever `Chemical compound` is selected.

## Behavior

- Show `Is the structure of this compound confidential? *` only when `Chemical compound` is selected.
- Require an explicit Yes or No for questionnaire completeness.
- Store the canonical boolean as `chemical_structure_confidential` in `erpm_intake`.
- Register the field as an audit/request-context input.
- Do not use the value for eligibility, template selection, agreement population, or signing.
- Remove stale applicability when a request no longer contains a chemical compound.

## Approaches considered

- **Required questionnaire-only field — selected.** Matches the source form while preserving the checklist as the sole eligibility authority.
- Optional questionnaire-only field. Rejected because the supplied form marks the question required.
- Eligibility rule. Rejected because the supplied eligibility checklist does not contain this condition.

