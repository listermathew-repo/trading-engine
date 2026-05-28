# session-close-reminder.ps1
# Fires 10 minutes before session close to force position review
# Scheduled twice: 16:50 ACST (London close) and 23:50 ACST (NY close + Gold cutoff)

$AlertsFolder = "C:\Users\mathe\trading-alerts"
$Day  = (Get-Date).DayOfWeek
$Hour = (Get-Date).Hour

if ($Day -eq "Saturday" -or $Day -eq "Sunday") {
    Write-Host "Weekend - no alert sent."
    exit
}

if ($Hour -eq 16) {
    # 16:50 ACST - London prime window closing
    $Title    = "London Close in 10 Min - Review Positions"
    $Message  = "London prime window closes at 17:00 ACST. Review ALL open positions now. Close, protect, or confirm you are holding with a valid reason."
    $Priority = "high"
    $Tags     = "warning"

} elseif ($Hour -eq 23) {
    # 23:50 ACST - NY close + Gold midnight cutoff
    $Title    = "NY Close + GOLD CUTOFF in 10 Min"
    $Message  = "NY session ends at midnight ACST. GOLD CUTOFF IN 10 MINUTES - no new Gold positions after 00:00 ACST. Close or protect all positions now."
    $Priority = "urgent"
    $Tags     = "warning"

} else {
    Write-Host "Hour $Hour - not a close window. No alert sent."
    exit
}

& "$AlertsFolder\Send-Alert.ps1" -Title $Title -Message $Message -Priority $Priority -Tags $Tags
