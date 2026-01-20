# List all detail-related methods

$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.','RevitMCPBridge2026',[System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(15000)
$writer = [System.IO.StreamWriter]::new($pipe)
$reader = [System.IO.StreamReader]::new($pipe)

$json = '{"method":"listMethods"}'
$writer.WriteLine($json)
$writer.Flush()
Start-Sleep -Milliseconds 2000
$response = $reader.ReadLine()
$data = $response | ConvertFrom-Json

if ($data.success) {
    Write-Host "Total methods: $($data.result.methods.Count)" -ForegroundColor Cyan

    # Filter for detail-related methods
    $detailMethods = $data.result.methods | Where-Object {
        $_ -match 'detail|repeat|component|drafting|line|text|annot'
    } | Sort-Object

    Write-Host "`n=== Detail-Related Methods ($($detailMethods.Count)) ===" -ForegroundColor Yellow
    $detailMethods | ForEach-Object { Write-Host "  $_" }
}

$pipe.Close()
