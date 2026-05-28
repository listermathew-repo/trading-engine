<#
.SYNOPSIS
Export all emails with stephen.lister@virgin.net to NotebookLM-ready Markdown files.

.DESCRIPTION
Searches all Outlook folders (Inbox, Sent, Archive, Deleted, Junk) for emails involving
stephen.lister@virgin.net, groups them by conversation thread, and exports to individual
markdown files ready for NotebookLM.

.REQUIREMENTS
- Outlook must be RUNNING before executing this script
- Run from PowerShell (not as Administrator usually, unless you get access errors)

.USAGE
    .\export-outlook-stephen.ps1
    .\export-outlook-stephen.ps1 -EmailAddress "other@example.com" -OutputDir ".\export"
#>

param(
    [string]$EmailAddress = "stephen.lister@virgin.net",
    [string]$OutputDir = ".\stephen_lister_export"
)

# Initialize Outlook COM
try {
    $outlook = New-Object -ComObject Outlook.Application
} catch {
    Write-Host "ERROR: Could not connect to Outlook. Make sure Outlook is running." -ForegroundColor Red
    exit 1
}

$namespace = $outlook.GetNamespace("MAPI")

# Get all folders to search
$folders = @(
    $namespace.GetDefaultFolder(6),   # Inbox (6)
    $namespace.GetDefaultFolder(5),   # Sent Items (5)
    $namespace.GetDefaultFolder(3),   # Deleted Items (3)
    $namespace.GetDefaultFolder(4)    # Junk (4)
)

# Try to get Archive if it exists
try {
    $archive = $namespace.Folders.Item("Archive")
    if ($archive) { $folders += $archive }
} catch { }

Write-Host "Searching for emails with $EmailAddress..." -ForegroundColor Cyan

# STEP 1: SEARCH - Find all matching emails across all folders
$allEmails = @()
$emailsByThread = @{}

foreach ($folder in $folders) {
    try {
        $items = $folder.Items
        foreach ($email in $items) {
            # Check if email matches sender, recipient, or cc
            $matches = $false

            if ($email.SenderEmailAddress -eq $EmailAddress) { $matches = $true }
            if ($email.To -like "*$EmailAddress*") { $matches = $true }
            if ($email.CC -like "*$EmailAddress*") { $matches = $true }
            if ($email.BCC -like "*$EmailAddress*") { $matches = $true }

            if ($matches) {
                $allEmails += $email

                # Group by conversation topic (thread identifier)
                $threadId = $email.ConversationTopic
                if (-not $threadId) { $threadId = $email.Subject }

                if (-not $emailsByThread[$threadId]) {
                    $emailsByThread[$threadId] = @()
                }
                $emailsByThread[$threadId] += $email
            }
        }
    } catch {
        Write-Warning "Error reading folder: $_"
    }
}

$totalCount = $allEmails.Count
Write-Host "Found $totalCount emails across all folders." -ForegroundColor Green
Write-Host "Grouped into $($emailsByThread.Count) conversation threads." -ForegroundColor Green
Write-Host ""

if ($totalCount -eq 0) {
    Write-Host "No emails found. Exiting." -ForegroundColor Yellow
    exit 0
}

# STEP 2: GROUP - Build manifest table
Write-Host "Building manifest..." -ForegroundColor Cyan
$manifest = @()

foreach ($threadId in $emailsByThread.Keys) {
    $emails = $emailsByThread[$threadId] | Sort-Object SentOn

    $subject = $emails[0].Subject -replace "^(Re:|Fwd:|\[.*?\])\s*", ""
    $participants = @()

    foreach ($email in $emails) {
        if ($email.SenderEmailAddress -and $participants -notcontains $email.SenderEmailAddress) {
            $participants += $email.SenderEmailAddress
        }
        if ($email.To) {
            $toList = $email.To -split ";" | ForEach-Object { $_.Trim() }
            foreach ($addr in $toList) {
                if ($addr -and $participants -notcontains $addr) {
                    $participants += $addr
                }
            }
        }
    }

    $dateStart = $emails[0].SentOn
    $dateEnd = $emails[-1].SentOn

    $manifest += [PSCustomObject]@{
        Subject     = $subject
        Participants = $participants.Count
        DateStart   = $dateStart.ToString("yyyy-MM-dd")
        DateEnd     = $dateEnd.ToString("yyyy-MM-dd")
        MessageCount = $emails.Count
        ThreadId    = $threadId
    }
}

Write-Host ""
Write-Host "=== THREAD MANIFEST ===" -ForegroundColor Yellow
$manifest | Format-Table -Property Subject, Participants, DateStart, DateEnd, MessageCount -AutoSize
Write-Host ""
Write-Host "Total threads: $($manifest.Count)" -ForegroundColor Green
Write-Host ""

# STEP 3: EXPORT - Create markdown files
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "Exporting to $OutputDir..." -ForegroundColor Cyan

$exportedThreads = @()

foreach ($threadManifest in $manifest) {
    $threadId = $threadManifest.ThreadId
    $emails = $emailsByThread[$threadId] | Sort-Object SentOn

    # Create filename from date + slugified subject
    $firstDate = $emails[0].SentOn
    $datePrefix = $firstDate.ToString("yyyy-MM-dd")
    $slugSubject = $threadManifest.Subject -replace "[^\w\s-]", "" -replace "\s+", "-" -replace "-+", "-" -replace "^-|-$", ""
    $slugSubject = $slugSubject.Substring(0, [Math]::Min(60, $slugSubject.Length))

    $filename = "${datePrefix}_${slugSubject}.md"
    $filepath = Join-Path $OutputDir $filename

    # Build markdown content
    $md = @()
    $md += "---"
    $md += "thread_subject: `"$($threadManifest.Subject)`""
    $md += "participants: [$(($threadManifest | Select-Object -ExpandProperty Participants))]"
    $md += "date_start: $($threadManifest.DateStart)"
    $md += "date_end: $($threadManifest.DateEnd)"
    $md += "message_count: $($threadManifest.MessageCount)"
    $md += "---"
    $md += ""
    $md += "# $($threadManifest.Subject)"
    $md += ""

    # Add each message
    $messageNum = 1
    foreach ($email in $emails) {
        $sender = $email.SenderName
        $date = $email.SentOn.ToString("yyyy-MM-dd HH:mm")

        $md += "## Message $messageNum - $sender - $date"

        # Get body - strip HTML if needed
        $body = $email.Body
        if ($email.HTMLBody) {
            # Simple HTML to plaintext (remove tags)
            $body = $email.HTMLBody -replace "<[^>]+>", ""
            $body = $body -replace "&nbsp;", " " -replace "&lt;", "<" -replace "&gt;", ">" -replace "&amp;", "&"
        }

        # Strip common signature patterns and quoted replies
        $body = $body -split "`n" | Where-Object {
            $_ -notmatch "^--\s*$" -and
            $_ -notmatch "^\s*_+\s*$" -and
            $_ -notmatch "^From: " -and
            $_ -notmatch "^Sent: " -and
            $_ -notmatch "^To: " -and
            $_ -notmatch "^Subject: " -and
            $_ -notmatch "^Cc: " -and
            $_ -notmatch "^(Best regards|Thanks|Regards|Sincerely)," -and
            $_ -notmatch "^This email|Confidential|Disclaimer|privilege"
        } | Join-String -Separator "`n"

        # Clean up excessive whitespace
        $body = $body.Trim() -replace "\n\s*\n\s*\n", "`n`n"

        $md += $body
        $md += ""

        # Add attachments if any
        if ($email.Attachments.Count -gt 0) {
            $attachmentNames = @()
            foreach ($att in $email.Attachments) {
                $attachmentNames += $att.FileName
            }
            $md += "**Attachments:** " + ($attachmentNames -join ", ")
            $md += ""
        }

        $messageNum++
    }

    # Write file
    $md -join "`n" | Out-File -FilePath $filepath -Encoding UTF8

    $exportedThreads += [PSCustomObject]@{
        Filename     = $filename
        Subject      = $threadManifest.Subject
        DateStart    = $threadManifest.DateStart
        DateEnd      = $threadManifest.DateEnd
        MessageCount = $threadManifest.MessageCount
    }

    Write-Host "  + $filename ($($threadManifest.MessageCount) messages)"
}

# STEP 4: INDEX - Create manifest file
Write-Host "Creating index..." -ForegroundColor Cyan

$indexMd = @()
$indexMd += "# Email Export Index"
$indexMd += ""
$indexMd += "**Correspondent:** stephen.lister@virgin.net"
$indexMd += "**Export Date:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$indexMd += ""
$indexMd += "## Summary"
$indexMd += "- **Total Threads:** $($exportedThreads.Count)"
$indexMd += "- **Total Messages:** $($exportedThreads | Measure-Object -Property MessageCount -Sum | Select-Object -ExpandProperty Sum)"
$indexMd += "- **Date Range:** $($exportedThreads | Sort-Object DateStart | Select-Object -First 1 -ExpandProperty DateStart) to $($exportedThreads | Sort-Object DateEnd -Descending | Select-Object -First 1 -ExpandProperty DateEnd)"
$indexMd += ""
$indexMd += "## Threads"
$indexMd += ""
$indexMd += "| Filename | Subject | Start | End | Messages |"
$indexMd += "|----------|---------|-------|-----|----------|"

foreach ($thread in ($exportedThreads | Sort-Object DateStart)) {
    $indexMd += "| [$($thread.Filename)]($($thread.Filename)) | $($thread.Subject) | $($thread.DateStart) | $($thread.DateEnd) | $($thread.MessageCount) |"
}

$indexMd -join "`n" | Out-File -FilePath (Join-Path $OutputDir "00_INDEX.md") -Encoding UTF8

Write-Host "  + 00_INDEX.md created"
Write-Host ""
Write-Host "=== EXPORT COMPLETE ===" -ForegroundColor Green
Write-Host "Output directory: $((Get-Item $OutputDir).FullName)"
Write-Host "Ready for NotebookLM import!"
