$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(5000)
$reader = New-Object System.IO.StreamReader($pipe)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true

# Get project info
$request = '{"method": "getProjectInfo", "params": {}}'
$writer.WriteLine($request)
$response = $reader.ReadLine()
Write-Output "PROJECT INFO: $response"

# Get walls count
$request = '{"method": "getWalls", "params": {}}'
$writer.WriteLine($request)
$response = $reader.ReadLine()
Write-Output "WALLS: $response"

$pipe.Close()
