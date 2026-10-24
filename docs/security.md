# Security

Security findings in the original, with what the enhanced build should do about them. Each has a row in
`records/bugs.tsv`; this file holds the longer write-up. Public CVEs and the fixes community clients apply go here
too, once confirmed against the reconstruction.

## B0004: Havok socket server (hkBsdSocket listen/accept)

The Store build links Havok's BSD socket layer (`System\Io\Platform\Bsd\hkBsdSocket.cpp`, 142A433D0–142A43DA0),
including `bind`/`listen` (142A43730, logging "Listening on host [ ] port") and `accept` (142A438F0). In Havok
this backs the Visual Debugger server, which accepts connections from the Havok VDB client and was never designed
for untrusted peers. Nothing calls these functions directly; they are reached through the vtable at 142DF6E50.

Open question: whether the retail game ever creates the VDB server (a debug-only dvar or build flag would keep it
dormant). Either way the enhanced build should remove the listener: the offline build has no use for it, and a
listening socket in a client is attack surface. See docs/network.md section 6.
