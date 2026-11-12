#!/usr/bin/env python3
"""Execute the independently implemented local GDK feature COM vtable.

Verifies GUID matching, IUnknown references, fail-closed feature responses,
and unsupported Xbox/service interfaces. No executable, Wine or network needed.
"""
import ctypes as C
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
class Guid(C.Structure):
    _fields_ = [("a", C.c_uint32), ("b", C.c_uint16), ("c", C.c_uint16), ("d", C.c_ubyte * 8)]

def gid(a, b, c, values):
    return Guid(a, b, c, (C.c_ubyte * 8)(*values))

FEATURE = gid(0x8836fe87, 0xedb9, 0x4fe3, [0x8d,0xad,0x05,0xf0,0xd2,0xcd,0x5b,0x40])
UNKNOWN = gid(0,0,0,[0xc0,0,0,0,0,0,0,0x46])
OTHER = gid(0x01acd177,0x91f9,0x4763,[0xa3,0x8e,0xcc,0xbb,0x55,0xce,0x32,0xe0])

def main():
    with tempfile.TemporaryDirectory() as root:
        binary = Path(root) / "feature.so"
        subprocess.run(["g++","-std=c++17","-shared","-fPIC","-Wall","-Wextra","-Werror",
                        str(ROOT/"enhanced/offline/gdk_feature.cpp"),"-o",str(binary)],check=True)
        dll = C.CDLL(str(binary))
        query = dll.T7OfflineFeatureQuery
        query.argtypes = [C.POINTER(Guid),C.POINTER(Guid),C.POINTER(C.c_void_p)]
        query.restype = C.c_int32
        out = C.c_void_p(123)
        assert query(C.byref(OTHER),C.byref(FEATURE),C.byref(out)) != 0 and out.value is None
        assert query(C.byref(FEATURE),C.byref(OTHER),C.byref(out)) != 0 and out.value is None
        assert query(C.byref(FEATURE),C.byref(FEATURE),C.byref(out)) == 0 and out.value
        object_ptr = out.value
        vtable = (C.c_void_p*4).from_address(C.c_void_p.from_address(object_ptr).value)
        get_available = C.CFUNCTYPE(C.c_bool,C.c_void_p,C.c_uint32)(vtable[3])
        query_interface = C.CFUNCTYPE(C.c_int32,C.c_void_p,C.POINTER(Guid),C.POINTER(C.c_void_p))(vtable[0])
        release = C.CFUNCTYPE(C.c_uint32,C.c_void_p)(vtable[2])
        for value in range(0,30):
            assert not get_available(object_ptr,value), value
        other = C.c_void_p()
        assert query_interface(object_ptr,C.byref(UNKNOWN),C.byref(other)) == 0
        assert other.value == object_ptr
        assert release(object_ptr) >= 1
        assert release(object_ptr) >= 1
        print("PASS: offline GDK feature COM singleton, IUnknown methods and all features unavailable")

if __name__ == "__main__":
    main()
