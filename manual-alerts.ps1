# manual-alerts.ps1
# Claude runs these during live sessions for trade management and risk enforcement
# Can also be run manually from PowerShell
# Usage: .\manual-alerts.ps1 -Type "news" -Pair "GOLD" -Details "CPI in 30 min"

param(
    [ValidateSet("news","breakeven","signal","nosetup","daily-summary","daily-limit","be-stopped","news-confirm")]
    [string]$Type,
    [string]$Pair    = "",
    [string]$Details = ""
)

# Guard: Type is required
if (-not $Type) {
    Write-Error "Must provide -Type. Options: news, breakeven, signal, nosetup, daily-summary, daily-limit, be-stopped, news-confirm"
    exit 1
}

$AlertsFolder = "C:\Users\mathe\trading-alerts"

switch ($Type) {

    "news" {
        $Title    = "NEWS WARNING - $Pair"
        $Message  = "RED event in 30 minutes - $Details. Close or protect positions NOW."
        $Priority = "urgent"
        $Tags     = "warning"
    }

    "breakeven" {
        $Title    = "Move SL to Breakeven - $Pair"
        $Message  = "$Pair hit profit trigger. Move Stop Loss to Breakeven + spread NOW. $Details"
        $Priority = "high"
        $Tags     = "white_check_mark"
    }

    "signal" {
        $Title    = "A+ Setup - $Pair"
        $Message  = "$Details. Sit down now - London open 15:30 ACST."
        $Priority = "high"
        $Tags     = "chart_with_upwards_trend"
    }

    "nosetup" {
        $Title    = "No Setups Today"
        $Message  = "Conditions not met on any pair. Stand down - enjoy your afternoon. $Details"
        $Priority = "default"
        $Tags     = "no_entry"
    }

    "daily-summary" {
        $Title    = "Daily Summary"
        $Message  = $Details
        $Priority = "default"
        $Tags     = "memo"
    }

    "daily-limit" {
        $Title    = "DAILY LOSS LIMIT HIT - STOP TRADING"
        $Message  = "You have reached the 2 percent daily loss limit ($1,600). Close ALL positions now. Trading is BLOCKED for the rest of today. $Details"
        $Priority = "urgent"
        $Tags     = "no_entry_sign"
    }

    "be-stopped" {
        $Title    = "Breakeven Stop Hit - $Pair"
        $Message  = "$Pair breakeven stop was triggered. You are flat. Do NOT re-enter this setup on emotion. $Details"
        $Priority = "default"
        $Tags     = "hand"
    }

    "news-confirm" {
        $Title    = "NEWS IN 5 MIN - Are Positions Closed? - $Pair"
        $Message  = "RED event in 5 minutes: $Details. Confirm all positions are CLOSED right now."
        $Priority = "urgent"
        $Tags     = "rotating_light"
    }
}

& "$AlertsFolder\Send-Alert.ps1" -Title $Title -Message $Message -Priority $Priority -Tags $Tags
