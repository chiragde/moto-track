# Tests

Automated checks live here, separate from application source code.

## Databases

| File | Purpose |
|------|---------|
| `moto_track.db` (project root) | Production / day-to-day data |
| `tests/data/moto_track_test.db` | Isolated database for test mode and smoke tests |

The test database is recreated on every smoke test run and is gitignored.

## Run smoke tests

```bash
python tests/run_smoke.py
```

Or on Windows:

```bat
run_smoke.bat
```

This resets `tests/data/moto_track_test.db`, then exercises routes and common POST flows against the Flask test client.

## Run the app in test mode

```bat
run_test.bat
```

Or:

```bash
set MOTO_TRACK_TEST=1
python app.py
```

The UI shows an orange banner when the isolated test database is active.

## Clean automated accounts from the main database

If smoke tests were previously run against `moto_track.db`, remove leftover QA accounts with:

```bash
python tests/cleanup_main_db.py
```
