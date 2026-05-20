# wednesday-skip-reminder.ps1
# Fires every Wednesday at 15:00 ACST alongside the signal check
# Rule updated: Wednesday is CAUTION not SKIP — A+ only, T2 maximum

$AlertsFolder = "C:\Users\mathe\trading-alerts"
$Day = (Get-Date).DayOfWeek

if ($Day -ne "Wednesday") {
    Write-Host "Not Wednesday - no caution alert sent."
    exit
}

& "$AlertsFolder\Send-Alert.ps1" `
    -Title "Wednesday Caution" `
    -Message "Wednesday: A+ setup ONLY. T2 maximum (no T3/T4). All 5 conditions must be met + Scenario 1 confirmed. Default posture = wait. If setup qualifies, take it. Check morning video for continuation bias before entry." `
    -Priority "default" `
    -Tags "warning"
