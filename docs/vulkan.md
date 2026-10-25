# Vulkan

The enhanced build is to get a native Vulkan renderer: our own Vulkan code under the render thread, in place of the
D3D11 calls. No translation layer (no DXVK or anything like it) and no D3D11 calls translated at run time. The
original D3D11 path stays in the exe untouched; the Vulkan backend is chosen behind a switch until it matches it.

## Shaders

The game ships its shaders only as compiled D3D bytecode (DXBC) in the fastfiles. There is no HLSL source and no
shader compiler in the exe (its only D3D imports are `D3D11CreateDevice` and `CreateDXGIFactory1`). The plan:

1. **First,** each shader's bytecode is converted to SPIR-V once, by a converter of our own in the decomp. The result
   is cached in the game's folder and loaded natively. Nothing is translated while the game runs.
2. **Then,** shaders are decompiled back to readable source and recompiled to SPIR-V, one at a time. Each one replaces
   its converted version, the way functions are swapped in. That gives shaders that can be read, checked and
   improved.

## The work, in order

1. **Map and decompile the renderer backend:**
   - the render thread's frame (`141D470F0`), scene drawing (`141D4E220`), the 2D pass (`141D46E40`) and present;
   - the draw-list jobs (`141D4ACB0` and the table they are dispatched from);
   - how command recording is split across worker threads and contexts.

   docs/late-latch.md has the part mapped so far.
2. **Map the D3D11 layer under it.** That is every resource, view, state object, shader and input layout the game
   creates, the constant-buffer and dynamic-buffer updates (`141DC65F0`), and how images and shaders come out of the
   fastfiles.
3. **The Vulkan backend:**
   - device and swap chain, presenting immediately (no V-Sync);
   - pipelines built from the D3D state combinations the game uses;
   - descriptor sets in place of D3D11's per-slot binding;
   - barriers and fences where D3D11's driver synchronised implicitly;
   - Reflex through `VK_NV_low_latency2`.
4. **Bring the enhanced changes across:** the late latch, refresh rates, latency, and the menu options
   (docs/menus.md).

## What the game asks of D3D11 (first count)

A scan of the decompiled code for interface calls on the device (`dx_device`, 1486F0DB0), the immediate context
(`dx_context`, 1486F0DB8) and the context a backend state draws with (state +0x40B8). These are only the calls whose
object the scan can follow; contexts passed in as parameters are not counted yet. So it is a lower bound, and the
missing draws (one `Draw`, no `DrawIndexed`) show where to look next.

| Interface | Methods seen (calls / functions) |
| --- | --- |
| Device | CreateShaderResourceView 36/20, CreateBuffer 14/9, CreateUnorderedAccessView 10/6, CreateTexture2D 10/9, CreateRenderTargetView 4/3, CreateDepthStencilView 3/2, CreateQuery 3/2, CreateTexture3D, CreateInputLayout, the six shader kinds (vertex, hull, domain, geometry, pixel, compute), CreateBlendState, CreateDepthStencilState, CreateRasterizerState, CreateSamplerState, GetDeviceRemovedReason |
| Context | compute: CSSetUnorderedAccessViews 122/19, CSSetShaderResources 78/16, CSSetShader 38/16, CSSetSamplers 26/13, Dispatch 4/4, DispatchIndirect 6/4; buffers: Map 15/15, Unmap 19/17, CopyResource 5/5, CopySubresourceRegion 5/4; drawing: DrawIndexedInstanced 5/5, DrawIndexedInstancedIndirect, IASetIndexBuffer 9/7, IASetVertexBuffers, IASetInputLayout, IASetPrimitiveTopology; the VS/HS/DS/GS/PS stages' shaders, resources, samplers and constant buffers; OMSetRenderTargets(AndUnorderedAccessViews), OMSetBlendState, OMSetDepthStencilState, RSSetState, RSSetViewports, RSSetScissorRects; ClearDepthStencilView, ClearUnorderedAccessViewUint, ResolveSubresource; Begin/End/GetData (queries); ExecuteCommandList, ClearState, Flush |

What the count already shows:
- **A lot of compute.** BO3's lighting and culling run as compute dispatches, so compute pipelines and storage
  images and buffers are first-class work, not an afterthought.
- **Tessellation is in use** (hull and domain shaders), and so are geometry shaders.
- **Command lists exist** (ExecuteCommandList): command recording on worker threads needs to be mapped (step 1).
  On Vulkan that becomes secondary command buffers, or per-thread primary ones.
