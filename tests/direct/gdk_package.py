#!/usr/bin/env python3
"""Execute actual native code for the opt-in no-Store local XPackage COM object."""
import ctypes as C
import subprocess
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

class Guid(C.Structure):
    _fields_=[("a",C.c_uint32),("b",C.c_uint16),("c",C.c_uint16),("d",C.c_ubyte*8)]
def guid(a,b,c,bytes8):return Guid(a,b,c,(C.c_ubyte*8)(*bytes8))
CLASS=guid(0xaf406016,0xe850,0x4aa8,[0xa8,0x8d,0x2f,0x3d,0xcb,0x9d,0xac,0x7e])
IID3=guid(0xe2a4734b,0x2f4a,0x456d,[0xaa,0x8f,0x06,0x5e,0x04,0xfb,0x20,0x09])
USER=guid(0x01acd177,0x91f9,0x4763,[0xa3,0x8e,0xcc,0xbb,0x55,0xce,0x32,0xe0])

def main():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);stub=root/"debug.cpp";dll=root/"package.so"
        stub.write_text('extern "C" void OutputDebugStringA(const char*) {}\n')
        subprocess.run(["g++","-std=c++17","-shared","-fPIC","-Wall","-Wextra",
                        "-Werror","-D__declspec(x)=",
                        str(ROOT/"enhanced/offline/gdk_package.cpp"),str(stub),
                        "-o",str(dll)],check=True)
        image=C.CDLL(str(dll));query=image.T7OfflinePackageQuery
        query.argtypes=[C.POINTER(Guid),C.POINTER(Guid),C.POINTER(C.c_void_p)]
        query.restype=C.c_int32
        handle=C.c_void_p(1234)
        assert query(C.byref(USER),C.byref(IID3),C.byref(handle))!=0 and not handle.value
        assert query(C.byref(CLASS),C.byref(IID3),C.byref(handle))==0 and handle.value
        table=(C.c_void_p*41).from_address(C.c_void_p.from_address(handle.value).value)
        packaged=C.CFUNCTYPE(C.c_bool,C.c_void_p)(table[4])
        assert packaged(handle.value) is False
        locale=C.CFUNCTYPE(C.c_int32,C.c_void_p,C.c_size_t,C.POINTER(C.c_char))(table[11])
        text=C.create_string_buffer(16)
        assert locale(handle.value,len(text),text)==0 and text.value==b"en-US"
        short=C.create_string_buffer(2)
        assert locale(handle.value,len(short),short)!=0
        assert short.raw==b"\\x00\\x00"
        blocked=C.CFUNCTYPE(C.c_int32,C.c_void_p)(table[3])
        assert blocked(handle.value)<0
        last=C.CFUNCTYPE(C.c_int32,C.c_void_p)(table[40])
        assert last(handle.value)<0
        release=C.CFUNCTYPE(C.c_uint32,C.c_void_p)(table[2])
        assert release(handle.value)>=1
        print("PASS: local XPackageImpl3 real COM vtable (41 slots), en-US locale, no Store/package identity")
if __name__=="__main__":main()
