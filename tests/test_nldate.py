from datetime import date

import pytest

from nldate import parse
from nldate.parser import DateParseError

TODAY = date(2025, 11, 20)


def test_today_tomorrow_and_yesterday() -> None:
    assert parse("today", TODAY) == date(2025, 11, 20)
    assert parse("tomorrow", TODAY) == date(2025, 11, 21)
    assert parse("yesterday", TODAY) == date(2025, 11, 19)


def test_day_after_tomorrow() -> None:
    assert parse("the day after tomorrow", TODAY) == date(2025, 11, 22)


def test_in_days() -> None:
    assert parse("in 3 days", TODAY) == date(2025, 11, 23)


def test_days_ago() -> None:
    assert parse("10 days ago", TODAY) == date(2025, 11, 10)


def test_next_weekday() -> None:
    assert parse("next Tuesday", TODAY) == date(2025, 11, 25)


def test_last_weekday() -> None:
    assert parse("last Friday", TODAY) == date(2025, 11, 14)


def test_absolute_month_name_with_ordinal() -> None:
    assert parse("December 1st, 2025", TODAY) == date(2025, 12, 1)


def test_dotted_month_abbreviation() -> None:
    assert parse("Dec. 1, 2025", TODAY) == date(2025, 12, 1)


def test_dotted_weekday_abbreviation() -> None:
    assert parse("next Tues.", TODAY) == date(2025, 11, 25)


def test_days_before_absolute_date() -> None:
    assert parse("5 days before December 1st, 2025", TODAY) == date(2025, 11, 26)


def test_multiple_offsets_after_relative_anchor() -> None:
    assert parse("1 year and 2 months after yesterday", TODAY) == date(2027, 1, 19)


def test_words_from_tomorrow() -> None:
    assert parse("two weeks from tomorrow", TODAY) == date(2025, 12, 5)


def test_hyphenated_number_word() -> None:
    assert parse("twenty-one days from today", TODAY) == date(2025, 12, 11)


def test_numeric_date() -> None:
    assert parse("12/1/2025", TODAY) == date(2025, 12, 1)


def test_numeric_date_without_year_uses_reference_year() -> None:
    assert parse("12/1", TODAY) == date(2025, 12, 1)


def test_iso_date() -> None:
    assert parse("2025-12-01", TODAY) == date(2025, 12, 1)


def test_month_overflow_clamps_to_last_day() -> None:
    assert parse("1 month after January 31, 2025", TODAY) == date(2025, 2, 28)


def test_raises_for_unknown_expression() -> None:
    with pytest.raises(DateParseError):
        parse("sometime around lunch", TODAY)
