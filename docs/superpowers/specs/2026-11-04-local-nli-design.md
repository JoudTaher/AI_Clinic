# Local NLI eligibility design

The eligibility checklist is the sole source of truth. Structured questionnaire
answers are evaluated with deterministic rules. Open-ended fields are evaluated
by one local natural-language-inference (NLI) model that compares submitted text
with each applicable checklist statement.

The classifier uses direct `entailment`, `contradiction`, and `neutral` scores plus
zero-shot semantic categories where the checklist requires contextual inference.
Only confident evidence produces a decision; neutral or low-confidence output
requires manual special-case review. A contradiction always overrides entailment
from another relevant text field.

There are no pass/fail phrase lists or regex fallbacks. The model is loaded lazily,
cached for the Streamlit process, and runs locally after its initial Hugging Face
download. If the model is unavailable, semantic criteria remain unresolved rather
than being guessed.

Checklist definitions and their relevant source fields live in one module and are
consumed by both eligibility and semantic classification. Deterministic form
answers remain authoritative; NLP fills unresolved facts, while explicit content
in Other Relevant Details can flag a contradiction. Evidence records the model,
criterion, source field, label, and scores so decisions remain auditable.
