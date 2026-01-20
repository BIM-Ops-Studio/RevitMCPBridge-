# Delete previously placed elements from SF-project-test-2
# Clears the project for retesting

# MCP helper function
function Invoke-MCPMethod {
    param(
        [string]$Method,
        [hashtable]$Params = @{}
    )

    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    $request = @{
        method = $Method
        params = $Params
    } | ConvertTo-Json -Depth 10 -Compress

    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    return $response | ConvertFrom-Json
}

Write-Host "=== Delete Previously Placed Elements ===" -ForegroundColor Cyan
Write-Host ""

# Switch to target project
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
Write-Host "Active document: $($switchResult.result.activatedDocument)" -ForegroundColor Gray
Write-Host ""

# Load placement results
$results = Get-Content "D:\RevitMCPBridge2026\family_placement_results_complete.json" | ConvertFrom-Json

$elementIds = @()
foreach ($item in $results.success) {
    $elementIds += $item.instanceId
}

Write-Host "Elements to delete: $($elementIds.Count)" -ForegroundColor Yellow

if ($elementIds.Count -gt 0) {
    $deleteResult = Invoke-MCPMethod -Method "deleteElements" -Params @{
        elementIds = $elementIds
    }

    if ($deleteResult.success) {
        Write-Host "Deleted $($deleteResult.deletedCount) elements" -ForegroundColor Green
    } else {
        Write-Host "Error: $($deleteResult.error)" -ForegroundColor Red
    }
} else {
    Write-Host "No elements to delete" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done. Project is ready for retesting." -ForegroundColor Cyan
