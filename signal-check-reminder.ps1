# signal-check-reminder.ps1
# Runs daily Mon-Fri at 15:00 ACST via Task Scheduler
# Calls Send-Alert.ps1 (central hub) - do not duplicate Invoke-RestMethod here

$AlertsFolder = "C:\Users\mathe\trading-alerts"
$Day = (Get-Date).DayOfWeek

if ($Day -eq "Saturday" -or $Day -eq "Sunday") {
    Write-Host "Weekend - no alert sent."
    exit
}

switch ($Day) {
    "Monday"    { $DayMsg = "Monday - run weekly bias + signal check" }
    "Tuesday"   { $DayMsg = "Tuesday - prime setup day, check all 3 pairs" }
    "Wednesday" { $DayMsg = "Wednesday - caution day, setups less likely" }
    "Thursday"  { $DayMsg = "Thursday - prime setup day, check all 3 pairs" }
    "Friday"    { $DayMsg = "Friday - optional session, check conditions first" }
}

& "$AlertsFolder\Send-Alert.ps1" `
    -Title "15:00 Signal Check - Open Claude" `
    -Message "Time for your pre-session check. $DayMsg. London open at 15:30 ACST." `
    -Priority "high" `
    -Tags "chart_with_upwards_trend"
