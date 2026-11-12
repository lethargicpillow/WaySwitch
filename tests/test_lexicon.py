"""Regression tests for the conversational vocabulary supplement."""

import pytest

from tests.fakes import RU, US, keys_for_text, make_keymap
from wayswitch.detector import SENSITIVITY, Detector, LanguageModel
from wayswitch.lexicon import EN_WORDS, RU_WORDS


@pytest.fixture(scope="module")
def detector():
    keymap = make_keymap()
    return Detector(keymap, {lang: LanguageModel.load(lang) for lang in ("ru", "en")})


@pytest.mark.parametrize("word", ["на", "по", "от", "за", "об", "не", "ни", "ли",
                                  "же", "бы", "че", "чё", "чо", "шо", "що",
                                  "щас", "крч", "кста", "спс", "пж", "имхо",
                                  "ваще", "прив", "здарова", "вопреки", "изо"])
def test_conversation_russian(detector, word):
    keys = keys_for_text(detector.keymap, word, RU)
    decision = detector.decide(keys, US, RU, ("ru", "ru"))
    assert decision.action == "fix", (word, decision.reason)
    assert decision.target_text == word
    assert detector.decide(keys, RU, US, ("ru", "ru")).action == "keep"


@pytest.mark.parametrize("word", ["in", "on", "to", "up", "so", "no", "or", "we",
                                  "lol", "brb", "idk", "ngl", "gonna", "wanna",
                                  "throughout", "underneath"])
def test_conversation_english(detector, word):
    keys = keys_for_text(detector.keymap, word, US)
    decision = detector.decide(keys, RU, US, ("en", "en"))
    assert decision.action == "fix", (word, decision.reason)
    assert decision.target_text == word
    assert detector.decide(keys, US, RU, ("en", "en")).action == "keep"


@pytest.mark.parametrize("word,target", [("bp", "из"), ("oj", "що"), ("lf", "да"),
                                         ("lj", "до"), ("rj", "ко"), ("j,", "об"),
                                         ("x`", "чё"), ("g;", "пж")])
def test_short_collisions_require_target_context(detector, word, target):
    keys = keys_for_text(detector.keymap, word, US)
    assert detector.decide(keys, US, RU, (None, None)).action == "keep"
    assert detector.decide(keys, US, RU, ("en", "en")).action == "keep"
    decision = detector.decide(keys, US, RU, ("ru", "ru"))
    assert decision.action == "fix"
    assert decision.target_text == target


@pytest.mark.parametrize("word", ["of", "he", "at", "by", "if", "vs", "BP", "OJ"])
def test_real_english_and_abbreviations_are_preserved(detector, word):
    keys = keys_for_text(detector.keymap, word, US)
    assert detector.decide(keys, US, RU, ("ru", "ru")).action == "keep"


def test_conservative_does_not_override_dictionary_collision(detector):
    keys = keys_for_text(detector.keymap, "bp", US)
    det = Detector(detector.keymap, detector.models, sensitivity=SENSITIVITY["conservative"])
    assert det.decide(keys, US, RU, ("ru", "ru")).action == "keep"


def test_supplement_loaded_without_retraining(detector):
    assert RU_WORDS <= detector.models["ru"].words
    assert EN_WORDS <= detector.models["en"].words


@pytest.mark.parametrize("word,source,target,previous", [
    ("на", US, RU, "en"), ("по", US, RU, "en"), ("от", US, RU, "en"),
    ("же", US, RU, "en"), ("бы", US, RU, "en"),
    ("че", US, RU, "en"), ("шо", US, RU, "en"),
    ("in", RU, US, "ru"), ("on", RU, US, "ru"), ("to", RU, US, "ru"),
])
def test_unambiguous_short_words_can_start_language_transition(
        detector, word, source, target, previous):
    keys = keys_for_text(detector.keymap, word, target)
    decision = detector.decide(keys, source, target, (previous, previous))
    assert (decision.action, decision.target_text) == ("fix", word), decision.reason
    assert decision.reason == "dict-short-transition"


def test_conservative_keeps_original_short_transition_policy(detector):
    keys = keys_for_text(detector.keymap, "на", RU)
    det = Detector(detector.keymap, detector.models, sensitivity=SENSITIVITY["conservative"])
    assert det.decide(keys, US, RU, ("en", "en")).action == "keep"


@pytest.mark.parametrize("context", [
    (None, None), ("ru", "ru"), (None, "en"), ("ru", "en"), ("en", "ru"),
])
def test_pri_lowercase_corpus_collision(detector, context):
    keys = keys_for_text(detector.keymap, "ghb", US)
    assert detector.models["en"].is_word("ghb")
    decision = detector.decide(keys, US, RU, context)
    assert decision.action == "fix", decision.reason
    assert decision.target_text == "при"


@pytest.mark.parametrize("word,context", [
    ("GHB", (None, None)), ("GHB", ("ru", "ru")),
    ("ghb", ("en", "en")), ("Ghb", ("ru", "ru")),
])
def test_ghb_acronym_and_english_context_are_protected(detector, word, context):
    keys = keys_for_text(detector.keymap, word, US)
    assert detector.decide(keys, US, RU, context).action == "keep"


def test_pri_collision_preserves_conservative_and_exceptions(detector):
    keys = keys_for_text(detector.keymap, "ghb", US)
    conservative = Detector(detector.keymap, detector.models,
                            sensitivity=SENSITIVITY["conservative"])
    assert conservative.decide(keys, US, RU, ("ru", "ru")).action == "keep"
    excluded = Detector(detector.keymap, detector.models, exceptions={"ghb"})
    assert excluded.decide(keys, US, RU, ("ru", "ru")).reason == "exception"


@pytest.mark.parametrize("word,group", [
    ("дефисы-соединители", RU), ("более-менее", RU), ("proof-of-concept", US),
])
def test_compound_layout_and_source_preservation(detector, word, group):
    keys = keys_for_text(detector.keymap, word, group)
    other = US if group == RU else RU
    result = detector.decide(keys, group, other, (None, None))
    assert result.action == "keep", result.reason
    result = detector.decide(keys, other, group, (None, None))
    assert (result.action, result.target_text) == ("fix", word), result.reason
