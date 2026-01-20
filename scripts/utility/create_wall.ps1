param(
    [double]$startX,
    [double]$startY,
    [double]$endX,
    [double]$endY,
    [int]$levelId = 30,
    [double]$height = 10.0,
    [int]$wallTypeId = 441445
)

$pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipeClient.Connect(5000)
$writer = New-Object System.IO.StreamWriter($pipeClient)
$reader = New-Object System.IO.StreamReader($pipeClient)

$json = '{"method":"createWallByPoints","params":{"startPoint":[' + $startX + ',' + $startY + ',0],"endPoint":[' + $endX + ',' + $endY + ',0],"levelId":' + $levelId + ',"height":' + $height + ',"wallTypeId":' + $wallTypeId + '}}'

$writer.WriteLine($json)
$writer.Flush()
$response = $reader.ReadLine()
$pipeClient.Close()
Write-Output $response
