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

def packet(payload): return b'T7DP\x01\0'+struct.pack('>H',len(payload))+payload+struct.pack('>H',checksum(payload))

def load(path):
    lib=C.CDLL(str(path))
    for name,args,ret in [
        ('Open',[C.c_char_p,C.c_int],C.c_int),('Close',[],None),
        ('SetKey',[C.c_char_p],C.c_int),('WireVersion',[],C.c_int),
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
    return result,bytes(memory)[:msg.size],source,msg

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
                        b'T7DP\x02'+packet(b'x')[5:],b'T7DP\x01\x01'+packet(b'x')[6:],
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
        # Unkeyed wildcard syntax is intentionally local-only at bind time,
        # not merely a post-recv packet filter. A 127.0.0.2 destination
        # reaches an INADDR_ANY socket but must not reach 127.0.0.1-only.
        assert not server.Open(b'192.0.2.44:0', 1)
        assert server.Port() == 0
        assert server.Open(b'0.0.0.0:0', 1)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.bind(('127.0.0.1', 0))
            probe.sendto(packet(b'wrong-bound-ip'), ('127.0.0.2', server.Port()))
            assert not receive(server)[0], "wildcard no-key socket exposed outside 127.0.0.1"
            probe.sendto(packet(b'bound-loopback'), ('127.0.0.1', server.Port()))
            assert receive(server)[:2] == (1, b'bound-loopback')
        server.Close()
        # No-key legacy datagrams are restricted to loopback.
        assert client.Open(b'127.0.0.1:0',0)
        assert not client.SelectPeer(b'192.0.2.44:27016')
        assert client.WireVersion()==1
        client.Close()
        # Authenticated v3: strictly formatted packets with key and replay window.
        key=b'000102030405060708090a0b0c0d0e0f'
        assert not client.SetKey(b'invalid') and client.WireVersion()==1
        assert client.SetKey(key) and server.SetKey(key)
        assert client.WireVersion()==server.WireVersion()==3
        assert client.Open(b'127.0.0.1:0',0) and server.Open(b'127.0.0.1:0',1)
        assert client.SelectPeer(f'127.0.0.1:{server.Port()}'.encode())
        assert client.Peer(C.byref(address))
        payload=b'authenticated T7 direct packet'
        assert client.Send(len(payload),payload,C.byref(address))
        result,data,source,_=receive(server)
        assert result and data==payload
        assert server.Send(len(payload),payload,C.byref(source))
        assert receive(client)[:2]==(1,payload)
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as other:
            other.bind(('127.0.0.1',0))
            other.settimeout(1)
            assert client.SelectPeer(f'127.0.0.1:{other.getsockname()[1]}'.encode())
            assert client.Peer(C.byref(address))
            assert client.Send(len(payload),payload,C.byref(address))
            wire,_=other.recvfrom(1400)
            assert wire[:6]==b'T7DP'+bytes((3,0))
            assert len(wire)==8+8+len(payload)+8
            # A captured client->server packet is never a valid server->client
            # packet, even when sent from the currently selected endpoint.
            other.sendto(wire, ('127.0.0.1', client.Port()))
            assert not receive(client)[0], "authenticated reflection accepted"
            # The old keyed v2 format must not be silently accepted by v3.
            old=bytearray(wire);old[4]=2
            other.sendto(old, ('127.0.0.1', server.Port()))
            assert not receive(server)[0], "keyed v2 downgrade accepted"
            destination=('127.0.0.1',server.Port())
            other.sendto(wire,destination)
            assert receive(server)[:2]==(1,payload)
            other.sendto(wire,destination)
            assert not receive(server)[0]
            corrupted=bytearray(wire);corrupted[16]^=1
            other.sendto(corrupted,destination)
            assert not receive(server)[0]
            other.sendto(packet(b'legacy'),destination)
            assert not receive(server)[0]
        assert not client.SetKey(b'wrong')
        assert client.WireVersion()==1 and not client.Peer(C.byref(address))
        server.Close()
    print('PASS: real UDP client/server round trip, framing, peer restrictions, malformed packets, bounds and shutdown')

if __name__=='__main__': main()
