# Outgoing MTA Automation Proof of Concept

This local Streamlit app presents only the outgoing MTA requester questionnaire. The automatic-approval checklist runs as backend rules; it is not a second requester form. A verified standard request is mapped to the correct supplied agreement, populated, and packaged for U-M SignNow. The app makes no network requests.

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

- Animal materials → AUTM MTA for Biological Materials
- Biological materials → UBMTA Implementing Letter
- Chemical materials → AUTM MTA for Chemical Materials
- Devices → Simple Letter Agreement

Mixed, unsupported, incomplete, or nonstandard requests route to the Standard MTA Process in eRPM.

## Structure

```text
src/intake.py                 requester-questionnaire completeness
src/eligibility.py            automatic-approval checklist rules
src/semantic_rules.py         conservative free-text checklist matching
src/input_usage.py            per-field backend consumer audit map
src/agreement_readiness.py    agreement and signing data completeness
src/templates/                template catalog and deterministic mapping
src/agreements/               normalized agreement data
src/pipeline/                 workflow states and audit events
src/adapters/                 DOCX population and SignNow package creation
reference_files/              unchanged supplied checklist and templates
```

Generated agreements and signing manifests are written under `outputs/`.

## Test

```bash
cd /Users/joudtaher/Documents/AI_Clinic
.venv/bin/python -m pytest -q
```

## Current boundary

The app creates a populated agreement and a local signing manifest. After a standard request passes, use **Download final agreement for signing** to save the exact populated `.docx` that the signing adapter would receive. It does not upload to SignNow, send email, sign documents, or connect to eRPM. Structured answers and explicit free-text statements are compared with every applicable checklist rule using local spaCy sentence processing plus auditable phrase rules; ambiguous or conflicting text routes to eRPM. A trusted backend verification source can supplement institutionally verified facts. The relevant PI is assigned as the provider signer under the delegation stated in the supplied eligibility checklist.
