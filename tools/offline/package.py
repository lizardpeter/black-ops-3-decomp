#!/usr/bin/env python3
"""Build the experimental offline package for the BO3 Store exe. Never modifies the supplied original.

    python3 tools/offline/package.py --original <BlackOps3.exe> --output <new dir> [--dll <recon.dll>]

Ported from ghosts-decomp tools/offline/package.py. Writes to the new output directory:
  BlackOps3_offline.exe   a copy of the pinned Store exe (sha256 checked against target.toml) with
                          - a new section .t7off holding a marker, new import descriptors and lookup tables;
                          - original IAT slots for network, HTTP, process launch, COM activation, event tracing and
                            dynamic loading pointed at recon.dll adapters (ADAPTERS below); slot addresses unchanged,
                            each provider's imports split into contiguous runs;
                          - the reviewed original function entries in ENTRIES overwritten with `jmp rel32` to their
                            recon.dll replacement;
                          - a bootstrap import of recon.dll, fixed base (DYNAMIC_BASE cleared), no signature or bound
                            imports, a recomputed checksum.
  recon.dll               tools/offline/build_dll.py output, fixed base 0x180000000
  manifest.json           hashes, every entry's original and new bytes, every redirected import

Every change is recorded in records/patches.tsv. Native Windows behaviour is not verified by building a package.
"""
import argparse
import hashlib
import json
import shutil
import struct
import tomllib
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parents[2]
BUILD = "BlackOps3_MSStore"
EXE_NAME = "BlackOps3_offline.exe"
MAGIC = b"T7OFFLINE1\0\0\x01\0\0\0"
SECTION = b".t7off\0\0"

# Original function entries replaced in the offline package: va -> recon.dll export. Each is a patch in
# records/patches.tsv; keep the two in step.
ENTRIES = {
    0x142920308: "T7OfflineGameRuntimeInitialize",  # P0002: XGameRuntimeInitialize (GDK static layer)
}


def adapter(dll, name, ordinal=None):
    """recon.dll export for an original import, or None to keep the original provider (P0001)."""
    dll = dll.lower()
    if dll == "winhttp.dll":
        return "T7DenyMinusOne" if name == "WinHttpSetStatusCallback" else "T7DenyNull"
    if dll == "xcurl.dll":
        if name == "curl_easy_strerror":
            return "T7OfflineErrorText"
        if name in {"curl_global_init", "curl_easy_setopt", "curl_easy_getinfo", "curl_easy_perform"}:
            return "T7DenyCurl"
        if name in {"curl_multi_add_handle", "curl_multi_remove_handle", "curl_multi_perform", "curl_multi_poll"}:
            return "T7DenyCurlMulti"
        return "T7DenyNull"
    if dll == "ws2_32.dll":
        if name in {"socket", "WSASocketA", "WSASocketW", "connect", "send", "sendto", "WSASendTo", "accept"}:
            return "T7DenySocket"
        if name == "gethostbyname":
            return "T7DenyDns"
        if name == "getaddrinfo":
            return "T7DenyAddrInfo"
    if dll == "kernel32.dll":
        if name in {"LoadLibraryA", "LoadLibraryW", "LoadLibraryExA", "LoadLibraryExW", "GetProcAddress"}:
            return "T7Offline" + name
        if name in {"CreateProcessA", "CreateProcessW"}:
            return "T7DenyNull"
    if dll == "ole32.dll" and name == "CoCreateInstance":
        return "T7DenyCom"
    if dll == "shell32.dll" and name == "ShellExecuteA":
        return "T7DenyStatus"
    if dll == "advapi32.dll":
        if name == "EventRegister":
            return "T7DenyEventRegister"
        if name in {"EventWriteTransfer", "EventSetInformation"}:
            return "T7DenyStatus"
    if dll.startswith("api-ms-win-crt-"):
        if name == "system":
            return "T7DenyMinusOne"
        if name == "_popen":
            return "T7DenyNull"
    return None


def sha(data):
    return hashlib.sha256(data).hexdigest()


def align(n, a):
    return (n + a - 1) // a * a


def function_sizes():
    import csv
    csv.field_size_limit(1 << 30)
    with open(ROOT / "analysis" / BUILD / "functions.tsv", newline="") as f:
        return {int(r["va"], 16): int(r["size"] or 0) for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)}


def grow_headers(data, pe):
    """Make room for one more section header when the table is full (the Store exe has 24 bytes left): insert one
    FileAlignment block after the headers and move every file offset that points past them. Virtual addresses,
    and so all code and data references, are unchanged."""
    oh = pe.OPTIONAL_HEADER
    table_end = pe.sections[-1].get_file_offset() + 40
    first_raw = min(s.PointerToRawData for s in pe.sections if s.SizeOfRawData)
    if table_end + 40 <= first_raw:
        return data
    shift = oh.FileAlignment
    if oh.SizeOfHeaders != first_raw or oh.SizeOfHeaders + shift > min(s.VirtualAddress for s in pe.sections):
        raise ValueError("headers cannot grow")
    data[oh.SizeOfHeaders:oh.SizeOfHeaders] = b"\0" * shift
    for s in pe.sections:
        if s.SizeOfRawData:
            struct.pack_into("<I", data, s.get_file_offset() + 20, s.PointerToRawData + shift)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DEBUG"]])
    for d in getattr(pe, "DIRECTORY_ENTRY_DEBUG", []):
        if d.struct.PointerToRawData:
            # the directory itself sits in a section that moved by `shift` too
            struct.pack_into("<I", data, d.struct.get_file_offset() + shift + 24, d.struct.PointerToRawData + shift)
    struct.pack_into("<I", data, oh.get_field_absolute_offset("SizeOfHeaders"), oh.SizeOfHeaders + shift)
    return data


def transform(original, dll_bytes):
    cfg = tomllib.loads((ROOT / "target.toml").read_text())
    expected = next(b["exe"]["sha256"] for b in cfg["build"] if b["id"] == BUILD)
    if sha(original) != expected:
        raise ValueError("original does not match the pinned Store exe sha256 in target.toml")
    pe = pefile.PE(data=original)
    dll = pefile.PE(data=dll_bytes)
    if pe.OPTIONAL_HEADER.ImageBase != 0x140000000 or dll.OPTIONAL_HEADER.ImageBase != 0x180000000:
        raise ValueError("fixed image bases required")
    if dll.OPTIONAL_HEADER.AddressOfEntryPoint == 0 or dll.OPTIONAL_HEADER.DllCharacteristics & 0x40:
        raise ValueError("recon.dll must have the offline entry and a fixed base (tools/offline/build_dll.py)")
    exports = {e.name.decode(): dll.OPTIONAL_HEADER.ImageBase + e.address
               for e in dll.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
    if not {"T7OfflineBootstrap", "T7OfflineDllMain", "T7DenySocket"} <= exports.keys():
        raise ValueError("offline exports missing")
    if exports["T7OfflineDllMain"] != dll.OPTIONAL_HEADER.ImageBase + dll.OPTIONAL_HEADER.AddressOfEntryPoint:
        raise ValueError("DLL entry must be the offline attach guard")
    if pe.OPTIONAL_HEADER.DATA_DIRECTORY[13].VirtualAddress:
        raise ValueError("unreviewed delay imports")

    data = grow_headers(bytearray(original), pe)
    pe = pefile.PE(data=bytes(data))
    oh = pe.OPTIONAL_HEADER
    rva = align(max(s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData) for s in pe.sections),
                oh.SectionAlignment)
    if rva != oh.SizeOfImage:
        raise ValueError("unexpected image layout")
    raw = align(len(data), oh.FileAlignment)
    section_header = pe.sections[-1].get_file_offset() + 40
    if section_header + 40 > min(s.PointerToRawData for s in pe.sections if s.SizeOfRawData):
        raise ValueError("no section header space")
    payload = bytearray(MAGIC)

    def add(blob, alignment=1):
        payload.extend(b"\0" * (align(len(payload), alignment) - len(payload)))
        at = rva + len(payload)
        payload.extend(blob)
        return at

    def text(s):
        return add(s.encode("ascii") + b"\0")

    runs, redirected = [], []
    for desc in pe.DIRECTORY_ENTRY_IMPORT:
        provider = desc.dll.decode("ascii")
        current = None
        for imp in desc.imports:
            name = imp.name.decode("ascii") if imp.name else None
            replacement = adapter(provider, name, imp.ordinal)
            dest = "recon.dll" if replacement else provider
            if current is None or current[0] != dest:
                current = [dest, imp.address - oh.ImageBase, []]
                runs.append(current)
            if replacement:
                if replacement not in exports:
                    raise ValueError("missing adapter " + replacement)
                redirected.append({"provider": provider, "name": name, "ordinal": imp.ordinal,
                                   "iat_rva": f"{imp.address - oh.ImageBase:X}", "export": replacement})
            target = replacement or name
            thunk = add(b"\0\0" + target.encode("ascii") + b"\0", 2) if target else (1 << 63) | imp.ordinal
            current[2].append(thunk)
    bootstrap_iat = add(b"\0" * 16, 8)  # recon.dll is loaded even if no adapter is ever called
    runs.append(["recon.dll", bootstrap_iat, [add(b"\0\0T7OfflineBootstrap\0", 2)]])
    descriptors = bytearray()
    for provider, iat, thunks in runs:
        ilt = add(struct.pack("<" + "Q" * (len(thunks) + 1), *thunks, 0), 8)
        descriptors.extend(struct.pack("<IIIII", ilt, 0, 0, text(provider), iat))
    imports_rva = add(descriptors + b"\0" * 20, 4)

    sizes = function_sizes()
    changes = []
    for va, symbol in sorted(ENTRIES.items()):
        if symbol not in exports:
            raise ValueError("recon.dll lacks " + symbol)
        if sizes.get(va, 0) < 5:
            raise ValueError(f"{va:X} is not a known function of at least 5 bytes")
        off = pe.get_offset_from_rva(va - oh.ImageBase)
        delta = exports[symbol] - (va + 5)
        if not -(1 << 31) <= delta < (1 << 31):
            raise ValueError("replacement out of rel32 range")
        patch = b"\xe9" + struct.pack("<i", delta)
        changes.append({"va": f"{va:09X}", "symbol": symbol, "export_va": f"{exports[symbol]:09X}",
                        "before": data[off:off + 5].hex(), "after": patch.hex()})
        data[off:off + 5] = patch

    raw_size = align(len(payload), oh.FileAlignment)
    data.extend(b"\0" * (raw - len(data)))
    data.extend(payload + b"\0" * (raw_size - len(payload)))
    struct.pack_into("<8sIIIIIIHHI", data, section_header, SECTION, len(payload), rva, raw_size, raw, 0, 0, 0, 0,
                     0xC0000040)  # initialized data, read/write

    def put(field, value, fmt="<I"):
        struct.pack_into(fmt, data, field, value)

    put(pe.FILE_HEADER.get_field_absolute_offset("NumberOfSections"), len(pe.sections) + 1, "<H")
    put(oh.get_field_absolute_offset("SizeOfImage"), align(rva + len(payload), oh.SectionAlignment))
    put(oh.get_field_absolute_offset("SizeOfInitializedData"), oh.SizeOfInitializedData + raw_size)
    put(oh.get_field_absolute_offset("DllCharacteristics"), oh.DllCharacteristics & ~0x60, "<H")  # fixed base
    for index in (4, 11):  # signature and bound imports no longer describe this copy
        put(oh.DATA_DIRECTORY[index].get_file_offset(), 0, "<Q")
    struct.pack_into("<II", data, oh.DATA_DIRECTORY[1].get_file_offset(), imports_rva, len(descriptors) + 20)
    put(oh.get_field_absolute_offset("CheckSum"), 0)
    put(oh.get_field_absolute_offset("CheckSum"), pefile.PE(data=bytes(data)).generate_checksum())
    manifest = {"format": 1, "mode": "offline", "build": BUILD, "original_sha256": expected,
                "exe": EXE_NAME, "exe_sha256": sha(data), "dll_sha256": sha(dll_bytes),
                "entries": changes, "imports": redirected,
                "native_windows_verified": False, "whole_process_egress_verified": False}
    return bytes(data), manifest


def package(original: Path, dll: Path, output: Path):
    dll_bytes = dll.read_bytes()
    patched, manifest = transform(original.read_bytes(), dll_bytes)
    output.mkdir(parents=True, exist_ok=False)
    try:
        (output / EXE_NAME).write_bytes(patched)
        (output / "recon.dll").write_bytes(dll_bytes)
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    except BaseException:
        shutil.rmtree(output)
        raise
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--dll", type=Path, default=ROOT / "build" / BUILD / "offline" / "recon.dll")
    ap.add_argument("--output", type=Path, required=True, help="new directory; must not exist")
    a = ap.parse_args()
    m = package(a.original, a.dll, a.output)
    print(f"packaged {len(m['entries'])} entry replacements and {len(m['imports'])} import redirects -> {a.output}")
