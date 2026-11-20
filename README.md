# Outgoing MTA automation

This Streamlit application demonstrates the automated standard path for outgoing Material Transfer Agreements. The requester completes one form; the backend evaluates the supplied eligibility checklist, selects and populates the correct approved agreement, requires review of the generated document, and prepares the recipient-side SignNow request. Requests that fail or cannot resolve a checklist condition move to staff review instead of receiving an automatic agreement.

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

Requests meeting every applicable checklist criterion qualify for the automated standard MTA process when one supported material category applies. Biological materials map to UBMTA and animal-derived materials map to the AUTM biological agreement for animal materials. Mixed, unsupported, unresolved, or out-of-scope requests move to the department's staff-review workflow. Production UBMTA routing should add authoritative verification of recipient-organization participation and authorized-official data; the current proof of concept relies on the organization and signer information submitted in the form.

## Structure

```text
src/intake.py                 requester-questionnaire completeness
src/field_validation.py       shared field-format validation
src/checklist.py              authoritative checklist criteria and evidence scope
src/eligibility.py            automatic-approval checklist rules
src/semantic_classifier.py    local Hugging Face semantic classification
src/agreement_review.py       final populated-agreement review and confirmation snapshot
src/request_identity.py       immutable submission hash and searchable MTA reference
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

The client workflow, technical design, current boundaries, and production handoff are documented in the [Outgoing MTA Automation Guide](docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx).

## Test

```bash
cd /Users/joudtaher/Documents/AI_Clinic
.venv/bin/python -m pytest -q
```

## SignNow Development Mode

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, enter the Development Mode API key and SignNow account email, then set `enabled = true`. The account email identifies the SignNow account sending the invitations; signer destination emails always come from the submitted form. Never commit `secrets.toml`.

When enabled, an eligible request is populated locally and stopped at a mandatory final review. The approved templates already contain Maggie Swift's provider-side signature, name, and title; the backend adds the agreement-generation date while keeping the Provider Scientist name and required academic/job title in their separate agreement fields. The Recipient Scientist academic/job title is also required whenever the selected agreement prints it, and the Recipient Authorized Official title remains required. The review shows every request value entering the agreement, the recipient-side signer identities and emails, the readable MTA reference, a downloadable populated DOCX, and non-blocking warnings for possible spelling, address, whitespace, or identity inconsistencies. Existing required-field and email validation remains blocking. The requester must explicitly confirm the exact reviewed snapshot; changing the form, template, or DOCX invalidates that confirmation. Only then is a temporary tagged copy uploaded to SignNow, the returned recipient-side roles verified, and invitations sent only to the recipient-side signer or signers required by that agreement.

Each request keeps the full SHA-256 submission identifier internally for idempotency and receives a readable reference in the form `MTA-YYYY-XXXXXXXX`. That reference is shown in final review and delivery results and is reused in generated agreement filenames, local signing manifests, screening reports, and the SignNow document name (`MTA-YYYY-XXXXXXXX — Project Title`). A future database record should use the same reference as the staff-facing business key while retaining the internal submission hash and SignNow document ID as separate technical correlation keys.

For the AUTM chemical and animal agreements, the renderer activates the existing Exhibit B termination option and inserts the entered project period as a relative term: the agreement terminates after that period measured from the date of the last signature. Templates without an approved termination slot are not changed.

The current review protects data and signer integrity, not Word layout. Fixture rendering found visible source-template artifacts in some populated agreements, including narrow AUTM label wrapping and a sparse device-template trailing page. Before production, normalize and version the approved source templates, render every automation-enabled agreement type with boundary-length data, inspect every page, and make visual approval a blocking delivery condition. UBMTA needs the same visual regression controls as the other active templates.

The current code records the returned SignNow document ID but does not yet retrieve or archive completed agreements. Production operation needs a verified completion-webhook receiver, idempotent status handling, final signed PDF and audit/certificate retrieval, an approved U-M document repository, and database metadata linking each stored file to the institutional case, signer history, checksum, retention state, and SignNow document ID. Development Mode documents are for integration testing; production activation and this completed-document lifecycle are separate steps.

The app does not connect to eRPM. Structured questionnaire answers are evaluated deterministically. Only checklist facts that remain unresolved are evaluated from criterion-approved open-text fields by the local `facebook/bart-large-mnli` Hugging Face model. The model is downloaded once and cached on the device; submitted form text is not sent to an external inference service. The backend contains no regex pass/fail phrase dictionary. Direct natural-language inference requires at least 0.80 entailment confidence to support a criterion and at least 0.90 contradiction confidence to reject it; low-confidence, neutral, unavailable, or conflicting semantic evidence remains unresolved. The review screen's local spelling dictionary is a separate document-quality aid and has no eligibility authority.
