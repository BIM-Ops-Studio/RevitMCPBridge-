param(
    [string]$scheduleName,
    [string]$category
)

$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipeClient.Connect(5000)
$writer = New-Object System.IO.StreamWriter($pipeClient)
$reader = New-Object System.IO.StreamReader($pipeClient)

$json = '{"method":"createSchedule","params":{"scheduleName":"' + $scheduleName + '","category":"' + $category + '"}}'

$writer.WriteLine($json)
$writer.Flush()
$response = $reader.ReadLine()
$pipeClient.Close()
Write-Output $response
