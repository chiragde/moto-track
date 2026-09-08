import json
import os
from datetime import date, datetime, timedelta
from functools import wraps

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from jinja2 import pass_context
from werkzeug.security import check_password_hash, generate_password_hash

from constants import (
    BIKE_CATALOG,
    CARE_TASK_ICONS,
    CARE_TASK_TYPES,
    CURRENCIES,
    DEFAULT_REMINDERS,
    MAINTENANCE_TIPS,
    TRIP_TAGS,
    UNIT_PRESETS,
)
from database import get_db, get_db_path, init_db, is_test_mode
from features import (
    calculate_cost_per_km,
    month_over_month_spend,
    register_features,
    seed_reminders_for_bike,
)
from receipt_parser import parse_receipt_image, parsing_available
from settings_helpers import (
    DEFAULT_SETTINGS,
    ensure_user_settings,
    get_user_settings,
    settings_for_template,
)
from uploads_util import (
    finalize_receipt_path,
    receipt_belongs_to_user,
    resolve_receipt_path,
    save_bike_photo,
    save_receipt_image,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-change-me-in-production")

if os.environ.get("FLASK_ENV") == "production" or os.environ.get("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def came_from_more():
    return request.args.get("from") == "more" or request.form.get("from") == "more"


def redirect_preserving_from(endpoint, **kwargs):
    if came_from_more():
        kwargs["from"] = "more"
    return redirect(url_for(endpoint, **kwargs))


def handle_receipt_submission(user_id):
    receipt_path = request.form.get("receipt_path", "").strip()
    if receipt_path and receipt_belongs_to_user(receipt_path, user_id):
        return finalize_receipt_path(receipt_path)

    uploaded = request.files.get("receipt_image")
    if uploaded and uploaded.filename:
        try:
            return save_receipt_image(user_id, uploaded, folder="receipts")
        except ValueError as exc:
            flash(str(exc), "error")
    return None


def get_user_bikes(user_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM bikes WHERE user_id = ? ORDER BY name",
            (user_id,),
        ).fetchall()


def get_active_bike_id(user_id):
    bike_id = session.get("active_bike_id")
    bikes = get_user_bikes(user_id)
    if not bikes:
        return None
    bike_ids = {bike["id"] for bike in bikes}
    if bike_id in bike_ids:
        return bike_id
    return bikes[0]["id"]


def get_bike_or_404(user_id, bike_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM bikes WHERE id = ? AND user_id = ?",
            (bike_id, user_id),
        ).fetchone()


def ensure_reminders_for_bike(bike_id):
    with get_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM reminders WHERE bike_id = ?",
            (bike_id,),
        ).fetchone()["count"]
    if count == 0:
        seed_default_reminders(bike_id)


def seed_default_reminders(bike_id, make=None, model=None):
    seed_reminders_for_bike(bike_id, make, model)


@app.context_processor
def inject_globals():
    prefs = settings_for_template(DEFAULT_SETTINGS)
    nav_bikes = []
    nav_active_bike = None
    if "user_id" in session:
        with get_db() as conn:
            prefs = settings_for_template(get_user_settings(conn, session["user_id"]))
        nav_bikes = get_user_bikes(session["user_id"])
        if nav_bikes:
            active_id = get_active_bike_id(session["user_id"])
            nav_active_bike = get_bike_or_404(session["user_id"], active_id)
    return {
        "user_settings": prefs,
        "trip_tags": TRIP_TAGS,
        "currencies": CURRENCIES,
        "unit_presets": UNIT_PRESETS,
        "care_task_types": CARE_TASK_TYPES,
        "care_task_icons": CARE_TASK_ICONS,
        "nav_bikes": nav_bikes,
        "nav_active_bike": nav_active_bike,
        "app_test_mode": is_test_mode(),
    }


@app.template_filter("money")
@pass_context
def money_filter(context, amount):
    if amount is None:
        return "—"
    prefs = context.get("user_settings") or settings_for_template(DEFAULT_SETTINGS)
    return f"{prefs['currency_symbol']}{amount:,.0f}"


def get_latest_odometer(bike_id):
    with get_db() as conn:
        latest = conn.execute(
            """
            SELECT reading, reading_date FROM odometer_readings
            WHERE bike_id = ?
            ORDER BY reading_date DESC, reading DESC
            LIMIT 1
            """,
            (bike_id,),
        ).fetchone()

        if latest:
            return dict(latest)

        fuel = conn.execute(
            """
            SELECT odometer AS reading, entry_date AS reading_date
            FROM fuel_entries
            WHERE bike_id = ?
            ORDER BY entry_date DESC, odometer DESC
            LIMIT 1
            """,
            (bike_id,),
        ).fetchone()

        if fuel:
            return dict(fuel)

        care = conn.execute(
            """
            SELECT odometer AS reading, entry_date AS reading_date
            FROM care_entries
            WHERE bike_id = ?
            ORDER BY entry_date DESC, odometer DESC
            LIMIT 1
            """,
            (bike_id,),
        ).fetchone()

        return dict(care) if care else None


def calculate_fuel_stats(bike_id):
    with get_db() as conn:
        entries = conn.execute(
            """
            SELECT * FROM fuel_entries
            WHERE bike_id = ?
            ORDER BY entry_date ASC, odometer ASC
            """,
            (bike_id,),
        ).fetchall()

    if not entries:
        return {
            "total_liters": 0,
            "total_cost": 0,
            "avg_efficiency": None,
            "entries": [],
            "efficiency_series": [],
            "monthly_spend": [],
        }

    total_liters = sum(entry["liters"] for entry in entries)
    total_cost = sum(entry["cost"] for entry in entries)

    efficiencies = []
    efficiency_series = []
    for i in range(1, len(entries)):
        prev = entries[i - 1]
        curr = entries[i]
        distance = curr["odometer"] - prev["odometer"]
        if distance > 0 and curr["liters"] > 0:
            eff = distance / curr["liters"]
            efficiencies.append(eff)
            efficiency_series.append(
                {
                    "date": curr["entry_date"],
                    "efficiency": round(eff, 1),
                    "odometer": curr["odometer"],
                }
            )

    monthly = {}
    for entry in entries:
        month_key = entry["entry_date"][:7]
        monthly[month_key] = monthly.get(month_key, 0) + entry["cost"]

    monthly_spend = [
        {"month": month, "cost": round(cost, 0)}
        for month, cost in sorted(monthly.items())
    ]

    avg_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else None

    return {
        "total_liters": total_liters,
        "total_cost": total_cost,
        "avg_efficiency": avg_efficiency,
        "entries": list(reversed(entries)),
        "efficiency_series": efficiency_series,
        "monthly_spend": monthly_spend,
    }


def get_reminders_with_status(bike_id, current_odo=None):
    with get_db() as conn:
        reminders = conn.execute(
            """
            SELECT * FROM reminders
            WHERE bike_id = ? AND is_active = 1
            ORDER BY title
            """,
            (bike_id,),
        ).fetchall()

    today = date.today()
    results = []

    for reminder in reminders:
        status = "ok"
        detail = None
        due_in_km = None
        due_in_days = None

        if reminder["interval_km"] and reminder["last_done_odometer"] is not None:
            next_km = reminder["last_done_odometer"] + reminder["interval_km"]
            if current_odo is not None:
                due_in_km = next_km - current_odo
                if due_in_km <= 0:
                    status = "overdue"
                    detail = f"Due {abs(due_in_km):.0f} km ago"
                elif due_in_km <= reminder["interval_km"] * 0.1:
                    status = "soon"
                    detail = f"Due in {due_in_km:.0f} km"

        if reminder["interval_days"] and reminder["last_done_date"]:
            last_done = datetime.strptime(reminder["last_done_date"], "%Y-%m-%d").date()
            next_date = last_done + timedelta(days=reminder["interval_days"])
            due_in_days = (next_date - today).days
            if due_in_days <= 0:
                status = "overdue"
                detail = detail or f"Overdue by {abs(due_in_days)} days"
            elif due_in_days <= 7:
                if status != "overdue":
                    status = "soon"
                detail = detail or f"Due in {due_in_days} days"

        if reminder["last_done_odometer"] is None and reminder["last_done_date"] is None:
            status = "setup"
            detail = "Mark as done to start tracking"

        results.append(
            {
                "reminder": reminder,
                "status": status,
                "detail": detail,
                "due_in_km": due_in_km,
                "due_in_days": due_in_days,
            }
        )

    results.sort(
        key=lambda item: (
            0 if item["status"] == "overdue" else 1 if item["status"] == "soon" else 2,
            item["due_in_km"] if item["due_in_km"] is not None else 99999,
        )
    )
    return results


def get_tip_of_day():
    day_index = date.today().toordinal() % len(MAINTENANCE_TIPS)
    return MAINTENANCE_TIPS[day_index]


def build_stats_payload(bike_id):
    fuel_stats = calculate_fuel_stats(bike_id)

    with get_db() as conn:
        maintenance = conn.execute(
            """
            SELECT entry_type, SUM(cost) AS total, COUNT(*) AS count
            FROM maintenance_entries
            WHERE bike_id = ?
            GROUP BY entry_type
            """,
            (bike_id,),
        ).fetchall()

        care_count = conn.execute(
            "SELECT COUNT(*) AS count FROM care_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchone()["count"]

        total_maintenance = conn.execute(
            "SELECT COALESCE(SUM(cost), 0) AS total FROM maintenance_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchone()["total"]

    maintenance_breakdown = [
        {"type": row["entry_type"], "total": row["total"], "count": row["count"]}
        for row in maintenance
    ]

    return {
        "fuel": fuel_stats,
        "maintenance_breakdown": maintenance_breakdown,
        "total_maintenance": total_maintenance,
        "total_spend": fuel_stats["total_cost"] + total_maintenance,
        "care_count": care_count,
        "cost_per_km": calculate_cost_per_km(bike_id),
        "month_change": month_over_month_spend(bike_id),
    }


@app.before_request
def load_user():
    g.user = None
    if "user_id" in session:
        with get_db() as conn:
            g.user = conn.execute(
                "SELECT id, username FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            flash("Username and password are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        else:
            try:
                with get_db() as conn:
                    cursor = conn.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, generate_password_hash(password)),
                    )
                    user_id = cursor.lastrowid
                    ensure_user_settings(conn, user_id)
                    conn.commit()
                flash("Account created. Please sign in.", "success")
                return redirect(url_for("login"))
            except Exception as exc:
                import sqlite3

                if isinstance(exc, sqlite3.IntegrityError):
                    flash("Username already exists.", "error")
                else:
                    app.logger.exception("Registration failed")
                    flash("Could not create account. Please try again.", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    bikes = get_user_bikes(user_id)

    if not bikes:
        return render_template(
            "dashboard.html",
            bikes=[],
            stats=None,
            bike=None,
            reminders=[],
            tip=get_tip_of_day(),
        )

    bike_id = get_active_bike_id(user_id)
    bike = get_bike_or_404(user_id, bike_id)
    ensure_reminders_for_bike(bike_id)
    fuel_stats = calculate_fuel_stats(bike_id)
    latest_odo = get_latest_odometer(bike_id)
    current_odo = latest_odo["reading"] if latest_odo else None

    with get_db() as conn:
        maintenance_total = conn.execute(
            "SELECT COALESCE(SUM(cost), 0) AS total FROM maintenance_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchone()["total"]

        recent_maintenance = conn.execute(
            """
            SELECT * FROM maintenance_entries
            WHERE bike_id = ?
            ORDER BY entry_date DESC
            LIMIT 3
            """,
            (bike_id,),
        ).fetchall()

        recent_care = conn.execute(
            """
            SELECT * FROM care_entries
            WHERE bike_id = ?
            ORDER BY entry_date DESC
            LIMIT 3
            """,
            (bike_id,),
        ).fetchall()

    reminders = get_reminders_with_status(bike_id, current_odo)
    urgent = [r for r in reminders if r["status"] in ("overdue", "soon")]
    next_milestone = urgent[0] if urgent else None

    stats = {
        "fuel_cost": fuel_stats["total_cost"],
        "maintenance_cost": maintenance_total,
        "avg_efficiency": fuel_stats["avg_efficiency"],
        "latest_odo": latest_odo,
        "recent_fuel": fuel_stats["entries"][:3],
        "recent_maintenance": recent_maintenance,
        "recent_care": recent_care,
        "cost_per_km": calculate_cost_per_km(bike_id),
    }

    return render_template(
        "dashboard.html",
        bikes=bikes,
        bike=bike,
        stats=stats,
        reminders=reminders[:5],
        next_milestone=next_milestone,
        tip=get_tip_of_day(),
        care_task_types=CARE_TASK_TYPES,
        care_task_icons=CARE_TASK_ICONS,
    )


def get_bikes_with_odo(user_id):
    bikes = get_user_bikes(user_id)
    enriched = []
    for bike in bikes:
        row = dict(bike)
        row["latest_odo"] = get_latest_odometer(bike["id"])
        enriched.append(row)
    return enriched


def get_timeline_entries(bike_id):
    items = []

    with get_db() as conn:
        fuel_rows = conn.execute(
            "SELECT * FROM fuel_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchall()
        for row in fuel_rows:
            tag_label = TRIP_TAGS.get(row["tag"] or "", "") if row["tag"] else ""
            subtitle = f'{row["liters"]:.1f} L'
            if tag_label and tag_label != "No tag":
                subtitle += f" · {tag_label}"
            items.append(
                {
                    "kind": "fuel",
                    "id": row["id"],
                    "date": row["entry_date"],
                    "title": "Fuel fill-up",
                    "subtitle": subtitle,
                    "odometer": row["odometer"],
                    "cost": row["cost"],
                    "notes": row["notes"],
                    "provider": None,
                    "icon": "fuel",
                }
            )

        service_rows = conn.execute(
            "SELECT * FROM maintenance_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchall()
        for row in service_rows:
            items.append(
                {
                    "kind": "service",
                    "id": row["id"],
                    "date": row["entry_date"],
                    "title": row["description"] or row["entry_type"].replace("_", " ").title(),
                    "subtitle": row["entry_type"].replace("_", " ").title(),
                    "odometer": row["odometer"],
                    "cost": row["cost"],
                    "notes": row["notes"],
                    "provider": "Service",
                    "icon": "settings-2",
                }
            )

        care_rows = conn.execute(
            "SELECT * FROM care_entries WHERE bike_id = ?",
            (bike_id,),
        ).fetchall()
        for row in care_rows:
            task_label = CARE_TASK_TYPES.get(row["task_type"], row["task_type"])
            items.append(
                {
                    "kind": "care",
                    "id": row["id"],
                    "date": row["entry_date"],
                    "title": row["description"] or task_label,
                    "subtitle": task_label,
                    "odometer": row["odometer"],
                    "cost": row["cost"] if row["cost"] else None,
                    "notes": row["notes"],
                    "provider": "DIY",
                    "icon": CARE_TASK_ICONS.get(row["task_type"], "wrench"),
                }
            )

        odo_rows = conn.execute(
            "SELECT * FROM odometer_readings WHERE bike_id = ?",
            (bike_id,),
        ).fetchall()
        for row in odo_rows:
            items.append(
                {
                    "kind": "odometer",
                    "id": row["id"],
                    "date": row["reading_date"],
                    "title": "Odometer reading",
                    "subtitle": f'{row["reading"]:,.0f} km logged',
                    "odometer": row["reading"],
                    "cost": None,
                    "notes": row["notes"],
                    "provider": "Snapshot",
                    "icon": "gauge",
                }
            )

    items.sort(key=lambda item: (item["date"], item["id"]), reverse=True)

    grouped = []
    month_map = {}
    for item in items:
        month_key = item["date"][:7]
        if month_key not in month_map:
            try:
                year, month = month_key.split("-")
                label = date(int(year), int(month), 1).strftime("%B %Y")
            except ValueError:
                label = month_key
            month_map[month_key] = {"key": month_key, "label": label, "entries": []}
            grouped.append(month_map[month_key])
        month_map[month_key]["entries"].append(item)

    return grouped


def attach_timeline_urls(months):
    url_map = {
        "fuel": ("edit_fuel", "delete_fuel"),
        "service": ("edit_maintenance", "delete_maintenance"),
        "care": ("edit_care", "delete_care"),
        "odometer": ("edit_odometer", "delete_odometer"),
    }
    for month in months:
        for item in month["entries"]:
            edit_name, delete_name = url_map[item["kind"]]
            item["edit_url"] = url_for(edit_name, entry_id=item["id"])
            item["delete_url"] = url_for(delete_name, entry_id=item["id"])
    return months


@app.route("/timeline")
@login_required
def timeline():
    user_id = session["user_id"]
    bikes = get_user_bikes(user_id)
    if not bikes:
        flash("Add a bike in Garage first.", "error")
        return redirect(url_for("garage"))

    bike_id = get_active_bike_id(user_id)
    bike = get_bike_or_404(user_id, bike_id)
    months = attach_timeline_urls(get_timeline_entries(bike_id))

    return render_template(
        "timeline.html",
        bikes=bikes,
        bike=bike,
        months=months,
    )


@app.route("/garage", methods=["GET", "POST"])
@app.route("/bikes", methods=["GET", "POST"])
@login_required
def garage():
    user_id = session["user_id"]

    if request.method == "POST":
        action = request.form.get("action", "add_bike")

        if action == "upload_photo":
            bike_id = request.form.get("bike_id", type=int)
            bike = get_bike_or_404(user_id, bike_id) if bike_id else None
            photo = request.files.get("photo")
            if not bike:
                flash("Bike not found.", "error")
            elif not photo or not photo.filename:
                flash("Choose a photo to upload.", "error")
            else:
                try:
                    photo_path = save_bike_photo(user_id, photo)
                    with get_db() as conn:
                        conn.execute(
                            "UPDATE bikes SET photo = ? WHERE id = ? AND user_id = ?",
                            (photo_path, bike_id, user_id),
                        )
                    flash("Bike photo updated.", "success")
                except ValueError as exc:
                    flash(str(exc), "error")
            return redirect(url_for("garage"))

        name = request.form.get("name", "").strip()
        make = request.form.get("make", "").strip()
        model = request.form.get("model", "").strip()
        make_custom = request.form.get("make_custom", "").strip()
        model_custom = request.form.get("model_custom", "").strip()
        year = request.form.get("year", "").strip()
        initial_odometer = request.form.get("initial_odometer", "").strip()
        photo = request.files.get("photo")

        if make == "Other":
            make = make_custom
        if model == "Custom / Other":
            model = model_custom

        if not name:
            flash("Nickname is required.", "error")
        else:
            try:
                odometer_val = float(initial_odometer) if initial_odometer else None
                if odometer_val is not None and odometer_val < 0:
                    raise ValueError
            except ValueError:
                flash("Enter a valid odometer reading.", "error")
            else:
                photo_path = None
                if photo and photo.filename:
                    try:
                        photo_path = save_bike_photo(user_id, photo)
                    except ValueError as exc:
                        flash(str(exc), "error")
                        return redirect(url_for("garage"))

                with get_db() as conn:
                    cursor = conn.execute(
                        """
                        INSERT INTO bikes (user_id, name, make, model, year, photo)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            name,
                            make or None,
                            model or None,
                            int(year) if year else None,
                            photo_path,
                        ),
                    )
                    bike_id = cursor.lastrowid
                    if odometer_val is not None:
                        conn.execute(
                            """
                            INSERT INTO odometer_readings (bike_id, reading_date, reading, notes)
                            VALUES (?, ?, ?, ?)
                            """,
                            (bike_id, date.today().isoformat(), odometer_val, "Initial reading"),
                        )
                seed_default_reminders(bike_id, make, model)
                session["active_bike_id"] = bike_id
                flash("Vehicle added to your garage.", "success")
                return redirect(url_for("garage"))

    bikes_list = get_bikes_with_odo(user_id)
    active_id = get_active_bike_id(user_id) if bikes_list else None
    active_bike = get_bike_or_404(user_id, active_id) if active_id else None
    return render_template(
        "garage.html",
        bikes=bikes_list,
        bike=active_bike,
        bike_catalog=BIKE_CATALOG,
    )


@app.route("/bikes/select/<int:bike_id>")
@login_required
def select_bike(bike_id):
    bike = get_bike_or_404(session["user_id"], bike_id)
    if bike:
        session["active_bike_id"] = bike_id
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/api/parse-receipt", methods=["POST"])
@login_required
def api_parse_receipt():
    entry_type = request.form.get("type", "fuel")
    if entry_type not in ("fuel", "maintenance"):
        return jsonify({"ok": False, "error": "Invalid receipt type."}), 400

    image = request.files.get("image")
    if not image or not image.filename:
        return jsonify({"ok": False, "error": "Choose an image to upload."}), 400

    user_id = session["user_id"]
    try:
        receipt_path = save_receipt_image(user_id, image, folder="pending")
        full_path = resolve_receipt_path(receipt_path)

        if not parsing_available():
            return jsonify(
                {
                    "ok": True,
                    "data": {},
                    "receipt_path": receipt_path,
                    "message": "Image attached. Set OPENAI_API_KEY to auto-fill, or enter details manually.",
                    "manual_only": True,
                }
            )

        try:
            parsed = parse_receipt_image(full_path, entry_type)
            return jsonify(
                {
                    "ok": True,
                    "data": parsed,
                    "receipt_path": receipt_path,
                    "message": "Receipt scanned. Review the fields before saving.",
                }
            )
        except Exception:
            return jsonify(
                {
                    "ok": True,
                    "data": {},
                    "receipt_path": receipt_path,
                    "message": "Image attached but could not be read. Enter details manually.",
                    "manual_only": True,
                }
            )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/receipts/<path:relative_path>")
@login_required
def serve_receipt(relative_path):
    if not receipt_belongs_to_user(relative_path, session["user_id"]):
        abort(404)
    path = resolve_receipt_path(relative_path)
    if not path:
        abort(404)
    return send_file(path)


@app.route("/fuel", methods=["GET", "POST"])
@login_required
def fuel():
    user_id = session["user_id"]
    bikes = get_user_bikes(user_id)
    if not bikes:
        flash("Add a bike first.", "error")
        return redirect(url_for("garage"))

    bike_id = get_active_bike_id(user_id)
    bike = get_bike_or_404(user_id, bike_id)

    if request.method == "POST":
        entry_date = request.form.get("entry_date", "")
        liters = request.form.get("liters", "")
        cost = request.form.get("cost", "")
        odometer = request.form.get("odometer", "")
        notes = request.form.get("notes", "").strip()
        tag = request.form.get("tag", "").strip() or None

        try:
            liters_val = float(liters)
            cost_val = float(cost)
            odometer_val = float(odometer)
            if liters_val <= 0 or cost_val < 0 or odometer_val < 0:
                raise ValueError
        except ValueError:
            flash("Enter valid fuel values.", "error")
        else:
            receipt_image = handle_receipt_submission(user_id)
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO fuel_entries
                    (bike_id, entry_date, liters, cost, odometer, notes, tag, receipt_image)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bike_id,
                        entry_date,
                        liters_val,
                        cost_val,
                        odometer_val,
                        notes or None,
                        tag,
                        receipt_image,
                    ),
                )
            flash("Fuel entry saved.", "success")
            return redirect(url_for("fuel"))

    fuel_stats = calculate_fuel_stats(bike_id)
    latest_odo = get_latest_odometer(bike_id)
    return render_template(
        "fuel.html",
        bikes=bikes,
        bike=bike,
        entries=fuel_stats["entries"],
        stats=fuel_stats,
        latest_odo=latest_odo,
        receipt_scanning_enabled=parsing_available(),
    )


@app.route("/maintenance", methods=["GET", "POST"])
@login_required
def maintenance():
    user_id = session["user_id"]
    bikes = get_user_bikes(user_id)
    if not bikes:
        flash("Add a bike first.", "error")
        return redirect(url_for("garage"))

    bike_id = get_active_bike_id(user_id)
    bike = get_bike_or_404(user_id, bike_id)

    if request.method == "POST":
        entry_date = request.form.get("entry_date", "")
        entry_type = request.form.get("entry_type", "service")
        description = request.form.get("description", "").strip()
        cost = request.form.get("cost", "")
        odometer = request.form.get("odometer", "").strip()
        notes = request.form.get("notes", "").strip()

        error = None
        try:
            cost_val = float(cost)
            odometer_val = float(odometer) if odometer else None
            if cost_val < 0 or (odometer_val is not None and odometer_val < 0):
                raise ValueError
        except ValueError:
            error = "Enter valid maintenance values."

        if not error and not description:
            error = "Description is required."

        if error:
            flash(error, "error")
        else:
            receipt_image = handle_receipt_submission(user_id)
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO maintenance_entries
                    (bike_id, entry_date, entry_type, description, cost, odometer, notes, receipt_image)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bike_id,
                        entry_date,
                        entry_type,
                        description,
                        cost_val,
                        odometer_val,
                        notes or None,
                        receipt_image,
                    ),
                )
            flash("Maintenance entry saved.", "success")
            return redirect(url_for("maintenance"))

    with get_db() as conn:
        entries = conn.execute(
            """
            SELECT * FROM maintenance_entries
            WHERE bike_id = ?
            ORDER BY entry_date DESC
            """,
            (bike_id,),
        ).fetchall()
        total_cost = sum(entry["cost"] for entry in entries)

    return render_template(
        "maintenance.html",
        bikes=bikes,
        bike=bike,
        entries=entries,
        total_cost=total_cost,
        receipt_scanning_enabled=parsing_available(),
    )


@app.route("/care", methods=["GET", "POST"])
@login_required
def care():
    user_id = session["user_id"]
    bikes = get_user_bikes(user_id)
    if not bikes:
        flash("Add a bike first.", "error")
        return redirect(url_for("garage"))

    bike_id = get_active_bike_id(user_id)
    bike = get_bike_or_404(user_id, bike_id)
    ensure_reminders_for_bike(bike_id)
    latest_odo = get_latest_odometer(bike_id)
    current_odo = latest_odo["reading"] if latest_odo else None

    if request.method == "POST":
        action = request.form.get("action", "add_entry")

        if action == "add_entry":
            entry_date = request.form.get("entry_date", "")
            task_type = request.form.get("task_type", "custom")
            description = request.form.get("description", "").strip()
            odometer = request.form.get("odometer", "")
            cost = request.form.get("cost", "0").strip()
            notes = request.form.get("notes", "").strip()

            if not description and task_type != "custom":
                description = CARE_TASK_TYPES.get(task_type, task_type)

            error = None
            try:
                odometer_val = float(odometer)
                cost_val = float(cost) if cost else 0
                if odometer_val < 0 or cost_val < 0:
                    raise ValueError
            except ValueError:
                error = "Enter valid odometer and cost values."

            if not error and not description:
                error = "Description is required."

            if error:
                flash(error, "error")
            else:
                with get_db() as conn:
                    conn.execute(
                        """
                        INSERT INTO care_entries
                        (bike_id, entry_date, task_type, description, odometer, cost, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            bike_id,
                            entry_date,
                            task_type,
                            description,
                            odometer_val,
                            cost_val,
                            notes or None,
                        ),
                    )
                    matching = conn.execute(
                        """
                        SELECT id FROM reminders
                        WHERE bike_id = ? AND reminder_type = ? AND is_active = 1
                        """,
                        (bike_id, task_type),
                    ).fetchone()
                    if matching:
                        conn.execute(
                            """
                            UPDATE reminders
                            SET last_done_date = ?, last_done_odometer = ?
                            WHERE id = ?
                            """,
                            (entry_date, odometer_val, matching["id"]),
                        )
                flash("Care entry logged.", "success")
                return redirect_preserving_from("care")

        elif action == "add_reminder":
            title = request.form.get("title", "").strip()
            reminder_type = request.form.get("reminder_type", "custom")
            interval_km = request.form.get("interval_km", "").strip()
            interval_days = request.form.get("interval_days", "").strip()

            if not title:
                flash("Reminder title is required.", "error")
            else:
                with get_db() as conn:
                    conn.execute(
                        """
                        INSERT INTO reminders
                        (bike_id, title, reminder_type, interval_km, interval_days)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            bike_id,
                            title,
                            reminder_type,
                            int(interval_km) if interval_km else None,
                            int(interval_days) if interval_days else None,
                        ),
                    )
                flash("Reminder added.", "success")
                return redirect_preserving_from("care")

        elif action == "mark_done":
            reminder_id = request.form.get("reminder_id")
            done_date = request.form.get("done_date", date.today().isoformat())
            done_odo = request.form.get("done_odometer", "").strip()

            try:
                done_odo_val = float(done_odo) if done_odo else current_odo
                if done_odo_val is None:
                    raise ValueError
            except (TypeError, ValueError):
                flash("Enter odometer reading to mark reminder done.", "error")
            else:
                with get_db() as conn:
                    conn.execute(
                        """
                        UPDATE reminders
                        SET last_done_date = ?, last_done_odometer = ?
                        WHERE id = ? AND bike_id = ?
                        """,
                        (done_date, done_odo_val, reminder_id, bike_id),
                    )
                flash("Reminder marked as done.", "success")
                return redirect_preserving_from("care")

    with get_db() as conn:
        entries = conn.execute(
            """
            SELECT * FROM care_entries
            WHERE bike_id = ?
            ORDER BY entry_date DESC, odometer DESC
            """,
            (bike_id,),
        ).fetchall()

    reminders = get_reminders_with_status(bike_id, current_odo)

    return render_template(
        "care.html",
        bikes=bikes,
        bike=bike,
        entries=entries,
        reminders=reminders,
        care_task_types=CARE_TASK_TYPES,
        latest_odo=latest_odo,
    )


@app.route("/stats")
@login_required
def stats():
    user_id = session["user_id"]
    bikes = get_user_bikes(user_id)
    if not bikes:
        flash("Add a bike first.", "error")
        return redirect(url_for("garage"))

    bike_id = get_active_bike_id(user_id)
    bike = get_bike_or_404(user_id, bike_id)
    payload = build_stats_payload(bike_id)

    return render_template(
        "stats.html",
        bikes=bikes,
        bike=bike,
        stats=payload,
        chart_data=json.dumps(
            {
                "efficiency": payload["fuel"]["efficiency_series"],
                "monthly_spend": payload["fuel"]["monthly_spend"],
                "maintenance": payload["maintenance_breakdown"],
            }
        ),
    )


@app.route("/more")
@login_required
def more():
    return render_template("more.html")


@app.route("/odometer", methods=["GET", "POST"])
@login_required
def odometer():
    user_id = session["user_id"]
    bikes = get_user_bikes(user_id)
    if not bikes:
        flash("Add a bike first.", "error")
        return redirect(url_for("garage"))

    bike_id = get_active_bike_id(user_id)
    bike = get_bike_or_404(user_id, bike_id)

    if request.method == "POST":
        reading_date = request.form.get("reading_date", "")
        reading = request.form.get("reading", "")
        notes = request.form.get("notes", "").strip()

        try:
            reading_val = float(reading)
            if reading_val < 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid odometer reading.", "error")
        else:
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO odometer_readings (bike_id, reading_date, reading, notes)
                    VALUES (?, ?, ?, ?)
                    """,
                    (bike_id, reading_date, reading_val, notes or None),
                )
            flash("Odometer reading saved.", "success")
            return redirect(url_for("odometer"))

    with get_db() as conn:
        readings = conn.execute(
            """
            SELECT * FROM odometer_readings
            WHERE bike_id = ?
            ORDER BY reading_date DESC, reading DESC
            """,
            (bike_id,),
        ).fetchall()

    return render_template(
        "odometer.html",
        bikes=bikes,
        bike=bike,
        readings=readings,
    )


init_db()
if is_test_mode():
    app.logger.warning("TEST MODE: using database at %s", get_db_path())

register_features(
    app,
    {
        "login_required": login_required,
        "get_user_bikes": get_user_bikes,
        "get_active_bike_id": get_active_bike_id,
        "get_bike_or_404": get_bike_or_404,
        "get_reminders_with_status": get_reminders_with_status,
        "get_latest_odometer": get_latest_odometer,
        "handle_receipt_submission": handle_receipt_submission,
        "parsing_available": parsing_available,
        "redirect_preserving_from": redirect_preserving_from,
    },
)

if __name__ == "__main__":
    import socket

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"

    def lan_ip():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except OSError:
            return None

    print(f"\n  On this computer:  http://localhost:{port}")
    network_ip = lan_ip()
    if network_ip:
        print(f"  On other devices:  http://{network_ip}:{port}")
        print("  (Use your Ethernet/Wi-Fi IPv4 address if that link fails.)\n")
    else:
        print("  (Could not detect LAN IP — run ipconfig and use your IPv4 address.)\n")

    app.run(debug=debug, host="0.0.0.0", port=port)
