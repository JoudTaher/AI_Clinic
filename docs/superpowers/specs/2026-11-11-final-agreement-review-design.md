# Final Agreement Review Design

## Intent

Prevent unreviewed form errors from being carried into an agreement and sent to SignNow while preserving automatic Standard MTA eligibility. Requester confirmation is a document-quality control, not a second legal or departmental approval.

## Selected approach

The backend prepares an exact populated DOCX and a review snapshot before delivery. The snapshot is built from the same normalized `AgreementData` and signer plan used by the renderer and SignNow adapter. It contains every populated agreement value and every signer identity, plus non-blocking warnings for suspicious text, incomplete addresses, and inconsistent signer identities. Existing required-field and email validation remains blocking.

The snapshot has a SHA-256 reference derived from the normalized request, selected template, and generated DOCX bytes. The delivery pipeline requires that exact reference. If any form value, template, or rendered document changes after review, the reference changes and SignNow delivery is stopped until the new agreement is reviewed.

## User flow

1. Complete the questionnaire and agreement information.
2. Run eligibility and deterministic template selection.
3. Generate the populated agreement without sending it.
4. Review all agreement-bound values, signer identities, warning messages, and the downloadable populated DOCX.
5. Correct source fields if needed and regenerate the review.
6. Confirm that the displayed snapshot is accurate.
7. Send that confirmed snapshot to SignNow or create the local signing package.

## Warnings

Warnings never alter legal names, scientific terms, addresses, or agreement text. They identify repeated words, repeated whitespace, likely spelling errors in narrative fields, addresses lacking common structural detail, and one email associated with inconsistent signer names. They are review prompts; required or malformed data continues to be handled by existing validation.

## Documentation

The existing product and technical Word document will be updated only after implementation and verification. It will describe the actual review module, pipeline states, snapshot reference, warning behavior, UI flow, tests, and the existing local Hugging Face BART MNLI classifier used as supporting evidence for unresolved open-text checklist criteria.

