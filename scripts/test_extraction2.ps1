# Test extraction - detailed
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
    $response = $reader.ReadLine()
    return ($response | ConvertFrom-Json)
}

# Open file
Write-Host "Opening file..." -ForegroundColor Cyan
$result = Invoke-MCP -Method "openProject" -Params @{
    filePath = "D:\Revit Detail Libraries\Revit Details\01 - Roof Details\PARAPET WALL DTL.rvt"
}
Write-Host "Opened: $($result.result.documentTitle)"
Start-Sleep -Seconds 3

# Get project info
Write-Host "`nGetting project info..." -ForegroundColor Yellow
$info = Invoke-MCP -Method "getProjectInfo"
$info | ConvertTo-Json -Depth 5

# Get open documents
Write-Host "`nGetting open documents..." -ForegroundColor Yellow
$docs = Invoke-MCP -Method "getOpenDocuments"
$docs | ConvertTo-Json -Depth 3

# Try getting active view
Write-Host "`nGetting active view..." -ForegroundColor Yellow
$activeView = Invoke-MCP -Method "getActiveView"
$activeView | ConvertTo-Json -Depth 3

# Get all elements regardless of category
Write-Host "`nGetting all elements (no filter)..." -ForegroundColor Yellow
$all = Invoke-MCP -Method "getElements" -Params @{}
Write-Host "Total: $($all.elements.Count) elements"
if ($all.elements) {
    $all.elements | Group-Object category | Sort-Object Count -Descending | Select-Object -First 15 | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Count)"
    }
}

# Close
Write-Host "`nClosing..." -ForegroundColor Yellow
Invoke-MCP -Method "closeProject" -Params @{save = $false}

$pipe.Close()
