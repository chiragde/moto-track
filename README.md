# Moto Track

A mobile-first web app to track fuel, maintenance, DIY care, and odometer readings for your motorbikes.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**[Getting started for testers →](docs/GETTING_STARTED.md)** · **[Hosting guide →](docs/HOSTING.md)** · **[Contributing →](CONTRIBUTING.md)**

---

## Features

- **Garage** — manage multiple bikes with photos and odometer at a glance
- **Fuel** — quick-add fill-ups, efficiency (km/L), trip tags, receipt photos
- **Service** — workshop visits and ad-hoc repairs
- **DIY Care** — chain lube, washes, custom reminders
- **Timeline** — chronological history across fuel, service, care, and odometer
- **Stats** — spend and efficiency charts
- **Dark mode**, CSV export, PWA install support
- **Receipt scanning** (optional, via OpenAI)

---

## Prerequisites

| What | Required? |
|------|-----------|
| Python 3.10 or newer | **Yes** |
| Git (to clone) | Recommended |
| Node.js | **No** |
| Database server | **No** (SQLite included) |
| OpenAI API key | Optional (receipt scanning only) |

**Local setup is lightweight:** Python + `pip install -r requirements.txt`. No Docker, no Node, no separate database install.

---

## Run locally (Windows)

```powershell
git clone https://github.com/YOUR_USERNAME/moto-track.git
cd moto-track
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env    # optional
run.bat
```

Open **http://localhost:5000**.

## Run locally (macOS / Linux)

```bash
git clone https://github.com/YOUR_USERNAME/moto-track.git
cd moto-track
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # optional
chmod +x run.sh && ./run.sh
```

Full walkthrough: **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**

---

## First use

1. **Register** a new account
2. Open **Garage** → tap **+** to add your bike (make/model, nickname, photo, odometer)
3. Log fuel, service, and care from the bottom tabs
4. Review everything on **Timeline**

---

## Test mode & smoke tests

| Command | Purpose |
|---------|---------|
| `run_test.bat` / `./run_test.sh` | Run app with isolated test database |
| `run_smoke.bat` / `./run_smoke.sh` | Automated route & form tests |

Details: [tests/README.md](tests/README.md)

---

## Configuration

Copy `.env.example` to `.env`:

```env
SECRET_KEY=change-me-to-a-long-random-string
# OPENAI_API_KEY=sk-...          # optional — receipt scanning
# DATABASE_URL=postgresql://...   # optional — production PostgreSQL
```

---

## Publish to GitHub

If this folder is not yet a git repository:

```powershell
# Install Git from https://git-scm.com/ if needed
cd C:\Users\Chirag\Projects\moto-track
git init
git add .
git commit -m "Initial public release of Moto Track"
```

Create a new repository on [github.com/new](https://github.com/new) (public, no README — this repo has one), then:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/moto-track.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Update `YOUR_USERNAME` in `docs/GETTING_STARTED.md` and `CONTRIBUTING.md` after publishing.

**Never commit:** `.env`, `moto_track.db`, `uploads/`, or `.venv/` (already in `.gitignore`).

---

## Hosting online (budget-friendly)

| Approach | Cost | Notes |
|----------|------|-------|
| **Local only** | Free | Share your Wi‑Fi URL with testers on the same network |
| **Render free tier** | $0 | Easy deploy; app may sleep; SQLite data can reset on redeploy |
| **Render + PostgreSQL** | $0–7/mo | Persistent data, better for real users |
| **Railway / Fly.io** | ~$5/mo typical | Good hobby hosting |

Step-by-step: **[docs/HOSTING.md](docs/HOSTING.md)**

---

## Project structure

```
moto-track/
├── app.py              # Flask app & routes
├── database.py         # SQLite / PostgreSQL
├── templates/          # HTML (Jinja2)
├── static/             # CSS, JS, PWA assets
├── tests/              # Smoke tests (isolated from app code)
├── docs/               # Guides for testers & hosting
├── run.bat / run.sh    # Start the server
└── requirements.txt    # Python dependencies
```

---

## Tech stack

- **Backend:** Python, Flask
- **Database:** SQLite (default) or PostgreSQL
- **Frontend:** Server-rendered HTML, vanilla CSS/JS
- **Deploy:** Gunicorn (`Procfile`), tested on Render

---

## License

[MIT](LICENSE) — free to use, modify, and share.

---

## Feedback

Found a bug or have an idea? Open an issue or see [CONTRIBUTING.md](CONTRIBUTING.md).
