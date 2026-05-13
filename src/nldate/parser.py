"""A compact natural-language date parser.

The parser deliberately favors common calendar phrases over a huge grammar. It
normalizes the input, handles recursively anchored expressions, and then falls
through from specific relative phrases to absolute date formats.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta


class DateParseError(ValueError):
    """Raised when a string cannot be parsed as a supported date expression."""


MONTHS: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sept": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

NUMBER_WORDS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "a": 1,
    "an": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

DATE_SEPARATORS = r"[./-]"
MONTH_NAMES = "|".join(sorted(MONTHS, key=len, reverse=True))
WEEKDAY_NAMES = "|".join(sorted(WEEKDAYS, key=len, reverse=True))
OFFSET_PATTERN = re.compile(
    r"(?P<num>\d+|[a-z]+(?:\s+[a-z]+)?)\s+"
    r"(?P<unit>days?|weeks?|months?|years?)",
)


@dataclass(frozen=True)
class Offset:
    value: int
    unit: str


def parse(s: str, today: date | None = None) -> date | None:
    """Parse a natural-language date expression into a ``datetime.date``.

    Args:
        s: The date expression to parse.
        today: Reference date for relative expressions. Defaults to today.

    Returns:
        The parsed date, or ``None`` if the expression is unsupported.
    """

    reference = date.today() if today is None else today
    normalized = _normalize(s)
    if not normalized:
        return None

    return _parse_normalized(normalized, reference)


def _parse_normalized(text: str, today: date) -> date | None:
    before_after = _parse_before_after(text, today)
    if before_after is not None:
        return before_after

    direct = _parse_direct_relative(text, today)
    if direct is not None:
        return direct

    weekday = _parse_weekday(text, today)
    if weekday is not None:
        return weekday

    absolute = _parse_absolute(text, today)
    if absolute is not None:
        return absolute

    return None


def _normalize(s: str) -> str:
    text = s.strip().lower()
    text = re.sub(r"\b(\d+)(st|nd|rd|th)\b", r"\1", text)
    text = re.sub(r"\b([a-z]+)\.", r"\1", text)
    text = re.sub(r"(?<=[a-z])-(?=[a-z])", " ", text)
    text = re.sub(r"\bfrom now\b", "from today", text)
    text = re.sub(r"\s*,\s*", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _parse_before_after(text: str, today: date) -> date | None:
    for keyword in ("before", "after", "from"):
        match = re.fullmatch(rf"(?P<offsets>.+)\s+{keyword}\s+(?P<anchor>.+)", text)
        if match is None:
            continue

        offsets = _parse_offsets(match.group("offsets"))
        if not offsets:
            continue

        anchor_text = match.group("anchor")
        anchor = (
            today
            if anchor_text == "today" and keyword == "from"
            else parse(
                anchor_text,
                today,
            )
        )
        if anchor is None:
            return None

        sign = -1 if keyword == "before" else 1
        return _apply_offsets(anchor, offsets, sign)

    return None


def _parse_direct_relative(text: str, today: date) -> date | None:
    special = {
        "today": today,
        "tomorrow": today + timedelta(days=1),
        "yesterday": today - timedelta(days=1),
        "day after tomorrow": today + timedelta(days=2),
        "the day after tomorrow": today + timedelta(days=2),
        "day before yesterday": today - timedelta(days=2),
        "the day before yesterday": today - timedelta(days=2),
    }
    if text in special:
        return special[text]

    match = re.fullmatch(r"in\s+(.+)", text)
    if match is not None:
        offsets = _parse_offsets(match.group(1))
        if offsets:
            return _apply_offsets(today, offsets, 1)

    match = re.fullmatch(r"(.+)\s+ago", text)
    if match is not None:
        offsets = _parse_offsets(match.group(1))
        if offsets:
            return _apply_offsets(today, offsets, -1)

    match = re.fullmatch(r"(next|last)\s+(day|week|month|year)", text)
    if match is not None:
        direction = 1 if match.group(1) == "next" else -1
        unit = match.group(2)
        return _apply_offsets(today, [Offset(1, unit)], direction)

    return None


def _parse_weekday(text: str, today: date) -> date | None:
    match = re.fullmatch(rf"(?:(next|last|this)\s+)?({WEEKDAY_NAMES})", text)
    if match is None:
        return None

    modifier = match.group(1)
    target = WEEKDAYS[match.group(2)]
    current = today.weekday()

    if modifier == "last":
        days = (current - target) % 7
        return today - timedelta(days=7 if days == 0 else days)

    if modifier == "this":
        return today + timedelta(days=(target - current) % 7)

    days_ahead = (target - current) % 7
    if modifier == "next" or days_ahead == 0:
        days_ahead = 7 if days_ahead == 0 else days_ahead
    return today + timedelta(days=days_ahead)


def _parse_absolute(text: str, today: date) -> date | None:
    parsed = _parse_iso_date(text)
    if parsed is not None:
        return parsed

    parsed = _parse_numeric_date(text, today)
    if parsed is not None:
        return parsed

    parsed = _parse_month_name_date(text, today)
    if parsed is not None:
        return parsed

    return None


def _parse_iso_date(text: str) -> date | None:
    match = re.fullmatch(
        rf"(\d{{4}}){DATE_SEPARATORS}(\d{{1,2}}){DATE_SEPARATORS}(\d{{1,2}})",
        text,
    )
    if match is None:
        return None
    year, month, day = (int(part) for part in match.groups())
    return _safe_date(year, month, day)


def _parse_numeric_date(text: str, today: date) -> date | None:
    match = re.fullmatch(
        rf"(\d{{1,2}}){DATE_SEPARATORS}(\d{{1,2}})"
        rf"(?:{DATE_SEPARATORS}(\d{{2,4}}))?",
        text,
    )
    if match is None:
        return None

    month = int(match.group(1))
    day = int(match.group(2))
    year_text = match.group(3)
    year = today.year if year_text is None else _normalize_year(year_text)
    return _safe_date(year, month, day)


def _parse_month_name_date(text: str, today: date) -> date | None:
    month_day = re.fullmatch(
        rf"(?P<month>{MONTH_NAMES})\s+(?P<day>\d{{1,2}})(?:\s+(?P<year>\d{{2,4}}))?",
        text,
    )
    if month_day is not None:
        month = MONTHS[month_day.group("month")]
        day = int(month_day.group("day"))
        year = _year_from_optional(month_day.group("year"), today)
        return _safe_date(year, month, day)

    day_month = re.fullmatch(
        rf"(?P<day>\d{{1,2}})\s+(?:of\s+)?(?P<month>{MONTH_NAMES})(?:\s+(?P<year>\d{{2,4}}))?",
        text,
    )
    if day_month is not None:
        month = MONTHS[day_month.group("month")]
        day = int(day_month.group("day"))
        year = _year_from_optional(day_month.group("year"), today)
        return _safe_date(year, month, day)

    return None


def _parse_offsets(text: str) -> list[Offset] | None:
    cleaned = text.replace(",", " ")
    cleaned = re.sub(r"\band\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None

    offsets: list[Offset] = []
    position = 0
    for match in OFFSET_PATTERN.finditer(cleaned):
        if cleaned[position : match.start()].strip():
            return None
        number = _parse_number(match.group("num"))
        if number is None:
            return None
        unit = match.group("unit").rstrip("s")
        offsets.append(Offset(number, unit))
        position = match.end()

    if cleaned[position:].strip() or not offsets:
        return None
    return offsets


def _parse_number(text: str) -> int | None:
    if text.isdigit():
        return int(text)
    if text in NUMBER_WORDS:
        return NUMBER_WORDS[text]
    if " " not in text:
        return None

    total = 0
    for part in text.split():
        value = NUMBER_WORDS.get(part)
        if value is None:
            return None
        total += value
    return total


def _apply_offsets(start: date, offsets: list[Offset], sign: int) -> date:
    result = start
    for offset in offsets:
        value = offset.value * sign
        if offset.unit == "day":
            result += timedelta(days=value)
        elif offset.unit == "week":
            result += timedelta(weeks=value)
        elif offset.unit == "month":
            result = _add_months(result, value)
        elif offset.unit == "year":
            result = _add_months(result, value * 12)
        else:
            msg = f"unsupported offset unit: {offset.unit!r}"
            raise DateParseError(msg)
    return result


def _add_months(start: date, months: int) -> date:
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _normalize_year(year_text: str) -> int:
    year = int(year_text)
    if len(year_text) == 2:
        return 2000 + year if year < 70 else 1900 + year
    return year


def _year_from_optional(year_text: str | None, today: date) -> int:
    if year_text is None:
        return today.year
    return _normalize_year(year_text)


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None
