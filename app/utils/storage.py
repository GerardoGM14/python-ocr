import os
from pathlib import Path

def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def save_bytes(base_dir: str, filename: str, content: bytes) -> str | None:
    if not base_dir:
        return None
    ensure_dir(base_dir)
    safe = filename.replace("..", "_").replace("\\", "_").replace("/", "_")
    full = os.path.join(base_dir, safe)
    with open(full, "wb") as f:
        f.write(content)
    return full
