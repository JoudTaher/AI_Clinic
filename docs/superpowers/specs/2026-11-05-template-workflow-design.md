# Template workflow design

## Intent

Make agreement population and signature routing easy to audit and change without
duplicating legal-role decisions across the UI, validation, package generation, and
SignNow delivery.

## Role invariants

- Contact PI is the U-M Provider Scientist and delegated provider signer.
- Primary Research Administrator is an internal administrative/routing contact and is
  never assigned signature authority automatically.
- Recipient Scientist is the recipient researcher and signs only where the selected
  agreement requires that role.
- Recipient Administrative Contact is a contact record, not an authorized signatory by
  default.
- Recipient Authorized Official/Signatory is collected only when the selected template
  requires one; it must never be inferred from an administrative contact.
- Each name and email has one canonical source and is reused rather than re-entered.
- The configured SignNow account is the sender; party emails are invitation recipients.

## Approaches

1. Keep separate rules in each layer. Smallest edit, but preserves drift risk.
2. Centralize only signer routing. Improves SignNow behavior but leaves required-field
   and UI-condition duplication.
3. Use a template workflow definition plus one canonical signer-plan builder. This is
   the chosen approach because the selected agreement is the legal source for required
   roles, ordering, and conditional signer requirements.

## Design

- Add a focused workflow module that defines signer roles and signing order by template.
- Build strict signer plans for delivery and non-strict previews for the UI from the same
  function.
- Make agreement readiness validate the signer plan instead of maintaining a separate
  signer-email rule set.
- Make both local SignNow packages and live SignNow delivery consume the same plan.
- Keep DOCX slot population template-specific because the supplied documents have
  different physical structures; continue using canonical normalized party fields.
- Keep eligibility and template-selection behavior unchanged.

## Non-goals

- Do not infer legal authority from titles, email domains, or administrative-contact
  status.
- Do not change the supplied templates or the checklist rules.
- Do not enable live SignNow delivery.
