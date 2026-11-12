#!/usr/bin/env python3
"""Stage genuine startup FastFiles beside the unchanged enhanced EXE.

The canonical enhanced launcher always runs an unmodified original EXE
under a private Wine prefix. Some original BO3 game paths resolve relative to
the EXE directory rather than the working directory. For a diagnostic subset,
copy verified original R2 assets into the already-audited enhanced package,
without rewriting any binaries or modifying the user's authentic install.
Original game assets are never uploaded as CI artifacts.
"""
import argparse
import hashlib
import os
import shutil
from pathlib import Path

from fetch_startup import load_manifest, DEFAULT_MANIFEST, checksums
from verify import audit


def stage(game, package, manifest=DEFAULT_MANIFEST):
    game, package = Path(game).absolute(), Path(package).absolute()
    audit(package)
    if package.is_symlink() or game.is_symlink():
        raise ValueError("Refuse symlinked runtime/game root")
    rows = load_manifest(manifest)
    count = 0
    for key, local, expected, etag, pinned_sha256 in rows:
        src = game / local
        dst = package / local
        if src.is_symlink() or not src.is_file():
            raise ValueError(f"Missing verified original startup asset: {local}")
        if any(p.is_symlink() for p in dst.parents):
            raise ValueError("Refusing symlinked enhanced asset folder")
        before, md5, sha = checksums(src)
        if before != expected or sha != pinned_sha256 or ("-" not in etag and md5 != etag):
            raise ValueError(f"Wrong original R2 startup asset contents: {local}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() or dst.is_symlink():
            raise FileExistsError(f"Refuse to overwrite enhanced stage asset: {local}")
        # Copies rather than hardlinks prevent the enhanced runtime from
        # modifying the original user's files through shared inodes.
        shutil.copyfile(src, dst)
        after, _, other_sha = checksums(dst)
        if after != expected or other_sha != sha:
            dst.unlink(missing_ok=True)
            raise ValueError(f"Staged original asset changed during copy: {local}")
        count += 1
    audit(package)  # package's PE hashes/exports still exactly match
    print(f"PASS: staged {count} authentic startup assets beside unmodified BO3 EXE; no fake files")
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game", type=Path, required=True)
    ap.add_argument("--package", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()
    stage(args.game, args.package, args.manifest)


if __name__ == "__main__":
    main()
