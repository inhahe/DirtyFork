# Register (or re-register) the web terminal's bridge with Task Scheduler, and start it.
#
#   powershell -NoProfile -File web\register-bridge.ps1
#   powershell -NoProfile -File web\register-bridge.ps1 -Listen 127.0.0.1:8023 -Bbs 127.0.0.1:23
#   Stop-ScheduledTask -TaskName 'DirtyFork web bridge'          # stop it until the next logon
#   Unregister-ScheduledTask -TaskName 'DirtyFork web bridge' -Confirm:$false   # remove it
#
# The bridge (web\jsterm_bridge.py) carries the browser terminal at inhahe.com/bbs.html
# to the BBS: nginx hands it wss://inhahe.com/bbs-ws, and it telnets to the BBS. It runs
# from logon, independently of the BBS: while the BBS is down, callers are told so.
# Runs as the current user, only while logged on (no stored password), with pythonw so
# no console window appears; restarted a minute after it exits. Logs to
# web\jsterm_bridge.log.
param([string]$Listen = '127.0.0.1:8023', [string]$Bbs = '127.0.0.1:23')
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$py = (Get-Command python -ErrorAction Stop).Source
$pyw = Join-Path (Split-Path -Parent $py) 'pythonw.exe'
if (-not (Test-Path $pyw)) { throw "pythonw.exe not found next to $py" }
& $py -c "import websockets" 2>$null
if ($LASTEXITCODE -ne 0) { throw "$py has no 'websockets' package: pip install websockets" }

$name = 'DirtyFork web bridge'
$action = New-ScheduledTaskAction -Execute $pyw -WorkingDirectory $root `
    -Argument "web\jsterm_bridge.py --listen $Listen --bbs $Bbs"
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Force `
    -Description "WebSocket-to-telnet bridge for the DirtyFork BBS web terminal (inhahe.com/bbs.html): $root\web\jsterm_bridge.py, $Listen -> BBS at $Bbs." | Out-Null
Start-ScheduledTask -TaskName $name

Get-ScheduledTask -TaskName $name | Select-Object TaskName, State,
    @{n = 'Last run'; e = { (Get-ScheduledTaskInfo $_).LastRunTime } } | Format-List
