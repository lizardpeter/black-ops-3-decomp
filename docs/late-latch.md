# Late latch: the view path from the mouse to the GPU

How the Store build (`BlackOps3_MSStore`) carries the view from the mouse read to the frame the GPU draws, and where
an enhanced late latch would go. Rust-test does this (`src/native_windows_input.rs`, `peek_motion()`): just before the
render thread records the camera, it rereads the raw-input totals and turns the camera by the movement that arrived
after the game frame read the mouse. Gameplay still takes that movement on its next frame.

This is a map, not a change: nothing here is implemented yet. Addresses are the Store build's; the names are the IW
names for functions of the same shape. They go into `records/names.tsv` at confidence 0.5–0.6, and the rest are
`sub_`.

## The path

All of this runs on the main thread up to the hand-off; the render thread does the rest.

1. **Screen draw.** `Scr_UpdateScreen` (14148CF00) → `141485BF0` (the screen draw: per-client views, then UI) →
   `CL_CGameRendering` (141477550) for each local client in game.
2. **Mouse and usercmd.** `CG_DrawActiveFrame` (1411C01A0) calls `1413BFDE0` partway through: that runs `IN_Frame`
   (which takes the raw-input counts) and `1413BBF50`, the command step, where `CL_MouseMove` (1413AE730) adds the
   turn to `cl->viewangles` (clientActive +0xB8C8 pitch, +0xB8CC yaw) and the usercmd is made (docs/input.md). So in
   game, the mouse is read **inside the cgame draw**, not at the start of the frame.
3. **Prediction and view.** Further on in `CG_DrawActiveFrame`, prediction runs from the new usercmd (the predicted
   playerState is cg +0x11A8B0), and the view is written to the **refdef at cg +0x131CF0**: `tanHalfFovX/Y` at
   +0x78/+0x7C (the FOV code, docs/fov.md, writes them at cg +0x131D68), `vieworg` at +0x88, `viewaxis` (3×3) at
   +0xA4. The function that turns the predicted angles into the axis (IW `CG_CalcViewValues`) is not pinned yet. It is
   one of the calls between 1413BFDE0 and the next step.
4. **View parms.** `141DE3D00(refdef)` takes a 0x290-byte slot from the frontend data (`frontEndData` 1486C3A78,
   count at +0xF63A0) and fills it with `R_SetupViewParms` (141DE3510): origin +0x240 (w = 1), axis +0x250, view
   matrix +0x000 (from origin and axis, 1423899C0), projection +0x040 and a second projection +0x080 (same FOV,
   reversed infinite depth; no reader found on the render thread), znear +0x274, tanHalfFov +0x280. `141DD52B0` then derives
   view×proj +0x0C0, view×proj2 +0x100, inverse +0x140, an unjittered projection +0x180 with its products
   +0x1C0/+0x200 (the jitter is the subpixel offset for TAA and supersampling, 14A333F50/64/68). Finally
   `R_CellForPoint` (141D81B90) walks the BSP to the origin's cell (+0x288), which decides portal visibility.
5. **Scene.** The cgame then adds entities and effects (1406E82D0, the end of `CG_DrawActiveFrame`) and calls
   `CL_RenderScene` (1413C9540) → `141DE3D80` → **`R_RenderScene` (141DDF580)**. That takes a scene slot of 0xD5F60
   bytes (`viewInfo`, frontend data +0xF6570, index at +0xF6568) and copies the view parms to its start
   (`141DDD1B0`). It sets up the per-view constants and culls with the frustum from those matrices (141DDDC20 and the
   jobs it starts). After the scene, `141DE3D80` saves the view parms as this client's **previous view**
   (148705570 + client × 0x290), which the next frame reprojects from (motion vectors, TAA).
6. **Hand-off.** At the end of the screen draw, `141DCAFC0` (`R_EndFrame`) → `141DCAD40`:
   - It waits for the frame's jobs to finish (a `Sleep(0)` loop over the job counters).
   - It waits for the render thread to finish the previous frame (`R_SyncRenderThread`, 142253630, on event
     1598047C8).
   - It publishes the frontend data (1598046C0) and signals 1598048A8.
   - `R_BeginFrame` (141DCB3C0) then flips to the other frontend buffer (two of 0xF9760 bytes, 1546790B8) for the
     next frame.
7. **Render thread.** `RB_RenderThread` (141D47510) wakes on 1598048A8 and runs `141D470F0`:
   - It uploads the dynamic vertex and index buffers (141DC65F0).
   - It draws each scene: `141D46D30`, or `141D50380` when 1486BEEA0 is set. Each scene's backend state is
     initialised from the scene's input block (`141DF1770`, a 0x1960-byte copy from `viewInfo` +0x1430), and
     `141D8F430` binds its targets.
   - It draws the 2D pass (`141D46E40`), presents (`141D469A0` → `sub_141D46720`, docs/presentation.md) and signals
     1598047C8.

## Where the time goes

The render thread works **one frame behind** the main thread: while it draws frame N, the main thread builds N+1,
and the main thread waits for N only when it is ready to hand over N+1. So the view the GPU draws was fixed when step
3 ran. After that come the rest of the cgame, `R_RenderScene` and its jobs, the wait for the previous frame, and the
render thread's own work, all before the GPU starts. At a CPU-bound 300–500 fps that is roughly one main-thread frame
(2–3 ms) plus the render thread's time. A late latch would recover that time for the camera.

## How the camera reaches the shaders

All of this happens on the render thread, from the view parms at the start of each `viewInfo`:

- **During play, scenes draw through `141D4E220`.** It is reached from `141D46D30` once `1486BEEA0` is 2, which
  `141DAD840` sets when the renderer starts; 0 is only the state before that. `141D4E220` draws the scene's draw
  lists (`viewInfo` +0x1428) itself and through job callbacks such as `141D4ACB0`. Every one of them takes the
  `viewInfo` from the render thread.
- **`R_Set3D` (141DF1B10)** copies the 0x290 bytes of view parms from the `viewInfo` the backend state points at
  (state +0x22B0) into the state's own copy (state +0x1DF0). It sets the eye offset (state +0x22A0 and code constant
  0xC3) and bumps the view, projection and view×projection versions (state +0x228A/C/E). Every draw path calls it
  after storing the `viewInfo`: `141D50380`, `141DC80B0`, `141D66110`, `141D69720`, `141DEF950`, `141D45FA0` (the
  draw-list jobs). `R_Set2D` (141DF1950) is the same for the 2D pass, with an orthographic projection.
- **`R_GetCodeMatrix` (141DED4D0)** returns a code matrix to the shader-argument code (141DE8AF0). It derives the
  matrix again only when its version is behind, through **`R_DeriveCodeMatrix` (141DED140)**:
  - view: the copy's +0x000, made camera-relative with the eye offset;
  - projection: +0x040;
  - view×projection: +0x0C0, or view × projection in the backend's mode 2.
  
  The inverse and transposed forms come from those, in groups of four as in IW.
- **Post-process filters** take what they need from the view parms on the render thread too: tanHalfFov, inverse
  view and so on. They are set up by the functions in the table at 142ECB860 (0x50 bytes per entry: name, material,
  init, setup), for example "tmode" (141D68730) and "hot zone" (141D68880).

So **the camera matrices are not multiplied out on the main thread.** Rewriting the view parms at the start of a
`viewInfo` on the render thread, before its scene is drawn, reaches every 3D shader through `R_Set3D` and the
version counters. Nothing else needs patching for the camera itself. No reader of the second projection (+0x080/+0x100) turned up
in any of this, so the viewmodel doesn't get its own matrix from here.

What the main thread **does** derive from the view, and the latch has to handle:

| Derived on the main thread | Where | What a latch does with it |
| --- | --- | --- |
| Culling frustum and its matrices | `141E069A0` (from `R_RenderScene`) into `viewInfo` +0x1440..+0x1664, from the cull view (the camera, or the locked view when the lock-view dvar 1486BF618 is on) | Cull with a wider FOV so a late turn finds nothing missing. The engine already takes the cull view apart from the render view. |
| Motion-vector and TAA reprojection blocks | `141DDC6C0` (from 141DDDC20) writes two 0xF0-byte blocks at frontend +0xF9590/+0xF95A0 from the current and previous view parms; their pointers sit at `viewInfo` +0xB2718/+0xB2720 | Recompute on the render thread with the latched view, or the frame reprojects with the turn missing |
| Previous view | `141DE3D80`, after `R_RenderScene`, copies the unlatched view to 148705570 + client × 0x290 | Store the latched view there, so the next frame's reprojection starts from what was shown |

## Where the latch goes

**On the render thread, before the main view's scene is drawn**: at the start of `141D470F0`, for the main view's
`viewInfo`. The main view is the scene `R_RenderScene` made when called from `141DE3D80`, so its index can be
recorded there.

1. Take the raw-input counts not yet consumed (the 64-bit counters from P0013; read them, don't take them, so the next
   game frame still applies the movement, as Rust-test does).
2. Turn them into a yaw and pitch change with the scale `CL_MouseMove` used last frame (sensitivity, m_yaw/m_pitch,
   ADS and FOV scale; stored by the enhanced `CL_MouseMove`). Clamp pitch the way the game does.
3. Rotate the view about its origin: recompute `viewInfo`'s view parms (the view matrix and everything
   `141DD52B0` derives from it) with the new axis. The origin stays put, so the BSP cell stays valid.

Besides the three main-thread items in the table above:

- **The viewmodel (still open).** The gun is placed in the world from the unlatched view. If it is drawn with the
  same view matrix as the world (nothing above gives it its own), a late turn moves it on screen by the turn: the gun
  would trail the camera for a frame. The fix is to move the gun's models by the same rotation about the eye.
  Finding where its placement reaches the draw lists is the next piece to map.
- **Other views.** Scopes with picture-in-picture, extra cameras (`141DE4020`) and splitscreen are separate scenes.
  Only the local player's main view is latched.
- **Shadows and sun cascades** are fitted to the old view. A small turn doesn't matter, so they stay as they are.

## Later: Reflex and Vulkan

The same map gives the points NVIDIA Reflex needs. The game already loads NvAPI (for SLI), and on D3D11 Reflex is
NvAPI's `NvAPI_D3D_SetSleepMode`, `NvAPI_D3D_Sleep` and `NvAPI_D3D_SetLatencyMarker`.

| Reflex call or marker | Where |
| --- | --- |
| `Sleep` | Where the frame-latency wait is now (P0020, before the second event loop) |
| `SIMULATION_START` | Start of `Com_Frame` |
| `INPUT_SAMPLE` | `IN_Frame` from 1413BFDE0 (and the latch, once it exists) |
| `RENDERSUBMIT_START` / `_END` | Around 141D470F0 |
| `PRESENT_START` / `_END` | Around the `Present` in 141D46720 |

A Vulkan backend would replace the D3D11 layer under the render thread (the device, the swap chain and steps 6–7).
Reflex then moves to `VK_NV_low_latency2`. The frontend map above stays the same.
