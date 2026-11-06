"""Exemples de l'énoncé, cas limites et propriétés des deux exercices."""

import random
import re

import pytest

from src.algorithms import full_justify, reverse_words


@pytest.mark.parametrize(("text", "expected"), [
    ("the sky is blue", "blue is sky the"),
    ("  hello world  ", "world hello"),
    ("a good   example", "example good a"),
    ("word", "word"),
    ("   word   ", "word"),
    ("a", "a"),
    ("A1   b2 C3", "C3 b2 A1"),
])
def test_reverse_words_examples_and_boundaries(text, expected):
    assert reverse_words(text) == expected


def test_reverse_words_at_maximum_input_length():
    text = " a" * 4999 + " b"
    assert len(text) == 10_000
    result = reverse_words(text)
    assert result == "b " + " ".join(["a"] * 4999)


@pytest.mark.parametrize(("words", "width", "expected"), [
    (
        ["This", "is", "an", "example", "of", "text", "justification."], 16,
        ["This    is    an", "example  of text", "justification.  "],
    ),
    (
        ["What", "must", "be", "acknowledgment", "shall", "be"], 16,
        ["What   must   be", "acknowledgment  ", "shall be        "],
    ),
    (
        ["Science", "is", "what", "we", "understand", "well", "enough", "to", "explain",
         "to", "a", "computer.", "Art", "is", "everything", "else", "we", "do"], 20,
        ["Science  is  what we", "understand      well", "enough to explain to",
         "a  computer.  Art is", "everything  else  we", "do                  "],
    ),
    (["a", "b", "c"], 1, ["a", "b", "c"]),
    (["hello"], 5, ["hello"]),
    (["hi"], 5, ["hi   "]),
    (["a", "b", "c", "d", "e"], 5, ["a b c", "d e  "]),
    (["long", "words"], 6, ["long  ", "words "]),
    (["aa", "bb", "cc", "dd", "eeeeeee"], 13, ["aa  bb  cc dd", "eeeeeee      "]),
    (["aa", "bb", "cc", "dd", "eeeeeee"], 14, ["aa  bb  cc  dd", "eeeeeee       "]),
    (["a", "bb", "c", "ddd", "elephant"], 12, ["a  bb  c ddd", "elephant    "]),
])
def test_justification_examples_and_boundaries(words, width, expected):
    before = words.copy()
    result = full_justify(words, width)
    assert result == expected
    assert all(len(line) == width for line in result)
    assert words == before


def assert_justification_rules(words, width):
    lines = full_justify(words, width)
    assert all(len(line) == width for line in lines)
    assert [word for line in lines for word in line.split()] == words
    consumed = 0
    for index, line in enumerate(lines):
        tokens = line.split()
        consumed += len(tokens)
        assert not line.startswith(" ")
        if index == len(lines) - 1 or len(tokens) == 1:
            assert line.rstrip() == " ".join(tokens)
        else:
            assert not line.endswith(" ")
            spaces = [len(gap) for gap in re.findall(r" +", line)]
            assert max(spaces) - min(spaces) <= 1
            assert spaces == sorted(spaces, reverse=True)
        if consumed < len(words):
            # Aucun mot supplémentaire ne doit tenir, même avec un seul espace par intervalle.
            minimum_length = sum(map(len, tokens)) + len(tokens) - 1
            assert minimum_length + 1 + len(words[consumed]) > width


def test_justification_at_maximum_constraints():
    words = ["x" * 20] * 300
    assert_justification_rules(words, 100)
    assert len(full_justify(words, 100)) == 75


def test_justification_rules_on_varied_inputs():
    generator = random.Random(2026)
    for _ in range(100):
        words = ["x" * generator.randint(1, 20) for _ in range(generator.randint(1, 300))]
        width = generator.randint(max(map(len, words)), 100)
        assert_justification_rules(words, width)


@pytest.mark.parametrize(("words", "width"), [
    (["a"], 0),
    (["a"], -1),
    ([], 5),
    ([""], 5),
    (["toolong"], 3),
])
def test_invalid_justification_inputs_are_rejected(words, width):
    with pytest.raises(ValueError):
        full_justify(words, width)
