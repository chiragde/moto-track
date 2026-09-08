import csv
import io
import os
import secrets
import smtplib
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText

from flask import (
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from constants import BIKE_SERVICE_INTERVALS, CARE_TASK_TYPES, CURRENCIES, TRIP_TAGS, UNIT_PRESETS
from database import get_db
from settings_helpers import get_user_settings, save_user_settings, settings_for_template
from uploads_util import delete_receipt, receipt_belongs_to_user


def register_features(app, helpers):
    login_required = helpers["login_required"]
    get_user_bikes = helpers["get_user_bikes"]
    get_active_bike_id = helpers["get_active_bike_id"]
    get_bike_or_404 = helpers["get_bike_or_404"]
    get_reminders_with_status = helpers["get_reminders_with_status"]
    get_latest_odometer = helpers["get_latest_odometer"]
    handle_receipt_submission = helpers["handle_receipt_submission"]
    parsing_available = helpers["parsing_available"]
    redirect_preserving_from = helpers["redirect_preserving_from"]

    def entry_belongs_to_user(user_id, table, entry_id):
        with get_db() as conn:
            row = conn.execute(
                f"""
                SELECT e.id FROM {table} e
                JOIN bikes b ON e.bike_id = b.id
                WHERE e.id = ? AND b.user_id = ?
                """,
                (entry_id, user_id),
            ).fetchone()
        return row is not None

    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    def settings():
        user_id = session["user_id"]
        if request.method == "POST":
            action = request.form.get("action", "save_settings")
            with get_db() as conn:
                if action == "save_settings":
                    save_user_settings(
                        conn,
                        user_id,
                        {
                            "currency": request.form.get("currency", "INR"),
                            "unit_system": request.form.get("unit_system", "metric"),
                            "theme": request.form.get("theme", "system"),
                            "email": request.form.get("email", "").strip(),
                            "notifications_enabled": request.form.get("notifications_enabled") == "on",
                        },
                    )
                    flash("Settings saved.", "success")
                elif action == "change_password":
                    current = request.form.get("current_password", "")
                    new_pw = request.form.get("new_password", "")
                    confirm = request.form.get("confirm_password", "")
                    user = conn.execute(
                        "SELECT * FROM users WHERE id = ?", (user_id,)
                    ).fetchone()
                    if not check_password_hash(user["password_hash"], current):
                        flash("Current password is incorrect.", "error")
                    elif new_pw != confirm:
                        flash("New passwords do not match.", "error")
                    elif len(new_pw) < 6:
                        flash("Password must be at least 6 characters.", "error")
                    else:
                        conn.execute(
                            "UPDATE users SET password_hash = ? WHERE id = ?",
                            (generate_password_hash(new_pw), user_id),
                        )
                        flash("Password updated.", "success")
            return redirect(url_for("settings"))

        with get_db() as conn:
            raw = get_user_settings(conn, user_id)
        return render_template(
            "settings.html",
            settings=raw,
            currencies=CURRENCIES,
            unit_presets=UNIT_PRESETS,
        )

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            with get_db() as conn:
                user = conn.execute(
                    "SELECT * FROM users WHERE username = ?", (username,)
                ).fetchone()
                if not user:
                    flash("If that account exists, a reset link was sent.", "success")
                    return redirect(url_for("login"))
                settings = get_user_settings(conn, user["id"])
                token = secrets.token_urlsafe(32)
                expires = (datetime.utcnow() + timedelta(hours=2)).isoformat()
                conn.execute(
                    "DELETE FROM password_reset_tokens WHERE user_id = ?",
                    (user["id"],),
                )
                conn.execute(
                    """
                    INSERT INTO password_reset_tokens (user_id, token, expires_at)
                    VALUES (?, ?, ?)
                    """,
                    (user["id"], token, expires),
                )
                reset_url = url_for("reset_password", token=token, _external=True)
                if settings.get("email") and _send_reset_email(settings["email"], reset_url):
                    flash("Password reset link sent to your email.", "success")
                else:
                    flash(
                        f"Reset link (valid 2h): {reset_url}",
                        "success",
                    )
            return redirect(url_for("login"))
        return render_template("forgot_password.html")

    @app.route("/reset-password/<token>", methods=["GET", "POST"])
    def reset_password(token):
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT * FROM password_reset_tokens
                WHERE token = ? AND expires_at > ?
                """,
                (token, datetime.utcnow().isoformat()),
            ).fetchone()
            if not row:
                flash("Invalid or expired reset link.", "error")
                return redirect(url_for("login"))

            if request.method == "POST":
                password = request.form.get("password", "")
                confirm = request.form.get("confirm", "")
                if password != confirm:
                    flash("Passwords do not match.", "error")
                elif len(password) < 6:
                    flash("Password must be at least 6 characters.", "error")
                else:
                    conn.execute(
                        "UPDATE users SET password_hash = ? WHERE id = ?",
                        (generate_password_hash(password), row["user_id"]),
                    )
                    conn.execute(
                        "DELETE FROM password_reset_tokens WHERE id = ?",
                        (row["id"],),
                    )
                    flash("Password reset. Please sign in.", "success")
                    return redirect(url_for("login"))

        return render_template("reset_password.html", token=token)

    @app.route("/export.csv")
    @login_required
    def export_csv():
        user_id = session["user_id"]
        bike_id = get_active_bike_id(user_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["type", "date", "description", "cost", "odometer", "notes", "tag"])

        with get_db() as conn:
            for row in conn.execute(
                """
                SELECT 'fuel' AS type, entry_date, notes, cost, odometer, notes, tag
                FROM fuel_entries WHERE bike_id = ? ORDER BY entry_date
                """,
                (bike_id,),
            ):
                writer.writerow(list(row))
            for row in conn.execute(
                """
                SELECT 'maintenance', entry_date, description, cost, odometer, notes, entry_type
                FROM maintenance_entries WHERE bike_id = ? ORDER BY entry_date
                """,
                (bike_id,),
            ):
                writer.writerow(list(row))
            for row in conn.execute(
                """
                SELECT 'care', entry_date, description, cost, odometer, notes, task_type
                FROM care_entries WHERE bike_id = ? ORDER BY entry_date
                """,
                (bike_id,),
            ):
                writer.writerow(list(row))

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=moto-track-export.csv"},
        )

    @app.route("/receipts")
    @login_required
    def receipts_gallery():
        user_id = session["user_id"]
        bike_id = get_active_bike_id(user_id)
        with get_db() as conn:
            fuel = conn.execute(
                "SELECT id, entry_date, cost, receipt_image FROM fuel_entries WHERE bike_id = ? AND receipt_image IS NOT NULL ORDER BY entry_date DESC",
                (bike_id,),
            ).fetchall()
            maint = conn.execute(
                "SELECT id, entry_date, description, cost, receipt_image FROM maintenance_entries WHERE bike_id = ? AND receipt_image IS NOT NULL ORDER BY entry_date DESC",
                (bike_id,),
            ).fetchall()
        return render_template(
            "receipts.html",
            fuel_receipts=fuel,
            maintenance_receipts=maint,
        )

    @app.route("/api/due-reminders")
    @login_required
    def api_due_reminders():
        user_id = session["user_id"]
        bike_id = get_active_bike_id(user_id)
        latest = get_latest_odometer(bike_id)
        current_odo = latest["reading"] if latest else None
        reminders = get_reminders_with_status(bike_id, current_odo)
        due = [
            {
                "title": r["reminder"]["title"],
                "status": r["status"],
                "detail": r["detail"],
            }
            for r in reminders
            if r["status"] in ("overdue", "soon")
        ]
        return jsonify({"due": due})

    # --- Fuel edit/delete ---
    @app.route("/fuel/<int:entry_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_fuel(entry_id):
        user_id = session["user_id"]
        if not entry_belongs_to_user(user_id, "fuel_entries", entry_id):
            flash("Entry not found.", "error")
            return redirect(url_for("fuel"))
        with get_db() as conn:
            entry = conn.execute(
                "SELECT * FROM fuel_entries WHERE id = ?", (entry_id,)
            ).fetchone()
            if request.method == "POST":
                conn.execute(
                    """
                    UPDATE fuel_entries
                    SET entry_date=?, liters=?, cost=?, odometer=?, notes=?, tag=?
                    WHERE id=?
                    """,
                    (
                        request.form.get("entry_date"),
                        float(request.form.get("liters")),
                        float(request.form.get("cost")),
                        float(request.form.get("odometer")),
                        request.form.get("notes", "").strip() or None,
                        request.form.get("tag") or None,
                        entry_id,
                    ),
                )
                flash("Fuel entry updated.", "success")
                return redirect(url_for("fuel"))
        return render_template(
            "edit_fuel.html",
            entry=entry,
            trip_tags=TRIP_TAGS,
            receipt_scanning_enabled=parsing_available(),
        )

    @app.route("/fuel/<int:entry_id>/delete", methods=["POST"])
    @login_required
    def delete_fuel(entry_id):
        user_id = session["user_id"]
        if not entry_belongs_to_user(user_id, "fuel_entries", entry_id):
            flash("Entry not found.", "error")
            return redirect(url_for("fuel"))
        with get_db() as conn:
            entry = conn.execute(
                "SELECT receipt_image FROM fuel_entries WHERE id = ?", (entry_id,)
            ).fetchone()
            if entry and entry["receipt_image"]:
                delete_receipt(entry["receipt_image"])
            conn.execute("DELETE FROM fuel_entries WHERE id = ?", (entry_id,))
        flash("Fuel entry deleted.", "success")
        return redirect(url_for("fuel"))

    # --- Maintenance edit/delete ---
    @app.route("/maintenance/<int:entry_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_maintenance(entry_id):
        user_id = session["user_id"]
        if not entry_belongs_to_user(user_id, "maintenance_entries", entry_id):
            flash("Entry not found.", "error")
            return redirect(url_for("maintenance"))
        with get_db() as conn:
            entry = conn.execute(
                "SELECT * FROM maintenance_entries WHERE id = ?", (entry_id,)
            ).fetchone()
            if request.method == "POST":
                conn.execute(
                    """
                    UPDATE maintenance_entries
                    SET entry_date=?, entry_type=?, description=?, cost=?, odometer=?, notes=?
                    WHERE id=?
                    """,
                    (
                        request.form.get("entry_date"),
                        request.form.get("entry_type"),
                        request.form.get("description"),
                        float(request.form.get("cost")),
                        float(request.form.get("odometer")) if request.form.get("odometer") else None,
                        request.form.get("notes", "").strip() or None,
                        entry_id,
                    ),
                )
                flash("Maintenance entry updated.", "success")
                return redirect(url_for("maintenance"))
        return render_template("edit_maintenance.html", entry=entry)

    @app.route("/maintenance/<int:entry_id>/delete", methods=["POST"])
    @login_required
    def delete_maintenance(entry_id):
        user_id = session["user_id"]
        if not entry_belongs_to_user(user_id, "maintenance_entries", entry_id):
            flash("Entry not found.", "error")
            return redirect(url_for("maintenance"))
        with get_db() as conn:
            entry = conn.execute(
                "SELECT receipt_image FROM maintenance_entries WHERE id = ?", (entry_id,)
            ).fetchone()
            if entry and entry["receipt_image"]:
                delete_receipt(entry["receipt_image"])
            conn.execute("DELETE FROM maintenance_entries WHERE id = ?", (entry_id,))
        flash("Maintenance entry deleted.", "success")
        return redirect(url_for("maintenance"))

    # --- Care edit/delete ---
    @app.route("/care/<int:entry_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_care(entry_id):
        user_id = session["user_id"]
        if not entry_belongs_to_user(user_id, "care_entries", entry_id):
            flash("Entry not found.", "error")
            return redirect(url_for("care"))
        with get_db() as conn:
            entry = conn.execute(
                "SELECT * FROM care_entries WHERE id = ?", (entry_id,)
            ).fetchone()
            if request.method == "POST":
                conn.execute(
                    """
                    UPDATE care_entries
                    SET entry_date=?, task_type=?, description=?, odometer=?, cost=?, notes=?
                    WHERE id=?
                    """,
                    (
                        request.form.get("entry_date"),
                        request.form.get("task_type"),
                        request.form.get("description"),
                        float(request.form.get("odometer")),
                        float(request.form.get("cost") or 0),
                        request.form.get("notes", "").strip() or None,
                        entry_id,
                    ),
                )
                flash("Care entry updated.", "success")
                return redirect_preserving_from("care")
        return render_template(
            "edit_care.html",
            entry=entry,
            care_task_types=CARE_TASK_TYPES,
        )

    @app.route("/care/<int:entry_id>/delete", methods=["POST"])
    @login_required
    def delete_care(entry_id):
        user_id = session["user_id"]
        if not entry_belongs_to_user(user_id, "care_entries", entry_id):
            flash("Entry not found.", "error")
            return redirect(url_for("care"))
        with get_db() as conn:
            conn.execute("DELETE FROM care_entries WHERE id = ?", (entry_id,))
        flash("Care entry deleted.", "success")
        return redirect_preserving_from("care")

    # --- Odometer edit/delete ---
    @app.route("/odometer/<int:entry_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_odometer(entry_id):
        user_id = session["user_id"]
        if not entry_belongs_to_user(user_id, "odometer_readings", entry_id):
            flash("Entry not found.", "error")
            return redirect(url_for("odometer"))
        with get_db() as conn:
            entry = conn.execute(
                "SELECT * FROM odometer_readings WHERE id = ?", (entry_id,)
            ).fetchone()
            if request.method == "POST":
                conn.execute(
                    """
                    UPDATE odometer_readings
                    SET reading_date=?, reading=?, notes=?
                    WHERE id=?
                    """,
                    (
                        request.form.get("reading_date"),
                        float(request.form.get("reading")),
                        request.form.get("notes", "").strip() or None,
                        entry_id,
                    ),
                )
                flash("Odometer reading updated.", "success")
                return redirect(url_for("odometer"))
        return render_template("edit_odometer.html", entry=entry)

    @app.route("/odometer/<int:entry_id>/delete", methods=["POST"])
    @login_required
    def delete_odometer(entry_id):
        user_id = session["user_id"]
        if not entry_belongs_to_user(user_id, "odometer_readings", entry_id):
            flash("Entry not found.", "error")
            return redirect(url_for("odometer"))
        with get_db() as conn:
            conn.execute("DELETE FROM odometer_readings WHERE id = ?", (entry_id,))
        flash("Odometer reading deleted.", "success")
        return redirect(url_for("odometer"))


def _send_reset_email(to_email, reset_url):
    host = os.environ.get("SMTP_HOST")
    if not host:
        return False
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    from_addr = os.environ.get("SMTP_FROM", user)
    msg = MIMEText(f"Reset your Moto Track password:\n\n{reset_url}\n\nLink expires in 2 hours.")
    msg["Subject"] = "Moto Track password reset"
    msg["From"] = from_addr
    msg["To"] = to_email
    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        return True
    except Exception:
        return False


def seed_reminders_for_bike(bike_id, make=None, model=None):
    from constants import DEFAULT_REMINDERS

    service_km = 5000
    make_lower = (make or "").lower()
    for brand, intervals in BIKE_SERVICE_INTERVALS.items():
        if brand in make_lower or (model and brand in model.lower()):
            service_km = intervals.get("service_km", service_km)
            break

    reminders = []
    for r in DEFAULT_REMINDERS:
        item = dict(r)
        if item["reminder_type"] == "service" and item.get("interval_km"):
            item["interval_km"] = service_km
        reminders.append(item)

    with get_db() as conn:
        for reminder in reminders:
            conn.execute(
                """
                INSERT INTO reminders
                (bike_id, title, reminder_type, interval_km, interval_days)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    bike_id,
                    reminder["title"],
                    reminder["reminder_type"],
                    reminder["interval_km"],
                    reminder["interval_days"],
                ),
            )


def calculate_cost_per_km(bike_id):
    fuel_stats_fn = None
    with get_db() as conn:
        fuel_total = conn.execute(
            "SELECT COALESCE(SUM(cost),0) AS t FROM fuel_entries WHERE bike_id=?",
            (bike_id,),
        ).fetchone()["t"]
        maint_total = conn.execute(
            "SELECT COALESCE(SUM(cost),0) AS t FROM maintenance_entries WHERE bike_id=?",
            (bike_id,),
        ).fetchone()["t"]
        first_odo = conn.execute(
            "SELECT MIN(odometer) AS o FROM fuel_entries WHERE bike_id=?",
            (bike_id,),
        ).fetchone()["o"]
        last_odo = conn.execute(
            "SELECT MAX(odometer) AS o FROM fuel_entries WHERE bike_id=?",
            (bike_id,),
        ).fetchone()["o"]

    distance = (last_odo or 0) - (first_odo or 0)
    if distance <= 0:
        return None
    return (fuel_total + maint_total) / distance


def month_over_month_spend(bike_id):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT substr(entry_date,1,7) AS month, SUM(cost) AS total
            FROM fuel_entries WHERE bike_id = ?
            GROUP BY month ORDER BY month DESC LIMIT 2
            """,
            (bike_id,),
        ).fetchall()
    if len(rows) < 2:
        return None
    current, previous = rows[0]["total"], rows[1]["total"]
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 1)
