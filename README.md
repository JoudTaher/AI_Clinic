# Outgoing MTA Automation Proof of Concept

This local Streamlit app presents only the outgoing MTA requester questionnaire. The automatic-approval checklist runs as backend rules; it is not a second requester form. A verified standard request is mapped to the correct supplied agreement, populated, and prepared for U-M SignNow. Local package mode is the safe default; SignNow Development Mode can be explicitly enabled.

## Run

In Finder, open:

```text
/Users/joudtaher/Documents/AI_Clinic
```

Double-click `run_app.command`. The app normally opens at `http://localhost:8501`.

Or run:

```bash
cd /Users/joudtaher/Documents/AI_Clinic
./run_app.command
```

## Automatic template mapping

- Animal materials → `Template_AUTM_Animal.docx`
- Biological materials → `Template_UBMTA_Biological.docx`
- Chemical materials → `Template_Chemical_Materials.docx`
- Devices → `Template_Simple Letter_Device.docx`

Requests meeting every applicable checklist criterion qualify for Standard MTA automatic approval. Mixed, unsupported, unresolved, or special-case requests require manual special-case review in eRPM.

## Structure

```text
src/intake.py                 requester-questionnaire completeness
src/field_validation.py       shared field-format validation
src/checklist.py              authoritative checklist criteria and evidence scope
src/eligibility.py            automatic-approval checklist rules
src/semantic_classifier.py    local Hugging Face semantic classification
src/agreement_review.py       final populated-agreement review and confirmation snapshot
src/input_usage.py            per-field backend consumer audit map
src/agreement_readiness.py    agreement and signing data completeness
src/templates/                template catalog and deterministic mapping
src/agreements/               normalized agreement data
src/pipeline/                 workflow states and audit events
src/adapters/                 DOCX population and SignNow delivery
src/signing/                  local-versus-API sender selection
reference_files/              approved checklist and four supplied agreement templates
```

Generated agreements and signing manifests are written under `outputs/`.

## Product and technical documentation

The complete current-state, signing, signed-document management, standalone-versus-integrated architecture, and roadmap reference is available in [University of Michigan Outgoing MTA Automation Product and Technical Documentation](docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx).

## Test

```bash
cd /Users/joudtaher/Documents/AI_Clinic
.venv/bin/python -m pytest -q
```

## SignNow Development Mode

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, enter the Development Mode API key and SignNow account email, then set `enabled = true`. The account email identifies the SignNow account sending the invitations; signer destination emails always come from the submitted form. Never commit `secrets.toml`.

When enabled, an eligible request is populated locally and stopped at a mandatory final review. The approved templates already contain Maggie Swift's provider-side signature, name, and title; the backend adds the agreement-generation date while keeping the Provider Scientist name and title in their separate agreement fields. The review shows every request value entering the agreement, the recipient-side signer identities and emails, a downloadable populated DOCX, and non-blocking warnings for possible spelling, address, whitespace, or identity inconsistencies. Existing required-field and email validation remains blocking. The requester must explicitly confirm the exact reviewed snapshot; changing the form, template, or DOCX invalidates that confirmation. Only then is a temporary tagged copy uploaded to SignNow, the returned recipient-side roles verified, and invitations sent only to the recipient-side signer or signers required by that agreement.

The current review protects data and signer integrity, not Word layout. Fixture rendering found visible source-template artifacts in some populated agreements, including narrow AUTM label wrapping, UBMTA placeholder punctuation or blank-line remnants, and a sparse device-template trailing page. Before production, normalize and version the approved source templates, render all four agreement types with boundary-length data, inspect every page, and make visual approval a blocking delivery condition.

The current code records the returned SignNow document ID but does not yet retrieve or archive completed agreements. Production operation needs a verified completion-webhook receiver, idempotent status handling, final signed PDF and audit/certificate retrieval, an approved U-M document repository, and database metadata linking each stored file to the institutional case, signer history, checksum, retention state, and SignNow document ID. Development Mode documents are for integration testing; production activation and this completed-document lifecycle are separate steps.

The app does not connect to eRPM. Structured questionnaire answers are evaluated deterministically. Only checklist facts that remain unresolved are evaluated from criterion-approved open-text fields by the local `facebook/bart-large-mnli` Hugging Face model. The model is downloaded once and cached on the device; submitted form text is not sent to an external inference service. The backend contains no regex pass/fail phrase dictionary. Direct natural-language inference requires at least 0.80 entailment confidence to support a criterion and at least 0.90 contradiction confidence to reject it; low-confidence, neutral, unavailable, or conflicting semantic evidence remains unresolved. The review screen's local spelling dictionary is a separate document-quality aid and has no eligibility authority.
