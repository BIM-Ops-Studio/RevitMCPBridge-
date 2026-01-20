param([int]$ElementId, [string]$ParamName)

$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

$json = @{
    method = "getElementParameter"
    params = @{
        elementId = $ElementId
        parameterName = $ParamName
    }
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$response = $reader.ReadLine()
$pipe.Close()

Write-Host $response
