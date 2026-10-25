# Mouse sensitivity

How the Store build (`BlackOps3_MSStore`) turns mouse counts into view angles, and what the enhanced build changes.
Raw-input collection (the thread that reads the mouse) is in docs/input.md.

## Original

1. **Counts.** The raw-input thread adds device counts; IN_MouseMove (1423BD4C0) hands them to `CL_MouseEvent`
   (1413AC9E0), which stores them in `cl_mouseDx/Dy[cl_mouseIndex]`.
2. **`CL_GetMouseMovement`** (1413ACBD0) takes them each command: `m_filter` halves them (B0017), `m_mouseFilter` > 0
   averages the last eight frames with weights (m_mouseFilter / 20)^i; the result is kept in `s_lastMouseX/Y`.
3. **`sub_1413ACDF0`** scales the last movement:

   `scale = (m_mouseSensitivity + m_mouseAcceleration × speed) × (adsSens × adsFraction + 1 − adsFraction) × tanY / 0.47780272`

   - `speed`: counts per millisecond of client frame (integer frame time, B0018);
   - `adsSens`: the weapon's ADS sensitivity (`sub_1427D0FC0`, attachments override), blended in by the ADS fraction;
   - `tanY`: tan of the current vertical half-FOV (cg_t + 0x131D6C, from `CG_CalcFOVfromLens`); 0.47780272 is that
     tangent for the default `cg_fov` 65 (horizontal at 4:3, Hor+). So sensitivity follows the FOV, hip fire
     included (B0016): ×1.317 at `cg_fov` 80, ×1.570 at 90, ×2.242 at 110.
4. **`CL_MouseMove`** (1413AE730): yaw −= `m_yaw` × scaled X, pitch += `m_pitch` × scaled Y (with the cgame's yaw and
   pitch speed caps), or strafe/forward with `m_side`/`m_forward`; then aim assist.

Defaults: `m_mouseSensitivity` 2 (0.1–30), `m_yaw` = `m_pitch` = 0.022. At `cg_fov` 65 hip fire one count turns
2 × 0.022 = 0.044 degrees. No m_ dvar is archived; config.ini saves the menu's (MouseSensitivity →
`m_mouseSensitivity`, MouseVerticalSensitivity → `m_pitch`, MouseAcceleration, MouseFilter).

## Enhanced build (P0011)

One count turns the view by **`m_mouseSensitivity` × 0.0066 degrees**, MW2019's unit, in hip fire and ADS, at any
FOV, zoom and speed. `m_mouseSensitivity` defaults to 1.5 (about 29 cm per 360° at 3200 DPI) and takes 0.01–100;
the menu and config.ini set it as before.

- `CL_GetMouseMovement` returns plain counts (no `m_filter`, no `m_mouseFilter`).
- `sub_1413ACDF0` returns counts × `m_mouseSensitivity` × 0.0066 / 0.022: no FOV tangent, no weapon ADS sensitivity,
  no acceleration.
- `CL_MouseMove` is unchanged. It still multiplies by `m_yaw` and `m_pitch`, so at their default 0.022 the rate is
  exact; the menu's vertical sensitivity (`m_pitch`) stays a vertical multiplier and a negative `m_pitch` still
  inverts.

Converting an old setting: old `m_mouseSensitivity` s at `cg_fov` f (hip fire) turned 0.022 × s × k(f) degrees a
count, k from step 3 (k(65) = 1); the same feel in MW2019 units is s × k(f) × 0.022 / 0.0066 = **3.33 × s × k(f)**
(default 2 at `cg_fov` 65 → 6.67).

Tests: tests/differential/test_cl_input.py (the three faithful functions), tests/enhanced/test_sensitivity.py.

## Not done yet

- **Double-precision view angles.** Ghosts' P0002 keeps the angles in double precision across frames. Here
  `CL_MouseMove` still adds in single precision; that needs `CL_MouseMove` decompiled.
- The location-selection cursor (1413B3110) also reads `m_mouseSensitivity`, so its speed changes with the new units.
