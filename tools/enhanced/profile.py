#!/usr/bin/env python3
"""Persistent, self-asserted T7 *local* identity (never an Xbox/XUID account).

Only used by the canonical enhanced Wine diagnostic launcher. Profile files
live in the private Wine prefix; names and IDs are never included in manifests.
"""
import json
import os
import re
import secrets
import tempfile
from pathlib import Path

NAME = re.compile(r"[A-Za-z0-9_-](?:[A-Za-z0-9 _-]{0,29}[A-Za-z0-9_-])?\Z", re.ASCII)
HEX_ID = re.compile(r"[0-9a-f]{16}\Z", re.ASCII)
FORMAT = 1


def valid_name(name):
    return isinstance(name, str) and bool(NAME.fullmatch(name))


def validate_profile(record):
    if not isinstance(record, dict) or set(record) != {"format", "id", "name"}:
        raise ValueError("Invalid local profile schema")
    if record["format"] != FORMAT or not isinstance(record["id"], str) or not HEX_ID.fullmatch(record["id"]):
        raise ValueError("Invalid local ID")
    if record["id"] == "0" * 16 or not valid_name(record["name"]):
        raise ValueError("Invalid local player")
    return record


def load_or_create(path, name=None):
    path = Path(path)
    if name is not None and not valid_name(name):
        raise ValueError("Local name must be 1..31 ASCII letters, digits, spaces, _ or -")
    if path.is_symlink():
        raise ValueError("Refusing symbolic link as local player profile")
    if path.exists():
        record = validate_profile(json.loads(path.read_text()))
        if name is None or name == record["name"]:
            return record
        record["name"] = name
    else:
        record = {"format": FORMAT, "id": secrets.token_hex(8), "name": name or "LocalPlayer"}
        while record["id"] == "0" * 16:
            record["id"] = secrets.token_hex(8)
    validate_profile(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replace avoids a truncated profile after an interrupted launch.
    temporary = None
    try:
        fd, filename = tempfile.mkstemp(prefix=".t7-profile-", dir=path.parent)
        temporary = Path(filename)
        os.chmod(temporary, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(record, stream, separators=(",", ":"))
            stream.write("\n")
        if path.is_symlink():
            raise ValueError("Profile path became a symlink")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return record
