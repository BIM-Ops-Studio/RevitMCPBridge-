# MCP Helper Script
param(
    [string]$Method,
    [string]$ParamsJson = "{}"
)

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

    return $response
}

# Convert JSON to hashtable manually for older PowerShell
$paramsObj = $ParamsJson | ConvertFrom-Json
$params = @{}
if ($paramsObj) {
    $paramsObj.PSObject.Properties | ForEach-Object {
        $params[$_.Name] = $_.Value
    }
}
$result = Invoke-MCPMethod -Method $Method -Params $params
Write-Output $result
