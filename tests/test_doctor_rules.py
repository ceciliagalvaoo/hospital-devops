"""Unit tests for the weekly availability rules of doctor registration (T-02.2)."""

from datetime import time

import pytest

from app.doctors import MESSAGES, WeeklyRange, validate_availability
from app.models import Weekday


def check(*rows):
    """Run the rules on rows of (weekday, start, end)."""
    columns = list(zip(*rows, strict=True)) if rows else [(), (), ()]
    return validate_availability(*(list(column) for column in columns))


def test_valid_ranges_are_read_in_the_order_given():
    ranges, errors = check(("2", "14:00", "18:00"), ("0", "08:00", "12:30"))

    assert errors == {}
    assert ranges == [
        WeeklyRange(Weekday.WEDNESDAY, time(14), time(18)),
        WeeklyRange(Weekday.MONDAY, time(8), time(12, 30)),
    ]


def test_at_least_one_range_is_required():
    assert check() == ([], {"availability": MESSAGES["availability_missing"]})
    assert check(("", "", ""), (" ", "", "")) == (
        [],
        {"availability": MESSAGES["availability_missing"]},
    )


def test_empty_rows_are_ignored_and_rows_keep_their_numbers():
    ranges, errors = check(("", "", ""), ("0", "08:00", "12:00"), ("1", "25:00", "26:00"))

    assert len(ranges) == 1
    assert errors == {"availability_3": MESSAGES["range_time"]}


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (("0", "08:00", ""), "range_incomplete"),
        (("", "08:00", "12:00"), "range_incomplete"),
        (("7", "08:00", "12:00"), "range_weekday"),
        (("monday", "08:00", "12:00"), "range_weekday"),
        (("-1", "08:00", "12:00"), "range_weekday"),
        (("0", "08:15", "12:00"), "range_time"),
        (("0", "8:00", "12:00"), "range_time"),
        (("0", "08:00", "24:00"), "range_time"),
        (("0", "08:00:00", "12:00"), "range_time"),
        (("0", "12:00", "12:00"), "range_order"),
        (("0", "12:00", "08:00"), "range_order"),
    ],
)
def test_invalid_ranges_are_identified_by_their_row(row, message):
    ranges, errors = check(("1", "08:00", "12:00"), row)

    assert errors == {"availability_2": MESSAGES[message]}
    assert len(ranges) == 1


def test_the_whole_day_on_the_half_hour_is_accepted():
    ranges, errors = check(("6", "00:00", "23:30"))

    assert errors == {}
    assert ranges == [WeeklyRange(Weekday.SUNDAY, time(0), time(23, 30))]


@pytest.mark.parametrize(
    "second",
    [
        ("0", "11:30", "13:00"),
        ("0", "07:00", "08:30"),
        ("0", "09:00", "10:00"),
        ("0", "08:00", "12:00"),
    ],
    ids=["end", "start", "inside", "same"],
)
def test_overlapping_ranges_on_the_same_day_are_rejected(second):
    _, errors = check(("0", "08:00", "12:00"), second)

    assert errors == {"availability_2": MESSAGES["range_overlap"]}


def test_adjacent_ranges_and_other_days_do_not_overlap():
    _, errors = check(("0", "08:00", "12:00"), ("0", "12:00", "14:00"), ("1", "08:00", "12:00"))

    assert errors == {}


def test_every_invalid_row_is_reported_at_once_in_row_order():
    _, errors = check(
        ("0", "08:00", "12:00"),
        ("9", "08:00", "12:00"),
        ("0", "10:00", "11:00"),
        ("1", "13:15", "14:00"),
    )

    assert errors == {
        "availability_2": MESSAGES["range_weekday"],
        "availability_3": MESSAGES["range_overlap"],
        "availability_4": MESSAGES["range_time"],
    }
    assert list(errors) == ["availability_2", "availability_3", "availability_4"]  # row order
