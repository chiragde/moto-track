CARE_TASK_TYPES = {
    "chain_lube": "Chain lube",
    "tire_check": "Tire check",
    "wash": "Wash & clean",
    "brake_check": "Brake check",
    "oil_topup": "Oil top-up",
    "custom": "Custom",
}

CARE_TASK_ICONS = {
    "chain_lube": "link",
    "tire_check": "circle-dot",
    "wash": "droplets",
    "brake_check": "octagon",
    "oil_topup": "flask-conical",
    "custom": "wrench",
    "service": "settings-2",
}

TRIP_TAGS = {
    "": "No tag",
    "commute": "Commute",
    "touring": "Touring",
    "city": "City ride",
    "highway": "Highway",
    "offroad": "Off-road",
}

CURRENCIES = {
    "INR": {"symbol": "₹", "label": "Indian Rupee"},
    "USD": {"symbol": "$", "label": "US Dollar"},
    "EUR": {"symbol": "€", "label": "Euro"},
    "GBP": {"symbol": "£", "label": "British Pound"},
}

UNIT_PRESETS = {
    "metric": {
        "distance_unit": "km",
        "volume_unit": "L",
        "efficiency_label": "km/L",
    },
    "imperial": {
        "distance_unit": "mi",
        "volume_unit": "gal",
        "efficiency_label": "mpg",
    },
}

DEFAULT_REMINDERS = [
    {
        "title": "Chain lube",
        "reminder_type": "chain_lube",
        "interval_km": 500,
        "interval_days": None,
    },
    {
        "title": "Full service",
        "reminder_type": "service",
        "interval_km": 5000,
        "interval_days": 180,
    },
    {
        "title": "Tire pressure check",
        "reminder_type": "tire_check",
        "interval_km": 1000,
        "interval_days": 30,
    },
]

# Make → models for the garage add-vehicle picker
BIKE_CATALOG = {
    "Bajaj": ["Pulsar 150", "Pulsar 220", "Dominar 400", "Avenger", "CT 100", "Platina"],
    "BMW": ["G 310 R", "G 310 GS", "F 850 GS", "R 1250 GS", "S 1000 RR"],
    "Ducati": ["Monster", "Scrambler", "Panigale V2", "Multistrada", "Diavel"],
    "Harley-Davidson": ["Sportster", "Iron 883", "Fat Boy", "Street Glide", "Pan America"],
    "Hero": ["Splendor", "Passion Pro", "Xtreme 160R", "Xpulse 200", "Karizma"],
    "Honda": ["CB350", "CB500X", "Africa Twin", "Activa", "Shine", "Unicorn", "Hornet 2.0"],
    "Kawasaki": ["Ninja 300", "Ninja 650", "Z900", "Versys 650", "Vulcan S"],
    "KTM": ["Duke 200", "Duke 390", "RC 390", "Adventure 390", "Adventure 250"],
    "Royal Enfield": ["Classic 350", "Meteor 350", "Hunter 350", "Himalayan", "Interceptor 650", "Continental GT 650"],
    "Suzuki": ["Gixxer", "Gixxer SF", "V-Strom 650", "Hayabusa", "Access 125"],
    "Triumph": ["Speed 400", "Bonneville", "Tiger 900", "Street Triple", "Rocket 3"],
    "TVS": ["Apache RTR 160", "Apache RR 310", "Jupiter", "Ntorq", "Raider"],
    "Yamaha": ["R15 V4", "MT-15", "FZ-S", "Ray ZR", "Fascino", "YZF-R3"],
    "Vespa": ["SXL 150", "VXL 150", "Sprint", "GTS 300"],
    "Ola Electric": ["S1 Pro", "S1 Air", "Roadster X"],
    "Ather": ["450X", "450S", "Rizta"],
    "Other": ["Custom / Other"],
}

BIKE_SERVICE_INTERVALS = {
    "honda": {"service_km": 4000, "oil_km": 4000},
    "yamaha": {"service_km": 5000, "oil_km": 5000},
    "bajaj": {"service_km": 5000, "oil_km": 3000},
    "royal enfield": {"service_km": 5000, "oil_km": 5000},
    "ktm": {"service_km": 7500, "oil_km": 7500},
    "hero": {"service_km": 4000, "oil_km": 4000},
    "tvs": {"service_km": 4000, "oil_km": 4000},
    "suzuki": {"service_km": 4000, "oil_km": 4000},
}

MAINTENANCE_TIPS = [
    "Lube your chain every 500–800 km, or sooner after rain rides.",
    "Check tire pressure weekly — under-inflated tires hurt mileage and grip.",
    "Warm up the engine for 30–60 seconds before riding off in cold weather.",
    "Replace engine oil per your manual; city riding often needs shorter intervals.",
    "Inspect brake pads when you lube the chain — worn pads are easy to miss.",
    "Clean your air filter regularly if you ride in dusty conditions.",
    "Log every fill-up to spot fuel efficiency drops early.",
    "Keep chain slack within spec; too tight wears sprockets faster.",
    "Use the correct grade of engine oil — thicker isn't always better.",
    "After washing, dry the chain and re-lube to prevent rust.",
    "Check coolant level monthly on liquid-cooled bikes.",
    "Rotate between two riding gloves — sweaty liners need time to dry.",
    "Note odometer at each service so you never miss an interval.",
    "A smooth throttle hand can improve fuel economy by 10% or more.",
    "Store your bike on a paddock stand to avoid flat spots on tires.",
]
