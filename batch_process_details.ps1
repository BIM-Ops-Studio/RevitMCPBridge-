# Batch Process Detail Library - Text Standardization
# Processes all RVT files in the detail library

$pipeName = "RevitMCPBridge2026"
$libraryPath = "D:\Revit Detail Libraries\Revit Details"
$logFile = "D:\RevitMCPBridge2026\logs\batch_process_log.txt"

# Ensure log directory exists
$logDir = Split-Path $logFile -Parent
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Add-Content -Path $logFile -Value $logMessage
    Write-Host $logMessage -ForegroundColor $Color
}

function Send-MCPRequest {
    param($Json, $Timeout = 180000)

    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect($Timeout)
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        $writer = New-Object System.IO.StreamWriter($pipe, $utf8)
        $writer.AutoFlush = $true
        $reader = New-Object System.IO.StreamReader($pipe, $utf8)
        $writer.WriteLine($Json)
        $response = $reader.ReadLine()
        $pipe.Close()
        return $response | ConvertFrom-Json
    } catch {
        return @{ success = $false; error = $_.Exception.Message }
    }
}

Write-Log "========================================" "Cyan"
Write-Log "Starting Batch Text Standardization" "Cyan"
Write-Log "Library: $libraryPath" "Cyan"
Write-Log "========================================" "Cyan"

$startTime = Get-Date
$processed = 0
$failed = 0

while ($true) {
    # Get next file
    $nextJson = '{"method":"getNextFileToProcess","params":{"libraryPath":"' + $libraryPath.Replace("\", "\\") + '"}}'
    $nextResult = Send-MCPRequest -Json $nextJson -Timeout 30000

    if (!$nextResult.success) {
        Write-Log "ERROR getting next file: $($nextResult.error)" "Red"
        break
    }

    if ($nextResult.complete) {
        Write-Log "========================================" "Green"
        Write-Log "BATCH COMPLETE!" "Green"
        Write-Log "Total processed: $processed" "Green"
        Write-Log "Failed: $failed" "Yellow"
        Write-Log "========================================" "Green"
        break
    }

    $filePath = $nextResult.nextFile
    $fileName = $nextResult.fileName
    $remaining = $nextResult.remainingCount
    $total = $nextResult.totalFiles

    Write-Log "[$($total - $remaining + 1)/$total] Processing: $fileName" "Yellow"

    # Process the file
    $escapedPath = $filePath.Replace("\", "\\")
    $processJson = '{"method":"processDetailFile","params":{"filePath":"' + $escapedPath + '","typeName":"3/32 ARIAL NOTES","fontName":"Arial","sizeInches":0.09375,"bold":false,"toUppercase":true,"arrowheadName":"Arrow Filled 20 Degree","saveFile":true}}'

    $processResult = Send-MCPRequest -Json $processJson -Timeout 180000

    if ($processResult.success) {
        Write-Log "  SUCCESS: $($processResult.totalTextNotes) notes, $($processResult.typeChanges) type changes, $($processResult.uppercaseChanges) uppercase" "Green"
        $processed++
        $markSuccess = $true
        $errorMsg = ""
    } else {
        Write-Log "  FAILED: $($processResult.error)" "Red"
        $failed++
        $markSuccess = $false
        $errorMsg = $processResult.error
    }

    # Mark as processed
    $markJson = '{"method":"markFileProcessed","params":{"filePath":"' + $escapedPath + '","success":' + $markSuccess.ToString().ToLower() + ',"errorMessage":"' + $errorMsg.Replace('"', '\"') + '"}}'
    Send-MCPRequest -Json $markJson -Timeout 10000 | Out-Null

    # Progress update every 10 files
    if (($processed + $failed) % 10 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        $avgTime = $elapsed.TotalSeconds / ($processed + $failed)
        $estRemaining = [math]::Round($avgTime * $remaining / 60, 1)
        Write-Log "  Progress: $($processed + $failed) done, $remaining remaining (~$estRemaining min left)" "Cyan"
    }
}

$totalTime = (Get-Date) - $startTime
Write-Log "Total time: $([math]::Round($totalTime.TotalMinutes, 1)) minutes" "Cyan"
