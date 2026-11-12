# Native Windows original BO3 startup observation

The byte-identical GDK replacement under Wine is **not** a Windows system
replacement. The Store build loads `xgameruntime.dll` from system32; never
install our diagnostic DLL in the real Windows system directory.

`tools/offline/ProbeNative.ps1` is an optional read-only native Windows
baseline, **not the enhanced playable game**. It verifies the pinned Store
EXE SHA-256, requires elevated PowerShell and enabled Firewall profiles,
installs an executable-specific outbound deny rule **before** launch, and
samples the original process for a bounded period. It stops the process,
removes the temporary rule in a `finally` block, and writes a local
`native-baseline.json` report. It does not modify the EXE, service state,
game files, DLL search paths, or registry.

On a Windows gaming PC with the complete authentic installation:

```powershell
.\tools\offline\ProbeNative.ps1 -ExePath 'D:\BO3\BlackOps3.exe' -GameDirectory 'D:\BO3' -OutputDirectory '.\t7-baseline' -Seconds 60
```

The probe does not start a map, join a lobby, contact a server, or launch
with special game commands. Review the report locally before sharing it.

A loaded GDK DLL, a D3D11 DLL or an allocated window proves only the
corresponding startup surface was reached. It is **not** proof of a rendered
menu, playable map, successful multiplayer join, or whole-process vendor
isolation. This native probe has not yet been executed on a real gaming PC.
