from constants import CURRENCIES, UNIT_PRESETS


DEFAULT_SETTINGS = {
    "currency": "INR",
    "unit_system": "metric",
    "theme": "system",
    "email": None,
    "notifications_enabled": 0,
}


def get_user_settings(conn, user_id):
    row = conn.execute(
        "SELECT * FROM user_settings WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if not row:
        return dict(DEFAULT_SETTINGS)
    return {
        "currency": row["currency"],
        "unit_system": row["unit_system"],
        "theme": row["theme"],
        "email": row["email"],
        "notifications_enabled": row["notifications_enabled"],
    }


def ensure_user_settings(conn, user_id):
    conn.execute(
        """
        INSERT OR IGNORE INTO user_settings (user_id)
        VALUES (?)
        """,
        (user_id,),
    )


def save_user_settings(conn, user_id, data):
    ensure_user_settings(conn, user_id)
    conn.execute(
        """
        UPDATE user_settings
        SET currency = ?, unit_system = ?, theme = ?, email = ?,
            notifications_enabled = ?
        WHERE user_id = ?
        """,
        (
            data["currency"],
            data["unit_system"],
            data["theme"],
            data.get("email") or None,
            1 if data.get("notifications_enabled") else 0,
            user_id,
        ),
    )


def settings_for_template(settings):
    currency = CURRENCIES.get(settings["currency"], CURRENCIES["INR"])
    units = UNIT_PRESETS.get(settings["unit_system"], UNIT_PRESETS["metric"])
    return {
        **settings,
        "currency_symbol": currency["symbol"],
        "distance_unit": units["distance_unit"],
        "volume_unit": units["volume_unit"],
        "efficiency_label": units["efficiency_label"],
    }


def format_money(amount, symbol):
    if amount is None:
        return "—"
    return f"{symbol}{amount:,.0f}"


def format_money_precise(amount, symbol):
    if amount is None:
        return "—"
    return f"{symbol}{amount:,.2f}"


def km_to_display(km, unit_system):
    if km is None:
        return None
    if unit_system == "imperial":
        return km * 0.621371
    return km


def liters_to_display(liters, unit_system):
    if liters is None:
        return None
    if unit_system == "imperial":
        return liters * 0.264172
    return liters


def efficiency_to_display(km_per_liter, unit_system):
    if km_per_liter is None:
        return None
    if unit_system == "imperial":
        return km_per_liter * 2.35215
    return km_per_liter


def distance_label(value, unit_system):
    if value is None:
        return "—"
    unit = UNIT_PRESETS[unit_system]["distance_unit"]
    return f"{value:,.0f} {unit}"


def volume_label(value, unit_system):
    if value is None:
        return "—"
    unit = UNIT_PRESETS[unit_system]["volume_unit"]
    return f"{value:,.1f} {unit}"


def efficiency_label(value, unit_system):
    if value is None:
        return "—"
    label = UNIT_PRESETS[unit_system]["efficiency_label"]
    return f"{value:.1f} {label}"
