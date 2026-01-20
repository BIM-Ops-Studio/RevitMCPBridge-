$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

$json = @{
    method = "getRooms"
    params = @{}
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$response = $reader.ReadLine()
$pipe.Close()

$result = $response | ConvertFrom-Json
if ($result.success -and $result.result.rooms) {
    Write-Host "ROOMS ($($result.result.rooms.Count)):"
    foreach ($r in $result.result.rooms) {
        Write-Host "$($r.id) | $($r.number) | $($r.name) | Level: $($r.level) | Area: $($r.area)"
    }
} else {
    Write-Host $response
}
