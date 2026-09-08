import base64
import json
import os
import re
from pathlib import Path

PROMPTS = {
    "fuel": """Analyze this fuel station receipt image for a motorbike owner in India.
Extract and return ONLY valid JSON with these keys:
- entry_date: date in YYYY-MM-DD format, or null
- liters: fuel quantity in liters as a number, or null
- cost: total amount paid in Indian Rupees as a number only, or null
- odometer: odometer reading in km if visible, or null
- notes: petrol pump name or other useful text, or null

Use null for missing fields. Do not include currency symbols in numbers.""",
    "maintenance": """Analyze this motorbike service or maintenance bill image from India.
Extract and return ONLY valid JSON with these keys:
- entry_date: date in YYYY-MM-DD format, or null
- description: brief summary of work done, or null
- cost: total amount paid in Indian Rupees as a number only, or null
- odometer: odometer reading in km if visible, or null
- entry_type: "service" for scheduled service, "adhoc" for repairs/parts, or null
- notes: garage name or extra details, or null

Use null for missing fields. Do not include currency symbols in numbers.""",
}


def parsing_available():
    return bool(os.environ.get("OPENAI_API_KEY"))


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _normalize_payload(data, entry_type):
    cleaned = {}
    for key, value in data.items():
        if value in (None, "", "null"):
            cleaned[key] = None
        else:
            cleaned[key] = value

    if entry_type == "maintenance" and cleaned.get("entry_type") not in ("service", "adhoc"):
        cleaned["entry_type"] = None

    for numeric in ("liters", "cost", "odometer"):
        if numeric in cleaned and cleaned[numeric] is not None:
            try:
                cleaned[numeric] = float(cleaned[numeric])
            except (TypeError, ValueError):
                cleaned[numeric] = None

    return cleaned


def parse_receipt_image(image_path, entry_type):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Receipt scanning is not configured. Set OPENAI_API_KEY in your environment."
        )

    if entry_type not in PROMPTS:
        raise ValueError("Unsupported receipt type.")

    image_path = Path(image_path)
    mime = "image/jpeg"
    if image_path.suffix.lower() == ".png":
        mime = "image/png"
    elif image_path.suffix.lower() == ".webp":
        mime = "image/webp"
    elif image_path.suffix.lower() == ".gif":
        mime = "image/gif"

    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPTS[entry_type]},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{encoded}"},
                    },
                ],
            }
        ],
        max_tokens=500,
    )

    raw = response.choices[0].message.content or "{}"
    data = _normalize_payload(_extract_json(raw), entry_type)
    return data
