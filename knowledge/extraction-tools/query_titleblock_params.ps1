# Query titleblock parameters to find firm name
$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipeClient.Connect(5000)

$reader = New-Object System.IO.StreamReader($pipeClient)
$writer = New-Object System.IO.StreamWriter($pipeClient)
$writer.AutoFlush = $true

# First get one titleblock element to examine its parameters
$request = @{
    jsonrpc = "2.0"
    id = 1
    method = "getElements"
    params = @{
        category = "TitleBlocks"
        limit = 1
    }
} | ConvertTo-Json -Depth 10

$writer.WriteLine($request)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.result -and $result.result.Count -gt 0) {
    $elementId = $result.result[0].id
    Write-Host "Found titleblock ID: $elementId"
    
    # Now get element details with parameters
    $detailRequest = @{
        jsonrpc = "2.0"
        id = 2
        method = "getElementParameters"
        params = @{
            elementId = $elementId
        }
    } | ConvertTo-Json -Depth 10
    
    $writer.WriteLine($detailRequest)
    $detailResponse = $reader.ReadLine()
    Write-Host $detailResponse
}

$pipeClient.Close()
