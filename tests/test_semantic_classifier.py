from __future__ import annotations

from dataclasses import dataclass

from src.models import Criterion, SemanticLabels
from src.semantic_classifier import analyze_open_text


CRITERION = Criterion(
    "chemical_not_used_in_humans",
    "Material will not be used in humans",
    "B",
)


@dataclass
class StubClassifier:
    predictions: list[dict[str, float]]
    ranked_predictions: list[dict[str, float]] | None = None
    model_id: str = "test/nli-model"

    def __post_init__(self) -> None:
        self.received_pairs: list[tuple[str, str]] = []

    def predict(
        self, pairs: list[tuple[str, str]]
    ) -> list[dict[str, float]]:
        self.received_pairs = pairs
        return self.predictions

    def rank(
        self, cases: list[tuple[str, SemanticLabels]]
    ) -> list[dict[str, float]]:
        return self.ranked_predictions or []


class UnavailableClassifier:
    model_id = "test/unavailable-model"

    def predict(
        self, pairs: list[tuple[str, str]]
    ) -> list[dict[str, float]]:
        raise OSError("model cache is unavailable")


def scores(
    *, entailment: float, contradiction: float, neutral: float
) -> dict[str, float]:
    return {
        "entailment": entailment,
        "contradiction": contradiction,
        "neutral": neutral,
    }


def test_entailment_passes_without_matching_a_phrase_list():
    classifier = StubClassifier(
        [scores(entailment=0.91, contradiction=0.03, neutral=0.06)]
    )

    result = analyze_open_text(
        {"recipient_experimental_plan": "Course-based laboratory investigation."},
        (CRITERION,),
        classifier=classifier,
    )

    assert result["facts"][CRITERION.field_id] is True
    assert classifier.received_pairs == [
        ("Course-based laboratory investigation.", CRITERION.label)
    ]
    assert result["evidence"][CRITERION.field_id]["source_fields"] == [
        "recipient_experimental_plan"
    ]


def test_contradiction_fails_the_criterion():
    classifier = StubClassifier(
        [scores(entailment=0.02, contradiction=0.94, neutral=0.04)]
    )

    result = analyze_open_text(
        {"recipient_experimental_plan": "Participants will receive the compound."},
        (CRITERION,),
        classifier=classifier,
    )

    assert result["facts"][CRITERION.field_id] is False


def test_contradiction_overrides_entailment_from_another_field():
    classifier = StubClassifier(
        [
            scores(entailment=0.92, contradiction=0.03, neutral=0.05),
            scores(entailment=0.01, contradiction=0.96, neutral=0.03),
        ]
    )

    result = analyze_open_text(
        {
            "recipient_experimental_plan": "Benchtop teaching experiment.",
            "related_details": "The material will be administered to volunteers.",
        },
        (CRITERION,),
        classifier=classifier,
    )

    assert result["facts"][CRITERION.field_id] is False
    assert result["evidence"][CRITERION.field_id]["source_fields"] == [
        "related_details"
    ]


def test_conflicting_sentences_in_one_field_are_evaluated_separately():
    criterion = Criterion(
        CRITERION.field_id,
        CRITERION.label,
        CRITERION.section,
        semantic_sources=("related_details",),
    )
    classifier = StubClassifier(
        [
            scores(entailment=0.96, contradiction=0.01, neutral=0.03),
            scores(entailment=0.01, contradiction=0.97, neutral=0.02),
        ]
    )

    result = analyze_open_text(
        {
            "related_details": (
                "The first statement supports the criterion. "
                "The second statement contradicts it."
            )
        },
        (criterion,),
        classifier=classifier,
    )

    assert len(classifier.received_pairs) == 2
    assert result["facts"][criterion.field_id] is False


def test_neutral_or_low_confidence_results_remain_unresolved():
    neutral = StubClassifier(
        [scores(entailment=0.08, contradiction=0.07, neutral=0.85)]
    )
    low_confidence = StubClassifier(
        [scores(entailment=0.55, contradiction=0.10, neutral=0.35)]
    )

    neutral_result = analyze_open_text(
        {"recipient_experimental_plan": "The team will study performance."},
        (CRITERION,),
        classifier=neutral,
    )
    low_confidence_result = analyze_open_text(
        {"recipient_experimental_plan": "A laboratory activity."},
        (CRITERION,),
        classifier=low_confidence,
    )

    assert neutral_result["facts"][CRITERION.field_id] is None
    assert low_confidence_result["facts"][CRITERION.field_id] is None


def test_semantic_category_fallback_handles_contextual_paraphrase():
    criterion = Criterion(
        CRITERION.field_id,
        CRITERION.label,
        CRITERION.section,
        semantic_sources=("recipient_experimental_plan",),
        semantic_labels=SemanticLabels(
            satisfied="non-human research use",
            violated="research involving human use",
            unknown="insufficient information about human use",
        ),
    )
    classifier = StubClassifier(
        [scores(entailment=0.04, contradiction=0.06, neutral=0.90)],
        ranked_predictions=[
            {
                criterion.semantic_labels.satisfied: 0.91,
                criterion.semantic_labels.violated: 0.03,
                criterion.semantic_labels.unknown: 0.06,
            }
        ],
    )

    result = analyze_open_text(
        {"recipient_experimental_plan": "Course-based laboratory investigation."},
        (criterion,),
        classifier=classifier,
    )

    assert result["facts"][criterion.field_id] is True
    assert result["evidence"][criterion.field_id]["decision_method"] == (
        "zero_shot_semantic_category"
    )


def test_model_failure_is_unresolved_and_auditable():
    result = analyze_open_text(
        {"recipient_experimental_plan": "Course-based laboratory investigation."},
        (CRITERION,),
        classifier=UnavailableClassifier(),
    )

    assert result["facts"][CRITERION.field_id] is None
    assert result["nlp_backend"] == {
        "available": False,
        "library": "transformers",
        "model": "test/unavailable-model",
        "error_type": "OSError",
    }


def test_empty_text_does_not_call_the_model():
    classifier = StubClassifier([])

    result = analyze_open_text(
        {"recipient_experimental_plan": "   "},
        (CRITERION,),
        classifier=classifier,
    )

    assert classifier.received_pairs == []
    assert result["facts"][CRITERION.field_id] is None
