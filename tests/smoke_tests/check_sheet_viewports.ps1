# Check viewports on sheet SP-1.0
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(15000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== CHECKING SP-1.0 SHEET ===" -ForegroundColor Cyan

# Get all sheets to find SP-1.0
$json = '{"method":"getViews","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

$siteSheet = $null
foreach ($view in $result.result.views) {
    if ($view.viewType -eq "DrawingSheet" -and $view.name -like "*SP-1.0*") {
        $siteSheet = $view
        Write-Host "Found sheet: $($view.name) (ID: $($view.id))"
    }
}

if ($siteSheet -eq $null) {
    # Try looking for any sheet with "SITE" in name
    foreach ($view in $result.result.views) {
        if ($view.viewType -eq "DrawingSheet" -and $view.name -like "*SITE*") {
            $siteSheet = $view
            Write-Host "Found sheet: $($view.name) (ID: $($view.id))"
        }
    }
}

# Get viewports on that sheet
if ($siteSheet -ne $null) {
    $json = "{`"method`":`"getViewportsOnSheet`",`"params`":{`"sheetId`":$($siteSheet.id)}}"
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $vpResult = $response | ConvertFrom-Json

    if ($vpResult.success) {
        Write-Host "`nViewports on sheet:" -ForegroundColor Yellow
        foreach ($vp in $vpResult.result.viewports) {
            Write-Host "  Viewport ID: $($vp.viewportId)"
            Write-Host "    View ID: $($vp.viewId)"
            Write-Host "    View Name: $($vp.viewName)"
            Write-Host "    Position: ($($vp.center.x), $($vp.center.y))"
            Write-Host ""
        }
    }
}

# Also check what viewId 29237 actually is
Write-Host "`nView ID 29237 details:" -ForegroundColor Yellow
foreach ($view in $result.result.views) {
    if ($view.id -eq 29237) {
        Write-Host "  Name: $($view.name)"
        Write-Host "  Type: $($view.viewType)"
    }
}

$pipe.Close()
