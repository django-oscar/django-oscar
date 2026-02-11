# Running Tests

## Setup

```bash
make venv
```

## Run tests

```bash
venv/bin/pytest --sqlite                                          # all tests, SQLite
venv/bin/pytest --sqlite tests/integration/offer/test_availability.py  # single file
venv/bin/pytest --sqlite tests/integration/offer/test_availability.py::TestASuspendedOffer::test_is_unavailable  # single test
```

Without `--sqlite`, tests require a running PostgreSQL server with a database named `oscar` (default config in `tests/settings.py`).
