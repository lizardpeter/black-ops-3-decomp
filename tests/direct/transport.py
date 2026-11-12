#!/usr/bin/env python3
"""Real localhost UDP tests for the same direct transport source built into recon.dll."""
import ctypes as C
import shutil
import socket
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class Address(C.Structure):
    _fields_ = [('type',C.c_int),('ip',C.c_ubyte*4),('port',C.c_ushort),('handle',C.c_uint)]
class Message(C.Structure):
    _fields_ = [('data',C.c_void_p),('capacity',C.c_int),('size',C.c_int)]

def checksum(data):
    total = sum((data[i]<<8)|data[i+1] for i in range(0,len(data)-1,2))
    if len(data)%2: total += data[-1]
    while total>>16: total=(total&65535)+(total>>16)
    return (~total)&65535

def packet(payload): return b'T7D\x01\0'+struct.pack('>H',len(payload))+payload+struct.pack('>H',checksum(payload))

def load(path):
    lib=C.CDLL(str(path))
    for name,args,ret in [
        ('Open',[C.c_char_p,C.c_int],C.c_int),('Close',[],None),
        ('SelectPeer',[C.c_char_p],C.c_int),('Peer',[C.POINTER(Address)],C.c_int),
        ('Port',[],C.c_ushort),('Parse',[C.c_char_p,C.POINTER(Address),C.c_int],C.c_int),
        ('Send',[C.c_int,C.c_void_p,C.POINTER(Address)],C.c_int),
        ('Receive',[C.POINTER(Address),C.POINTER(Message)],C.c_int),
        ('SameAddress',[C.POINTER(Address),C.POINTER(Address),C.c_int],C.c_int),
    ]:
        fn=getattr(lib,'T7Direct'+name);fn.argtypes=args;fn.restype=ret
        setattr(lib,name,fn)
    return lib

def receive(lib):
    memory=C.create_string_buffer(1300)
    msg=Message(data=C.addressof(memory),capacity=1300,size=99)
    source=Address()
    result=lib.Receive(C.byref(source),C.byref(msg))
    return result,bytes(memory)[:msg.cursize],source,msg

def main():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        library=root/'client.so'
        subprocess.run(['g++','-std=c++17','-O1','-g','-shared','-fPIC','-pthread','-Wall','-Wextra','-Werror',
                        '-I'+str(ROOT/'include'),str(ROOT/'enhanced/direct/transport.cpp'),'-o',str(library)],check=True)
        shutil.copyfile(library,root/'server.so')
        client,server=load(library),load(root/'server.so')
        address=Address()
        for text in [b'',b'127.0.0.1',b'127.0.0.1:0',b'127.0.0.1:65536',b'256.1.1.1:1',
                     b'1.2.3:1',b'1.2.3.4.5:1',b'localhost:27016',b'1.2.3.4:1 extra',
                     b'1.2.3.4:1;quit',b'224.1.1.1:1',b'255.255.255.255:1',b'0.0.0.0:1']:
            assert not client.Parse(text,C.byref(address),0),text
            assert bytes(address)==bytes(C.sizeof(address)),text
        assert client.Open(b'127.0.0.1:0',0)
        assert server.Open(b'127.0.0.1:0',1)
        assert client.Port() and server.Port()
        peer=f'127.0.0.1:{server.Port()}'.encode()
        assert client.SelectPeer(peer) and client.Peer(C.byref(address))
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as stranger:
            stranger.bind(('127.0.0.1',0))
            stranger.sendto(packet(b'wrong peer'),('127.0.0.1',client.Port()))
            result,data,_,msg=receive(client)
            assert not result and not data
            # Listener has not received any client packet: unsolicited send is refused.
            client_addr=Address()
            assert server.Parse(f'127.0.0.1:{client.Port()}'.encode(),C.byref(client_addr),0)
            assert not server.Send(1,b'x',C.byref(client_addr))
            # Two C++ transports exchange exact game-framed bytes over real sockets.
            for payload in [b'',b'\xff'*4+b'getchallenge 0 "Player1"',b'abc',bytes(range(256))*4,b'x'*1262]:
                assert client.Send(len(payload),payload,C.byref(address))
                result,data,source,msg=receive(server)
                assert result and data==payload
                assert server.Send(len(payload),payload,C.byref(source))
                result,data,source,_=receive(client)
                assert result and data==payload
                assert client.SameAddress(C.byref(address),C.byref(source),1)
            # Framing verified against an independent Python socket and checksum.
            assert not client.SelectPeer(b'not-an-ip:4')
            assert not client.Send(1,b'x',C.byref(address))
            assert client.SelectPeer(f'127.0.0.1:{stranger.getsockname()[1]}'.encode())
            assert client.Peer(C.byref(address))
            payload=b'\xff'*4+b'getchallenge 0 "Player1"'
            assert client.Send(len(payload),payload,C.byref(address))
            stranger.settimeout(1)
            raw,sender=stranger.recvfrom(1400)
            assert raw==packet(payload)
            for bad in [b'',b'x',b'abc\0\0',b'x'*1273,
                        b'legacy'+struct.pack('>H',checksum(b'legacy')),
                        b'T7D\x02'+packet(b'x')[5:],b'T7D\x01\x01'+packet(b'x')[6:],
                        packet(b'x')[:6]+b'\0\x02'+packet(b'x')[8:]]:
                stranger.sendto(bad,sender)
                assert not receive(client)[0]
            stranger.sendto(packet(b'good'),sender)
            assert receive(client)[:2]==(1,b'good')
            # Check buffers before copy, including one-byte destinations.
            stranger.sendto(packet(b'too big'),sender)
            memory=C.create_string_buffer(b'GUARD')
            msg=Message(data=C.addressof(memory),capacity=1)
            source=Address()
            assert not client.Receive(C.byref(source),C.byref(msg)) and memory.value==b'GUARD'
            assert not client.Send(-1,None,C.byref(address))
            assert not client.Send(1263,b'x',C.byref(address))
            assert not client.Send(1,None,C.byref(address))
            other=Address.from_buffer_copy(address);other.ip[3]^=1
            assert not client.SameAddress(C.byref(address),C.byref(other),1)
            other=Address.from_buffer_copy(address);other.port^=1
            assert not client.SameAddress(C.byref(address),C.byref(other),1)
            assert client.SameAddress(C.byref(address),C.byref(other),0)
        assert not client.Open(b'invalid',0) and client.Port()==0
        client.Close();server.Close()
        assert not client.Send(0,None,C.byref(address))
        assert not receive(client)[0]
        assert server.Open(b'0.0.0.0:0',1) # Explicit wildcard bind; never a remote peer.
        server.Close()
    print('PASS: real UDP client/server round trip, framing, peer restrictions, malformed packets, bounds and shutdown')

if __name__=='__main__': main()
