"""HTTP smoke tests for all primary routes and POST flows."""

from __future__ import annotations

import re
import traceback
from datetime import date

from app import app, get_db

FAILURES: list[str] = []
PASSED: list[str] = []
USER = "qa_runner"
PASSWORD = "testpass123"


def ok(name: str, resp, binary: bool = False) -> bool:
    if resp.status_code >= 400:
        FAILURES.append(f"{name}: HTTP {resp.status_code}")
        return False
    if not binary:
        body = resp.get_data(as_text=True)
        if "Traceback (most recent call last)" in body:
            FAILURES.append(f"{name}: traceback in HTML")
            return False
    PASSED.append(name)
    return True


def login(client):
    client.get("/logout", follow_redirects=True)
    client.post(
        "/register",
        data={"username": USER, "password": PASSWORD, "confirm": PASSWORD},
        follow_redirects=True,
    )
    resp = client.post(
        "/login",
        data={"username": USER, "password": PASSWORD},
        follow_redirects=True,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"login failed: {resp.status_code}")
    return resp


def run_smoke_tests() -> int:
    client = app.test_client()

    for path in ["/", "/login", "/register", "/forgot-password"]:
        ok(f"GET {path}", client.get(path, follow_redirects=True))

    login(client)

    pages = [
        "/dashboard",
        "/timeline",
        "/garage",
        "/bikes",
        "/fuel",
        "/maintenance",
        "/care",
        "/stats",
        "/more",
        "/odometer",
        "/settings",
        "/receipts",
        "/expenses",
        "/export.csv",
        "/export.pdf",
        "/api/backup",
        "/api/due-reminders",
        "/api/vapid-public-key",
        "/care?from=more",
        "/stats?from=more",
    ]
    for path in pages:
        binary = path.endswith(".pdf") or path.endswith("/api/backup")
        ok(f"GET {path}", client.get(path), binary=binary)

    today = date.today().isoformat()

    ok(
        "POST garage",
        client.post(
            "/garage",
            data={
                "action": "add_bike",
                "name": "QA Bike",
                "make": "Honda",
                "model": "X",
                "year": "2021",
            },
            follow_redirects=True,
        ),
    )

    ok(
        "POST fuel",
        client.post(
            "/fuel",
            data={
                "entry_date": today,
                "liters": "11",
                "cost": "950",
                "odometer": "10000",
                "tag": "city",
                "notes": "qa",
            },
            follow_redirects=True,
        ),
    )

    ok(
        "POST maintenance",
        client.post(
            "/maintenance",
            data={
                "entry_date": today,
                "entry_type": "service",
                "description": "Oil change",
                "cost": "2000",
                "odometer": "10000",
                "notes": "",
            },
            follow_redirects=True,
        ),
    )

    ok(
        "POST care entry",
        client.post(
            "/care",
            data={
                "action": "add_entry",
                "task_type": "chain_lube",
                "entry_date": today,
                "odometer": "10000",
                "description": "Lube",
                "cost": "0",
                "notes": "",
            },
            follow_redirects=True,
        ),
    )

    ok(
        "POST care reminder",
        client.post(
            "/care",
            data={
                "action": "add_reminder",
                "title": "Tires",
                "reminder_type": "tire_check",
                "interval_km": "1000",
                "interval_days": "",
            },
            follow_redirects=True,
        ),
    )

    ok(
        "POST odometer",
        client.post(
            "/odometer",
            data={"reading_date": today, "reading": "10100", "notes": "qa"},
            follow_redirects=True,
        ),
    )

    ok("GET timeline data", client.get("/timeline"))

    ok(
        "POST settings",
        client.post(
            "/settings",
            data={
                "action": "save_settings",
                "theme": "dark",
                "currency": "INR",
                "unit_system": "metric",
                "email": "qa@test.com",
            },
            follow_redirects=True,
        ),
    )

    with get_db() as conn:
        user = conn.execute("SELECT id FROM users WHERE username=?", (USER,)).fetchone()
        bike = conn.execute("SELECT id FROM bikes WHERE user_id=?", (user["id"],)).fetchone()
        bike_id = bike["id"]
        fuel_id = conn.execute(
            "SELECT id FROM fuel_entries WHERE bike_id=? LIMIT 1", (bike_id,)
        ).fetchone()["id"]
        maint_id = conn.execute(
            "SELECT id FROM maintenance_entries WHERE bike_id=? LIMIT 1", (bike_id,)
        ).fetchone()["id"]
        care_id = conn.execute(
            "SELECT id FROM care_entries WHERE bike_id=? LIMIT 1", (bike_id,)
        ).fetchone()["id"]
        odo_id = conn.execute(
            "SELECT id FROM odometer_readings WHERE bike_id=? LIMIT 1", (bike_id,)
        ).fetchone()["id"]
        reminder_id = conn.execute(
            "SELECT id FROM reminders WHERE bike_id=? LIMIT 1", (bike_id,)
        ).fetchone()["id"]

    ok(f"GET edit fuel {fuel_id}", client.get(f"/fuel/{fuel_id}/edit"))
    ok(f"GET edit maintenance {maint_id}", client.get(f"/maintenance/{maint_id}/edit"))
    ok(f"GET edit care {care_id}", client.get(f"/care/{care_id}/edit"))
    ok(f"GET edit odometer {odo_id}", client.get(f"/odometer/{odo_id}/edit"))

    ok(
        "POST mark reminder done",
        client.post(
            "/care",
            data={
                "action": "mark_done",
                "reminder_id": reminder_id,
                "done_date": today,
                "done_odometer": "10100",
            },
            follow_redirects=True,
        ),
    )

    fuel_html = client.get("/fuel").get_data(as_text=True)
    if not re.search(r"/fuel/\d+/edit", fuel_html):
        FAILURES.append("fuel page missing edit link")
    else:
        PASSED.append("fuel edit links present")

    ok(
        "POST garage second bike",
        client.post(
            "/garage",
            data={"action": "add_bike", "name": "QA Bike 2", "make": "", "model": "", "year": ""},
            follow_redirects=True,
        ),
    )

    with get_db() as conn:
        bikes = conn.execute(
            "SELECT id FROM bikes WHERE user_id=(SELECT id FROM users WHERE username=?) ORDER BY id",
            (USER,),
        ).fetchall()
    ok("GET select bike", client.get(f"/bikes/select/{bikes[1]['id']}", follow_redirects=True))

    resp = client.post("/api/parse-receipt", data={"type": "fuel"})
    if resp.status_code not in (400, 200):
        FAILURES.append(f"parse-receipt unexpected {resp.status_code}")
    else:
        PASSED.append("POST /api/parse-receipt")

    ok(
        "POST fuel partial",
        client.post(
            "/fuel",
            data={
                "entry_date": today,
                "liters": "5",
                "cost": "500",
                "odometer": "10150",
                "is_partial": "1",
                "station_name": "Shell QA",
            },
            follow_redirects=True,
        ),
    )

    ok(
        "POST expenses",
        client.post(
            "/expenses",
            data={
                "entry_date": today,
                "category": "insurance",
                "amount": "3500",
                "notes": "qa policy",
            },
            follow_redirects=True,
        ),
    )

    ok(
        "POST api sync",
        client.post(
            "/api/sync",
            json={
                "entries": [
                    {
                        "kind": "fuel",
                        "data": {
                            "entry_date": today,
                            "liters": "10",
                            "cost": "900",
                            "odometer": "10200",
                            "is_partial": False,
                            "station_name": "Offline Station",
                        },
                    }
                ]
            },
        ),
    )

    ok("GET logout", client.get("/logout", follow_redirects=True))

    print(f"\nPASSED ({len(PASSED)}):")
    for item in PASSED:
        print(f"  + {item}")
    if FAILURES:
        print(f"\nFAILED ({len(FAILURES)}):")
        for item in FAILURES:
            print(f"  - {item}")
        return 1
    print("\nAll tests passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run_smoke_tests())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1) from None
