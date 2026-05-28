<#
.SYNOPSIS
Find Outlook installation on your Windows laptop

.DESCRIPTION
Searches common installation paths and registry for Outlook.exe location
#>

Write-Host "Searching for Outlook installation..." -ForegroundColor Cyan
Write-Host ""

$outlookPaths = @()

# Common installation paths to check
$pathsToCheck = @(
    "C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
    "C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
    "C:\Program Files\Microsoft Office\Office16\OUTLOOK.EXE",
    "C:\Program Files (x86)\Microsoft Office\Office16\OUTLOOK.EXE",
    "C:\Program Files\Microsoft Office\root\Office15\OUTLOOK.EXE",
    "C:\Program Files (x86)\Microsoft Office\root\Office15\OUTLOOK.EXE",
    "C:\Program Files\Microsoft Office\Office15\OUTLOOK.EXE",
    "C:\Program Files (x86)\Microsoft Office\Office15\OUTLOOK.EXE"
)

Write-Host "Checking common installation paths..." -ForegroundColor Yellow
foreach ($path in $pathsToCheck) {
    if (Test-Path $path) {
        Write-Host "  FOUND: $path" -ForegroundColor Green
        $outlookPaths += $path
    }
}

Write-Host ""
Write-Host "Checking Windows Registry..." -ForegroundColor Yellow

# Check registry for Outlook installation
$regPaths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE"
)

foreach ($regPath in $regPaths) {
    try {
        if (Test-Path $regPath) {
            $outlookPath = (Get-ItemProperty $regPath)."(Default)"
            if ($outlookPath -and (Test-Path $outlookPath)) {
                Write-Host "  FOUND: $outlookPath" -ForegroundColor Green
                if ($outlookPaths -notcontains $outlookPath) {
                    $outlookPaths += $outlookPath
                }
            }
        }
    } catch { }
}

Write-Host ""

# Also try to find it via where command
Write-Host "Checking PATH environment variable..." -ForegroundColor Yellow
try {
    $whereResult = where.exe outlook.exe 2>$null
    if ($whereResult) {
        Write-Host "  FOUND: $whereResult" -ForegroundColor Green
        if ($outlookPaths -notcontains $whereResult) {
            $outlookPaths += $whereResult
        }
    }
} catch { }

Write-Host ""
Write-Host "=== RESULTS ===" -ForegroundColor Cyan
Write-Host ""

if ($outlookPaths.Count -gt 0) {
    Write-Host "Outlook found at the following location(s):" -ForegroundColor Green
    $outlookPaths | ForEach-Object { Write-Host "  $_" }
    Write-Host ""

    $primaryPath = $outlookPaths[0]
    Write-Host "Primary path: $primaryPath" -ForegroundColor Green
    Write-Host ""

    Write-Host "To launch Outlook:" -ForegroundColor Yellow
    Write-Host "  & '$primaryPath'" -ForegroundColor Gray
    Write-Host ""

    Write-Host "To launch and keep running for email export script:" -ForegroundColor Yellow
    Write-Host "  Start-Process '$primaryPath'" -ForegroundColor Gray

} else {
    Write-Host "Outlook not found. It may not be installed." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Microsoft Office/Outlook from:" -ForegroundColor Yellow
    Write-Host "  https://www.microsoft.com/en-us/microsoft-365" -ForegroundColor Gray
}

Write-Host ""
