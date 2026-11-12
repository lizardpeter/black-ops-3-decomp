#!/usr/bin/env python3
"""Stage genuine BO3 startup assets from the owner's R2 public read-only origin.

Never synthesize a FastFile or bundle game data in GitHub artifacts. The
checked-in TSV pins source keys, sizes, and R2 object ETags discovered from
the owner's connected R2 bucket. Singlepart ETags are checked as MD5; multipart
ETags are checked against the HTTPS response when available, with a fresh SHA256
reported for every downloaded object. No file is overwritten on mismatch.

    python3 tools/enhanced/fetch_startup.py --out .work/originals
    python3 tools/enhanced/fetch_startup.py --dry-run
"""
import argparse
import csv
import hashlib
import os
import re
import tempfile
import tomllib
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "records" / "bo3-startup-r2.tsv"
PREFIX = "bo3/DUMP/"
ETAG = re.compile(r"^[0-9a-f]{32}(?:-[0-9]+)?$")


def load_manifest(path):
    with Path(path).open(newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if not rows or len(rows) > 100:
        raise ValueError("Empty or unexpectedly large pinned startup inventory")
    seen, result = set(), []
    for r in rows:
        key = r["key"]
        if not key.startswith(PREFIX):
            raise ValueError("Wrong R2 prefix: " + key)
        local = key[len(PREFIX):]
        parts = Path(local).parts
        if (not parts or any(x in (".", "..") for x in parts) or
                not (local == "localization_en.txt" or
                     (len(parts) == 2 and parts[0] == "zone" and
                      (parts[1].startswith("core_") or
                       parts[1].startswith("en_core_") or
                       parts[1] in ("en_base.xpak", "en_initial.xpak")) and
                      parts[1].endswith((".ff", ".xpak"))))):
            raise ValueError("Unrecognized startup asset path: " + key)
        size = int(r["bytes"])
        if size <= 0 or size > 2_000_000_000:
            raise ValueError("Missing or oversized pinned asset: " + key)
        etag = r["etag"].lower()
        if not ETAG.fullmatch(etag) or local in seen:
            raise ValueError("Duplicate or invalid object ETag: " + key)
        digest = r["sha256"].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Missing SHA-256 pinned asset hash: " + key)
        seen.add(local)
        result.append((key, local, size, etag, digest))
    return result


def origin():
    cfg = tomllib.loads((ROOT / "target.toml").read_text())
    base = cfg["r2_public"]
    if not base.startswith("https://") or not base.endswith("/"):
        raise ValueError("R2 source must be a pinned HTTPS root")
    return base


def safe_target(output, local):
    path = output / local
    if output.is_symlink() or any(p.is_symlink() for p in (output, *path.parents)):
        raise ValueError("Symlinked asset destination ancestry")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("Refusing to replace symlinked original asset")
    return path


def checksums(file):
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk); md5.update(chunk); size += len(chunk)
    return size, md5.hexdigest(), sha.hexdigest()


def transfer(item, output, source):
    key, local, size, etag, pinned_sha256 = item
    target = safe_target(output, local)
    if target.exists():
        observed, md5, sha = checksums(target)
        if observed != size or sha != pinned_sha256 or ("-" not in etag and md5 != etag):
            raise ValueError("Existing original asset does not match pinned size/MD5: " + local)
        return local, size, sha, "reused"

    url = source + urllib.parse.quote(key, safe="/")
    request = urllib.request.Request(url, headers={"User-Agent": "bo3-enhanced-startup/audit-only"})
    fd, tmp_name = tempfile.mkstemp(prefix=".t7-asset-", dir=target.parent)
    os.close(fd)
    temp = Path(tmp_name)
    try:
        sha, md5 = hashlib.sha256(), hashlib.md5()
        total = 0
        with urllib.request.urlopen(request, timeout=120) as response, temp.open("wb") as stream:
            source_etag = (response.headers.get("ETag") or "").strip('"').lower()
            if source_etag and source_etag != etag:
                raise ValueError("R2 ETag differs from pinned metadata: " + local)
            for block in iter(lambda: response.read(1024 * 1024), b""):
                total += len(block)
                if total > size:
                    raise ValueError("Downloaded asset exceeds pinned byte count: " + local)
                stream.write(block); md5.update(block); sha.update(block)
        if total != size:
            raise ValueError("Downloaded asset size differs from pinned inventory: " + local)
        if "-" not in etag and md5.hexdigest() != etag:
            raise ValueError("Downloaded asset MD5 differs from pinned object: " + local)
        if sha.hexdigest() != pinned_sha256:
            raise ValueError("Downloaded original SHA-256 differs from verified R2 inventory: " + local)
        if target.exists() or target.is_symlink():
            raise FileExistsError("Asset appeared during fetch: " + local)
        os.replace(temp, target)
        return local, total, sha.hexdigest(), "downloaded"
    finally:
        temp.unlink(missing_ok=True)


def fetch(out, inventory=DEFAULT_MANIFEST, threads=4):
    if threads < 1 or threads > 8:
        raise ValueError("Only 1..8 simultaneous asset downloads allowed")
    items = load_manifest(inventory)
    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=True)
    base = origin()
    records = []
    with ThreadPoolExecutor(max_workers=threads) as pool:
        tasks = [pool.submit(transfer, item, out, base) for item in items]
        for future in as_completed(tasks):
            result = future.result()
            records.append(result)
            print(f"{result[3]} {result[0]}: {result[1]} bytes sha256={result[2]}", flush=True)
    print(f"PASS: {len(records)} authentic R2 startup assets; downloaded/reused, no synthetic FastFiles")
    return sorted(records)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    items = load_manifest(args.manifest)
    if args.dry_run:
        print(f"PINNED_STARTUP_ITEMS={len(items)} BYTES={sum(row[2] for row in items)}")
        return
    if not args.out:
        ap.error("--out required unless --dry-run")
    fetch(args.out, args.manifest, args.threads)


if __name__ == "__main__":
    main()
