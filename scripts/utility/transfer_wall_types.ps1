# Transfer Wall Types from Avon Park to SF-project-test-2
# This uses the copyElementsBetweenDocuments method

# Function to call MCP method
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

Write-Host "=== Transfer Wall Types ===" -ForegroundColor Cyan
Write-Host ""

# Wall types to transfer from Avon Park
$wallTypesToTransfer = @(
    @{ sourceId = 1200718; name = "8`" CMU Exterior Wall - W1" },
    @{ sourceId = 1936965; name = "5/8`" Stone Veneer" }
)

# Try to copy elements between documents
Write-Host "Attempting to transfer wall types..." -ForegroundColor Yellow

foreach ($wallType in $wallTypesToTransfer) {
    Write-Host ""
    Write-Host "Transferring: $($wallType.name) (ID: $($wallType.sourceId))" -ForegroundColor White

    $result = Invoke-MCPMethod -Method "copyElementsBetweenDocuments" -Params @{
        sourceDocumentName = "1700 West Sheffield Road"
        targetDocumentName = "SF-project-test-2"
        elementIds = @($wallType.sourceId)
    }

    if ($result.success) {
        Write-Host "  SUCCESS: Transferred" -ForegroundColor Green
        if ($result.newElementIds) {
            Write-Host "  New ID in target: $($result.newElementIds -join ', ')" -ForegroundColor Gray
        }
    } else {
        Write-Host "  FAILED: $($result.error)" -ForegroundColor Red
    }

    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "Transfer complete. Checking target wall types..." -ForegroundColor Yellow

# Verify transfer by checking SF-project-test-2
$switchResult = Invoke-MCPMethod -Method "setActiveDocument" -Params @{ documentName = "SF-project-test-2" }
$types = Invoke-MCPMethod -Method "getWallTypes" -Params @{}

Write-Host ""
Write-Host "CMU Wall Types in SF-project-test-2:" -ForegroundColor Cyan
foreach ($type in $types.wallTypes) {
    if ($type.name -like "*CMU*W1*" -or $type.name -like "*Stone Veneer*") {
        Write-Host "  $($type.wallTypeId): $($type.name) (width: $([math]::Round($type.width * 12, 2))`")" -ForegroundColor Green
    }
}
