# Late latch: the view path from the mouse to the GPU

How the Store build (`BlackOps3_MSStore`) carries the view from the mouse read to the frame the GPU draws, and where
an enhanced late latch would go. Rust-test does this (`src/native_windows_input.rs`, `peek_motion()`): just before the
render thread records the camera, it rereads the raw-input totals and turns the camera by the movement that arrived
after the game frame read the mouse. Gameplay still takes that movement on its next frame.

The enhanced build does it too: P0021, described under "The latch" below. It has run in the emulator only, not yet
in the game. Addresses are the Store build's; the names are the IW names for functions of the same shape. They are in
`records/names.tsv` at confidence 0.5–0.6, and the rest are `sub_`.

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
  - view×projection: +0x0C0 moved by the eye offset; view × projection when +0x22B8 is 0x40000000; the view without
    its translation × projection in camera-relative mode 1.
  
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

## The latch (P0021)

`enhanced/gfx_d3d/r_late_latch.cpp` holds it; the overrides it hooks into are listed in `records/patches.tsv` P0021.
The faithful versions of the hooked functions are in `src/` with differential tests: `CL_RenderScene`
(src/client/cl_cgame.cpp), `141D46D30` (src/gfx_d3d/rb_backend.cpp), and `R_GetCodeMatrix`/`R_DeriveCodeMatrix`
(src/gfx_d3d/r_state.cpp, bit-exact).

**Main thread, in `CL_RenderScene`** (just before and after the main view's `R_RenderScene`), per frontend buffer:

- It decides whether the view follows the mouse:
  - `CL_MouseMove` notes each frame whether a count turned the view by the plain scale: mouse look on, no strafe, no
    turn cap (cl +0xB7D0/+0xB7D4, or the limited mode).
  - The view's yaw and pitch must have turned with the client's angles (cl +0xB8C8/+0xB8CC) the last time those
    moved. That rules out killcams, vehicles and scripted cameras.
  - There must be one local client and `r_lateLatch` (new, default 1) must be on.
- If so, it notes:
  - the mouse counts the frame took (running totals kept by the raw input thread, `IN_RawMouseTotals`);
  - the degrees per count (`m_yaw`/`m_pitch` × sensitivity × 0.0066/0.022; yaw negated, since the view turns left
    for positive yaw);
  - the refdef fields the reprojection reads (+0x24, +0x38, +0x74, +0x1A681C);
  - the previous view this frame's reprojection uses (148705570 + client × 0x290, copied before `R_RenderScene`
    replaces it).
- It hands `R_RenderScene` a **cull view widened by a margin** at every edge: 1 degree plus 1.5 × the last latch's
  turn, at most 8. A late turn up to the margin then finds nothing culled at the screen's edges.
- After `R_RenderScene`, it notes the `viewInfo` of the scene that was made: the index read from 14A333F74
  beforehand, if frontend +0xF6568 and +0xF656C agree.

**Render thread, at the start of `141D46D30`** (before any scene is drawn):

1. The turn is (counts read now − counts the frame took) × degrees per count, at most the margin each way. The counts
   stay with the game, as in Rust-test: the next frame takes them as usual.
2. The view's axis is turned by that much: yaw about the world's up, pitch about its own right, roll kept, pitch
   stopped at 85 degrees.
3. Its view parms are made again: `MatrixForViewer` and every product, exactly as `R_SetupViewParms` would make
   them from that axis (the test checks this byte for byte). They are copied to the view's slot too.
4. The reprojection blocks are made again by the game's own `141DDC6C0`, from the turned view and the noted previous
   view. In AA modes 4 and 5 that function jitters by the parity of the frame the main thread is filling, which is
   now the next one. The frame's own jitter is put back: a column shift of half a pixel each way.
5. The previous view the next frame starts from is replaced by the turned one, unless the main thread has already
   moved past this frame.

**The gun.** It is placed in the world on the main thread, from the view before the turn, so drawing it with the
turned view would make it trail the turn for a frame. But it is drawn apart from the world:
- **Placement.** `CG_AddViewWeapon` (14126DD20) places it in `14126D750` from the view-model axis and origin (cg
  +0x2E7514/+0x2E7538), `cg_gun_x/y/z` and the FOV compensation from `cg_fov`. It is added through `14126B900` →
  `141269850` → `R_AddDObjToScene` (141DE5460) with render flags 0x40000001.
- **Sort key.** Bit 30 of those flags goes into its surfaces' sort key (`141D77770`).
- **Drawing.** Every pass that draws the gun's lists switches the backend into view-model mode (+0x22B8 = 1) around
  them. It does that in `141D4AB30` for list 0, with the depth range [0.984375, 1] (reversed Z), and through
  `141DF18A0` and its siblings in the other passes. The switch bumps the projection and view×projection versions.

So the enhanced `R_DeriveCodeMatrix` derives from the view as the frame made it while a latched `viewInfo` is drawn
in view-model mode. The view matrix's version isn't bumped by the switch, so the enhanced `R_GetCodeMatrix` flips its
top bit while in that mode, and the view is made again on the way in and on the way out. The gun lands exactly where
the game put it. That view-model mode means only the gun rests on the flags and the depth range; it is the first
thing to check in the game.

**Not handled:**
- Scopes with picture-in-picture, extra cameras (`141DE4020`) and split screen are separate scenes and keep their
  views.
- Shadows and sun cascades stay fitted to the view before the turn; a turn within the margin doesn't change them
  visibly.
- The wider cull view may cost a little more drawing. Any LOD that reads its field of view sees the wider one.

## Later: Reflex and Vulkan

The same map gives the points NVIDIA Reflex needs. The game already loads NvAPI (for SLI), and on D3D11 Reflex is
NvAPI's `NvAPI_D3D_SetSleepMode`, `NvAPI_D3D_Sleep` and `NvAPI_D3D_SetLatencyMarker`.

| Reflex call or marker | Where |
| --- | --- |
| `Sleep` | Where the frame-latency wait is now (P0020, before the second event loop) |
| `SIMULATION_START` | Start of `Com_Frame` |
| `INPUT_SAMPLE` | `IN_Frame` from 1413BFDE0, and the latch at the start of 141D46D30 |
| `RENDERSUBMIT_START` / `_END` | Around 141D470F0 |
| `PRESENT_START` / `_END` | Around the `Present` in 141D46720 |

A Vulkan backend would replace the D3D11 layer under the render thread (the device, the swap chain and steps 6–7).
Reflex then moves to `VK_NV_low_latency2`. The frontend map above stays the same.
