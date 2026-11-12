#!/usr/bin/env python3
"""Native local identity validation; no OS account, file or network access."""
import ctypes as C
import subprocess
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    with tempfile.TemporaryDirectory() as temp:
        output=Path(temp)/'profile.so'
        subprocess.run(['g++','-std=c++17','-shared','-fPIC','-Wall','-Wextra','-Werror',
                        str(ROOT/'enhanced/direct/profile.cpp'),'-o',str(output)],check=True)
        dll=C.CDLL(str(output))
        configure=dll.T7DirectPlayerConfigure;configure.argtypes=[C.c_char_p,C.c_char_p]
        identity=dll.T7DirectPlayerId;identity.argtypes=[C.c_int];identity.restype=C.c_uint64
        text=dll.T7DirectPlayerIdText;text.argtypes=[C.c_int];text.restype=C.c_char_p
        name=dll.T7DirectPlayerName;name.argtypes=[C.c_int];name.restype=C.c_char_p
        assert identity(0)==0 and text(0)==b'' and name(0)==b''
        for bad_id in (b'',b'0'*16,b'1',b'f'*17,b'g'*16,None):
            assert not configure(bad_id,b'Player') and identity(0)==0
        for bad_name in (b'',b' bad',b'bad ',b'bad;quit',b'bad\\key',b'bad"name',b'bad\nname',b'x'*32,None):
            assert not configure(b'123456789ABCDEF0',bad_name) and identity(0)==0
        for player_id in (1,0x123456789ABCDEF0,0xFFFFFFFFFFFFFFFF):
            assert configure(f'{player_id:016X}'.encode(),b'Local Player_1-2')
            assert identity(0)==player_id and text(0)==f'{player_id:016x}'.encode()
            assert name(0)==b'Local Player_1-2'
            for invalid in (-1,1,7,0x7FFFFFFF):
                assert identity(invalid)==0 and text(invalid)==b'' and name(invalid)==b''
        assert not configure(b'invalid',b'Player') and identity(0)==0 and text(0)==b'' and name(0)==b''
    print('PASS: local identity/name configuration, bounds, invalid-controller rejection and failed-config revocation')
if __name__=='__main__':main()
