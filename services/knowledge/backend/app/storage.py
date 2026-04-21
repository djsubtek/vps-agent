import os
import uuid
from pathlib import Path

STORAGE_ROOT = Path(os.environ.get("STORAGE_ROOT", "/storage"))


def save_file(file_bytes, filename):
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4()}_{Path(filename).name}"
    file_path = STORAGE_ROOT / stored_name
    file_path.write_bytes(file_bytes)
    return str(file_path)


def get_file(path):
    return Path(path).read_bytes()
