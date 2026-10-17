#!/usr/bin/env python3
"""Generate the graph import set for re_t7 from analysis/ + records/.

    python3 tools/graph/sync.py

Writes analysis/graph/:
  *.jsonl         one JSON object per row; a table over 40 MB is split into <name>.part-NN.jsonl
  manifest.json   ordered list of {file, sha256, cypher}; each cypher has one {{ROWS}} placeholder

To load: put the folder in the Graph DB server's import directory as t7/ and run every manifest entry,
in order, with the bulk_import_file tool (graph = target.toml `graph`). Every statement is
MERGE-by-key, so re-running is safe and the graph can be dropped and rebuilt at any time.

Schema (the whole of it; change it only here):
  (:Build {id, timestamp, exe_sha256, pdb_guid})
  (:Subsystem {name})                       top-level source folder, or _lib:<name> / _external
  (:SourceFile {path})-[:PART_OF]->(:Subsystem)
  (:Function {key, name, symbol})           build-independent identity (MAP decorated name when known)
  (:Function)-[:DEFINED_IN {line}]->(:SourceFile)
  (:FunctionInstance {id, build, va, size, status, type, src, bytes_sha256})
  (:FunctionInstance)-[:INSTANCE_OF]->(:Function)
  (:FunctionInstance)-[:IN_BUILD]->(:Build)
  (:FunctionInstance)-[:CALLS {kind}]->(:FunctionInstance)   from Ghidra's call graph, once available
No code text is ever stored in the graph.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import ROOT, config, load, read_tsv  # noqa: E402

OUT = ROOT / "analysis" / "graph"

SCHEMA = [
    "CREATE INDEX FOR (n:Build) ON (n.id)",
    "CREATE INDEX FOR (n:Subsystem) ON (n.name)",
    "CREATE INDEX FOR (n:SourceFile) ON (n.path)",
    "CREATE INDEX FOR (n:Function) ON (n.key)",
    "CREATE INDEX FOR (n:FunctionInstance) ON (n.id)",
]

CYPHER = {
    "builds": "UNWIND {{ROWS}} AS r MERGE (b:Build {id:r.id}) "
              "SET b.timestamp=r.timestamp, b.exe_sha256=r.exe_sha256, b.pdb_guid=r.pdb_guid",
    "sourcefiles": "UNWIND {{ROWS}} AS r MERGE (s:Subsystem {name:r.subsystem}) "
                   "MERGE (f:SourceFile {path:r.path}) MERGE (f)-[:PART_OF]->(s)",
    "functions": "UNWIND {{ROWS}} AS r MATCH (b:Build {id:r.build}) "
                 "MERGE (fn:Function {key:r.key}) SET fn.name = coalesce(fn.name, r.name), fn.symbol = r.symbol "
                 "MERGE (fi:FunctionInstance {id:r.id}) SET fi.build=r.build, fi.va=r.va, fi.size=r.size, "
                 "fi.status=r.status, fi.type=r.type, fi.src=r.src, fi.bytes_sha256=r.sha "
                 "MERGE (fi)-[:INSTANCE_OF]->(fn) MERGE (fi)-[:IN_BUILD]->(b) "
                 "WITH fn, r WHERE r.source <> '' "
                 "MATCH (sf:SourceFile {path:r.source}) MERGE (fn)-[d:DEFINED_IN]->(sf) SET d.line=r.line",
    "calls": "UNWIND {{ROWS}} AS r MATCH (a:FunctionInstance {id:r.caller}) "
             "MATCH (c:FunctionInstance {id:r.callee}) MERGE (a)-[e:CALLS]->(c) SET e.kind=r.kind",
}


PART_BYTES = 40 << 20  # GitHub rejects files over 100 MB; big tables are split into parts under this size


def write_jsonl(name, rows):
    """Write rows as <name>.jsonl, or as <name>.part-NN.jsonl when they exceed PART_BYTES. Returns manifest
    entries, one per file, all with the same cypher."""
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows]
    parts, cur, size = [], [], 0
    for line in lines:
        n = len(line.encode())
        if cur and size + n > PART_BYTES:
            parts.append(cur)
            cur, size = [], 0
        cur.append(line)
        size += n
    parts.append(cur)
    out = []
    for i, part in enumerate(parts):
        path = OUT / (f"{name}.jsonl" if len(parts) == 1 else f"{name}.part-{i:02d}.jsonl")
        data = "".join(part).encode()
        path.write_bytes(data)
        out.append({"file": f"t7/{path.name}", "sha256": hashlib.sha256(data).hexdigest(),
                    "rows": len(part), "cypher": CYPHER[name.split("-")[0]]})
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.jsonl"):
        old.unlink()
    cfg = config()
    manifest = {"graph": cfg["graph"], "schema": SCHEMA, "imports": []}
    builds, files = [], set()
    per_build = {}
    for b in cfg.get("build", []):
        fns = load(b["id"])
        if not fns:
            continue
        per_build[b["id"]] = fns
        builds.append({"id": b["id"], "timestamp": b.get("timestamp", ""), "exe_sha256": b["exe"]["sha256"],
                       "pdb_guid": b.get("pdb_guid", "")})
        files |= {(f.source, f.subsystem) for f in fns.values() if f.source}
    manifest["imports"].extend(write_jsonl("builds", builds))
    manifest["imports"].extend(write_jsonl("sourcefiles", [{"path": p, "subsystem": s} for p, s in sorted(files)]))
    for bid, fns in per_build.items():
        rows = [{"id": f"{bid}:{f.va}", "build": bid, "va": f.va, "size": f.size, "status": f.status,
                 "type": f.type, "src": f.src, "sha": f.extra.get("bytes_sha256", ""), "key": f.key,
                 "name": f.name, "symbol": f.symbol, "source": f.source, "line": f.line}
                for f in sorted(fns.values(), key=lambda f: f.va)]
        manifest["imports"].extend(write_jsonl(f"functions-{bid}", rows))
    for bid in per_build:
        edges = read_tsv(ROOT / "analysis" / bid / "ghidra" / "callgraph.tsv")
        uniq = sorted({(e["caller"], e["callee"], e["kind"]) for e in edges})
        if uniq:
            manifest["imports"].extend(write_jsonl(f"calls-{bid}", [
                {"caller": f"{bid}:{a}", "callee": f"{bid}:{c}", "kind": k} for a, c, k in uniq]))
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for m in manifest["imports"]:
        print(f"{m['rows']:>8}  {m['file']}")


if __name__ == "__main__":
    main()
