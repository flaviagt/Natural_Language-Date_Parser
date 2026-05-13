write a Python package named `nldate` that has a `parse()` function with the following signature:

```python
from datetime import date

def parse(s: str, today: date | None = None) -> date:
    ...
```

Given a natural language date, like "5 days before December 1st, 2025" or "next
Tuesday", the `parse()` function should return a `datetime.date` object
representing the date that the input string refers to. The `today` parameter is
used as a reference point for relative date expressions (like "next Tuesday" or
"in 3 days"). If `today` is not provided, it should default to the current
date.

## Requirements
- Your project should be a Python project managed with `uv`.
- Your project should contain a `tests/` directory containing a pytest test
  suite with at least 10 tests. All tests must pass.
- `mypy` and `ruff` should pass with no errors on your codebase.