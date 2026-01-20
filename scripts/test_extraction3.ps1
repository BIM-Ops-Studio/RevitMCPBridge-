# Test extraction - using view-specific methods
$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(10000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

function Invoke-MCP {
    param([string]$Method, [hashtable]$Params = @{})
    $json = @{method = $Method; params = $Params} | ConvertTo-Json -Depth 10 -Compress
    $writer.WriteLine($json)
    $writer.Flush()
    Start-Sleep -Milliseconds 500
    return ($reader.ReadLine() | ConvertFrom-Json)
}

Write-Host "=== TESTING VIEW-SPECIFIC EXTRACTION ===" -ForegroundColor Cyan

# Get active view first (parapet file should still be open)
$activeView = Invoke-MCP -Method "getActiveView"
$viewId = $activeView.viewId
Write-Host "Active View: $($activeView.viewName) (ID: $viewId)" -ForegroundColor Green

# Get elements in view
Write-Host "`nGetting elements in view..." -ForegroundColor Yellow
$elementsInView = Invoke-MCP -Method "getElementsInView" -Params @{viewId = $viewId}
if ($elementsInView.success -and $elementsInView.elements) {
    Write-Host "Elements in view: $($elementsInView.elements.Count)" -ForegroundColor Green
    $elementsInView.elements | Group-Object category | Sort-Object Count -Descending | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Count)"
    }
} else {
    Write-Host "Error: $($elementsInView.error)" -ForegroundColor Red
}

# Get detail lines in view
Write-Host "`nGetting detail lines in view..." -ForegroundColor Yellow
$lines = Invoke-MCP -Method "getDetailLinesInView" -Params @{viewId = $viewId}
if ($lines.success -and $lines.lines) {
    Write-Host "Detail Lines: $($lines.lines.Count)" -ForegroundColor Green
    $lines.lines | Select-Object -First 5 | ForEach-Object {
        Write-Host "  Style: $($_.lineStyle)"
    }
    $lineStyles = $lines.lines | Group-Object lineStyle
    Write-Host "Line styles used:"
    $lineStyles | ForEach-Object { Write-Host "  $($_.Name): $($_.Count)" }
} else {
    Write-Host "Error or no lines: $($lines.error)" -ForegroundColor Yellow
}

# Get text elements
Write-Host "`nGetting text elements..." -ForegroundColor Yellow
$texts = Invoke-MCP -Method "getTextElements" -Params @{}
if ($texts.success -and $texts.texts) {
    Write-Host "Text Elements: $($texts.texts.Count)" -ForegroundColor Green
    $texts.texts | Select-Object -First 10 | ForEach-Object {
        Write-Host "  - $($_.text)"
    }
} else {
    Write-Host "Error or no text: $($texts.error)" -ForegroundColor Yellow
}

# Get dimensions in view
Write-Host "`nGetting dimensions in view..." -ForegroundColor Yellow
$dims = Invoke-MCP -Method "getDimensionsInView" -Params @{viewId = $viewId}
if ($dims.success -and $dims.dimensions) {
    Write-Host "Dimensions: $($dims.dimensions.Count)" -ForegroundColor Green
} else {
    Write-Host "Error or no dims: $($dims.error)" -ForegroundColor Yellow
}

$pipe.Close()
Write-Host "`nDone!" -ForegroundColor Green
