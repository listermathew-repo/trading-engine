# heartbeat.ps1
# Runs at 07:55 ACST Mon-Fri (5 min before morning briefing)
# Sends a silent min-priority notification to confirm the alert pipeline is alive
# If this stops arriving on your phone, the system is broken before the real alerts fire

$AlertsFolder = "C:\Users\mathe\trading-alerts"
$Day = (Get-Date).DayOfWeek

if ($Day -eq "Saturday" -or $Day -eq "Sunday") {
    exit
}

& "$AlertsFolder\Send-Alert.ps1" `
    -Title "System OK" `
    -Message "Alert pipeline healthy. Morning briefing fires in 5 minutes." `
    -Priority "min" `
    -Tags "white_check_mark"
