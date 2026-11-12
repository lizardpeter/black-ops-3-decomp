#!/usr/bin/env python3
"""Read-only BO3 asset readiness inventory for the canonical enhanced launcher.

A fastfile existing on disk does not prove the game opened or loaded it.
Only file counts and bounded basenames are reported; never absolute paths.
"""
from pathlib import Path

def inspect(game):
    game = Path(game)
    zone = game / "zone"
    result = {
        "zone_directory_present": False,
        "fastfiles_present": False,
        "fastfile_count": 0,
        "ui_fastfile_basename_candidates": [],
        "status": "unknown",
        "note": "Disk inventory is not a FastFile-open, renderer or menu test."
    }
    if not zone.is_dir() or zone.is_symlink():
        result["status"] = "missing-zone-directory"
        return result
    result["zone_directory_present"] = True
    count = 0
    ui = []
    # Prevent unexpected filesystem layouts or giant trees from consuming an
    # unbounded amount of diagnostic time; inspect at most 20000 fastfiles.
    try:
        for path in zone.rglob("*"):
            if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".ff":
                continue
            count += 1
            name = path.name.lower()
            if "ui" in name and name not in ui and len(ui) < 16:
                ui.append(name)
            if count >= 20000:
                break
    except (OSError, PermissionError):
        result["status"] = "file-enumeration-error"
        return result
    result["fastfile_count"] = count
    result["fastfiles_present"] = count > 0
    result["ui_fastfile_basename_candidates"] = ui
    result["status"] = "fastfiles-present-open-unverified" if count else "no-fastfiles-found"
    return result
