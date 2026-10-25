# Outgoing MTA Automation Proof of Concept

A local Streamlit application that evaluates an outgoing MTA request, selects and fills the approved agreement, and creates a U-M SignNow-ready package. It does not make network requests.

## Run It

Open this folder in Finder:

```text
/Users/joudtaher/Documents/AI_Clinic
```

Then double-click `run_app.command`. The application opens in your browser, normally at `http://localhost:8501`.

If macOS blocks the launcher, Control-click `run_app.command`, choose **Open**, and confirm once.

You can also launch it from Terminal:

```bash
cd /Users/joudtaher/Documents/AI_Clinic
./run_app.command
```

Before preparing a signing package, configure the U-M institutional signer in the same Terminal window:

```bash
export MTA_UM_SIGNER_NAME="Approved signer name"
export MTA_UM_SIGNER_TITLE="Approved signer title"
export MTA_UM_SIGNER_EMAIL="approved.signer@umich.edu"
./run_app.command
```

The signer values are deployment configuration, not questionnaire answers. If they are absent, the app still opens but blocks package preparation with a clear error.

## Test It

```bash
cd /Users/joudtaher/Documents/AI_Clinic
.venv/bin/python -m pytest -v
```

## Backend Structure

```text
src/templates/   template catalog, validation, and matching rules
src/agreements/  normalized agreement data
src/pipeline/    eligibility, routing, idempotency, and workflow states
src/signing/     deployment-owned signer configuration
src/adapters/    DOCX population and local SignNow-package creation
```

Automatic mapping is fixed to the confirmed rules:

- Chemical → AUTM Chemical
- Biological → UBMTA Implementing Letter
- Non-living animal-derived → AUTM Biological
- Device, mixed, unsupported, or nonstandard → eRPM

The Simple Letter remains in the catalog but is disabled until its institutional rule is confirmed. Generated DOCX files and signing manifests are written under `outputs/`.

## Current Boundary

This version fills agreements and creates local signing manifests. It does not upload to SignNow, send email, sign documents, or connect to eRPM. A future authenticated U-M SignNow adapter can replace the local package adapter without changing the eligibility, selection, or rendering code.
