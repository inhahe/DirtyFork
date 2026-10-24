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
# How often: the task runs every -Minutes (default 15), and the sync paces each source
# itself: a run checks a source only once 30 times as long as its last check took has
# passed (file_library.sync_pace; zipping not counted), and at least once a day. So a
# source that is quick to check is checked at every run, and one that takes minutes, as
# a big folder does on a disk busy with something else, waits hours. The first run
# brings everything up to date, however long that takes (zips are kept as they are made).
#
# It runs as the current user, only while logged on (no stored password), with pythonw so
# no console window appears. A run still going when the next is due has that one skipped
# (one at a time); a run that hangs is stopped after 3 hours.
param(
    [string]$DataDir = 'me',
    [int]$Minutes = 15
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
$data = if ([IO.Path]::IsPathRooted($DataDir)) { $DataDir } else { Join-Path $root $DataDir }
$data = (Resolve-Path $data).Path
if ($Minutes -lt 1) { throw "-Minutes must be at least 1" }
"Python: $pyw"
"Data directory: $data"

$name = 'DirtyFork library sync'
$action = New-ScheduledTaskAction -Execute $pyw -WorkingDirectory $root -Argument "library_sync.py --data-dir `"$data`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes($Minutes) -RepetitionInterval (New-TimeSpan -Minutes $Minutes)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Force `
    -Description "Refreshes the DirtyFork BBS file library from its sources, each as often as its cost allows, looking every $Minutes minutes: $root\library_sync.py --data-dir $data (log: $data\library_sync.log)." | Out-Null

Get-ScheduledTask -TaskName $name | Select-Object TaskName, State,
    @{n = 'Every'; e = { "$Minutes minutes" } },
    @{n = 'Next run'; e = { (Get-ScheduledTaskInfo $_).NextRunTime } } | Format-List
