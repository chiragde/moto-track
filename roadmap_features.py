"""Extended roadmap features: expenses, reports, backup, push, sync."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import date
from io import BytesIO

from flask import Response, flash, jsonify, redirect, render_template, request, session, url_for

from database import get_db, get_db_path
from model_specs import get_model_specs
from parts_health import sync_part_from_task
from settings_helpers import save_user_settings
from tco import EXPENSE_CATEGORIES, build_tco_summary, get_monthly_tco


def register_roadmap_features(app, helpers):
    login_required = helpers["login_required"]
    get_user_bikes = helpers["get_user_bikes"]
    get_active_bike_id = helpers["get_active_bike_id"]
    get_bike_or_404 = helpers["get_bike_or_404"]
    get_latest_odometer = helpers["get_latest_odometer"]
    calculate_fuel_stats = helpers["calculate_fuel_stats"]
    get_timeline_entries = helpers["get_timeline_entries"]
    get_reminders_with_status = helpers["get_reminders_with_status"]

    @app.route("/expenses", methods=["GET", "POST"])
    @login_required
    def expenses():
        user_id = session["user_id"]
        bikes = get_user_bikes(user_id)
        if not bikes:
            flash("Add a bike first.", "error")
            return redirect(url_for("garage"))
        bike_id = get_active_bike_id(user_id)
        bike = get_bike_or_404(user_id, bike_id)

        if request.method == "POST":
            entry_date = request.form.get("entry_date", date.today().isoformat())
            category = request.form.get("category", "other")
            amount = request.form.get("amount", "")
            notes = request.form.get("notes", "").strip()
            try:
                amount_val = float(amount)
                if amount_val < 0:
                    raise ValueError
            except ValueError:
                flash("Enter a valid amount.", "error")
            else:
                with get_db() as conn:
                    conn.execute(
                        """
                        INSERT INTO expense_entries (bike_id, entry_date, category, amount, notes)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (bike_id, entry_date, category, amount_val, notes or None),
                    )
                flash("Expense saved.", "success")
                return redirect(url_for("expenses"))

        with get_db() as conn:
            entries = conn.execute(
                """
                SELECT * FROM expense_entries WHERE bike_id = ?
                ORDER BY entry_date DESC, id DESC
                """,
                (bike_id,),
            ).fetchall()

        fuel_stats = calculate_fuel_stats(bike_id)
        with get_db() as conn:
            maint = conn.execute(
                "SELECT COALESCE(SUM(cost),0) AS t FROM maintenance_entries WHERE bike_id=?",
                (bike_id,),
            ).fetchone()["t"]
        tco = build_tco_summary(bike_id, fuel_stats["total_cost"], maint)

        return render_template(
            "expenses.html",
            bike=bike,
            entries=entries,
            categories=EXPENSE_CATEGORIES,
            tco=tco,
        )

    @app.route("/export.pdf")
    @login_required
    def export_pdf():
        from fpdf import FPDF

        user_id = session["user_id"]
        bikes = get_user_bikes(user_id)
        if not bikes:
            flash("Add a bike first.", "error")
            return redirect(url_for("garage"))
        bike_id = get_active_bike_id(user_id)
        bike = get_bike_or_404(user_id, bike_id)
        fuel_stats = calculate_fuel_stats(bike_id)
        with get_db() as conn:
            maint = conn.execute(
                "SELECT COALESCE(SUM(cost),0) AS t FROM maintenance_entries WHERE bike_id=?",
                (bike_id,),
            ).fetchone()["t"]
        tco = build_tco_summary(bike_id, fuel_stats["total_cost"], maint)
        reminders = get_reminders_with_status(bike_id, (get_latest_odometer(bike_id) or {}).get("reading"))
        specs = get_model_specs(bike["make"], bike["model"])

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, "Moto Track - Vehicle Report", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, f"{bike['name']} - {bike.get('make') or ''} {bike.get('model') or ''}", ln=True)
        pdf.cell(0, 8, f"Generated {date.today().isoformat()}", ln=True)
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Total cost of ownership", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"Fuel: {tco['fuel']:.0f}  |  Service: {tco['maintenance']:.0f}  |  Care: {tco['care']:.0f}  |  Other: {tco['other']:.0f}", ln=True)
        pdf.cell(0, 7, f"Grand total: {tco['total']:.0f}", ln=True)
        pdf.ln(4)

        if specs.get("tire_front_psi"):
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, "Specs (verify with manual)", ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, f"Tire pressure: front {specs.get('tire_front_psi')} psi, rear {specs.get('tire_rear_psi')} psi", ln=True)
            if specs.get("oil_type"):
                pdf.cell(0, 7, f"Oil: {specs['oil_type']}", ln=True)
            pdf.ln(4)

        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Upcoming maintenance", ln=True)
        pdf.set_font("Helvetica", "", 11)
        urgent = [r for r in reminders if r["status"] in ("overdue", "soon", "setup")][:8]
        if urgent:
            for item in urgent:
                pdf.cell(0, 7, f"- {item['reminder']['title']}: {item['detail'] or item['status']}", ln=True)
        else:
            pdf.cell(0, 7, "All reminders on track.", ln=True)

        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=moto-track-{bike['name']}.pdf"},
        )

    @app.route("/api/backup")
    @login_required
    def api_backup():
        user_id = session["user_id"]
        payload = {"exported": date.today().isoformat(), "user_id": user_id, "bikes": [], "tables": {}}
        with get_db() as conn:
            bikes = conn.execute("SELECT * FROM bikes WHERE user_id=?", (user_id,)).fetchall()
            payload["bikes"] = [dict(b) for b in bikes]
            bike_ids = [b["id"] for b in bikes]
            if bike_ids:
                placeholders = ",".join("?" * len(bike_ids))
                for table in (
                    "fuel_entries", "maintenance_entries", "care_entries",
                    "odometer_readings", "reminders", "expense_entries", "bike_parts",
                ):
                    rows = conn.execute(
                        f"SELECT * FROM {table} WHERE bike_id IN ({placeholders})",
                        bike_ids,
                    ).fetchall()
                    payload["tables"][table] = [dict(r) for r in rows]
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("backup.json", json.dumps(payload, indent=2, default=str))
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/zip",
            headers={"Content-Disposition": "attachment; filename=moto-track-backup.zip"},
        )

    @app.route("/api/push-subscribe", methods=["POST"])
    @login_required
    def api_push_subscribe():
        data = request.get_json(silent=True) or {}
        endpoint = data.get("endpoint")
        keys = data.get("keys") or {}
        if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
            return jsonify({"ok": False, "error": "Invalid subscription"}), 400
        user_id = session["user_id"]
        with get_db() as conn:
            conn.execute("DELETE FROM push_subscriptions WHERE endpoint = ?", (endpoint,))
            conn.execute(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, endpoint, keys["p256dh"], keys["auth"]),
            )
            save_user_settings(conn, user_id, {"notifications_enabled": True})
        return jsonify({"ok": True})

    @app.route("/api/sync", methods=["POST"])
    @login_required
    def api_sync():
        """Replay offline-queued entries."""
        user_id = session["user_id"]
        bike_id = get_active_bike_id(user_id)
        get_bike_or_404(user_id, bike_id)
        payload = request.get_json(silent=True) or {}
        queued = payload.get("entries") or []
        synced = 0
        errors = []

        for item in queued:
            kind = item.get("kind")
            data = item.get("data") or {}
            try:
                if kind == "fuel":
                    with get_db() as conn:
                        conn.execute(
                            """
                            INSERT INTO fuel_entries
                            (bike_id, entry_date, liters, cost, odometer, notes, tag, is_partial, station_name)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                bike_id,
                                data.get("entry_date"),
                                float(data.get("liters", 0)),
                                float(data.get("cost", 0)),
                                float(data.get("odometer", 0)),
                                data.get("notes"),
                                data.get("tag"),
                                1 if data.get("is_partial") else 0,
                                data.get("station_name"),
                            ),
                        )
                    synced += 1
                elif kind == "care":
                    with get_db() as conn:
                        conn.execute(
                            """
                            INSERT INTO care_entries
                            (bike_id, entry_date, task_type, description, odometer, cost, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                bike_id,
                                data.get("entry_date"),
                                data.get("task_type", "custom"),
                                data.get("description") or "",
                                float(data.get("odometer", 0)),
                                float(data.get("cost", 0)),
                                data.get("notes"),
                            ),
                        )
                    sync_part_from_task(
                        bike_id,
                        data.get("task_type", "custom"),
                        float(data.get("odometer", 0)),
                        data.get("entry_date"),
                    )
                    synced += 1
            except Exception as exc:
                errors.append(str(exc))

        return jsonify({"ok": True, "synced": synced, "errors": errors})

    @app.route("/api/vapid-public-key")
    def api_vapid_public_key():
        import os
        key = os.environ.get("VAPID_PUBLIC_KEY", "")
        return jsonify({"publicKey": key})
