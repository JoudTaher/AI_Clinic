# Automatic MTA Signing Package Design

## Intent

Standard outgoing MTA requests should not wait for an internal template-approval step. The questionnaire rules decide whether a request is standard, select the approved agreement by material type, populate it, and prepare a U-M SignNow-ready package. Requests outside the documented standard path route to eRPM without guessing.

## Approved automatic mapping

- Chemical materials use `autm_chemical`.
- Biological materials use `ubmta_implementing_letter`.
- Non-living animal-derived materials use `autm_biological`.
- Devices route to eRPM until Innovation Partnerships supplies or confirms a device agreement.
- `simple_letter_agreement` remains catalogued but is not automatically selected until its approved rule is confirmed.
- Mixed, missing, unsupported, or failed-eligibility requests route to eRPM.

## Workflow

`intake -> completeness check -> eligibility rules -> automatic template selection -> document population -> SignNow-ready package`

No human approves or chooses a template in the standard path. Signers still sign the agreement. The interim adapter performs no network action: it writes the populated agreement and a signing manifest containing signer roles, email addresses, order, request ID, template ID, and audit events. A future U-M SignNow adapter will implement the same sender interface after ITS provides approved API credentials.

## Safety constraints

- Selection must be deterministic and fail closed to eRPM.
- The system must never silently substitute a template.
- Template legal terms remain unchanged; only documented data slots are populated.
- U-M institutional signer identity comes from deployment configuration, not applicant input.
- Missing signer data stops signing-package preparation with an explicit status.
- Request IDs remain idempotent and changed data under a completed ID is rejected.

## Approaches

The selected approach is a provider-neutral signing package plus a SignNow adapter boundary. Direct SignNow API integration is deferred because U-M credentials and API authorization are not yet available. Manual text replacement in arbitrary Word files was rejected as too brittle; each supported template instead has an explicit, tested population strategy.

