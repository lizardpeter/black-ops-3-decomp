// P0009: r_refreshRate accepts up to 1000 Hz (B0012). P0021: registers r_lateLatch (docs/late-latch.md).
//
// The original registers r_refreshRate with the domain [1, 240]. Dvar_SetVariant rejects anything outside a dvar's
// domain and keeps the old value, so on a monitor faster than 240 Hz: the first-run hardware detection (141DA9620)
// tries to set the fastest mode's rate and is refused (the default, 60, stays); choosing a faster rate in the menu or
// the console is refused too; and the swap chain (141DA7A00) then picks the mode closest to at most 240. Display-mode
// enumeration has no limit of its own and com_maxfps already goes to 1000, so the domain is the only cap. The enhanced
// build allows up to 1000 Hz, com_maxfps's own ceiling; the default and everything else this function registers
// are unchanged. docs/refresh-rate.md.

#include "universal/dvar.h"
#include "gfx_d3d/r_dvars.h"
#include "r_late_latch.h"

#define T7_SOURCE "gfx_d3d/r_dvars.cpp"
#include <t7_static.h>

T7_STATIC const dvar_t *s_developer T7_AT("", "s_developer");
T7_STATIC const dvar_t *s_sv_cheats T7_AT("", "s_sv_cheats");
T7_STATIC const char *s_debugShowNames[] T7_AT("", "s_debugShowNames");
T7_STATIC const char *s_sizeNames[] T7_AT("", "s_sizeNames");

// 141D976E0  gfx_d3d/r_dvars.cpp
void sub_141D976E0()
{
	r_exposureTweak = Dvar_RegisterBool(0x0488B535, "", false, 0x40, "", false);
	r_exposureValue = Dvar_RegisterFloat(0x9E388F86, "", 3.0f, -32.0f, 31.0f, 0x40, "", false);
	r_exposureEyeWeight = Dvar_RegisterFloat(0xDBE3190E, "", 0.5f, 0.0f, 1.0f, 0x40, "", false);
	Dvar_RegisterVec3(0xADC8196C, "", 0.0f, 0.0f, 0.0f, -5.0f, 5.0f, 0x40, "", false);  // r_finalShiftX
	Dvar_RegisterVec3(0xD3CA93D5, "", 0.0f, 0.0f, 0.0f, -5.0f, 5.0f, 0x40, "", false);  // r_finalShiftY
	Dvar_RegisterBool(0x15730EA4, "", false, 0x100, "", false);  // r_primaryLightUseTweaks
	Dvar_RegisterFloat(0x24674DDB, "", 1.0f, 0.0f, 10.0f, 0x100, "", false);  // r_primaryLightTweakDiffuseStrength
	Dvar_RegisterFloat(0xFBC093DE, "", 1.0f, 0.0f, 10.0f, 0x100, "", false);  // r_primaryLightTweakSpecularStrength
	r_num_viewports = Dvar_RegisterInt(0x42AC6A90, "", 0, 0, 4, 0x0, "", false);
	s_developer = Dvar_RegisterInt(0x3C109F4D, "", 0, 0, 2, 0x0, "", false);
	s_sv_cheats = Dvar_RegisterBool(0xF70E34E1, "", false, 0x24, "", false);
	r_monitor = Dvar_RegisterInt(0x5FE4031A, "", 0, 0, 8, 0x10, "", false);
	r_currentMonitor = Dvar_RegisterInt(0x383BE173, "", 0, 0, 8, 0x0, "", false);
	r_monitorCount = Dvar_RegisterInt(0x69CBE7A7, "", 0, 0, 8, 0x0, "", false);
	r_mode = Dvar_RegisterString(0x236AF761, "", "800x600", 0x10, "", false);
	r_refreshRate = Dvar_RegisterFloat(0x3727533B, "", 60.0f, 1.0f, 1000.0f, 0x10, "", false);  // P0009: was 240
	r_sceneResolutionMultiplier = Dvar_RegisterInt(0xBB27457F, "", 100, 50, 200, 0x10, "", false);
	r_videoMemoryMultiplier = Dvar_RegisterFloat(0x7EF0C871, "", 1.0f, 0.75f, 1.0f, 0x0, "", false);
	dvar_EBC13010 = Dvar_RegisterFloat(0xEBC13010, "", 0.0f, 0.0f, 1.0f, 0x0, "", false);
	r_cmdlistChain = Dvar_RegisterBool(0x531063B3, "", true, 0x0, "", false);
	r_grassEnable = Dvar_RegisterBool(0x5FB22163, "", true, 0x0, "", false);
	Dvar_RegisterInt(0x695C2335, "", 0, 0, 2, 0x0, "", false);  // r_takeScreenShot
	r_skyTransition = Dvar_RegisterFloat(0x57DE83E6, "", 0.0f, 0.0f, 1.0f, 0x40, "", false);
	r_skyRotation = Dvar_RegisterFloat(0x42C821AD, "", 0.0f, -360.0f, 360.0f, 0x40, "", false);
	Dvar_RegisterBool(0xB3220890, "", false, 0x40, "", false);  // r_enableCubicUpsample
	Dvar_RegisterFloat(0x6B423062, "", -0.5f, -1.0f, 1.0f, 0x40, "", false);  // r_cubicUpsampleParam
	Dvar_RegisterInt(0x18DEC138, "", 0, 0, 32, 0x40, "", false);  // r_skyBoxColorIDX
	Dvar_RegisterInt(0x2106C1D2, "", 0, 0, 2, 0x100, "", false);  // r_blinkForwardSSS
	Dvar_RegisterInt(0x1A204438, "", 0, 0, 2, 0x100, "", false);  // r_blinkTrans
	Dvar_RegisterInt(0xA8BE071C, "", 0, 0, 2, 0x100, "", false);  // r_blinkCullNone
	r_sortDrawSurfsBsp = Dvar_RegisterBool(0x69DAC11C, "", false, 0x100, "", false);
	r_sortDrawSurfsStaticModel = Dvar_RegisterBool(0x2738B26E, "", true, 0x100, "", false);
	Dvar_RegisterBool(0xA8DFDF97, "", true, 0x100, "", false);  // r_sortBackToFront
	Dvar_RegisterEnum(0x94D6B133, "", s_debugShowNames, 0, 0x100, "", false);  // r_debugShowPrimaryLights
	Dvar_RegisterEnum(0xA8CEC8EA, "", s_debugShowNames, 0, 0x100, "", false);  // r_debugShowDynamicLights
	Dvar_RegisterInt(0x46067315, "", -1, -1, 3000, 0x100, "", false);  // r_debugShowLightBoundsSelect
	Dvar_RegisterEnum(0x5E161647, "", s_debugShowNames, 0, 0x100, "", false);  // r_debugShowProbes
	r_debugShowProbeBlends = Dvar_RegisterBool(0xA5FB2F7C, "", false, 0x100, "", false);
	Dvar_RegisterInt(0x25B45D18, "", -1, -1, 256, 0x100, "", false);  // r_debugShowProbesBoundsSelect
	r_debugDisableLocalProbes = Dvar_RegisterBool(0x0B6712FD, "", false, 0x100, "", false);
	Dvar_RegisterBool(0x70D89D25, "", false, 0x100, "", false);  // r_debugShowCoronas
	Dvar_RegisterBool(0xABDA3A59, "", false, 0x100, "", false);  // r_debugMetalStorm
	r_disableGenericFilter = Dvar_RegisterBool(0xF8963311, "", false, 0x100, "", false);
	Dvar_RegisterBool(0x58C6B0CF, "", false, 0x100, "", false);  // r_drawDebugFogParams
	Dvar_RegisterInt(0xCE3883FC, "", 0, 0, 109, 0x100, "", false);  // r_rendertarget_debug_display
	Dvar_RegisterInt(0xCD6A7C70, "", -2, -2, 126, 0x100, "", false);  // r_ui3d_debug_display
	Dvar_RegisterInt(0xD5F31084, "", -1, -1, 126, 0x100, "", false);  // r_ui3d_use_debug_values
	Dvar_RegisterFloat(0x20BFA81E, "", 0.0f, 0.0f, 1024.0f, 0x100, "", false);  // r_ui3d_x
	Dvar_RegisterFloat(0x46C22287, "", 0.0f, 0.0f, 1024.0f, 0x100, "", false);  // r_ui3d_y
	Dvar_RegisterFloat(0x329F70C9, "", 1024.0f, 0.0f, 1024.0f, 0x100, "", false);  // r_ui3d_w
	Dvar_RegisterFloat(0x80E74EAE, "", 1024.0f, 0.0f, 1024.0f, 0x100, "", false);  // r_ui3d_h
	Dvar_RegisterBool(0x4B95848B, "", false, 0x100, "", false);  // r_font_cache_debug_display
	Dvar_RegisterEnum(0xB85D3C07, "", s_sizeNames, 0, 0x100, "", false);  // r_extracam_show_render_targets
	r_extracam_custom_aspectratio = Dvar_RegisterFloat(0x00D31D5F, "", -1.0f, -1.0f, 5.0f, 0x40, "", false);
	Dvar_RegisterBool(0x4D5B1CD3, "", false, 0x100, "", false);  // r_extracam_add_debug_cam
	Dvar_RegisterInt(0xEC6B7572, "", 1200, 64, 1920, 0x100, "", false);  // r_extracam_add_debug_cam_width
	Dvar_RegisterBool(0x1521B806, "", false, 0x100, "", false);  // r_extracam_remove_debug_cam
	Dvar_RegisterBool(0x42B140D7, "", false, 0x100, "", false);  // r_extracam_show_axis
	Dvar_RegisterInt(0x14E3F791, "", -1, -1, 12, 0x100, "", false);  // r_qrcode_debug_display
	Dvar_RegisterFloat(0x69E783CF, "", 400.0f, 0.0f, 2000.0f, 0x100, "", false);  // r_qrcode_debug_display_size
	Dvar_RegisterFloat(0xA0669E75, "", -1.0f, -2.0f, 2000.0f, 0x100, "", false);  // r_shader_constant_set_debug_range
	r_shader_constant_set_enable = Dvar_RegisterBool(0xA591BC4F, "", true, 0x100, "", false);
	r_fog_disable = Dvar_RegisterBool(0xC690B1E9, "", false, 0x100, "", false);
	// P0021: the late latch, on unless turned off (r_lateLatch 0); a new dvar, after all of the original's
	r_lateLatch = Dvar_RegisterBool(0x4113CAB2, "", true, 0x0, "", false);
}
