# Batch Text Standardization Script
# ===================================
# Processes all detail RVT files in the library to standardize text
#
# Configuration:
$config = @{
    LibraryPath = "D:\Revit Detail Libraries\Revit Details"
    TypeName = '3/32" ARIAL NOTES'
    FontName = "Arial"
    SizeInches = 0.09375  # 3/32"
    Bold = $false
    ToUppercase = $true
    LogFile = "D:\RevitMCPBridge2026\logs\batch_standardize.log"
    ProgressFile = "D:\RevitMCPBridge2026\logs\batch_progress.json"
    PipeName = "RevitMCPBridge2026"
    DryRun = $false  # Set to $true to preview without saving
    DelayBetweenFiles = 5  # Seconds to wait between files
}

# MCP Client Functions
function Send-MCPRequest {
    param(
        [string]$Method,
        [hashtable]$Params = @{}
    )

    $request = @{
        method = $Method
        params = $Params
    } | ConvertTo-Json -Depth 10

    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $config.PipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(5000)  # 5 second timeout

        $writer = New-Object System.IO.StreamWriter($pipe)
        $reader = New-Object System.IO.StreamReader($pipe)

        $writer.WriteLine($request)
        $writer.Flush()

        $response = $reader.ReadLine()

        $pipe.Close()

        return $response | ConvertFrom-Json
    }
    catch {
        Write-Host "  ERROR: MCP request failed - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Write-Log {
    param([string]$Message, [string]$Color = "White")

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"

    Write-Host $logEntry -ForegroundColor $Color

    # Append to log file
    $logDir = Split-Path $config.LogFile -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir | Out-Null
    }
    Add-Content -Path $config.LogFile -Value $logEntry
}

function Get-DetailFiles {
    $files = Get-ChildItem -Path $config.LibraryPath -Filter "*.rvt" -Recurse
    return $files | Sort-Object DirectoryName, Name
}

function Process-SingleFile {
    param([string]$FilePath)

    $fileName = Split-Path $FilePath -Leaf
    $folder = Split-Path (Split-Path $FilePath -Parent) -Leaf

    Write-Log "Processing: $folder\$fileName" "Cyan"

    $params = @{
        filePath = $FilePath
        typeName = $config.TypeName
        fontName = $config.FontName
        sizeInches = $config.SizeInches
        bold = $config.Bold
        toUppercase = $config.ToUppercase
        saveFile = -not $config.DryRun
    }

    $result = Send-MCPRequest -Method "processDetailFile" -Params $params

    if ($result -and $result.success) {
        Write-Log "  Notes: $($result.totalTextNotes), Types Changed: $($result.typeChanges), Uppercase: $($result.uppercaseChanges)" "Green"
        return $true
    }
    else {
        $error = if ($result) { $result.error } else { "Connection failed" }
        Write-Log "  FAILED: $error" "Red"
        return $false
    }
}

function Load-Progress {
    if (Test-Path $config.ProgressFile) {
        try {
            return Get-Content $config.ProgressFile | ConvertFrom-Json
        }
        catch {
            return @{ ProcessedFiles = @(); FailedFiles = @() }
        }
    }
    return @{ ProcessedFiles = @(); FailedFiles = @() }
}

function Save-Progress {
    param($Progress)

    $progressDir = Split-Path $config.ProgressFile -Parent
    if (-not (Test-Path $progressDir)) {
        New-Item -ItemType Directory -Path $progressDir | Out-Null
    }

    $Progress | ConvertTo-Json -Depth 10 | Set-Content $config.ProgressFile
}

# Main Execution
function Start-BatchStandardization {
    Write-Log "=" * 60
    Write-Log "DETAIL LIBRARY TEXT STANDARDIZATION"
    Write-Log "=" * 60
    Write-Log "Library: $($config.LibraryPath)"
    Write-Log "Text Type: $($config.TypeName)"
    Write-Log "Font: $($config.FontName)"
    Write-Log "Size: $($config.SizeInches)"" (3/32"")"
    Write-Log "Uppercase: $($config.ToUppercase)"
    Write-Log "Dry Run: $($config.DryRun)"
    Write-Log "=" * 60

    # Get all files
    $allFiles = Get-DetailFiles
    $totalFiles = $allFiles.Count

    Write-Log "Found $totalFiles RVT files to process"

    # Load progress
    $progress = Load-Progress
    $processedSet = @{}
    foreach ($f in $progress.ProcessedFiles) {
        $processedSet[$f] = $true
    }

    $successCount = $progress.ProcessedFiles.Count
    $failCount = 0
    if ($progress.FailedFiles) { $failCount = $progress.FailedFiles.Count }

    Write-Log "Already processed: $successCount files"
    Write-Log ""

    $current = 0
    foreach ($file in $allFiles) {
        $current++
        $filePath = $file.FullName

        # Skip if already processed
        if ($processedSet.ContainsKey($filePath)) {
            Write-Log "[$current/$totalFiles] SKIP (already done): $($file.Name)" "DarkGray"
            continue
        }

        Write-Log "[$current/$totalFiles]" "Yellow"

        $success = Process-SingleFile -FilePath $filePath

        if ($success) {
            $progress.ProcessedFiles += $filePath
            $successCount++
        }
        else {
            if (-not $progress.FailedFiles) {
                $progress.FailedFiles = @()
            }
            $progress.FailedFiles += @{ Path = $filePath; Time = (Get-Date).ToString() }
            $failCount++
        }

        # Save progress after each file
        Save-Progress -Progress $progress

        # Delay between files to let Revit recover
        if ($config.DelayBetweenFiles -gt 0) {
            Start-Sleep -Seconds $config.DelayBetweenFiles
        }
    }

    # Summary
    Write-Log ""
    Write-Log "=" * 60
    Write-Log "SUMMARY"
    Write-Log "=" * 60
    Write-Log "Total files: $totalFiles"
    Write-Log "Successful: $successCount" "Green"
    Write-Log "Failed: $failCount" $(if ($failCount -gt 0) { "Red" } else { "Green" })
    Write-Log "=" * 60
}

# Run the batch process
Start-BatchStandardization
