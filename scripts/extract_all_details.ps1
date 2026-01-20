# =============================================================================
# BATCH DETAIL LIBRARY EXTRACTION
# =============================================================================
# Extracts all detail components, text, dimensions from every .rvt file
# in the Revit Detail Libraries folder. Saves structured JSON for AI learning.
#
# Usage: .\extract_all_details.ps1 [-StartIndex 0] [-MaxFiles 0] [-Category "all"]
#
# Parameters:
#   -StartIndex: Skip first N files (for resuming)
#   -MaxFiles: Limit number of files (0 = all)
#   -Category: Filter by category folder name (e.g., "01 - Roof Details")
# =============================================================================

param(
    [int]$StartIndex = 0,
    [int]$MaxFiles = 0,
    [string]$Category = "all"
)

$ErrorActionPreference = "Continue"

# Configuration
$LibraryRoot = "D:\Revit Detail Libraries\Revit Details"
$OutputDir = "D:\RevitMCPBridge2026\knowledge\detail_library\extractions"
$LogFile = "D:\RevitMCPBridge2026\knowledge\detail_library\extraction_log.txt"
$ProgressFile = "D:\RevitMCPBridge2026\knowledge\detail_library\extraction_progress.json"

# Ensure output directory exists
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# MCP Connection
$pipe = $null
$writer = $null
$reader = $null

function Connect-MCP {
    Write-Host "Connecting to Revit MCP..." -ForegroundColor Cyan
    try {
        $script:pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.', 'RevitMCPBridge2026', [System.IO.Pipes.PipeDirection]::InOut)
        $script:pipe.Connect(10000)
        $script:writer = [System.IO.StreamWriter]::new($script:pipe)
        $script:reader = [System.IO.StreamReader]::new($script:pipe)
        Write-Host "Connected!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Failed to connect: $_" -ForegroundColor Red
        return $false
    }
}

function Disconnect-MCP {
    if ($script:pipe) {
        $script:pipe.Close()
        $script:pipe = $null
    }
}

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})

    try {
        $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 10 -Compress
        $script:writer.WriteLine($json)
        $script:writer.Flush()
        Start-Sleep -Milliseconds 300
        $response = $script:reader.ReadLine()
        return ($response | ConvertFrom-Json)
    }
    catch {
        Write-Host "MCP Error: $_" -ForegroundColor Red
        return @{success = $false; error = $_.ToString()}
    }
}

function Open-RevitFile {
    param([string]$FilePath)

    Write-Host "  Opening: $([System.IO.Path]::GetFileName($FilePath))..." -NoNewline
    $result = Invoke-MCP -Method "openProject" -Params @{
        filePath = $FilePath
    }

    if ($result.success) {
        Write-Host " OK" -ForegroundColor Green
        Start-Sleep -Milliseconds 2000  # Let Revit settle
        return $true
    }
    else {
        Write-Host " FAILED: $($result.error)" -ForegroundColor Red
        return $false
    }
}

function Close-RevitFile {
    Write-Host "  Closing file..." -NoNewline
    # Note: closeProject may fail for active document - that's OK
    $result = Invoke-MCP -Method "closeProject" -Params @{
        save = $false
    }
    if ($result.success) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        # Try opening a blank/home view instead
        Write-Host " (will close on next open)" -ForegroundColor Yellow
    }
    Start-Sleep -Milliseconds 500
}

function Extract-DetailData {
    param([string]$FilePath)

    $extraction = @{
        file = [System.IO.Path]::GetFileName($FilePath)
        filePath = $FilePath
        extractedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        activeView = $null
        views = @()
        elementsInView = @()
        textNotes = @()
        error = $null
    }

    try {
        # Get active view info
        Write-Host "  Getting view info..." -NoNewline
        $activeView = Invoke-MCP -Method "getActiveView"
        if ($activeView.success) {
            $extraction.activeView = @{
                id = $activeView.viewId
                name = $activeView.viewName
                type = $activeView.viewType
                scale = $activeView.scale
            }
            Write-Host " $($activeView.viewName) (1:$($activeView.scale))" -ForegroundColor Cyan
            $viewId = $activeView.viewId
        }
        else {
            Write-Host " Failed" -ForegroundColor Red
            return $extraction
        }

        # Get all views in document
        Write-Host "  Getting all views..." -NoNewline
        $views = Invoke-MCP -Method "getViews"
        if ($views.success -and $views.views) {
            $extraction.views = $views.views | ForEach-Object {
                @{
                    id = $_.id
                    name = $_.name
                    type = $_.viewType
                    scale = $_.scale
                }
            }
            Write-Host " $($extraction.views.Count)" -ForegroundColor Cyan
        }
        else {
            Write-Host " 0" -ForegroundColor Yellow
        }

        # Get elements in the active view
        Write-Host "  Getting elements in view..." -NoNewline
        $elements = Invoke-MCP -Method "getElementsInView" -Params @{viewId = $viewId}
        if ($elements.success -and $elements.elements) {
            $extraction.elementsInView = $elements.elements | ForEach-Object {
                @{
                    id = $_.id
                    category = $_.category
                    typeName = $_.typeName
                    familyName = $_.familyName
                }
            }
            Write-Host " $($extraction.elementsInView.Count)" -ForegroundColor Cyan

            # Group by category
            $grouped = $extraction.elementsInView | Group-Object category
            foreach ($g in $grouped) {
                Write-Host "    $($g.Name): $($g.Count)" -ForegroundColor DarkGray
            }
        }
        else {
            Write-Host " 0" -ForegroundColor Yellow
        }

        # Get text elements
        Write-Host "  Getting text notes..." -NoNewline
        $texts = Invoke-MCP -Method "getTextElements"
        if ($texts.success -and $texts.texts) {
            $extraction.textNotes = $texts.texts | ForEach-Object {
                $_.text
            } | Select-Object -Unique
            Write-Host " $($extraction.textNotes.Count)" -ForegroundColor Cyan
        }
        else {
            Write-Host " 0" -ForegroundColor Yellow
        }
    }
    catch {
        $extraction.error = $_.ToString()
        Write-Host "  ERROR: $_" -ForegroundColor Red
    }

    return $extraction
}

function Save-Extraction {
    param($Extraction, [string]$Category)

    # Create category subfolder
    $categoryDir = Join-Path $OutputDir ($Category -replace '[^\w\-]', '_')
    New-Item -ItemType Directory -Force -Path $categoryDir | Out-Null

    # Save individual file
    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($Extraction.file) + ".json"
    $filePath = Join-Path $categoryDir $fileName
    $Extraction | ConvertTo-Json -Depth 10 | Set-Content $filePath -Encoding UTF8

    return $filePath
}

function Update-Progress {
    param([int]$Processed, [int]$Total, [int]$Success, [int]$Failed, [string]$CurrentFile)

    $progress = @{
        lastUpdated = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        processed = $Processed
        total = $Total
        success = $Success
        failed = $Failed
        percentComplete = [math]::Round(($Processed / $Total) * 100, 1)
        currentFile = $CurrentFile
        estimatedRemaining = if ($Processed -gt 0) {
            $avgTime = 30  # seconds per file estimate
            $remaining = ($Total - $Processed) * $avgTime
            [TimeSpan]::FromSeconds($remaining).ToString("hh\:mm\:ss")
        } else { "calculating..." }
    }

    $progress | ConvertTo-Json | Set-Content $ProgressFile -Encoding UTF8
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  REVIT DETAIL LIBRARY BATCH EXTRACTION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Get all .rvt files
Write-Host "Scanning for .rvt files..." -ForegroundColor Yellow
$allFiles = Get-ChildItem -Path $LibraryRoot -Filter "*.rvt" -Recurse |
    Where-Object {
        $Category -eq "all" -or $_.Directory.Name -like "*$Category*"
    } |
    Select-Object -ExpandProperty FullName

Write-Host "Found $($allFiles.Count) files" -ForegroundColor Green

# Apply filters
if ($StartIndex -gt 0) {
    Write-Host "Skipping first $StartIndex files (resume mode)" -ForegroundColor Yellow
    $allFiles = $allFiles | Select-Object -Skip $StartIndex
}

if ($MaxFiles -gt 0 -and $allFiles.Count -gt $MaxFiles) {
    Write-Host "Limiting to $MaxFiles files" -ForegroundColor Yellow
    $allFiles = $allFiles | Select-Object -First $MaxFiles
}

$totalFiles = $allFiles.Count
Write-Host ""
Write-Host "Processing $totalFiles files..." -ForegroundColor Cyan
Write-Host "Output: $OutputDir" -ForegroundColor Gray
Write-Host ""

# Connect to MCP
if (-not (Connect-MCP)) {
    Write-Host "Cannot proceed without MCP connection. Is Revit open?" -ForegroundColor Red
    exit 1
}

# Process files
$processed = 0
$success = 0
$failed = 0
$startTime = Get-Date

foreach ($file in $allFiles) {
    $processed++
    $category = (Get-Item $file).Directory.Name

    Write-Host ""
    Write-Host "[$processed/$totalFiles] $category" -ForegroundColor White
    Write-Host "  File: $([System.IO.Path]::GetFileName($file))" -ForegroundColor Gray

    # Update progress
    Update-Progress -Processed $processed -Total $totalFiles -Success $success -Failed $failed -CurrentFile $file

    # Open file
    if (Open-RevitFile -FilePath $file) {
        # Extract data
        $extraction = Extract-DetailData -FilePath $file

        if (-not $extraction.error) {
            # Save extraction
            $savedPath = Save-Extraction -Extraction $extraction -Category $category
            Write-Host "  Saved: $([System.IO.Path]::GetFileName($savedPath))" -ForegroundColor Green
            $success++

            # Log success
            "$((Get-Date).ToString('HH:mm:ss')) SUCCESS: $file" | Add-Content $LogFile
        }
        else {
            $failed++
            "$((Get-Date).ToString('HH:mm:ss')) ERROR: $file - $($extraction.error)" | Add-Content $LogFile
        }

        # Close file
        Close-RevitFile
    }
    else {
        $failed++
        "$((Get-Date).ToString('HH:mm:ss')) FAILED TO OPEN: $file" | Add-Content $LogFile
    }

    # Progress update
    $elapsed = (Get-Date) - $startTime
    $avgPerFile = $elapsed.TotalSeconds / $processed
    $remaining = ($totalFiles - $processed) * $avgPerFile
    Write-Host "  Progress: $([math]::Round(($processed/$totalFiles)*100, 1))% | ETA: $([TimeSpan]::FromSeconds($remaining).ToString('hh\:mm\:ss'))" -ForegroundColor DarkGray
}

# Cleanup
Disconnect-MCP

# Final summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  EXTRACTION COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Total Files: $totalFiles" -ForegroundColor White
Write-Host "  Successful:  $success" -ForegroundColor Green
Write-Host "  Failed:      $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host "  Duration:    $($elapsed.ToString('hh\:mm\:ss'))" -ForegroundColor Gray
Write-Host ""
Write-Host "  Output: $OutputDir" -ForegroundColor Gray
Write-Host "  Log:    $LogFile" -ForegroundColor Gray
Write-Host ""
