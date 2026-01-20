$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

$json = @{
    method = "getTextNoteTypes"
    params = @{}
} | ConvertTo-Json -Compress

$writer.WriteLine($json)
$response = $reader.ReadLine()
$pipe.Close()

$result = $response | ConvertFrom-Json
if ($result.result.textNoteTypes) {
    foreach ($t in $result.result.textNoteTypes) {
        Write-Host "$($t.id) | $($t.name)"
    }
}
