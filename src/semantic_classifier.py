from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import Any, Protocol

from src.models import Criterion, SemanticLabels


MODEL_ID = "facebook/bart-large-mnli"
ENTAILMENT_THRESHOLD = 0.80
CONTRADICTION_THRESHOLD = 0.90

TEXT_FIELDS = (
    "project_title",
    "recipient_entity",
    "recipient_experimental_plan",
    "related_details",
    "material_description",
    "human_derived_description",
    "human_data_classification",
    "protocol_consent_transfer_sections",
)

NLI_LABELS = frozenset({"entailment", "contradiction", "neutral"})
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


class SemanticClassifier(Protocol):
    model_id: str

    def predict(
        self, pairs: list[tuple[str, str]]
    ) -> list[dict[str, float]]: ...

    def rank(
        self, cases: list[tuple[str, SemanticLabels]]
    ) -> list[dict[str, float]]: ...


def _load_pretrained(loader: Any, model_id: str) -> Any:
    try:
        return loader.from_pretrained(model_id, local_files_only=True)
    except OSError:
        return loader.from_pretrained(model_id)


class HuggingFaceSemanticClassifier:
    """Local BART classifier supporting direct NLI and semantic categories."""

    def __init__(self, model_id: str = MODEL_ID) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.model_id = model_id
        self._torch = torch
        self._tokenizer = _load_pretrained(AutoTokenizer, model_id)
        self._model = _load_pretrained(
            AutoModelForSequenceClassification, model_id
        )
        self._model.eval()

        self._labels = {
            int(index): str(label).casefold()
            for index, label in self._model.config.id2label.items()
        }
        if set(self._labels.values()) != NLI_LABELS:
            raise ValueError(
                f"Model {model_id!r} does not expose the required NLI labels"
            )
        self._entailment_index = next(
            index
            for index, label in self._labels.items()
            if label == "entailment"
        )

        use_mps = (
            hasattr(torch.backends, "mps")
            and torch.backends.mps.is_available()
        )
        self._device = torch.device("mps" if use_mps else "cpu")
        self._model.to(self._device)

    def _logits(self, pairs: list[tuple[str, str]]) -> Any:
        premises, hypotheses = zip(*pairs, strict=True)
        encoded = self._tokenizer(
            list(premises),
            list(hypotheses),
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        encoded = {key: value.to(self._device) for key, value in encoded.items()}
        with self._torch.inference_mode():
            return self._model(**encoded).logits.cpu()

    def predict(
        self, pairs: list[tuple[str, str]]
    ) -> list[dict[str, float]]:
        if not pairs:
            return []
        probabilities = self._torch.softmax(self._logits(pairs), dim=-1).tolist()
        return [
            {
                self._labels[index]: float(score)
                for index, score in enumerate(row)
            }
            for row in probabilities
        ]

    def rank(
        self, cases: list[tuple[str, SemanticLabels]]
    ) -> list[dict[str, float]]:
        if not cases:
            return []

        pairs: list[tuple[str, str]] = []
        labels_by_case: list[tuple[str, str, str]] = []
        for text, labels in cases:
            candidates = (labels.satisfied, labels.violated, labels.unknown)
            labels_by_case.append(candidates)
            pairs.extend(
                (text, f"The intended use is {candidate}.")
                for candidate in candidates
            )

        logits = self._logits(pairs)
        entailment_logits = logits[:, self._entailment_index].reshape(
            len(cases), 3
        )
        ranked_probabilities = self._torch.softmax(
            entailment_logits, dim=1
        ).tolist()
        return [
            {
                label: float(score)
                for label, score in zip(labels, row, strict=True)
            }
            for labels, row in zip(
                labels_by_case, ranked_probabilities, strict=True
            )
        ]


@lru_cache(maxsize=1)
def get_default_classifier() -> HuggingFaceSemanticClassifier:
    return HuggingFaceSemanticClassifier()


def _source_text(values: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    return {
        field_id: tuple(
            sentence
            for sentence in SENTENCE_BOUNDARY.split(value.strip())
            if sentence
        )
        for field_id in TEXT_FIELDS
        if isinstance((value := values.get(field_id)), str) and value.strip()
    }


def _criterion_sources(
    criterion: Criterion, sources: Mapping[str, tuple[str, ...]]
) -> list[tuple[str, str]]:
    permitted = criterion.semantic_sources or TEXT_FIELDS
    return [
        (field_id, sentence)
        for field_id in permitted
        if field_id in sources
        for sentence in sources[field_id]
    ]


def _unresolved_result(
    criteria: Sequence[Criterion],
    *,
    model_id: str,
    available: bool,
    error_type: str | None = None,
) -> dict[str, Any]:
    backend: dict[str, Any] = {
        "available": available,
        "library": "transformers",
        "model": model_id,
    }
    if error_type is not None:
        backend["error_type"] = error_type
    return {
        "method": "local_huggingface_semantic_classification",
        "nlp_backend": backend,
        "facts": {criterion.field_id: None for criterion in criteria},
        "evidence": {
            criterion.field_id: {
                "criterion": criterion.label,
                "decision": None,
                "decision_method": None,
                "source_fields": [],
                "observations": [],
            }
            for criterion in criteria
        },
    }


def _validate_scores(scores: Mapping[str, Any]) -> dict[str, float]:
    normalized = {
        label: float(scores[label])
        for label in NLI_LABELS
        if label in scores
    }
    if set(normalized) != NLI_LABELS:
        raise ValueError("NLI prediction is missing a required label")
    return normalized


def _rank_decision(
    labels: SemanticLabels, scores: Mapping[str, float]
) -> bool | None:
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_label, top_score = ordered[0]
    margin = top_score - ordered[1][1]
    if margin < labels.minimum_margin:
        return None
    if top_label == labels.satisfied and top_score >= labels.satisfied_threshold:
        return True
    if top_label == labels.violated and top_score >= labels.violated_threshold:
        return False
    return None


def analyze_open_text(
    values: Mapping[str, Any],
    criteria: Sequence[Criterion],
    *,
    classifier: SemanticClassifier | None = None,
) -> dict[str, Any]:
    """Evaluate open text without pass/fail regex or phrase matching."""

    criteria = tuple(criteria)
    sources = _source_text(values)
    selected_classifier = classifier
    model_id = getattr(selected_classifier, "model_id", MODEL_ID)

    if not criteria or not sources:
        return _unresolved_result(criteria, model_id=model_id, available=True)

    pair_metadata = [
        (criterion, field_id, text)
        for criterion in criteria
        for field_id, text in _criterion_sources(criterion, sources)
    ]
    pairs = [
        (text, criterion.label)
        for criterion, _field_id, text in pair_metadata
    ]

    try:
        if selected_classifier is None:
            selected_classifier = get_default_classifier()
            model_id = selected_classifier.model_id
        predictions = selected_classifier.predict(pairs)
        if len(predictions) != len(pair_metadata):
            raise ValueError("NLI classifier returned an unexpected result count")
    except Exception as error:
        return _unresolved_result(
            criteria,
            model_id=model_id,
            available=False,
            error_type=type(error).__name__,
        )

    observations: dict[str, list[dict[str, Any]]] = {
        criterion.field_id: [] for criterion in criteria
    }
    try:
        for (criterion, field_id, _text), raw_scores in zip(
            pair_metadata, predictions, strict=True
        ):
            normalized_scores = _validate_scores(raw_scores)
            label = max(normalized_scores, key=normalized_scores.__getitem__)
            observations[criterion.field_id].append(
                {
                    "source_field": field_id,
                    "mode": "direct_nli",
                    "label": label,
                    "confidence": normalized_scores[label],
                    "scores": normalized_scores,
                }
            )
    except (KeyError, TypeError, ValueError) as error:
        return _unresolved_result(
            criteria,
            model_id=model_id,
            available=False,
            error_type=type(error).__name__,
        )

    facts: dict[str, bool | None] = {}
    methods: dict[str, str | None] = {}
    decisive_sources: dict[str, list[str]] = {}
    pending_rank_cases: list[tuple[Criterion, str, str]] = []

    for criterion in criteria:
        criterion_observations = observations[criterion.field_id]
        contradictions = [
            item
            for item in criterion_observations
            if item["label"] == "contradiction"
            and item["confidence"] >= CONTRADICTION_THRESHOLD
        ]
        entailments = [
            item
            for item in criterion_observations
            if item["label"] == "entailment"
            and item["confidence"] >= ENTAILMENT_THRESHOLD
        ]
        decisive = contradictions or entailments
        decision = False if contradictions else True if entailments else None
        facts[criterion.field_id] = decision
        methods[criterion.field_id] = "direct_nli" if decisive else None
        decisive_sources[criterion.field_id] = [
            item["source_field"] for item in decisive
        ]

        if decision is None and criterion.semantic_labels is not None:
            pending_rank_cases.extend(
                (criterion, field_id, text)
                for field_id, text in _criterion_sources(criterion, sources)
            )

    rank_error_type: str | None = None
    if pending_rank_cases:
        try:
            ranked = selected_classifier.rank(
                [
                    (text, criterion.semantic_labels)
                    for criterion, _field_id, text in pending_rank_cases
                    if criterion.semantic_labels is not None
                ]
            )
            if len(ranked) != len(pending_rank_cases):
                raise ValueError(
                    "Semantic classifier returned an unexpected result count"
                )
            ranked_by_criterion: dict[
                str, list[tuple[str, bool | None, dict[str, float]]]
            ] = {}
            for (criterion, field_id, _text), raw_scores in zip(
                pending_rank_cases, ranked, strict=True
            ):
                labels = criterion.semantic_labels
                if labels is None:
                    continue
                scores = {
                    labels.satisfied: float(raw_scores[labels.satisfied]),
                    labels.violated: float(raw_scores[labels.violated]),
                    labels.unknown: float(raw_scores[labels.unknown]),
                }
                decision = _rank_decision(labels, scores)
                ranked_by_criterion.setdefault(criterion.field_id, []).append(
                    (field_id, decision, scores)
                )
                observations[criterion.field_id].append(
                    {
                        "source_field": field_id,
                        "mode": "zero_shot_semantic_category",
                        "decision": decision,
                        "scores": scores,
                    }
                )

            for criterion_id, ranked_items in ranked_by_criterion.items():
                failures = [item for item in ranked_items if item[1] is False]
                passes = [item for item in ranked_items if item[1] is True]
                decisive = failures or passes
                if decisive:
                    facts[criterion_id] = False if failures else True
                    methods[criterion_id] = "zero_shot_semantic_category"
                    decisive_sources[criterion_id] = [
                        field_id for field_id, _decision, _scores in decisive
                    ]
        except Exception as error:
            rank_error_type = type(error).__name__

    evidence = {
        criterion.field_id: {
            "criterion": criterion.label,
            "decision": facts[criterion.field_id],
            "decision_method": methods[criterion.field_id],
            "source_fields": list(
                dict.fromkeys(decisive_sources[criterion.field_id])
            ),
            "observations": observations[criterion.field_id],
        }
        for criterion in criteria
    }
    backend: dict[str, Any] = {
        "available": True,
        "library": "transformers",
        "model": model_id,
    }
    if rank_error_type is not None:
        backend["semantic_category_error_type"] = rank_error_type

    return {
        "method": "local_huggingface_semantic_classification",
        "nlp_backend": backend,
        "facts": facts,
        "evidence": evidence,
    }
