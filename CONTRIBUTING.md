# Contributing & testing

Thanks for trying Moto Track. This project is in active development and your feedback helps a lot.

## How to test

1. Follow [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) to run the app locally.
2. Create a test account (please don’t use a real password you use elsewhere).
3. Try the main flows:
   - Add a bike in **Garage**
   - Log fuel on **Fuel**
   - Add a service entry via **More → Service**
   - Log DIY care and reminders on **Care**
   - Check **Timeline** for combined history
   - Switch bikes with the orange pills under the page title
   - Swipe left on history rows to edit or delete
4. Optional: run smoke tests — `run_smoke.bat` (Windows) or `./run_smoke.sh` (macOS/Linux).

## Reporting issues

Open a [GitHub issue](https://github.com/YOUR_USERNAME/moto-track/issues) and include:

- **Environment:** Windows / macOS / Linux, browser, phone model if relevant
- **Python version:** output of `python --version`
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Screenshots or screen recording** when UI-related

## Suggesting features

Issues labeled `enhancement` are welcome. Describe the problem you’re solving and how you’d expect it to work on mobile.

## Code contributions

1. Fork the repository.
2. Create a branch for your change.
3. Run smoke tests before opening a pull request.
4. Keep changes focused — one feature or fix per PR.

## What not to commit

- `.env` (secrets)
- `moto_track.db` or `uploads/` (personal data)
- `.venv/` (virtual environment)

These are listed in `.gitignore`.
