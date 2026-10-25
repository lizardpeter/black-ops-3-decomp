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
   reversed infinite depth; probably the viewmodel's), znear +0x274, tanHalfFov +0x280. `141DD52B0` then derives
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

## Where the latch goes

**On the render thread, just before a scene is drawn** (the start of `141D46D30` / `141D50380` for that `viewInfo`):

1. Take the raw-input counts not yet consumed (the 64-bit counters from P0013; read them, don't take them, so the next
   game frame still applies the movement, as Rust-test does).
2. Turn them into a yaw and pitch change with the scale `CL_MouseMove` used last frame (sensitivity, m_yaw/m_pitch,
   ADS and FOV scale; stored by the enhanced `CL_MouseMove`). Clamp pitch the way the game does.
3. Rotate the view about its origin: recompute `viewInfo`'s view parms (the view matrix and everything
   `141DD52B0` derives from it) with the new axis. The origin stays put, so the BSP cell stays valid.

Things to get right, each to be checked before any code:

- **Which constants come from the view parms on the render thread.** The 0x1960-byte input block is filled on the
  main thread (141DDD1B0, 141DDDC20). If the camera matrices sit in that block already multiplied out, those have to
  be patched as well (or instead). This is the next thing to map: the reads of `viewInfo` +0x000..+0x290 and of the
  input block's matrices in the 141D4–141E0 render-thread code.
- **The viewmodel.** The gun is placed from the old view. If it is drawn with the second view×proj (+0x100), keeping
  +0x100 unrotated holds it fixed on screen while the world turns. If it is drawn with the world matrices, it would
  lag the turn and has to be moved with the camera.
- **Culling.** Surfaces were culled against the old frustum, so a late turn can show the edge of the screen missing
  geometry. Options: cull with a slightly wider frustum (a small FOV margin in step 5) or cap the late turn. Rust-test
  doesn't have BO3's portal culling, so this is new work.
- **Reprojection.** The previous-view copy (step 5) is saved from the unlatched parms. It has to save the latched
  ones, or TAA and motion blur see a false camera move. Because it is written on the main thread for the frame after,
  the latched parms need handing back.
- **Other views.** Scopes with picture-in-picture, extra cameras and splitscreen are separate scenes. Only the local
  player's main view should be latched.
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
