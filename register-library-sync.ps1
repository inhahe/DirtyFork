# Register (or re-register) the file library's sync with Task Scheduler.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File register-library-sync.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File register-library-sync.ps1 -DataDir me -Minutes 60
#   Start-ScheduledTask -TaskName 'DirtyFork library sync'                        # run it now
#   Unregister-ScheduledTask -TaskName 'DirtyFork library sync' -Confirm:$false  # remove it
#
# The task runs library_sync.py for the BBS whose data directory is -DataDir: every
# source not marked "scheduled: false" in its config (file_library.sources), which
# fetches the GitHub repositories that changed and replaces only their changed files in
# their zips, zips websites and webpages that are new or changed, and lists new
# pictures and videos. Its log is library_sync.log in the data directory.
#
# How often: unless -Minutes is given, this runs the sync once to bring everything up to
# date, then again to time a run with nothing much to do, and repeats the task every
# Factor times that long (a sync that takes longer runs less often), at least every
# 15 minutes and at most once a day, rounded up to 5 minutes. Run this again after the
# sources grow to recalibrate.
#
# It runs as the current user, only while logged on (no stored password), with pythonw so
# no console window appears. A run still going when the next is due has that one skipped
# (one at a time); a run that hangs is stopped after 3 hours.
param(
    [string]$DataDir = 'me',
    [int]$Minutes = 0,
    [int]$Factor = 30
)
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$venv = Join-Path $root 'env\Scripts'
if (Test-Path (Join-Path $venv 'python.exe')) {
    $py = Join-Path $venv 'python.exe'
} else {
    $py = (Get-Command python -ErrorAction Stop).Source
}
$pyw = Join-Path (Split-Path -Parent $py) 'pythonw.exe'
if (-not (Test-Path $pyw)) { throw "pythonw.exe not found next to $py" }
$data = (Resolve-Path (Join-Path $root $DataDir)).Path
"Python: $pyw"
"Data directory: $data"

function Invoke-Sync {
    # Runs the sync; returns how long it took. (Windows PowerShell 5.1 turns a native
    # program's stderr, the sync's log, into a terminating error under 'Stop'.)
    $ErrorActionPreference = 'Continue'
    Push-Location $root
    try {
        $took = Measure-Command { & $py library_sync.py --data-dir $data 2>&1 | Out-Null }
        $code = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    if ($code -eq 3) { throw "Another library_sync is running; run this again when it has finished." }
    if ($code -ne 0) { Write-Host "library_sync exited with $code (a source failed; see $data\library_sync.log)" }
    $took
}

if ($Minutes -le 0) {
    "Bringing the library up to date..."
    $first = Invoke-Sync
    "  took {0:N0} s" -f $first.TotalSeconds
    "Timing a run with nothing new..."
    $second = Invoke-Sync
    "  took {0:N1} s" -f $second.TotalSeconds
    $Minutes = [int][Math]::Ceiling($second.TotalSeconds * $Factor / 60 / 5) * 5
    $Minutes = [Math]::Min([Math]::Max($Minutes, 15), 1440)
    "Every $Minutes minutes ($Factor times $([Math]::Round($second.TotalSeconds, 1)) s, rounded up, 15 minutes to a day)"
}

$name = 'DirtyFork library sync'
$action = New-ScheduledTaskAction -Execute $pyw -WorkingDirectory $root -Argument "library_sync.py --data-dir `"$data`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes($Minutes) -RepetitionInterval (New-TimeSpan -Minutes $Minutes)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Force `
    -Description "Refreshes the DirtyFork BBS file library from its sources every $Minutes minutes: $root\library_sync.py --data-dir $data (log: $data\library_sync.log)." | Out-Null

Get-ScheduledTask -TaskName $name | Select-Object TaskName, State,
    @{n = 'Every'; e = { "$Minutes minutes" } },
    @{n = 'Next run'; e = { (Get-ScheduledTaskInfo $_).NextRunTime } } | Format-List
