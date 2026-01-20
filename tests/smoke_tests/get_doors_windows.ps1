$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

# Get doors
$json = @{
    method = "getDoors"
    params = @{}
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$doorResponse = $reader.ReadLine()

# Get windows
$json = @{
    method = "getWindows"
    params = @{}
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$windowResponse = $reader.ReadLine()

$pipe.Close()

$doors = ($doorResponse | ConvertFrom-Json)
$windows = ($windowResponse | ConvertFrom-Json)

Write-Host "DOORS: $($doors.result.doorCount)"
Write-Host "WINDOWS: $($windows.result.windowCount)"
