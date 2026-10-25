# Presentation

How the Store build (`BlackOps3_MSStore`) makes its swap chain and presents frames, what that costs in latency, and
what the enhanced build changes (P0017-P0019, ported from ghosts-decomp's P0003/P0004 and adapted). Addresses are
the Store build's; names in `records/names.tsv`.

## The original

**Creation** (`sub_141DAB250`, src/gfx_d3d/r_init.cpp). From the D3D11 device it takes `IDXGIDevice1`, its adapter
(`IDXGIAdapter1`) and that adapter's `IDXGIFactory1`. `sub_141DA7A00` fills a `DXGI_SWAP_CHAIN_DESC` from the window
parameters: **`DXGI_SWAP_EFFECT_DISCARD`** (the blit model), `Windowed` 1, flags `ALLOW_MODE_SWITCH`, buffer count
`r_backBufferCount`. The swap chain is not created here: the function `SendMessageA(win_hWnd, 0x8042, factory,
&desc)`s the window thread, whose window procedure calls `IDXGIFactory::CreateSwapChain` into `dx_swapChain`. Then
`MakeWindowAssociation(hwnd, 7)` (no Alt+Enter, no window-change handling by DXGI), the interfaces are released, the
monitor's size is noted, fullscreen is entered (`sub_141DAC020`, again by message: 0x8044 → `SetFullscreenState`),
twelve dynamic constant buffers are made and the raw-input window registers the mouse. When anything before the
message fails, it returns without releasing what it holds (B0034); when creation fails, `r_fullscreen` is set to 0
and a windowed retry is requested.

**Resize** (`sub_141DAD0C0`). Unbinds the render-target views, releases the back buffer, pumps messages, then
`ResizeBuffers(count, w, h, format, 2)`: the flags are always `ALLOW_MODE_SWITCH`.

**Present** (`sub_141D46720`, src/gfx_d3d/r_present.cpp), reached from `141D469A0` on the render thread and from the
main-thread path:

1. With NvAPI and more than one GPU, under the D3D context lock, `NvAPI_D3D_GetCurrentSLIState`: a repeated AFR index
   sets `dx_afrIndexRepeated`. The index is stored even when the call failed (an uninitialised stack value, B0033).
2. With `r_vsync`, an AMD adapter (`dx_vendor` 2) **and `dx_remoteScreenUpdateNesting` nonzero**, it sleeps
   `trunc(1000 / r_refreshRate) - 2` ms. The nesting count is nonzero only while a loading screen is drawn from its own
   thread, so this pacer never runs in play. The ledger's earlier reading (every AMD present, B0015) was corrected
   after decompiling.
3. `SendMessageA(win_hWnd, 0x8043, r_vsync, 0)`: the window procedure calls `IDXGISwapChain::Present(vsync, 0)` and
   returns its HRESULT (B0031).
4. A failure is reported with `Com_Error` (`DXGI_ERROR_DEVICE_REMOVED` with its reason, or `DEVICE_RESET`).
5. 3D Vision: if stereo is active, the convergence is set from `r_convergence`.

**Input.** `IN_Frame` (1423BDB70, src/win32/win_input.cpp) reads the mouse once a frame: in game from 1413BFDE0
right before the usercmd is made, otherwise from 141402E70. Nothing before it waits for the display (B0032). The
device's maximum frame latency is `r_maxFrameLatency` (default 1, raised to the GPU count with AFR; set by
141DAA790), but that only limits the GPU queue: with the blit model, the desktop compositor adds its own frame.

### What it costs

- **Blit model** (B0030): in a window or borderless, the compositor copies each frame into the desktop, adding
  about a frame and ruling out independent flip. With `r_vsync 0` a window cannot tear, so the game is held to the
  desktop's rate with compositor queueing.
- **Present by message** (B0031): every present needs the window thread to take the message. Before P0014 that
  thread slept 1 ms between passes (B0043), so each present waited up to a millisecond. With P0014 it waits on
  `MsgWaitForMultipleObjectsEx` and wakes at once, but the present still costs two thread switches. During a vsync
  `Present` (which can block for most of a refresh) the window thread is busy inside it and cannot pump keyboard and
  mouse messages. Presenting from the thread that finished the frame removes both costs. It is safe because swap
  chain creation, resize and fullscreen switches still go through the window thread, and the window thread keeps
  pumping (P0014), which DXGI needs when a present on another thread changes fullscreen state.
- **No wait before input** (B0032): with vsync on, or when the GPU is the bottleneck, the main thread samples the
  mouse as soon as it can, and the frame waits in the queue. Input reaches the screen as old as the queue is deep.

## The enhanced build

**P0017: flip model and tearing** (enhanced/gfx_d3d/r_init.cpp, `R_CreateSwapChain`). The original description, with
`DXGI_SWAP_EFFECT_FLIP_DISCARD` and the flags `FRAME_LATENCY_WAITABLE_OBJECT`, plus `ALLOW_TEARING` when
`IDXGIFactory5::CheckFeatureSupport(PRESENT_ALLOW_TEARING)` says yes. It is still sent to the window thread (0x8042).
Fallbacks:

- if the swap chain is refused, the same again without the waitable flag (a defensive retry: FLIP_DISCARD itself needs Windows 10, which supports the flag, but
  wrappers and overlays sometimes reject it);
- if that is refused too, the original description, and everything else stays original.

The buffer count stays `r_backBufferCount` (flip model needs at least 2; the default is 2). `ResizeBuffers` now
passes the flags the swap chain was made with, because the fixed 2 would be refused for a waitable or tearing swap
chain. In the present, `r_vsync 0` outside exclusive fullscreen (`GetFullscreenState`) presents with
`DXGI_PRESENT_ALLOW_TEARING`, so a borderless window runs uncapped or with VRR.

**P0018: frame-latency wait** (enhanced/gfx_d3d/r_init.cpp; the wait in `sub_1413ED0D0`, enhanced/client/cl_keys.cpp,
since P0020). After
creation, `IDXGISwapChain2::SetMaximumFrameLatency` gets the latency the original gives the device. That is
`r_maxFrameLatency`, default 1, raised to the GPU count if lower. It is not set for 0, which keeps DXGI's default.
The swap chain's waitable object is kept. The wait follows ghosts-decomp's scheme:

- each successful present is counted;
- the frame first waits once for every present counted since its last wait, so keys, the mouse and the usercmd are
  taken only when the display has room for the frame;
- the timeout is two refresh periods at `r_refreshRate`, clamped to 50 ms – 1 s; a timeout drains the pending
  signals on the next frame and starts counting again;
- frames that were never presented are never waited for;
- a replaced swap chain closes the old object.

**Where.** First in `IN_Frame`, the last thing before the mouse is sampled. That left keys pressed during the wait
for the next frame, since the frame's event loop runs before the draw that samples the mouse. P0020 moved the wait
to `sub_1413ED0D0`, just before that event loop: docs/input.md, "Keys after the frame wait".

**P0019: direct present** (enhanced/gfx_d3d/r_present.cpp, `R_PresentFlip`). With a flip-model swap chain, the
thread that finished the frame calls `Present` itself, under the D3D context lock its callers hold. The sync
interval is 1 for `r_vsync` and 0 otherwise. Around the call:

- flip model unbinds the back buffer at `Present`, so the eight render targets and the depth-stencil view bound
  before it are bound again after it, which is what the renderer's state cache believes;
- the AMD loading-screen sleep is dropped, because the frame-latency wait paces frames.

Without flip model, the present is the original. The SLI check, the error report and 3D Vision are unchanged.

## Tests

- tests/differential/test_r_present.py (300 cases), test_r_swapchain.py (creation 240, resize 60) and
  test_in_frame.py (240): the faithful functions against the original, with COM modelled by tests/differential/com.py.
- tests/enhanced/test_present.py checks that each patched function behaves like the original on the same inputs,
  except for the intended changes:
  - **creation:** flip description, tearing exactly when supported, the two fallbacks, and the waitable object and
    latency;
  - **present:** direct `Present`, sync interval, the tearing flag only when windowed with vsync off, render targets
    re-bound and released, counting only on success;
  - **resize:** the flags passed to `ResizeBuffers`;
  - **frame wait:** waits per counted present, timeouts, resync, and a replaced swap chain.

## Open questions

- Nothing here has run on hardware. The tests check the calls made, not what DXGI does with them.
- Flip model also unbinds the back buffer when it is bound as a shader resource. Only render targets and the
  depth-stencil view are re-bound. If the renderer's state cache believes the back buffer's SRV is still bound, it
  needs the same treatment.
- Exclusive fullscreen with flip model relies on DXGI's own handling (Windows 10 promotes a borderless flip-model
  window to independent flip anyway). `ALLOW_MODE_SWITCH` is kept in the flags.
