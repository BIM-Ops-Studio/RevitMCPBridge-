# Navigate to door schedule sheet and check viewports
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== FINDING DOOR SCHEDULE SHEETS ===" -ForegroundColor Cyan

# Get all sheets
$json = '{"method":"getViews","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

$doorSheets = @()
foreach ($view in $result.result.views) {
    if ($view.viewType -eq "DrawingSheet") {
        if ($view.name -like "*A7*" -or $view.name -like "*DOOR*") {
            $doorSheets += $view
            Write-Host "  Sheet: $($view.name) (ID: $($view.id))"
        }
    }
}

# Navigate to first door sheet (likely A7.1)
foreach ($sheet in $doorSheets) {
    if ($sheet.name -like "*A7.1*" -or ($sheet.name -like "*DOOR*" -and $sheet.name -like "*SCHEDULE*")) {
        Write-Host "`nNavigating to: $($sheet.name)" -ForegroundColor Yellow
        $json = "{`"method`":`"setActiveView`",`"params`":{`"viewId`":$($sheet.id)}}"
        $writer.WriteLine($json)
        $response = $reader.ReadLine()

        # Get viewports on this sheet
        $json = "{`"method`":`"getViewportsOnSheet`",`"params`":{`"sheetId`":$($sheet.id)}}"
        $writer.WriteLine($json)
        $response = $reader.ReadLine()
        $vpResult = $response | ConvertFrom-Json

        if ($vpResult.success) {
            Write-Host "`nViewports on sheet:" -ForegroundColor Yellow
            foreach ($vp in $vpResult.result.viewports) {
                Write-Host "  View: $($vp.viewName) (ViewId: $($vp.viewId))"
            }
        }
        break
    }
}

# Also check DOOR SCHEDULES sheet (1545074)
Write-Host "`n=== DOOR SCHEDULES SHEET (1545074) ===" -ForegroundColor Cyan
$json = '{"method":"getViewportsOnSheet","params":{"sheetId":1545074}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$vpResult = $response | ConvertFrom-Json

if ($vpResult.success) {
    Write-Host "Viewports:" -ForegroundColor Yellow
    foreach ($vp in $vpResult.result.viewports) {
        Write-Host "  View: $($vp.viewName) (ViewId: $($vp.viewId))"
    }
}

$pipe.Close()
