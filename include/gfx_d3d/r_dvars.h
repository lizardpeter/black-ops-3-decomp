// gfx_d3d/r_dvars.h (reconstructed: only what reconstructed code uses so far)
#pragma once

struct dvar_t;

extern const dvar_t *dvar_EBC13010;
extern const dvar_t *r_backBufferCount;  // registered by 141D91120
extern const dvar_t *r_cmdlistChain;
extern const dvar_t *r_convergence;      // registered by 141D91120 (3D Vision)
extern const dvar_t *r_fullscreen;       // registered by 141D91120: 0 windowed, 1 fullscreen, 2 borderless
extern const dvar_t *r_maxFrameLatency;  // registered by 141D91120: frames DXGI may queue (0: DXGI's default)
extern const dvar_t *r_currentMonitor;
extern const dvar_t *r_debugDisableLocalProbes;
extern const dvar_t *r_debugShowProbeBlends;
extern const dvar_t *r_disableGenericFilter;
extern const dvar_t *r_exposureEyeWeight;
extern const dvar_t *r_exposureTweak;
extern const dvar_t *r_exposureValue;
extern const dvar_t *r_extracam_custom_aspectratio;
extern const dvar_t *r_fog_disable;
extern const dvar_t *r_grassEnable;
extern const dvar_t *r_mode;
extern const dvar_t *r_monitor;
extern const dvar_t *r_monitorCount;
extern const dvar_t *r_num_viewports;
extern const dvar_t *r_refreshRate;
extern const dvar_t *r_sceneResolutionMultiplier;
extern const dvar_t *r_shader_constant_set_enable;
extern const dvar_t *r_skyRotation;
extern const dvar_t *r_skyTransition;
extern const dvar_t *r_sortDrawSurfsBsp;
extern const dvar_t *r_sortDrawSurfsStaticModel;
extern const dvar_t *r_videoMemoryMultiplier;
extern const dvar_t *r_vsync;            // registered by 141D91AF0: sync interval 1 when set

void sub_141D976E0();
