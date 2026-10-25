// Calling an original function so that it returns into the exe.
//
// Build environment, not game source. The game hides some global pointers (the cgame state cg at 149B25A20, cgs at
// 149B25A28, ...) behind an encoding that each user decodes with an inlined state machine keyed on the PEB's address
// (docs/fov.md, "Obfuscated pointers"). Those machines also look at the return address of the function they sit in:
// when it lies outside the exe (below 140000000 or above 160000000) and the bytes before it don't look like the
// exe's own call sites, their starting state changes, and for about half of the possible PEB addresses the machine
// then never reaches its end state: the call never returns. recon.dll is based at 180000000, so a reconstructed or
// enhanced function must not call such an original function (or a standalone decoder) directly.
//
// T7ExeCall(fn, args...) calls fn(args...) with an exe address as its return address: a call site in the
// exe that is followed by `add rsp, 28h; ret` (T7_EXE_RETURN). When fn returns there, that epilogue drops 28h bytes
// of the frame built below and returns to the real caller. At most five arguments (the fifth is copied into place;
// a sixth would overlap the real return address). The return value (RAX or XMM0) passes through untouched.
//
//     T7ExeCall(CG_CalcFOVfromLens, localClientNum, &fov, &tanHalfFov, &tanHalfFovX, &tanHalfFovY);
//     char *cgArray = T7ExeCall(sub_141406ED0);
#pragma once

// 140096EE3: call 140096E00; 140096EE8: add rsp, 28h; ret (inside 140096ED0). Store build only.
#define T7_EXE_RETURN 0x140096EE8ull

// t7_exe_call(a1, a2, a3, a4, a5, target): a1-a5 in their usual places (RCX/RDX/R8/R9 or XMM0-3, fifth on the
// stack at +28h), the target as a sixth argument at +30h. Frame for the target at S = entry - 30h:
//   [S] = T7_EXE_RETURN, [S+8..S+27h] home space, [S+28h] = a5, [S+30h] = our caller's return address.
static __attribute__((naked, unused)) void t7_exe_call()
{
	__asm__ volatile(
		"subq $0x30, %rsp\n\t"
		"movq 0x58(%rsp), %rax\n\t"
		"movq %rax, 0x28(%rsp)\n\t"
		"movq 0x60(%rsp), %rax\n\t"
		"movabsq $0x140096EE8, %r10\n\t"
		"movq %r10, (%rsp)\n\t"
		"jmpq *%rax\n\t");
}

// T7ExeCall(fn, args...): fn(args...) returning into the exe. Every argument list is padded to five (the padding is
// ignored by the callee), then the target is appended.
template <typename T> struct t7_same
{
	typedef T type;
};
typedef long long t7_pad;

template <typename R> R T7ExeCall(R (*fn)())
{
	return ((R(*)(t7_pad, t7_pad, t7_pad, t7_pad, t7_pad, void *))t7_exe_call)(0, 0, 0, 0, 0, (void *)fn);
}
template <typename R, typename A1> R T7ExeCall(R (*fn)(A1), typename t7_same<A1>::type a1)
{
	return ((R(*)(A1, t7_pad, t7_pad, t7_pad, t7_pad, void *))t7_exe_call)(a1, 0, 0, 0, 0, (void *)fn);
}
template <typename R, typename A1, typename A2>
R T7ExeCall(R (*fn)(A1, A2), typename t7_same<A1>::type a1, typename t7_same<A2>::type a2)
{
	return ((R(*)(A1, A2, t7_pad, t7_pad, t7_pad, void *))t7_exe_call)(a1, a2, 0, 0, 0, (void *)fn);
}
template <typename R, typename A1, typename A2, typename A3>
R T7ExeCall(R (*fn)(A1, A2, A3), typename t7_same<A1>::type a1, typename t7_same<A2>::type a2,
            typename t7_same<A3>::type a3)
{
	return ((R(*)(A1, A2, A3, t7_pad, t7_pad, void *))t7_exe_call)(a1, a2, a3, 0, 0, (void *)fn);
}
template <typename R, typename A1, typename A2, typename A3, typename A4>
R T7ExeCall(R (*fn)(A1, A2, A3, A4), typename t7_same<A1>::type a1, typename t7_same<A2>::type a2,
            typename t7_same<A3>::type a3, typename t7_same<A4>::type a4)
{
	return ((R(*)(A1, A2, A3, A4, t7_pad, void *))t7_exe_call)(a1, a2, a3, a4, 0, (void *)fn);
}
template <typename R, typename A1, typename A2, typename A3, typename A4, typename A5>
R T7ExeCall(R (*fn)(A1, A2, A3, A4, A5), typename t7_same<A1>::type a1, typename t7_same<A2>::type a2,
            typename t7_same<A3>::type a3, typename t7_same<A4>::type a4, typename t7_same<A5>::type a5)
{
	return ((R(*)(A1, A2, A3, A4, A5, void *))t7_exe_call)(a1, a2, a3, a4, a5, (void *)fn);
}
