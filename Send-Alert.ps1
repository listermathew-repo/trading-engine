# Send-Alert.ps1 - Core ntfy notification sender
# Central hub for ALL alerts. All other scripts call this one.
# Usage: .\Send-Alert.ps1 -Title "Alert Title" -Message "Alert body" -Priority "high" -Tags "warning"

param(
    [string]$Title    = "Trading Alert",
    [string]$Message  = "",
    [string]$Priority = "high",
    [string]$Tags     = "chart_with_upwards_trend"
)

$Channel = "mgm-7k4x-live"
$Uri     = "https://ntfy.sh/$Channel"
$LogDir  = "C:\Users\mathe\trading-alerts\logs"
$LogFile = "$LogDir\alert-log.txt"

# Create logs directory if it does not exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Log rotation - archive if over 1MB
if ((Get-Item $LogFile -ErrorAction SilentlyContinue).Length -gt 1MB) {
    $archive = $LogFile -replace '\.txt$', "-$(Get-Date -Format yyyyMMdd).txt"
    Move-Item $LogFile $archive -Force
}

function Write-Log {
    param([string]$Entry)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$stamp] $Entry" | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

$headers = @{
    "Title"    = $Title
    "Priority" = $Priority
    "Tags"     = $Tags
}

try {
    Invoke-RestMethod -Method Post -Uri $Uri -Headers $headers -Body $Message -ContentType "text/plain" | Out-Null
    Write-Host "Alert sent: $Title"
    Write-Log "SENT [$Priority] $Title | $Message"
} catch {
    Write-Log "FAILED [$Priority] $Title | $($_.Exception.Message)"
    Write-Host "Send failed - retrying in 10 seconds..."
    Start-Sleep -Seconds 10
    try {
        Invoke-RestMethod -Method Post -Uri $Uri -Headers $headers -Body $Message -ContentType "text/plain" | Out-Null
        Write-Host "Retry successful: $Title"
        Write-Log "RETRY OK [$Priority] $Title"
    } catch {
        Write-Host "Retry also failed: $_"
        Write-Log "RETRY FAILED [$Priority] $Title | $($_.Exception.Message)"
    }
}
