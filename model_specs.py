"""
Model-specific motorcycle specs: service intervals, tire pressure, fluids.
Sourced from manufacturer manuals and public maintenance guides.
Use as defaults when seeding reminders and parts — always verify against your manual.
"""

from __future__ import annotations

# make -> model -> specs
MODEL_SPECS: dict[str, dict[str, dict]] = {
    "Honda": {
        "CB350": {
            "oil_km": 6000,
            "oil_months": 12,
            "chain_lube_km": 1000,
            "chain_service_km": 5000,
            "valve_check_km": 24000,
            "tire_front_psi": 29,
            "tire_rear_psi": 33,
            "tire_rear_psi_loaded": 36,
            "oil_type": "10W-30 JASO MA",
            "tank_liters": 15.0,
            "tire_front": "100/90-19",
            "tire_rear": "130/70-18",
        },
        "Activa": {
            "oil_km": 6000,
            "oil_months": 6,
            "chain_lube_km": 1000,
            "tire_front_psi": 22,
            "tire_rear_psi": 29,
            "oil_type": "10W-30",
            "tank_liters": 5.3,
        },
        "Unicorn": {
            "oil_km": 6000,
            "chain_lube_km": 500,
            "tire_front_psi": 29,
            "tire_rear_psi": 33,
            "oil_type": "10W-30",
            "tank_liters": 13.0,
        },
        "CB500X": {
            "oil_km": 12000,
            "chain_lube_km": 1000,
            "valve_check_km": 24000,
            "tire_front_psi": 36,
            "tire_rear_psi": 41,
            "oil_type": "10W-30",
            "tank_liters": 17.1,
        },
    },
    "Yamaha": {
        "R15 V4": {
            "oil_km": 10000,
            "chain_lube_km": 500,
            "tire_front_psi": 29,
            "tire_rear_psi": 36,
            "oil_type": "10W-40",
            "tank_liters": 11.0,
        },
        "MT-15": {
            "oil_km": 10000,
            "chain_lube_km": 500,
            "tire_front_psi": 29,
            "tire_rear_psi": 33,
            "oil_type": "10W-40",
            "tank_liters": 10.0,
        },
        "FZ-S": {
            "oil_km": 10000,
            "chain_lube_km": 500,
            "tire_front_psi": 28,
            "tire_rear_psi": 32,
            "oil_type": "20W-40",
            "tank_liters": 12.0,
        },
    },
    "Royal Enfield": {
        "Classic 350": {
            "oil_km": 10000,
            "oil_months": 12,
            "chain_lube_km": 1000,
            "chain_service_km": 5000,
            "valve_check_km": 10000,
            "tire_front_psi": 32,
            "tire_rear_psi": 32,
            "oil_type": "15W-50 semi-synthetic",
            "tank_liters": 13.0,
            "tire_front": "100/90-19",
            "tire_rear": "120/80-18",
        },
        "Meteor 350": {
            "oil_km": 10000,
            "chain_lube_km": 1000,
            "chain_service_km": 5000,
            "tire_front_psi": 32,
            "tire_rear_psi": 32,
            "oil_type": "15W-50",
            "tank_liters": 15.0,
        },
        "Himalayan": {
            "oil_km": 10000,
            "chain_lube_km": 1000,
            "chain_service_km": 5000,
            "tire_front_psi": 32,
            "tire_rear_psi": 36,
            "oil_type": "15W-50",
            "tank_liters": 15.0,
        },
        "Interceptor 650": {
            "oil_km": 10000,
            "chain_lube_km": 1000,
            "valve_check_km": 20000,
            "tire_front_psi": 32,
            "tire_rear_psi": 39,
            "oil_type": "15W-50",
            "tank_liters": 12.5,
        },
    },
    "Bajaj": {
        "Pulsar 150": {
            "oil_km": 5000,
            "chain_lube_km": 500,
            "tire_front_psi": 28,
            "tire_rear_psi": 32,
            "oil_type": "20W-50",
            "tank_liters": 15.0,
        },
        "Pulsar 220": {
            "oil_km": 5000,
            "chain_lube_km": 500,
            "tire_front_psi": 28,
            "tire_rear_psi": 32,
            "oil_type": "20W-50",
            "tank_liters": 15.0,
        },
        "Dominar 400": {
            "oil_km": 10000,
            "chain_lube_km": 500,
            "tire_front_psi": 32,
            "tire_rear_psi": 36,
            "oil_type": "10W-50",
            "tank_liters": 13.0,
        },
    },
    "KTM": {
        "Duke 200": {
            "oil_km": 7500,
            "chain_lube_km": 500,
            "tire_front_psi": 32,
            "tire_rear_psi": 36,
            "oil_type": "10W-50",
            "tank_liters": 13.4,
        },
        "Duke 390": {
            "oil_km": 7500,
            "chain_lube_km": 500,
            "valve_check_km": 15000,
            "tire_front_psi": 32,
            "tire_rear_psi": 36,
            "oil_type": "10W-50",
            "tank_liters": 13.4,
        },
    },
    "TVS": {
        "Apache RTR 160": {
            "oil_km": 5000,
            "chain_lube_km": 500,
            "tire_front_psi": 28,
            "tire_rear_psi": 32,
            "oil_type": "10W-30",
            "tank_liters": 12.0,
        },
        "Apache RR 310": {
            "oil_km": 10000,
            "chain_lube_km": 500,
            "tire_front_psi": 32,
            "tire_rear_psi": 36,
            "oil_type": "10W-50",
            "tank_liters": 11.0,
        },
    },
    "Suzuki": {
        "Gixxer": {
            "oil_km": 6000,
            "chain_lube_km": 500,
            "tire_front_psi": 29,
            "tire_rear_psi": 33,
            "oil_type": "10W-40",
            "tank_liters": 12.0,
        },
    },
    "Hero": {
        "Splendor": {
            "oil_km": 4000,
            "chain_lube_km": 500,
            "tire_front_psi": 28,
            "tire_rear_psi": 32,
            "oil_type": "20W-40",
            "tank_liters": 9.8,
        },
        "Xpulse 200": {
            "oil_km": 5000,
            "chain_lube_km": 500,
            "tire_front_psi": 28,
            "tire_rear_psi": 32,
            "oil_type": "10W-30",
            "tank_liters": 13.0,
        },
    },
}

# Brand-level defaults when exact model not in database
BRAND_DEFAULTS: dict[str, dict] = {
    "Honda": {"oil_km": 12000, "chain_lube_km": 1000, "tire_front_psi": 29, "tire_rear_psi": 33},
    "Yamaha": {"oil_km": 10000, "chain_lube_km": 500, "tire_front_psi": 29, "tire_rear_psi": 33},
    "Royal Enfield": {"oil_km": 10000, "chain_lube_km": 1000, "tire_front_psi": 32, "tire_rear_psi": 32},
    "Bajaj": {"oil_km": 5000, "chain_lube_km": 500, "tire_front_psi": 28, "tire_rear_psi": 32},
    "KTM": {"oil_km": 7500, "chain_lube_km": 500, "tire_front_psi": 32, "tire_rear_psi": 36},
    "TVS": {"oil_km": 5000, "chain_lube_km": 500, "tire_front_psi": 28, "tire_rear_psi": 32},
    "Suzuki": {"oil_km": 6000, "chain_lube_km": 500, "tire_front_psi": 29, "tire_rear_psi": 33},
    "Hero": {"oil_km": 4000, "chain_lube_km": 500, "tire_front_psi": 28, "tire_rear_psi": 32},
    "BMW": {"oil_km": 10000, "chain_lube_km": 1000, "tire_front_psi": 36, "tire_rear_psi": 42},
    "Harley-Davidson": {"oil_km": 8000, "chain_lube_km": 1000, "tire_front_psi": 36, "tire_rear_psi": 40},
}

GENERIC_DEFAULTS = {
    "oil_km": 6000,
    "oil_months": 12,
    "chain_lube_km": 500,
    "chain_service_km": 5000,
    "valve_check_km": 20000,
    "tire_front_psi": 32,
    "tire_rear_psi": 36,
    "brake_fluid_km": 20000,
    "brake_fluid_months": 24,
    "tire_replace_km": 15000,
}


def get_model_specs(make: str | None, model: str | None) -> dict:
    """Resolve specs for make/model with brand and generic fallbacks."""
    specs = dict(GENERIC_DEFAULTS)
    if not make:
        return specs

    make_key = next((k for k in MODEL_SPECS if k.lower() == make.lower()), None)
    if not make_key:
        brand = next((k for k in BRAND_DEFAULTS if k.lower() == make.lower()), None)
        if brand:
            specs.update(BRAND_DEFAULTS[brand])
        return specs

    if model:
        for model_name, model_specs in MODEL_SPECS[make_key].items():
            if model_name.lower() in model.lower() or model.lower() in model_name.lower():
                specs.update(model_specs)
                return specs

    specs.update(BRAND_DEFAULTS.get(make_key, {}))
    return specs


def specs_to_reminders(specs: dict) -> list[dict]:
    """Build default reminder definitions from model specs."""
    reminders = []
    if specs.get("chain_lube_km"):
        reminders.append({
            "title": "Chain lube",
            "reminder_type": "chain_lube",
            "interval_km": specs["chain_lube_km"],
            "interval_days": None,
        })
    if specs.get("oil_km"):
        reminders.append({
            "title": "Engine oil change",
            "reminder_type": "service",
            "interval_km": specs["oil_km"],
            "interval_days": specs.get("oil_months") and specs["oil_months"] * 30,
        })
    if specs.get("tire_replace_km"):
        reminders.append({
            "title": "Tire check",
            "reminder_type": "tire_check",
            "interval_km": min(1000, specs["tire_replace_km"] // 10),
            "interval_days": 30,
        })
    if specs.get("brake_fluid_km"):
        reminders.append({
            "title": "Brake fluid",
            "reminder_type": "brake_check",
            "interval_km": specs["brake_fluid_km"],
            "interval_days": specs.get("brake_fluid_months") and specs["brake_fluid_months"] * 30,
        })
    return reminders


PART_DEFINITIONS = [
    {"part_type": "engine_oil", "label": "Engine oil", "icon": "droplets", "interval_km_key": "oil_km"},
    {"part_type": "chain", "label": "Drive chain", "icon": "link", "interval_km_key": "chain_lube_km"},
    {"part_type": "tires", "label": "Tires", "icon": "circle-dot", "interval_km_key": "tire_replace_km"},
    {"part_type": "brake_fluid", "label": "Brake fluid", "icon": "octagon", "interval_km_key": "brake_fluid_km"},
    {"part_type": "air_filter", "label": "Air filter", "icon": "wind", "interval_km_key": None, "default_km": 10000},
]
