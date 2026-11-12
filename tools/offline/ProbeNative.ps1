# Read-only, original-only Windows startup probe. Offline by mandatory app-specific firewall block.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$ExePath,
  [Parameter(Mandatory=$true)][string]$GameDirectory,
  [Parameter(Mandatory=$true)][string]$OutputDirectory,
  [ValidateRange(10,180)][int]$Seconds = 60
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows only' }
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw 'Elevated PowerShell is required for the temporary firewall rule'
}
$exe = (Resolve-Path -LiteralPath $ExePath).Path
$game = (Resolve-Path -LiteralPath $GameDirectory).Path
$expected = '72c8a21763adbfac9e1b2bcd6f93b05ecf437610e16430d99a1680ea0f827c17'
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLowerInvariant()
if ($hash -ne $expected) { throw 'Executable does not match pinned Store original' }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Output directory already exists' }
$profiles = @(Get-NetFirewallProfile)
if ($profiles.Count -lt 1 -or @($profiles | Where-Object { -not $_.Enabled }).Count -gt 0) {
  throw 'All Windows Firewall profiles must be enabled'
}
New-Item -ItemType Directory -Path $OutputDirectory -ErrorAction Stop | Out-Null
$name = 'T7OfflineProbe-' + [Guid]::NewGuid().ToString('N')
$hasRule = $false
$removedRule = $false
$proc = $null
$samples = @()
$errorText = $null
try {
  New-NetFirewallRule -Name $name -DisplayName $name -Direction Outbound -Action Block -Program $exe -Profile Any -Enabled True | Out-Null
  $hasRule = $true
  $rule = Get-NetFirewallRule -Name $name -ErrorAction Stop
  if ($rule.Action -ne 'Block' -or $rule.Direction -ne 'Outbound' -or -not $rule.Enabled) {
    throw 'Outbound block not active'
  }
  # No sign-in, connect, host, map or vendor command is issued.
  $proc = Start-Process -FilePath $exe -WorkingDirectory $game -PassThru -ErrorAction Stop
  $clock = [Diagnostics.Stopwatch]::StartNew()
  while ($clock.Elapsed.TotalSeconds -lt $Seconds) {
    Start-Sleep -Seconds 5
    try { $proc.Refresh() } catch {}
    $alive = -not $proc.HasExited
    $modules = @()
    $known = $false
    if ($alive) {
      try {
        $modules = @((Get-Process -Id $proc.Id -ErrorAction Stop).Modules |
          ForEach-Object { $_.ModuleName.ToLowerInvariant() } | Sort-Object -Unique)
        $known = $true
      } catch {}
    }
    $samples += [pscustomobject]@{
      elapsed_s = [math]::Round($clock.Elapsed.TotalSeconds,1)
      alive = $alive
      window_handle_present = if ($alive) { [bool]($proc.MainWindowHandle -ne [IntPtr]::Zero) } else { $false }
      modules_read = $known
      gdk_loaded = if ($known) { $modules -contains 'xgameruntime.dll' } else { $null }
      xcurl_loaded = if ($known) { $modules -contains 'xcurl.dll' } else { $null }
      winhttp_loaded = if ($known) { $modules -contains 'winhttp.dll' } else { $null }
      d3d11_loaded = if ($known) { $modules -contains 'd3d11.dll' } else { $null }
    }
    if (-not $alive) { break }
  }
} catch { $errorText = $_.Exception.Message } finally {
  if ($null -ne $proc) { try { if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force } } catch {} }
  if ($hasRule) {
    try {
      Remove-NetFirewallRule -Name $name -ErrorAction Stop
      $removedRule = -not [bool](Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue)
    } catch { $removedRule = $false }
  }
  [pscustomobject]@{
    build = 'BlackOps3_MSStore'
    sha256 = $hash
    process_started = ($null -ne $proc)
    outbound_rule_installed_before_launch = $hasRule
    outbound_rule_removed = $removedRule
    observations = $samples
    error = $errorText
    rendered_menu_verified = $false
    map_loaded_verified = $false
    join_verified = $false
    whole_process_vendor_isolation_verified = $false
    note = 'Window handles and DLL loads are not evidence of a rendered menu, map or traffic isolation'
  } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'native-baseline.json')
}
if ($hasRule -and -not $removedRule) { throw "Firewall cleanup failed; inspect rule $name" }
if ($errorText) { throw $errorText }
Write-Host 'Native baseline written to' (Join-Path $OutputDirectory 'native-baseline.json')
