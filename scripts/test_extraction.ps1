# Test extraction on single detail file
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

# Open the parapet file
Write-Host "Opening PARAPET WALL DTL.rvt..." -ForegroundColor Cyan
$result = Invoke-MCP -Method "openProject" -Params @{
    filePath = "D:\Revit Detail Libraries\Revit Details\01 - Roof Details\PARAPET WALL DTL.rvt"
}
Write-Host "Open result: $($result.success)"
Start-Sleep -Seconds 3

# Get ALL views
Write-Host "`nGetting all views..." -ForegroundColor Yellow
$views = Invoke-MCP -Method "getViews"
Write-Host "Views found: $($views.views.Count)" -ForegroundColor Green
foreach ($v in $views.views) {
    Write-Host "  [$($v.viewType)] $($v.name)"
}

# Get lines
Write-Host "`nGetting lines..." -ForegroundColor Yellow
$lines = Invoke-MCP -Method "getElementsByCategory" -Params @{categoryName = "OST_Lines"}
if ($lines.elements) {
    Write-Host "Lines: $($lines.elements.Count)" -ForegroundColor Green
    $lineStyles = $lines.elements | Select-Object -ExpandProperty typeName -Unique
    foreach ($s in $lineStyles) { Write-Host "  Style: $s" }
}

# Get text
Write-Host "`nGetting text notes..." -ForegroundColor Yellow
$texts = Invoke-MCP -Method "getElementsByCategory" -Params @{categoryName = "OST_TextNotes"}
if ($texts.elements) {
    Write-Host "Text Notes: $($texts.elements.Count)" -ForegroundColor Green
}

# Get detail components
Write-Host "`nGetting detail components..." -ForegroundColor Yellow
$details = Invoke-MCP -Method "getElementsByCategory" -Params @{categoryName = "OST_DetailComponents"}
if ($details.elements) {
    Write-Host "Detail Components: $($details.elements.Count)" -ForegroundColor Green
    $details.elements | Select-Object -First 10 | ForEach-Object {
        Write-Host "  - $($_.typeName) [$($_.familyName)]"
    }
}

# Get dimensions
Write-Host "`nGetting dimensions..." -ForegroundColor Yellow
$dims = Invoke-MCP -Method "getElementsByCategory" -Params @{categoryName = "OST_Dimensions"}
if ($dims.elements) {
    Write-Host "Dimensions: $($dims.elements.Count)" -ForegroundColor Green
}

# Close
Write-Host "`nClosing file..." -ForegroundColor Yellow
$close = Invoke-MCP -Method "closeProject" -Params @{save = $false}
Write-Host "Done!" -ForegroundColor Green

$pipe.Close()
