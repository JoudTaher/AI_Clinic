# Outgoing MTA Screening Proof of Concept

A local Streamlit application that mirrors the submitted outgoing MTA eRPM worksheet, evaluates eligibility, and recommends an agreement from a configurable template catalog. Unclear or conflicting requests stop for manual review.

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

## Test It

```bash
cd /Users/joudtaher/Documents/AI_Clinic
.venv/bin/python -m pytest -v
```

## Backend Structure

```text
src/templates/   template catalog, validation, and matching rules
src/pipeline/    screening, approval, idempotency, and workflow states
src/adapters/    reference-template copying and local dry-run delivery
```

The initial catalog contains the four supplied agreements. Add another template by placing its source file in `reference_files/` and adding one validated entry to `src/templates/catalog.json`; the matching engine does not need to be rewritten.

Every recommendation requires a named approver. The included sender only creates a local JSON email package under `outputs/`; it never sends a real message.

## Important Limits

This is a proof of concept using synthetic data. It is not connected to eRPM, does not provide legal approval, does not fill or sign legal agreements, and does not send email. Live email, e-signature, authentication, and production persistence require separate reviewed adapters.
