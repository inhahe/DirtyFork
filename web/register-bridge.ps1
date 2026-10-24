# Register (or re-register) the web terminal's bridge with Task Scheduler, and start it.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File web\register-bridge.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File web\register-bridge.ps1 -Listen 127.0.0.1:8023 -Bbs 127.0.0.1:23 -Origins https://example.com
#   Stop-ScheduledTask -TaskName 'DirtyFork web bridge'          # stop it (it comes back within 5 minutes)
#   Unregister-ScheduledTask -TaskName 'DirtyFork web bridge' -Confirm:$false   # remove it
#
# The bridge (web\jsterm_bridge.py) carries the browser terminal at inhahe.com/bbs.html
# to the BBS: nginx hands it wss://inhahe.com/bbs-ws, and it telnets to the BBS. It runs
# from logon, independently of the BBS: while the BBS is down, callers are told so.
# It runs as the current user, only while logged on (no stored password), with pythonw
# so no console window appears, and logs to web\jsterm_bridge.log.
#
# Task Scheduler's "restart on failure" covers only a task that fails to start, not a
# program that exits, so the task also fires every 5 minutes: while the bridge runs the
# new start is ignored (one instance at a time), and when it has stopped it starts again.
# -Origins: the pages allowed to connect (other sites' pages are refused).
param(
    [string]$Listen = '127.0.0.1:8023',
    [string]$Bbs = '127.0.0.1:23',
    [string[]]$Origins = @('https://inhahe.com', 'http://inhahe.com', 'https://www.inhahe.com', 'http://www.inhahe.com')
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$py = (Get-Command python -ErrorAction Stop).Source
$pyw = Join-Path (Split-Path -Parent $py) 'pythonw.exe'
if (-not (Test-Path $pyw)) { throw "pythonw.exe not found next to $py" }
# websockets 13 introduced the API the bridge uses. Windows PowerShell 5.1 turns a
# native program's stderr into a terminating error under 'Stop', so relax it here.
$ErrorActionPreference = 'Continue'
& $py -c "import websockets.asyncio.server" 2>&1 | Out-Null
$haveWebsockets = $LASTEXITCODE -eq 0
$ErrorActionPreference = 'Stop'
if (-not $haveWebsockets) { throw "$py lacks websockets 13 or later: pip install -U websockets" }

$name = 'DirtyFork web bridge'
$arguments = "web\jsterm_bridge.py --listen $Listen --bbs $Bbs" + (($Origins | ForEach-Object { " --origin $_" }) -join '')
$action = New-ScheduledTaskAction -Execute $pyw -WorkingDirectory $root -Argument $arguments
$triggers = @(
    (New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"),
    (New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5))
)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

# A running bridge keeps its old settings, and a start while it runs is ignored: stop it
# first, and wait until its port is free, or the new one cannot listen there.
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) { Stop-ScheduledTask -TaskName $name }
$port = [int]($Listen -replace '^.*:', '')
for ($i = 0; $i -lt 40 -and (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue); $i++) {
    Start-Sleep -Milliseconds 250
}
if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
    throw "Something else still listens on port ${port}: stop it (a hand-started bridge?) and run this again."
}

Register-ScheduledTask -TaskName $name -Action $action -Trigger $triggers -Settings $settings `
    -Principal $principal -Force `
    -Description "WebSocket-to-telnet bridge for the DirtyFork BBS web terminal (inhahe.com/bbs.html): $root\web\jsterm_bridge.py, $Listen -> BBS at $Bbs." | Out-Null
Start-ScheduledTask -TaskName $name

Get-ScheduledTask -TaskName $name | Select-Object TaskName, State,
    @{n = 'Last run'; e = { (Get-ScheduledTaskInfo $_).LastRunTime } } | Format-List
