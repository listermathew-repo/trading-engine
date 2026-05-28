# enable-wake-to-run.ps1
# Sets WakeToRun on ALL trading scheduled tasks
# Run any time a new task is added

$tasks = @(
    "Trading - Daily Briefing 0800",
    "Trading - Signal Check 1500",
    "Trading - London Close Warning 1650",
    "Trading - NY Close Warning 2350",
    "Trading - Heartbeat 0755",
    "Trading - Wednesday Skip 1500"
)

foreach ($taskName in $tasks) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
        $task.Settings.WakeToRun = $true
        Set-ScheduledTask -InputObject $task | Out-Null
        Write-Host "Wake-to-run enabled: $taskName"
    } catch {
        Write-Host "FAILED for '$taskName': $_"
    }
}

Write-Host ""
Write-Host "All done. Also enable wake timers in Windows Power Options:"
Write-Host "  Control Panel > Power Options > Change plan settings"
Write-Host "  > Change advanced power settings > Sleep > Allow wake timers > Enable"
