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
src/input_usage.py            per-field backend consumer audit map
src/agreement_readiness.py    agreement and signing data completeness
src/templates/                template catalog and deterministic mapping
src/agreements/               normalized agreement data
src/pipeline/                 workflow states and audit events
src/adapters/                 DOCX population and SignNow delivery
src/signing/                  local-versus-API sender selection
reference_files/              approved checklist and four clean agreement templates
```

Generated agreements and signing manifests are written under `outputs/`.

## Test

```bash
cd /Users/joudtaher/Documents/AI_Clinic
.venv/bin/python -m pytest -q
```

## SignNow Development Mode

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, enter the Development Mode API key and SignNow account email, then set `enabled = true`. The account email identifies the SignNow account sending the invitations; signer destination emails always come from the submitted form. Never commit `secrets.toml`.

When enabled, an eligible request is populated locally, a temporary tagged copy is uploaded to SignNow, the returned signer roles are verified, and role-based invitations are sent in the template-specific order. The clean populated agreement remains downloadable. Development Mode documents are for integration testing; production activation and webhook status tracking are separate steps.

The app does not connect to eRPM. Structured questionnaire answers are evaluated deterministically. Only checklist facts that remain unresolved are evaluated from relevant open-text fields by the local `facebook/bart-large-mnli` Hugging Face model. The model is downloaded once and cached on the device; submitted form text is not sent to an external inference service. The backend contains no regex pass/fail phrase dictionary. Low-confidence or conflicting semantic evidence requires manual special-case review.
