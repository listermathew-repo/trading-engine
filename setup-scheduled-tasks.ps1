# setup-scheduled-tasks.ps1 — uses schtasks.exe (no Admin required)

$AlertsFolder = "C:\Users\mathe\trading-alerts"

# --- Task 1: Daily briefing at 08:00 ACST Mon-Fri ---
$cmd1 = "schtasks /create /f /tn `"Trading - Daily Briefing 0800`" " +
        "/tr `"powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \`"$AlertsFolder\planning-session-reminder.ps1\`"`" " +
        "/sc WEEKLY /d MON,TUE,WED,THU,FRI /st 08:00"

$result1 = cmd /c $cmd1 2>&1
Write-Host "Task 1: $result1"

# --- Task 2: Signal check at 15:00 ACST Mon-Fri ---
$cmd2 = "schtasks /create /f /tn `"Trading - Signal Check 1500`" " +
        "/tr `"powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \`"$AlertsFolder\signal-check-reminder.ps1\`"`" " +
        "/sc WEEKLY /d MON,TUE,WED,THU,FRI /st 15:00"

$result2 = cmd /c $cmd2 2>&1
Write-Host "Task 2: $result2"

Write-Host ""
Write-Host "Done. Verify with: schtasks /query /tn `"Trading - Daily Briefing 0800`""
