$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

$writer.WriteLine('{"method":"getViews","params":{}}')
$response = $reader.ReadLine()
$pipe.Close()

$result = $response | ConvertFrom-Json
$views = $result.result.views
$sheets = $views | Where-Object { $_.viewType -eq "DrawingSheet" } | Sort-Object { $_.sheetNumber }

Write-Host "SHEETS ($($sheets.Count)) sorted by number:"
foreach ($s in $sheets) {
    Write-Host "$($s.id) | $($s.sheetNumber) | $($s.name)"
}
