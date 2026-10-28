from __future__ import annotations

import re
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

import spacy
from spacy.language import Language


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


def _compile(*patterns: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)


@lru_cache(maxsize=1)
def _english_pipeline() -> Language:
    pipeline = spacy.blank("en")
    pipeline.add_pipe("sentencizer")
    return pipeline


def _sentence_scoped(text: str) -> str:
    document = _english_pipeline()(text)
    return "\n".join(sentence.text.strip() for sentence in document.sents)


RULES: dict[str, dict[str, tuple[re.Pattern[str], ...]]] = {
    "recipient_is_us_nonprofit": {
        "pass": _compile(
            r"\b(?:u\.?s\.?|united states)[ -]+non[- ]profit\b",
            r"\bnon[- ]profit (?:u\.?s\.? |united states )?(?:institution|organization|university|college)\b",
        ),
        "fail": _compile(
            r"\bfor[- ]profit\b",
            r"\b(?:company|corporation|llc|inc\.?|ltd\.?|gmbh)\b",
        ),
    },
    "um_owned_without_third_party_restrictions": {
        "pass": _compile(
            r"\bowned by (?:u[- ]m|the university of michigan).{0,80}\bno third[- ]party restrictions?\b",
            r"\bno third[- ]party restrictions?.{0,80}\bowned by (?:u[- ]m|the university of michigan)\b",
        ),
        "fail": _compile(
            r"\bowned by (?:another|a third) party\b",
            r"\bsubject to third[- ]party restrictions?\b",
            r"\bthird[- ]party owned\b",
            r"\blicensed (?:from|to|by) (?:a )?third[- ]party\b",
            r"\bincorporates? (?:a )?third[- ]party (?:components?|software|firmware|materials?)\b",
            r"\b(?:made|developed|generated) using third[- ]party (?:components?|software|firmware|materials?)\b",
        ),
    },
    "internal_noncommercial_research_only": {
        "pass": _compile(
            r"\binternal[, ]+(?:academic[, ]+)?non[- ]commercial\b",
            r"\bnon[- ]commercial (?:laboratory |academic |internal )?research(?: only)?\b",
            r"\bresearch use only\b",
        ),
        "fail": _compile(
            r"(?<!non-)(?<!non )\bcommercial(?:ization|isation|ize|ise|ly)?\b",
            r"\bproduct development\b",
            r"\bcompany decision\b",
            r"\bmanufactur(?:e|ing).{0,30}\b(?:sale|market)\b",
        ),
    },
    "chemical_not_used_in_humans": {
        "pass": _compile(
            r"\bnot (?:intended |approved )?for (?:clinical |diagnostic )?use in humans?\b",
            r"\bnot (?:be )?used in humans?\b",
            r"\bno human (?:use|subjects?|patients?)\b",
            r"\bin vitro (?:research )?only\b",
        ),
        "fail": _compile(
            r"\b(?:use|used|test|tested|administer(?:ed)?|inject(?:ed)?|implant(?:ed)?) (?:on|in|into|to) (?:a )?(?:humans?|patients?|subjects?)\b",
            r"\b(?:will be |is |are )?(?:used|tested|intended).{0,50}\b(?:humans?|patients?|subjects?)\b",
            r"\bhuman (?:testing|use|trial)\b",
            r"\bclinical trial\b",
        ),
    },
    "device_not_used_in_humans": {
        "pass": _compile(
            r"\bnot (?:intended |approved )?for (?:clinical |diagnostic )?use in humans?\b",
            r"\bnot (?:be )?used in humans?\b",
            r"\bno human (?:use|subjects?|patients?)\b",
            r"\bin vitro (?:research )?only\b",
        ),
        "fail": _compile(
            r"\b(?:use|used|test|tested|administer(?:ed)?|inject(?:ed)?|implant(?:ed)?) (?:on|in|into|to) (?:a )?(?:humans?|patients?|subjects?)\b",
            r"\bclinical trial\b",
        ),
    },
    "device_not_clinical_or_diagnostic": {
        "pass": _compile(
            r"\bnot (?:for |intended for )?(?:clinical|diagnostic)(?: use)?\b",
            r"\bnot .{0,60}(?:clinical|diagnostic) use\b",
            r"\bno (?:clinical|diagnostic) use\b",
            r"\bnot .{0,40}for diagnosis\b",
            r"\bresearch use only\b",
        ),
        "fail": _compile(
            r"\bclinical (?:use|trial|application|device)\b",
            r"\bdiagnostic (?:use|test|application|device)\b",
            r"\bclinical diagnos(?:is|tic)\b",
            r"\b(?:clinical|diagnostic).{0,30}\b(?:testing|evaluation|diagnos(?:is|tic))\b",
        ),
    },
    "device_no_embedded_third_party_ip": {
        "pass": _compile(
            r"\bno (?:embedded )?third[- ]party (?:ip|intellectual property|software|firmware|components?|restrictions?)\b",
        ),
        "fail": _compile(
            r"\bthird[- ]party (?:ip|intellectual property|software|firmware|components?)\b",
            r"\bproprietary (?:software|firmware|component)\b",
            r"\blicensed (?:from|to|by) (?:a )?third[- ]party\b",
            r"\bincorporates? (?:a )?third[- ]party (?:components?|software|firmware)\b",
        ),
    },
    "no_funding_restrictions": {
        "pass": _compile(r"\bno (?:external )?funding restrictions?\b"),
        "fail": _compile(
            r"\bfunding (?:agreement )?(?:terms?|restrictions?) (?:apply|follow|restrict)\b",
            r"\bsponsor approval (?:is )?required\b",
        ),
    },
    "not_invention_report_patented_or_encumbered": {
        "pass": _compile(
            r"\bno (?:invention report,? )?(?:patent,? )?(?:license,? )?(?:or )?encumbrance applies\b",
            r"\bnot (?:the subject of )?an invention report and (?:is )?not patented or encumbered\b",
            r"\bnot patented,? licensed,? encumbered,? or the subject of an invention report\b",
        ),
        "fail": _compile(
            r"\bpatented\b",
            r"\bencumbered\b",
            r"\bsubject (?:of|to) an invention report\b",
            r"\blicensed by (?:u[- ]m|the university of michigan)\b",
        ),
    },
    "no_human_subjects_materials_or_data": {
        "pass": _compile(
            r"\bno human[- ]subjects?[- ]derived (?:materials?|data)\b",
            r"\bno human[- ]derived (?:materials?|data)\b",
        ),
        "fail": _compile(
            r"\bhuman[- ]subjects?[- ]derived (?:materials?|data)\b",
            r"\bhuman[- ]derived (?:materials?|samples?|tissues?|data)\b",
        ),
    },
    "not_controlled_beyond_ear99": {
        "pass": _compile(
            r"\bear99\b",
            r"\bnot (?:export[- ]controlled|a controlled substance)\b",
        ),
        "fail": _compile(
            r"\bdea schedule [ivx0-9]+\b",
            r"\bcontrolled substance\b",
            r"\bexport[- ]controlled\b",
        ),
    },
    "return_not_required": {
        "pass": _compile(r"\bno return is required\b", r"\breturn is not required\b"),
        "fail": _compile(r"\breturn is required\b", r"\bmust be returned\b"),
    },
    "chemical_no_heightened_ehs_risk": {
        "pass": _compile(
            r"\bno heightened (?:ehs|environmental health and safety) risk\b",
            r"\bstandard laboratory handling\b",
        ),
        "fail": _compile(
            r"\bheightened (?:ehs|environmental health and safety) risk\b",
            r"\b(?:explosive|acutely toxic|highly toxic|dangerous to handle)\b",
        ),
    },
    "biological_nonradioactive": {
        "pass": _compile(r"\bnon[- ]radioactive\b", r"\bnot radioactive\b"),
        "fail": _compile(r"\bradioactive\b"),
    },
    "biological_material_definition_met": {
        "pass": _compile(
            r"\b(?:cell lines?|bacteria|fungi|viruses?|plasmids?|vectors?|synthetic nucleic acids?)\b"
        ),
        "fail": _compile(r"\bnot (?:a )?biological material\b"),
    },
    "biological_safe_handling_storage_use": {
        "pass": _compile(r"\bsafe (?:for|to) handl(?:e|ing),? stor(?:e|age),? and use\b"),
        "fail": _compile(
            r"\bdangerous to (?:handle|store|use)\b",
            r"\bunsafe to (?:handle|store|use)\b",
        ),
    },
    "animal_no_live_animals": {
        "pass": _compile(
            r"\bno live animals?\b",
            r"\bnon[- ]living (?:animal )?(?:materials?|derivatives?|samples?)\b",
        ),
        "fail": _compile(
            r"\blive animals?\b",
            r"\bin vivo animal\b",
        ),
    },
    "animal_no_restricted_species_or_permits": {
        "pass": _compile(
            r"\bno restricted species\b",
            r"\bno (?:special )?permits? (?:are )?(?:needed|required|involved)\b",
        ),
        "fail": _compile(
            r"\brestricted species\b",
            r"\b(?:special |wildlife |import |export )permit (?:is )?(?:needed|required)\b",
        ),
    },
    "animal_nonliving_derivative_definition_met": {
        "pass": _compile(
            r"\bnon[- ]living (?:animal )?(?:derivatives?|materials?|samples?)\b",
            r"\bnon[- ]living .{0,30}(?:tissues?|samples?|organs?|cell lines?)\b",
            r"\b(?:fixed (?:animal )?samples?|animal tissues?|animal organs?|mouse cell lines?)\b",
            r"\bno live animals?\b",
        ),
        "fail": _compile(r"\blive animals?\b", r"\bwhole living organism\b"),
    },
}


def _source_text(values: Mapping[str, Any]) -> dict[str, str]:
    return {
        field_id: _sentence_scoped(value.strip())
        for field_id in TEXT_FIELDS
        if isinstance((value := values.get(field_id)), str) and value.strip()
    }


def analyze_open_text(values: Mapping[str, Any]) -> dict[str, Any]:
    """Apply small, deterministic phrase rules to checklist-relevant free text.

    A rule passes only on explicit language. Any conflicting or disqualifying phrase
    fails the rule. Text with neither remains unresolved; it is never guessed.
    """

    sources = _source_text(values)
    facts: dict[str, bool | None] = {}
    evidence: dict[str, dict[str, Any]] = {}

    for fact_id, rule in RULES.items():
        pass_matches: list[tuple[str, str]] = []
        fail_matches: list[tuple[str, str]] = []
        for field_id, text in sources.items():
            for pattern in rule["pass"]:
                if match := pattern.search(text):
                    pass_matches.append((field_id, match.group(0)))
            fail_text = text
            for pattern in rule["pass"]:
                fail_text = pattern.sub(lambda match: " " * len(match.group(0)), fail_text)
            for pattern in rule["fail"]:
                if match := pattern.search(fail_text):
                    fail_matches.append((field_id, match.group(0)))

        if fail_matches:
            value: bool | None = False
            matches = fail_matches
        elif pass_matches:
            value = True
            matches = pass_matches
        else:
            value = None
            matches = []
        facts[fact_id] = value
        evidence[fact_id] = {
            "decision": value,
            "matched_phrases": list(dict.fromkeys(match for _, match in matches)),
            "source_fields": list(dict.fromkeys(field for field, _ in matches)),
        }

    return {
        "method": "spacy_sentence_scoped_phrase_rules",
        "nlp_backend": {
            "library": "spacy",
            "pipeline": "blank_en_with_sentencizer",
            "network_required": False,
        },
        "facts": facts,
        "evidence": evidence,
    }
