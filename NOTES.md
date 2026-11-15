# Notes

## How to run

Everything runs in Docker from the repository root.

Server (listens on `0.0.0.0:8080`; every container starts with an empty SQLite database):

```
docker build -t app .
docker run -p 8080:8080 app
curl http://localhost:8080/health
```

Tests (the `test` stage runs them during the build, and the build fails if any test fails):

```
docker build --target test -t app-test .
docker run --rm app-test
```

There is one request-flow test per part, each against a fresh server:

- `tests/test_part1_members.py`: register a member, look the member up by phone in every spelling, and the core rejections.
- `tests/test_part2_plans_and_invoices.py`: create a plan and an agreement, read the invoice schedule, and an invalid range.
- `tests/test_part3_reconciliation.py`: post the specification's reconciliation run, read it back by id, and a duplicate transaction.

Without Docker (Python 3.12):

```
pip install -r requirements-test.txt
python -m uvicorn app.main:application --host 0.0.0.0 --port 8080
python -m pytest -v -s
```

The database file is set by the `DATABASE_PATH` environment variable (default `/tmp/server.sqlite3`); it is deleted and recreated on every start.

## What I skipped

- Dates near the end of the calendar: an agreement or range whose next due date would fall after 9999-12-31, or a run for month `9999-12`, returns 500 instead of a normal response.
- Amounts above SQLite's integer limit (2^63 - 1) for `monthly` or `joining_fee` return 500 instead of 422.
- The test suite covers each part's core flow only; edge cases such as due day 31 clamping, the other reconciliation verdicts, and concurrent requests are not covered by tests.

## Assumptions

### Part 1 - Members and phones

- During member registration, an international phone number should ideally match the country code sent with it. If they disagree, the phone's country is taken from its dial code and overrides the country code that was sent when the phone is validated and stored.

### Part 2 - Plans and the invoice schedule

- A member may hold several agreements, but only one per plan: a second agreement for the same member and plan is 409 AGREEMENT_EXISTS.
- On GET /agreements/{id}/invoices, an unknown agreement is 404 NOT_FOUND even when the range is also invalid or malformed; missing from or to is still 422 VALIDATION.

### Part 3 - Reconciling the gateway file

_None._
