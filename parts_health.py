"""Parts wear tracking and health percentages."""

from __future__ import annotations

from datetime import date

from database import get_db
from model_specs import PART_DEFINITIONS, get_model_specs


def seed_parts_for_bike(bike_id: int, make: str | None, model: str | None) -> None:
    specs = get_model_specs(make, model)
    with get_db() as conn:
        existing = conn.execute(
            "SELECT part_type FROM bike_parts WHERE bike_id = ?", (bike_id,)
        ).fetchall()
        existing_types = {row["part_type"] for row in existing}
        for part in PART_DEFINITIONS:
            if part["part_type"] in existing_types:
                continue
            interval_km = specs.get(part.get("interval_km_key") or "") or part.get("default_km")
            conn.execute(
                """
                INSERT INTO bike_parts (bike_id, part_type, label, interval_km, last_done_odometer, last_done_date)
                VALUES (?, ?, ?, ?, NULL, NULL)
                """,
                (bike_id, part["part_type"], part["label"], interval_km),
            )


def sync_part_from_task(bike_id: int, task_type: str, odometer: float, entry_date: str) -> None:
    mapping = {
        "chain_lube": "chain",
        "tire_check": "tires",
        "brake_check": "brake_fluid",
        "oil_topup": "engine_oil",
        "service": "engine_oil",
    }
    part_type = mapping.get(task_type)
    if not part_type:
        return
    with get_db() as conn:
        conn.execute(
            """
            UPDATE bike_parts
            SET last_done_odometer = ?, last_done_date = ?
            WHERE bike_id = ? AND part_type = ?
            """,
            (odometer, entry_date, bike_id, part_type),
        )


def get_parts_health(bike_id: int, current_odo: float | None, make: str | None, model: str | None) -> list[dict]:
    specs = get_model_specs(make, model)
    with get_db() as conn:
        parts = conn.execute(
            "SELECT * FROM bike_parts WHERE bike_id = ? ORDER BY part_type",
            (bike_id,),
        ).fetchall()

    if not parts:
        seed_parts_for_bike(bike_id, make, model)
        with get_db() as conn:
            parts = conn.execute(
                "SELECT * FROM bike_parts WHERE bike_id = ? ORDER BY part_type",
                (bike_id,),
            ).fetchall()

    icon_map = {d["part_type"]: d["icon"] for d in PART_DEFINITIONS}
    results = []

    for part in parts:
        interval = part["interval_km"] or 5000
        health = 100
        status = "ok"
        detail = "Good"
        km_remaining = None

        if part["last_done_odometer"] is not None and current_odo is not None:
            used = current_odo - part["last_done_odometer"]
            pct_used = min(100, max(0, (used / interval) * 100))
            health = max(0, round(100 - pct_used))
            km_remaining = interval - used
            if km_remaining <= 0:
                status = "overdue"
                detail = f"Overdue {abs(km_remaining):.0f} km"
            elif km_remaining <= interval * 0.15:
                status = "soon"
                detail = f"Due in {km_remaining:.0f} km"
            else:
                detail = f"{km_remaining:.0f} km remaining"
        elif part["last_done_date"]:
            detail = f"Last: {part['last_done_date']}"
        else:
            status = "setup"
            detail = "Log service to track"

        results.append({
            "part": part,
            "health": health,
            "status": status,
            "detail": detail,
            "icon": icon_map.get(part["part_type"], "wrench"),
            "km_remaining": km_remaining,
        })

    results.sort(key=lambda x: (0 if x["status"] == "overdue" else 1 if x["status"] == "soon" else 2, x["health"]))
    return results, specs
