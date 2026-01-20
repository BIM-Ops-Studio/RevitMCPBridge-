param(
    [string]$method,
    [string]$paramName,
    [string]$paramValue
)

$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipeClient.Connect(5000)
$writer = New-Object System.IO.StreamWriter($pipeClient)
$reader = New-Object System.IO.StreamReader($pipeClient)

if ($paramName -and $paramValue) {
    $json = '{"method":"' + $method + '","params":{"' + $paramName + '":' + $paramValue + '}}'
} else {
    $json = '{"method":"' + $method + '"}'
}

$writer.WriteLine($json)
$writer.Flush()
$response = $reader.ReadLine()
$pipeClient.Close()
Write-Output $response
