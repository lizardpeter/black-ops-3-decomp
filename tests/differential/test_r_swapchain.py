"""Hand-written cases for gfx_d3d/r_init.cpp: making the swap chain (sub_141DAB250) and resizing it (sub_141DAD0C0).

COM objects come from a model (com.py) that logs every method call with its arguments: the device's QueryInterface
(the interface id compared by content) and CreateBuffer (the buffer description compared by content), the DXGI
device's and adapter's GetParent, the factory's MakeWindowAssociation, the swap chain's GetContainingOutput,
GetFullscreenState and ResizeBuffers, the output's GetDesc, the context's Flush and every Release. Any of the first
three calls can fail, the containing output can be missing, the swap chain may or may not end up fullscreen.

SendMessageA stands in for the window procedure: for message 0x8042 it logs the swap chain description (the whole
DXGI_SWAP_CHAIN_DESC sub_141DA7A00 made, which runs for real on mode lists set up per case) and makes a swap chain
or fails. The other callees are faked and logged: GetSystemMetrics (sizes per case), GetMonitorInfoA (success or
not), the fullscreen entry, Dvar_SetInt, the window-parameter functions (sub_141DABB90 fills the parameters, so the
copy the next call gets is compared), RegisterRawInputDevices (the RAWINPUTDEVICE compared), the constant-buffer
binding. Results stored in dx globals are compared.

The resize gets the render-target table as an argument buffer (so every byte it zeroes is compared), message pumps
scripted like the window thread's test (with and without WM_QUIT), and the callback present or not.

Mutation check: see the commit adding this file.
"""
import random
import struct

import syms
from com import ComModel
from harness import _MACHINES, HEAP, SCRATCH, program_write
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

CREATE = "?sub_141DAB250@@YAJPEBUGfxWindowParms@@@Z"
RESIZE = "?sub_141DAD0C0@@YAXXZ"
DEV, CTX, UNK, ADP, FAC, OUT, SWC = ("ID3D11Device", "ID3D11DeviceContext", "IUnknown", "IDXGIAdapter",
                                     "IDXGIFactory", "IDXGIOutput", "IDXGISwapChain")
QI, RELEASE, GET_PARENT = 0, 2 * 8, 6 * 8
SIGS = {
    (DEV, QI): "pp", (DEV, 3 * 8): "ppp",
    (UNK, GET_PARENT): "pp", (UNK, RELEASE): "",
    (ADP, GET_PARENT): "pp", (ADP, RELEASE): "",
    (FAC, 8 * 8): "pi", (FAC, RELEASE): "",
    (SWC, 15 * 8): "p", (SWC, 11 * 8): "pp", (SWC, 13 * 8): "iiiii",
    (OUT, 7 * 8): "p", (OUT, RELEASE): "",
    (CTX, 111 * 8): "",
}
DUMPS = {(DEV, QI): {0: 16}, (UNK, GET_PARENT): {0: 16}, (ADP, GET_PARENT): {0: 16}, (DEV, 3 * 8): {0: 24}}
HWND = 0x0001_0042
BACKBUFFER_DVAR = 0x6300_0000_0010
FULLSCREEN_DVAR = 0x6300_0000_0020
CALLBACK = SCRATCH + 0x7F000  # fake code: hooked, never executed


def regs(mu):
    return [mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]


def stack(mu, i):
    return struct.unpack("<Q", bytes(mu.mem_read(mu.reg_read(UC_X86_REG_RSP) + 8 + 8 * i, 8)))[0]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def parms_bytes(r, fullscreen):
    return (struct.pack("<Q", HWND) + struct.pack("<f", r.choice([60.0, 144.0, 0.0])) + bytes([fullscreen]) + bytes(3)
            + struct.pack("<iiiiiiii", r.choice([1, 2, 0]), 3, 22, 1920, 1080, *r.choice([(1920, 1080), (2560, 1440)]),
                          0))


def fill_parms(c):
    def fn(mu):
        p = regs(mu)[0]
        record(mu, "sub_141DABB90")
        mu.mem_write(p, struct.pack("<QfB3xiiiiiiii", HWND, 144.0, 0, 1, 0, 0, 1280, 720, *c["new_size"], 7))
    return fn


def common_fakes(c):
    return {
        "Dvar_GetInt": lambda mu: (record(mu, "Dvar_GetInt", regs(mu)[0]), c["backbuffers"])[1],
        "sub_141DABB90": fill_parms(c),
        "sub_141DAB810": lambda mu: record(mu, "sub_141DAB810", bytes(mu.mem_read(regs(mu)[0], 0x30))),
        "R_StoreWindowSettings": lambda mu: record(mu, "R_StoreWindowSettings", bytes(mu.mem_read(regs(mu)[0], 0x30))),
    }


# ---- sub_141DAB250 --------------------------------------------------------------------------------------------

def create_fakes(c, model_box):
    def send(mu):
        hwnd, msg, wparam, lparam = regs(mu)
        model = model_box[0]
        record(mu, "SendMessageA", hwnd, msg & 0xFFFFFFFF, model.objects.get(wparam, (None, wparam))[1],
               bytes(mu.mem_read(lparam, 0x48)))
        if c["create_hr"] < 0x80000000:
            program_write(mu, syms.va("dx_swapChain"), struct.pack("<Q", model.new(SWC, mu)))
        return c["create_hr"]

    def metrics(mu):
        i = regs(mu)[0] & 0xFFFFFFFF
        record(mu, "GetSystemMetrics", i)
        return c["metrics"][i] & 0xFFFFFFFF

    def monitor_info(mu):
        hmon, info = regs(mu)[:2]
        record(mu, "GetMonitorInfoA", hmon, bytes(mu.mem_read(info, 4)))
        if c["monitor_ok"]:
            mu.mem_write(info + 4, struct.pack("<iiii", *c["monitor_rect"]))
        return c["monitor_ok"]

    fakes = common_fakes(c)
    fakes.update({
        "USER32.dll!SendMessageA": send,
        "USER32.dll!GetSystemMetrics": metrics,
        "USER32.dll!GetMonitorInfoA": monitor_info,
        "USER32.dll!RegisterRawInputDevices": lambda mu: (record(mu, "RegisterRawInputDevices",
                                                                 bytes(mu.mem_read(regs(mu)[0], 16)),
                                                                 regs(mu)[1] & 0xFFFFFFFF, regs(mu)[2] & 0xFFFFFFFF), 1)[1],
        "sub_141DAC020": lambda mu: record(mu, "sub_141DAC020"),
        "Dvar_SetInt": lambda mu: record(mu, "Dvar_SetInt", *[v & 0xFFFFFFFF for v in regs(mu)[1:3]], regs(mu)[0]),
        "sub_141DAC3E0": lambda mu: record(mu, "sub_141DAC3E0"),
        "sub_141DAB1C0": lambda mu: record(mu, "sub_141DAB1C0", model_box[0].objects.get(regs(mu)[0], (0, 0))[1]),
    })
    return fakes


def create_setup(c, model_box):
    def apply(w):
        def qi(call):
            if c["qi_hr"]:
                return c["qi_hr"]
            return call.out_object(1, UNK) and 0

        def parent(kind, key):
            def fn(call):
                if c[key]:
                    return c[key]
                return call.out_object(1, kind) and 0
            return fn

        def containing_output(call):
            if c["output"]:
                call.out_object(0, OUT)
            else:
                call.write(call.arg(0), struct.pack("<Q", 0))
            return 0 if c["output"] else 0x887A0002

        def output_desc(call):
            call.write(call.arg(0), bytes(0x40) + struct.pack("<iiiiII", 0, 0, 2560, 1440, 1, 0)
                       + struct.pack("<Q", c["hmonitor"]))
            return 0

        def fullscreen_state(call):
            call.write(call.arg(0), struct.pack("<I", c["is_fullscreen"]))
            return 0

        def create_buffer(call):
            if call.arg(2):
                call.write(call.arg(2), struct.pack("<Q", 0xB0F0_0000 + call.mu.reg_read(UC_X86_REG_RDX) % 0x1000))
            return 0

        model = ComModel(SIGS, {(DEV, QI): qi, (UNK, GET_PARENT): parent(ADP, "adapter_hr"),
                                (ADP, GET_PARENT): parent(FAC, "factory_hr"),
                                (SWC, 15 * 8): containing_output, (OUT, 7 * 8): output_desc,
                                (SWC, 11 * 8): fullscreen_state, (DEV, 3 * 8): create_buffer}, DUMPS)
        model.install(w.m)
        model_box[0] = model
        w.u64(syms.va("dx_device"), model.new(DEV))
        w.u64(syms.va("dx_context"), model.new(CTX))
        w.u64(syms.va("dx_swapChain"), model.new(SWC) if c["old_swapchain"] else 0)
        w.u64(syms.va("win_hWnd"), HWND)
        w.u64(syms.va("win_hRawInputWnd"), 0x0003_0099)
        w.u64(syms.va("r_backBufferCount"), BACKBUFFER_DVAR)
        w.u64(syms.va("r_fullscreen"), FULLSCREEN_DVAR)
        w.u32(syms.va("dx_monitorCount"), 1)
        w.u32(syms.va("dx_modeCount"), 0)
        for i in range(12):
            w.u64(syms.va("dx_constantBuffers") + 8 * i, 0xDEAD0000 + i)
        w.write(syms.va("dx_needVideoChange"), b"\x00")
        w.write(syms.va("dx_needFullscreen"), b"\x00")
    return apply


def create_inputs():
    r = random.Random(250)
    out = []
    for _ in range(240):
        fullscreen = r.choice([0, 1])
        c = {
            "qi_hr": r.choice([0] * 8 + [0x80004002]), "adapter_hr": r.choice([0] * 8 + [0x80004005]),
            "factory_hr": r.choice([0] * 8 + [0x80004005]), "create_hr": r.choice([0, 0, 1, 0x087A0001, 0x887A0001]),
            "old_swapchain": r.choice([0, 1]), "output": r.choice([0, 1, 1]), "hmonitor": r.choice([0, 0x10001]),
            "monitor_ok": r.choice([0, 1, 1]), "monitor_rect": r.choice([(0, 0, 2560, 1440), (-1920, 0, 0, 1080),
                                                                       (100, 50, 100, 50)]),
            "metrics": {0: r.choice([1920, 0, -5]), 1: r.choice([1080, 0])},
            "is_fullscreen": r.choice([0, 1]), "backbuffers": r.choice([2, 3]), "new_size": (1280, 720),
        }
        box = [None]
        out.append({"args": [parms_bytes(r, fullscreen)], "setup": create_setup(c, box),
                    "fakes": create_fakes(c, box)})
    return out


# ---- sub_141DAD0C0 --------------------------------------------------------------------------------------------

VIEWS = 0x6E
VIEW_SIZE = 0xAE0
TABLE = HEAP  # the first argument buffer


def resize_fakes(c, model_box):
    def peek(mu):
        msg, hwnd, lo, hi = regs(mu)
        record(mu, "PeekMessageA", hwnd, lo, hi, stack(mu, 4) & 0xFFFFFFFF)
        if c["queue"]:
            message = c["queue"][0]
            mu.mem_write(msg, struct.pack("<QII", 0, message, 0))
            return 1
        return 0

    def get(mu):
        msg = regs(mu)[0]
        message = c["queue"].pop(0)
        record(mu, "GetMessageA", *regs(mu)[1:])
        mu.mem_write(msg, struct.pack("<QII", 0, message, 0))
        return 0 if message == 0x12 else 1

    fakes = common_fakes(c)
    fakes.update({
        "sub_141DD3730": lambda mu: record(mu, "sub_141DD3730", regs(mu)[0], regs(mu)[1] & 0xFFFFFFFF),
        "sub_141DD2C80": lambda mu: record(mu, "sub_141DD2C80", regs(mu)[0] - TABLE, regs(mu)[1] & 0xFFFFFFFF),
        "sub_141DCA670": lambda mu: record(mu, "sub_141DCA670"),
        "USER32.dll!PeekMessageA": peek,
        "USER32.dll!GetMessageA": get,
        "USER32.dll!TranslateMessage": lambda mu: (record(mu, "TranslateMessage"), 0)[1],
        "USER32.dll!DispatchMessageA": lambda mu: (record(mu, "DispatchMessageA"), 0)[1],
        "KERNEL32.dll!SetEvent": lambda mu: (record(mu, "SetEvent", regs(mu)[0]), 1)[1],
        "sub_141DCDA90": lambda mu: record(mu, "sub_141DCDA90", *[v & 0xFFFFFFFF for v in regs(mu)],
                                           stack(mu, 4) & 0xFF, stack(mu, 5) & 0xFF),
        "sub_141DB5010": lambda mu: record(mu, "sub_141DB5010"),
        "sub_141DEBFA0": lambda mu: record(mu, "sub_141DEBFA0"),
        CALLBACK: lambda mu: record(mu, "callback", regs(mu)[0] & 0xFF),
    })
    return fakes


def resize_setup(c, model_box, queue):
    def apply(w):
        c["queue"] = list(queue)
        model = ComModel(SIGS, {}, DUMPS)
        model.install(w.m)
        model_box[0] = model
        w.u64(syms.va("dx_context"), model.new(CTX))
        w.u64(syms.va("dx_swapChain"), model.new(SWC) if c["swapchain"] else 0)
        w.u64(syms.va("dx_backBuffer"), model.new(UNK) if c["backbuffer"] else 0)
        w.u64(syms.va("dx_windowHwnd"), HWND if c["window"] else 0)
        w.u64(syms.va("gfx_renderTargetState"), TABLE)
        w.u64(syms.va("r_backBufferCount"), BACKBUFFER_DVAR)
        w.u32(syms.va("dx_monitorCount"), 0)
        w.u64(syms.va("sys_quitEvent"), 0x5EE0)
        w.u64(syms.va("dx_videoChangeCallback"), CALLBACK if c["callback"] else 0)
        for name, v in zip(("vidConfig_sceneWidth", "vidConfig_sceneHeight", "vidConfig_displayWidth",
                            "vidConfig_displayHeight"), c["vid"]):
            w.u32(syms.va(name), v)
    return apply


def table_bytes(r):
    t = bytearray(r.randbytes(VIEWS * VIEW_SIZE))
    for i in range(VIEWS):
        t[i * VIEW_SIZE + 0xA89] = r.choice([0, 0, 1])
        t[i * VIEW_SIZE + 0xAD8] = r.choice([0, 0x40, 0xBF, 0x41])
    t[0x20E8:0x20F0] = struct.pack("<Q", SCRATCH + 0x100)
    return bytes(t)


def resize_inputs():
    r = random.Random(0xD0C0)
    out = []
    for _ in range(60):
        c = {"swapchain": r.choice([1, 1, 1, 0]), "window": r.choice([1, 1, 1, 0]), "backbuffer": r.choice([0, 1]),
             "callback": r.choice([0, 1]), "vid": (1280, 720, *r.choice([(1280, 720), (1920, 1080)])),
             "backbuffers": r.choice([2, 3]), "new_size": r.choice([(1280, 720), (1920, 1080), (1280, 1080)])}
        queue = [r.choice([0x100, 0x200, 0x12, 0x8043]) for _ in range(r.randint(0, 3))]
        box = [None]

        def setup(w, c=c, box=box, queue=queue):
            resize_setup(c, box, queue)(w)
            w.write(SCRATCH + 0x100, struct.pack("<Q", 0x7777_0000_1234))
        out.append({"args": [table_bytes(r)], "setup": setup, "fakes": resize_fakes(c, box)})
    return out


CASES = [
    {"symbol": CREATE, "ret": "int", "inputs": create_inputs()},
    {"symbol": RESIZE, "ret": "void", "inputs": resize_inputs()},
]
