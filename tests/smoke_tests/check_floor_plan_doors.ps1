# Navigate to first floor plan and check doors
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== FINDING FLOOR PLANS ===" -ForegroundColor Cyan

# Get views
$json = '{"method":"getViews","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

# Find floor plan views
$floorPlans = @()
foreach ($view in $result.result.views) {
    if ($view.viewType -eq "FloorPlan" -and $view.name -like "*Floor*") {
        $floorPlans += $view
        Write-Host "  $($view.name) (ID: $($view.id))"
    }
}

# Navigate to a floor plan (try 2nd floor as it usually has units)
foreach ($plan in $floorPlans) {
    if ($plan.name -like "*2ND*" -or $plan.name -like "*Second*") {
        Write-Host "`nNavigating to: $($plan.name)" -ForegroundColor Yellow
        $json = "{`"method`":`"setActiveView`",`"params`":{`"viewId`":$($plan.id)}}"
        $writer.WriteLine($json)
        $response = $reader.ReadLine()
        break
    }
}

Start-Sleep -Seconds 1

# Zoom to fit
$json = '{"method":"zoomToFit","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

$pipe.Close()
Write-Host "Ready for screenshot"
