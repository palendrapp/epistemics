"""Exclusive private artifacts and exact-byte commitments."""

import hashlib
import json
import os
from pathlib import Path


def encoded(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, raw):
    path = Path(path)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError("Existing artifact bytes differ; refuse overwrite") from None
    else:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)


def fingerprint():
    import importlib.metadata

    root = Path(__file__).parent
    files = sorted(root.glob("*.py")) + sorted((root / "assets").glob("*"))
    files += sorted((root.parent / "source_inference").glob("*.py"))
    files += [
        root.parent / p for p in ("models.py", "participants.py", "service.py", "live/web.py")
    ]
    return digest(
        encoded(
            {
                "files": {str(p.relative_to(root.parent)): digest(p.read_bytes()) for p in files},
                "dependencies": {
                    name: importlib.metadata.version(name) for name in ("numpy", "pydantic", "mcp")
                },
            }
        )
    )
