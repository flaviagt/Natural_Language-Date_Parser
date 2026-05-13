# Natural Language Date Parser

Made for "DSC190 SP2026: Tools of Trade" Class.

`nldate` is a small Python package that parses common natural-language date
phrases into `datetime.date` objects.

```python
from datetime import date

from nldate import parse

assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)
assert parse("next Tuesday", date(2025, 11, 20)) == date(2025, 11, 25)
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy .
```
