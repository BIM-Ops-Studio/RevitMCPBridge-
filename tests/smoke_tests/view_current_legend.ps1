# View current state of TYPES - DOOR legend
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

# Navigate to TYPES - DOOR legend
$json = '{"method":"setActiveView","params":{"viewId":1760142}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
Write-Host "Navigated to TYPES - DOOR legend"

Start-Sleep -Milliseconds 500

# Zoom to fit
$json = '{"method":"zoomToFit","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

$pipe.Close()
Write-Host "Ready for screenshot"
