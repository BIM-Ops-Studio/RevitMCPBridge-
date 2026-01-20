param([int]$ViewId)

$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

$request = "{`"method`":`"getTextNotesInView`",`"params`":{`"viewId`":$ViewId}}"
$writer.WriteLine($request)
$response = $reader.ReadLine()
$pipe.Close()

$result = $response | ConvertFrom-Json
if ($result.success -eq $false) {
    Write-Host "Error: $($result.error)"
} else {
    Write-Host $response
}
