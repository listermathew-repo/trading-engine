# planning-session-reminder.ps1
# Runs daily Mon-Fri at 08:00 ACST via Task Scheduler
# Calls Send-Alert.ps1 (central hub) - do not duplicate Invoke-RestMethod here

$AlertsFolder = "C:\Users\mathe\trading-alerts"
$Day = (Get-Date).DayOfWeek

if ($Day -eq "Saturday" -or $Day -eq "Sunday") {
    Write-Host "Weekend - no alert sent."
    exit
}

if ($Day -eq "Monday") {
    $Title    = "Monday Planning Session - Open Claude"
    $Message  = "Good morning! Time for your weekly planning session. Watch the scenario video, paste ForexFactory calendar, then open Claude at 08:30 ACST."
    $Tags     = "spiral_calendar"
    $Priority = "high"
} else {
    $Title    = "Daily Briefing - Open Claude"
    $Message  = "Good morning! Quick daily check-in: scenario video done? Paste today's ForexFactory calendar to Claude. Session starts 15:30 ACST."
    $Tags     = "sun_with_face"
    $Priority = "default"
}

& "$AlertsFolder\Send-Alert.ps1" -Title $Title -Message $Message -Priority $Priority -Tags $Tags
