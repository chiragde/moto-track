# Hosting Moto Track online (budget-friendly)

You can share a **live demo** so testers don’t need to install anything. Here are practical options from free to low-cost.

## Comparison at a glance

| Option | Typical cost | Difficulty | Data persistence | Best for |
|--------|--------------|------------|------------------|----------|
| **Render** (free web service) | $0 | Easy | ⚠️ SQLite may reset on redeploy | Quick public demo |
| **Render** + persistent disk | ~$7/mo disk + compute | Medium | ✅ Yes | Small production app |
| **Render** + PostgreSQL | Free DB tier or ~$7/mo | Medium | ✅ Yes | Real multi-user hosting |
| **Railway** | ~$5/mo credit (often enough) | Easy | ✅ With volume/DB | Hobby projects |
| **Fly.io** | Free allowance | Medium | ✅ With volume | Developers comfortable with CLI |
| **PythonAnywhere** | Free tier available | Easy | ✅ Limited on free | Simple Python hosting |
| **VPS** (Hetzner, DigitalOcean) | ~$4–6/mo | Harder | ✅ Full control | Long-term self-hosting |
| **Local only** | $0 | Easiest | ✅ On your PC | Friends on same network |

---

## Recommended path for “please test my app”

### Phase 1 — Free demo (good enough for feedback)

1. Push code to **GitHub** (public repo).
2. Deploy on **[Render](https://render.com)** using the included `Procfile`.
3. Set environment variables:
   - `SECRET_KEY` — long random string (required)
   - `FLASK_ENV` = `production`
   - `RENDER` = `true`
4. Share the URL (e.g. `https://moto-track.onrender.com`).

**Caveat:** Render’s free tier may **sleep** when idle (slow first load) and **ephemeral disk** can wipe SQLite on redeploy. Fine for short testing rounds; tell testers data may not be permanent.

### Phase 2 — Stable hosting (~$0–10/month)

- Add **Render PostgreSQL** (free tier exists) and set `DATABASE_URL` in Render dashboard, **or**
- Add a **persistent disk** on Render for SQLite, **or**
- Use **Railway** / **Fly.io** with a small database or volume.

The app already supports PostgreSQL via `DATABASE_URL`.

---

## Deploy to Render (step by step)

1. Create a GitHub repository and push this project.
2. On [render.com](https://render.com), **New → Web Service**.
3. Connect your GitHub repo.
4. Settings:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** (leave empty — uses `Procfile`)
5. **Environment variables:**
   ```
   SECRET_KEY=<generate-a-long-random-string>
   FLASK_ENV=production
   RENDER=true
   ```
6. Deploy and open the provided URL.

Optional: `OPENAI_API_KEY` for receipt scanning on the hosted site.

---

## What testers need if you host online

**Nothing installed** — just a browser and your URL.

If they run **locally** instead, they only need **Python 3.10+** (see [GETTING_STARTED.md](GETTING_STARTED.md)).

---

## Security reminders before going public

- Never commit `.env`, `moto_track.db`, or `uploads/` (already in `.gitignore`).
- Always set a strong `SECRET_KEY` in production.
- Treat early public deployments as **beta** — use test accounts, not real sensitive data.
