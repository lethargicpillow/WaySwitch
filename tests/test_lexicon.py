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
