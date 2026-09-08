"""Total cost of ownership helpers."""

from __future__ import annotations

from database import get_db

EXPENSE_CATEGORIES = {
    "insurance": "Insurance",
    "registration": "Registration / RTO",
    "toll": "Tolls",
    "parking": "Parking",
    "gear": "Gear & accessories",
    "other": "Other",
}


def get_expense_totals(bike_id: int) -> dict:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT category, SUM(amount) AS total, COUNT(*) AS count
            FROM expense_entries
            WHERE bike_id = ?
            GROUP BY category
            """,
            (bike_id,),
        ).fetchall()
        total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expense_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchone()["total"]
        care_total = conn.execute(
            "SELECT COALESCE(SUM(cost), 0) AS total FROM care_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchone()["total"]
    by_category = {row["category"]: {"total": row["total"], "count": row["count"]} for row in rows}
    return {
        "by_category": by_category,
        "expense_total": total,
        "care_total": care_total,
    }


def build_tco_summary(bike_id: int, fuel_cost: float, maintenance_cost: float) -> dict:
    expenses = get_expense_totals(bike_id)
    other = expenses["expense_total"]
    care = expenses["care_total"]
    total = fuel_cost + maintenance_cost + care + other
    return {
        "fuel": fuel_cost,
        "maintenance": maintenance_cost,
        "care": care,
        "other": other,
        "total": total,
        "by_category": expenses["by_category"],
    }


def get_monthly_tco(bike_id: int) -> list[dict]:
    """Aggregate all costs by month for charts."""
    with get_db() as conn:
        fuel = conn.execute(
            "SELECT entry_date, cost FROM fuel_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchall()
        maint = conn.execute(
            "SELECT entry_date, cost FROM maintenance_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchall()
        care = conn.execute(
            "SELECT entry_date, cost FROM care_entries WHERE bike_id = ? AND cost > 0",
            (bike_id,),
        ).fetchall()
        other = conn.execute(
            "SELECT entry_date, amount FROM expense_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchall()

    monthly: dict[str, dict] = {}
    for row in fuel:
        key = row["entry_date"][:7]
        monthly.setdefault(key, {"fuel": 0, "maintenance": 0, "care": 0, "other": 0})
        monthly[key]["fuel"] += row["cost"]
    for row in maint:
        key = row["entry_date"][:7]
        monthly.setdefault(key, {"fuel": 0, "maintenance": 0, "care": 0, "other": 0})
        monthly[key]["maintenance"] += row["cost"]
    for row in care:
        key = row["entry_date"][:7]
        monthly.setdefault(key, {"fuel": 0, "maintenance": 0, "care": 0, "other": 0})
        monthly[key]["care"] += row["cost"]
    for row in other:
        key = row["entry_date"][:7]
        monthly.setdefault(key, {"fuel": 0, "maintenance": 0, "care": 0, "other": 0})
        monthly[key]["other"] += row["amount"]

    return [
        {
            "month": month,
            "fuel": round(v["fuel"], 0),
            "maintenance": round(v["maintenance"], 0),
            "care": round(v["care"], 0),
            "other": round(v["other"], 0),
            "total": round(v["fuel"] + v["maintenance"] + v["care"] + v["other"], 0),
        }
        for month, v in sorted(monthly.items())
    ]
