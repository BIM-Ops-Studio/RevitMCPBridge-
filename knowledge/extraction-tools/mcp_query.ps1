param(
    [string]$Method = "getProjectInfo",
    [string]$Params = "{}"
)

$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipeClient.Connect(5000)
$writer = New-Object System.IO.StreamWriter($pipeClient)
$reader = New-Object System.IO.StreamReader($pipeClient)

$request = '{"method":"' + $Method + '","params":' + $Params + '}'
$writer.WriteLine($request)
$writer.Flush()

$response = $reader.ReadLine()
Write-Output $response

$pipeClient.Close()
