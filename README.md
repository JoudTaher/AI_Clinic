# Outgoing MTA Screening Proof of Concept

A local Streamlit application that mirrors the submitted outgoing MTA eRPM worksheet, evaluates the supplied eligibility checklist, explains the decision, and reports template-selection questions for manual review.

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

## Important Limits

This is a proof of concept using synthetic data. It is not connected to eRPM, does not provide legal approval, does not select a final agreement automatically, and does not create or sign an agreement.
