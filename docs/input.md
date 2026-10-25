# Input

How the Store build (`BlackOps3_MSStore`) gets the mouse and keyboard to the game, what is wrong with it, and what
the enhanced build changes. Addresses are the Store build's; names and evidence in `records/names.tsv`. Ghosts'
version of this work is `ghosts-decomp` docs/input.md (P0001, P0009 there); BO3 starts from a different place.

## Threads

BO3 runs input on two threads of its own, both started by the window setup (141DAB970) with Sys_CreateThread
(142253520):

- **The window thread** (`sub_1423F49B0`, index 0x15) creates the game window ("CoDBlackOps", `win_hWnd`) and runs
  its message loop: `PeekMessageA(hWnd, PM_REMOVE | PM_NOYIELD)`, `TranslateMessage`, `DispatchMessageA` for everything
  waiting, then **`Sleep(1)`**, then the cursor's show count, then again. The window procedure (1423F3CE0) therefore
  runs here: keys, mouse buttons and the wheel are turned into events (Sys_QueEvent 1423BF210, a 256-entry ring under
  lock 0x31) that the main thread's Com_EventLoop (142212190, through Sys_GetEvent 1423BF460) hands to the client.
  The renderer's messages run here too: the render thread `SendMessageA`s the window 0x8042 (create the swap chain),
  0x8043 (Present) and 0x8044 (fullscreen state), and a sent message waits until this thread next looks at its queue.
- **The raw input thread** (`sub_1423F4B70`, index 0x16) creates a message-only window ("CoDBlackOpsInputs",
  `win_hRawInputWnd`). The window setup (141DAB250) registers the mouse (usage page 1, usage 2) to it with
  `RIDEV_INPUTSINK`, so raw reports arrive whichever window is in front. The thread reads every waiting report with
  `GetRawInputBuffer`, adds `lLastX`/`lLastY` to two 32-bit counters (`win_rawMouseDx`/`Dy`, lock cmpxchg), then
  **`Sleep(1)`**, then again.

`timeBeginPeriod(1)` is called at start-up (1423BF710), so each `Sleep(1)` is about a millisecond.

## The mouse

BO3 already aims with raw device counts: no Windows pointer speed or acceleration, nothing lost between frames (the
Ghosts problem P0001 fixed there does not exist here). Once a frame, IN_Frame (1423BDB70) calls IN_MouseMove
(1423BD4C0), which:

1. returns at once if the system is suspended (`win_suspended`, WM_POWERBROADCAST) or another window is in front;
2. in exclusive fullscreen (`r_fullscreen 1`) moves the cursor back inside the window if it left it;
3. takes both counters with `xchg`;
4. if there was movement, switches the client's input device to keyboard and mouse (with a 200 ms hysteresis and a
   notification, 1422081C0 / 141720810);
5. calls CL_MouseEvent (1413AC9E0) with the cursor position in the window and the counts, and recentres the cursor if
   the game took the movement.

Then CL_GetMouseMovement (1413ACBD0), the sensitivity scaling (1413ACDF0) and CL_MouseMove (1413AE730) turn the counts
into view angles (sensitivity work, not covered here).

What's wrong:

- **B0040** Movement made while the game is not in front is counted and lands on the view when it comes back.
  `RIDEV_INPUTSINK` keeps the raw input thread counting in the background, IN_MouseMove returns without taking the
  counts while another window is in front, and IN_Frame does not call it at all while the window is inactive; the
  first frame back takes everything at once.
- **B0041** The raw input thread polls: a report waits up to about a millisecond (one `Sleep(1)`) before it is
  counted, so a frame can read the mouse as it was up to a millisecond earlier.
- **B0042** Absolute reports (`MOUSE_MOVE_ABSOLUTE`: tablets, remote desktop, some virtual machines) are added as if
  they were movement: their `lLastX`/`lLastY` are screen positions (0-65535), so the view spins.
- The counters are 32-bit and wrap (not a practical problem at frame rates; the enhanced build uses 64 bits anyway).

## Keys and buttons

- **B0043** The window thread polls too: a key or button press waits up to about a millisecond before the window
  procedure queues it, and every message the render thread sends (each Present) waits for the window thread to wake
  from its `Sleep(1)` before it can run. That adds up to a millisecond to every Present and makes the render thread's
  frame time uneven.

## Enhanced build

- **P0013** (`enhanced/win32/win_input.cpp`, B0040-B0042): the raw input thread waits for raw input
  (`MsgWaitForMultipleObjectsEx(QS_RAWINPUT, MWMO_INPUTAVAILABLE)`, 10 ms timeout only for the shutdown handshake)
  and reads each report as soon as Windows has it; it counts relative mouse reports only, in 64-bit counters, and only
  while the game window is in front. IN_MouseMove takes the counts every frame (clamped to int) and throws them away
  when the game isn't in front or the system is suspended; otherwise it is the original, call for call.
- **P0014** (`enhanced/win32/win_input.cpp`, B0043): the window thread waits for messages
  (`MsgWaitForMultipleObjectsEx(QS_ALLINPUT)`, 1 ms timeout, so the cursor and quit checks keep the original's
  cadence): input and the renderer's sent messages are handled as soon as they arrive. Otherwise it is the original,
  call for call.

`MsgWaitForMultipleObjectsEx` is not imported by the exe; each thread looks it up in user32 when it starts and falls
back to the original `Sleep(1)` without it. Tests: `tests/enhanced/test_raw_input.py`; the faithful functions'
differential tests are `tests/differential/test_win_input.py`.

These take effect once the reconstruction is hosted in the running game (docs/native-launch.md).

## Late input (Ghosts P0009): not done yet

Ghosts hands keys and mouse buttons pressed during the frame wait to the same frame's usercmd. In BO3 the pieces are
different, and doing it safely needs work that isn't done:

- **Where the frame waits.** Com_Frame is 1422174C0. It runs Com_EventLoop (142212190) early (1422175C8), the client
  frame 141402E70 (which calls IN_Frame unless the command step already did, flag 149BB4724) at 142217CE3, Com_EventLoop
  again at 142217CEF, and the command step 141403040 -> 1413BFDE0 (IN_Frame, then 1413BBF50: CL_GetMouseMovement and
  the usercmd, 1413B9EE0) at 142217DD4. Its `Sleep` calls (142217613, 142217922, 142217972, 142217ECB) are the
  candidates for the com_maxfps wait; which one, and where the main thread waits for the render thread, is not
  established. The presentation work (flip model, frame-latency waitable) is about to move that wait, so the late
  pump should be placed after it is settled.
- **What to drain.** In BO3 the window procedure already runs on its own thread (and with P0014 without delay), so
  "pumping messages again" means draining Sys_GetEvent's queue again just before the usercmd is built, with
  Com_EventLoop's dispatch (CL key handling 1413EA6C0, char events 1413EFC50, console text 1413E6580).
- **What is safe mid-frame.** As in Ghosts, only events whose handlers don't run console commands, cgame or LUI calls
  that the rest of the frame doesn't expect (Escape, console, chat, the weapon/equipment/menu binds...). That needs
  the key-binding table and the key catchers (client flags 1440E38F4: 1, 8, 0x10 and 0x20 are tested by
  Com_EventLoop) decompiled and named.
