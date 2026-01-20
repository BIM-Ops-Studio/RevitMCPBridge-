# Replicate detail lines from source view to target view
# Source: 2136700 (SECTION DETAIL @ GARAGE ROOF)
# Target: 2238350 (New Drafting View)

param(
    [int]$BatchSize = 50,
    [switch]$DryRun
)

$sourceViewId = 2136700
$targetViewId = 2238350

# Coordinate offsets (from crop region)
$offsetX = 31.28
$offsetZ = 2.17

Write-Host "=== Detail Line Replication ===" -ForegroundColor Cyan
Write-Host "Source: $sourceViewId -> Target: $targetViewId"
Write-Host "Offset: X=$offsetX, Z=$offsetZ"

# Get detail lines from source
$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

$json = @{method = "getDetailLinesInViewVA"; params = @{viewId = $sourceViewId}} | ConvertTo-Json -Compress
$writer.WriteLine($json)
$writer.Flush()
Start-Sleep -Milliseconds 3000
$response = $reader.ReadLine()
$data = $response | ConvertFrom-Json

if (-not $data.success) {
    Write-Host "Failed to get detail lines: $($data.error)" -ForegroundColor Red
    $pipe.Close()
    exit 1
}

$lines = $data.result.lines
Write-Host "Retrieved $($lines.Count) detail lines" -ForegroundColor Green

# Process in batches
$successCount = 0
$failCount = 0
$totalBatches = [Math]::Ceiling($lines.Count / $BatchSize)

for ($batch = 0; $batch -lt $totalBatches; $batch++) {
    $start = $batch * $BatchSize
    $end = [Math]::Min($start + $BatchSize, $lines.Count)
    Write-Host "`nBatch $($batch + 1)/$totalBatches (lines $start-$($end-1))..." -ForegroundColor Yellow

    for ($i = $start; $i -lt $end; $i++) {
        $line = $lines[$i]

        # Normalize coordinates (Z in source is vertical, maps to Y in drafting view)
        $x1 = [Math]::Round($line.start.x - $offsetX, 4)
        $y1 = [Math]::Round($line.start.z - $offsetZ, 4)
        $x2 = [Math]::Round($line.end.x - $offsetX, 4)
        $y2 = [Math]::Round($line.end.z - $offsetZ, 4)

        $lineStyle = $line.lineStyle
        if (-not $lineStyle) { $lineStyle = "Thin Lines" }

        if ($DryRun) {
            Write-Host "  Would create: ($x1, $y1) -> ($x2, $y2) [$lineStyle]"
            $successCount++
            continue
        }

        $createJson = @{
            method = "createDetailLineInDraftingView"
            params = @{
                viewId = $targetViewId
                startX = $x1
                startY = $y1
                endX = $x2
                endY = $y2
                lineStyle = $lineStyle
            }
        } | ConvertTo-Json -Compress

        $writer.WriteLine($createJson)
        $writer.Flush()
        Start-Sleep -Milliseconds 100

        $createResponse = $reader.ReadLine()
        $createResult = $createResponse | ConvertFrom-Json

        if ($createResult.success) {
            $successCount++
        } else {
            $failCount++
            if ($failCount -le 5) {
                Write-Host "  Line $i failed: $($createResult.error)" -ForegroundColor Red
            }
        }
    }

    Write-Host "  Batch complete. Success: $successCount, Failed: $failCount"
}

$pipe.Close()

Write-Host "`n=== Replication Complete ===" -ForegroundColor Green
Write-Host "Total lines: $($lines.Count)"
Write-Host "Created: $successCount"
Write-Host "Failed: $failCount"
