"""Unit tests for reading a patient search query (T-09.1)."""

import pytest

from app.patients import SEARCH_MESSAGES, InvalidSearch, SearchQuery, _contains, parse_search


@pytest.mark.parametrize("query", ["P-000042", "p-000042", "P42", "p42", "42", "000042", " P-42 "])
def test_record_numbers_in_every_usual_form(query):
    assert parse_search(query) == SearchQuery(42, ())


@pytest.mark.parametrize(
    ("query", "words"),
    [
        ("maria", ("maria",)),
        ("  Silva   Maria ", ("Silva", "Maria")),
        ("P-maria", ("P-maria",)),
        ("42a", ("42a",)),
    ],
)
def test_other_queries_are_words_of_the_name(query, words):
    assert parse_search(query) == SearchQuery(None, words)


@pytest.mark.parametrize("query", ["", "   ", None])
def test_empty_query_is_refused(query):
    with pytest.raises(InvalidSearch, match=SEARCH_MESSAGES["empty"]):
        parse_search(query)


def test_one_letter_is_too_short_but_one_digit_is_a_record_number():
    with pytest.raises(InvalidSearch, match=SEARCH_MESSAGES["too_short"]):
        parse_search("m")
    assert parse_search("7") == SearchQuery(7, ())


def test_like_wildcards_are_matched_literally():
    assert _contains("50%") == "%50\\%%"
    assert _contains("a_b") == "%a\\_b%"
    assert _contains("a\\b") == "%a\\\\b%"
