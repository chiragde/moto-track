# Getting started with Moto Track

This guide is for anyone who wants to run Moto Track on their own computer for testing or personal use.

## What you need

| Requirement | Required? | Notes |
|-------------|-----------|-------|
| **Python 3.10+** | Yes | [python.org/downloads](https://www.python.org/downloads/) |
| **Git** | Only to clone | [git-scm.com](https://git-scm.com/) |
| **Node.js** | No | Not used by this project |
| **Database server** | No | Uses SQLite (a single file on disk) |
| **OpenAI API key** | No | Only for AI receipt scanning |
| **SMTP / email** | No | Only for password-reset emails in production |

**Bottom line:** if you have Python installed, setup is about **5 minutes** — create a virtual environment, install a handful of Python packages, and run the app.

---

## Quick start (Windows)

### 1. Get the code

```powershell
git clone https://github.com/YOUR_USERNAME/moto-track.git
cd moto-track
```

Or download the repository as a ZIP from GitHub and extract it.

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Install dependencies

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. (Optional) Configure environment

```powershell
copy .env.example .env
```

Edit `.env` if you want receipt scanning (`OPENAI_API_KEY`). For basic testing you can skip this step.

### 5. Run the app

Double-click **`run.bat`**, or from the project folder:

```powershell
.\run.bat
```

Open **http://localhost:5000** in your browser (Chrome, Edge, or Safari recommended). Use your phone on the same Wi‑Fi network with `http://YOUR-PC-IP:5000` to test the mobile layout.

### 6. Create an account

1. Tap **Create an account** on the login page.
2. Open **Garage** and tap **+** to add your bike.
3. Explore **Home**, **Fuel**, **Care**, and **Timeline**.

---

## Quick start (macOS / Linux)

```bash
git clone https://github.com/YOUR_USERNAME/moto-track.git
cd moto-track
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional
chmod +x run.sh
./run.sh
```

Then open http://localhost:5000.

---

## Project scripts

| Script | Purpose |
|--------|---------|
| `run.bat` / `run.sh` | Start the app (production data in `moto_track.db`) |
| `run_test.bat` / `run_test.sh` | Start with isolated test database |
| `run_smoke.bat` / `run_smoke.sh` | Run automated smoke tests |

See [tests/README.md](../tests/README.md) for testing details.

---

## Where data is stored

| Path | Contents |
|------|----------|
| `moto_track.db` | Your accounts, bikes, fuel, maintenance, etc. |
| `uploads/` | Receipt and bike photos |
| `tests/data/moto_track_test.db` | Test-only database (created by smoke tests) |

These files are **not** uploaded to GitHub (see `.gitignore`). Each person who runs the app locally gets their own private data.

---

## Optional features

### Receipt scanning (OpenAI)

1. Copy `.env.example` to `.env`.
2. Add an API key from [OpenAI](https://platform.openai.com/api-keys).
3. Restart the app.
4. On **Fuel** or **Service**, use **Scan receipt** to auto-fill fields.

Without a key, you can still attach receipt images manually.

### Password reset emails

Set `SMTP_*` variables in `.env` (see `.env.example`). Not needed for local testing.

---

## Troubleshooting

### `python` is not recognized

Install Python from [python.org](https://www.python.org/downloads/) and enable **“Add Python to PATH”** on Windows.

### Port 5000 already in use

```powershell
set PORT=5001
python app.py
```

Then open http://localhost:5001.

### Virtual environment not found (`run.bat`)

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### App works on this PC but not from phone / another computer

1. **Use the network URL, not localhost.**  
   On the other device, open `http://192.168.x.x:5000` (your host PC’s IPv4).  
   When you start the app, it prints **“On other devices:”** with the right URL.

2. **Find your PC’s IP manually** (if needed):
   ```powershell
   ipconfig
   ```
   Use the **IPv4 Address** under your **Ethernet** adapter (e.g. `192.168.1.42`).

3. **Allow Windows Firewall** (most common fix on Windows).  
   Run PowerShell **as Administrator** once:
   ```powershell
   New-NetFirewallRule -DisplayName "Moto Track (port 5000)" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
   ```
   Or when Windows shows “Allow Python to communicate on private networks?”, click **Allow**.

4. **Same network, not guest Wi‑Fi.**  
   Phone and PC must be on the same router. **Guest Wi‑Fi** often blocks access to LAN devices.

5. **Use `http://` not `https://`.**

6. **Router client isolation.**  
   Some routers have “AP isolation” / “guest network isolation” — disable it or put both devices on the main LAN.

---

## Giving feedback

If something breaks or feels confusing, please open a GitHub issue with:

- Your OS (Windows / macOS / Linux)
- Python version (`python --version`)
- What you expected vs what happened
- Screenshots if helpful

Thank you for testing Moto Track.
