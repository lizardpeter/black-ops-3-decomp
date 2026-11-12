#!/usr/bin/env python3
"""Static regression for the optional native Windows observer, not a native run."""
from pathlib import Path
root = Path(__file__).resolve().parents[2]
s = (root / "tools/offline/ProbeNative.ps1").read_text()
for value in ("Get-FileHash", "New-NetFirewallRule", "Get-NetFirewallRule",
              "Start-Process", "Stop-Process", "Remove-NetFirewallRule", "finally",
              "native-baseline.json", "whole_process_vendor_isolation_verified = $false"):
    assert value in s, value
assert s.index("New-NetFirewallRule") < s.index("Start-Process")
assert s.index("Remove-NetFirewallRule") > s.index("finally")
assert s.count("Start-Process") == 1
print("PASS: native original probe requires prelaunch block, samples, and cleanup")
