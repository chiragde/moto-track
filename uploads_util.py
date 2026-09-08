import uuid
from pathlib import Path

from werkzeug.utils import secure_filename

UPLOAD_ROOT = Path(__file__).parent / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _extension_for_file(filename, mimetype):
    ext = Path(filename or "").suffix.lower()
    if ext in ALLOWED_EXTENSIONS:
        return ext
    return MIME_TO_EXT.get(mimetype or "", ".jpg")


def save_receipt_image(user_id, file_storage, folder="pending"):
    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_UPLOAD_BYTES:
        raise ValueError("Image must be 10 MB or smaller.")

    ext = _extension_for_file(file_storage.filename, file_storage.mimetype)
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Upload a JPG, PNG, or WEBP image.")

    safe_name = f"{uuid.uuid4().hex}{ext}"
    target_dir = UPLOAD_ROOT / folder / str(user_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name
    file_storage.save(target_path)

    return f"{folder}/{user_id}/{safe_name}"


def save_bike_photo(user_id, file_storage):
    return save_receipt_image(user_id, file_storage, folder="bikes")


def resolve_receipt_path(relative_path):
    if not relative_path:
        return None
    full_path = (UPLOAD_ROOT / relative_path).resolve()
    if not str(full_path).startswith(str(UPLOAD_ROOT.resolve())):
        return None
    return full_path if full_path.is_file() else None


def receipt_belongs_to_user(relative_path, user_id):
    if not relative_path:
        return False
    parts = Path(relative_path).parts
    if len(parts) < 2:
        return False
    return parts[1] == str(user_id)


def finalize_receipt_path(relative_path):
    source = resolve_receipt_path(relative_path)
    if not source:
        return None

    parts = Path(relative_path).parts
    if len(parts) < 3 or parts[0] != "pending":
        return relative_path

    dest_relative = Path("receipts") / parts[1] / parts[2]
    dest = UPLOAD_ROOT / dest_relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    source.replace(dest)
    return str(dest_relative).replace("\\", "/")


def delete_receipt(relative_path):
    path = resolve_receipt_path(relative_path)
    if path:
        path.unlink(missing_ok=True)
