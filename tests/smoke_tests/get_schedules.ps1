$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

$json = @{
    method = "getSchedules"
    params = @{}
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$response = $reader.ReadLine()
$pipe.Close()

$result = $response | ConvertFrom-Json
if ($result.success -and $result.result.schedules) {
    foreach ($s in $result.result.schedules) {
        Write-Host "$($s.id) | $($s.name)"
    }
} else {
    Write-Host $response
}
