# add-new-tasks.ps1
# Adds the 3 new scheduled tasks: London close, NY close, and heartbeat
# Run once after setup-scheduled-tasks.ps1 has already been run

$AlertsFolder = "C:\Users\mathe\trading-alerts"

# Task 3: Heartbeat at 07:55 ACST Mon-Fri (pipeline health check)
$cmd3 = "schtasks /create /f /tn ""Trading - Heartbeat 0755"" " +
        "/tr ""powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \""$AlertsFolder\heartbeat.ps1\""`" " +
        "/sc WEEKLY /d MON,TUE,WED,THU,FRI /st 07:55"
$result3 = cmd /c $cmd3 2>&1
Write-Host "Task 3 (Heartbeat 07:55): $result3"

# Task 4: London close warning at 16:50 ACST Mon-Fri
$cmd4 = "schtasks /create /f /tn ""Trading - London Close Warning 1650"" " +
        "/tr ""powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \""$AlertsFolder\session-close-reminder.ps1\""`" " +
        "/sc WEEKLY /d MON,TUE,WED,THU,FRI /st 16:50"
$result4 = cmd /c $cmd4 2>&1
Write-Host "Task 4 (London close 16:50): $result4"

# Task 5: NY close + Gold cutoff warning at 23:50 ACST Mon-Fri
$cmd5 = "schtasks /create /f /tn ""Trading - NY Close Warning 2350"" " +
        "/tr ""powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \""$AlertsFolder\session-close-reminder.ps1\""`" " +
        "/sc WEEKLY /d MON,TUE,WED,THU,FRI /st 23:50"
$result5 = cmd /c $cmd5 2>&1
Write-Host "Task 5 (NY close 23:50): $result5"

Write-Host ""
Write-Host "Done. Now run enable-wake-to-run.ps1 to set wake-to-run on all 5 tasks."
Write-Host "Verify tasks: schtasks /query /fo LIST | findstr ""Task Name"""
