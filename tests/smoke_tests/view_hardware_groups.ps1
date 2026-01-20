# Navigate to sheet A-7.1 and view hardware groups section
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== VIEWING HARDWARE GROUPS ===" -ForegroundColor Cyan

# Navigate to sheet A-7.1 DOOR SCHEDULES
$json = '{"method":"setActiveView","params":{"viewId":1545074}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

Start-Sleep -Milliseconds 500

# Zoom to fit
$json = '{"method":"zoomToFit","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()

$pipe.Close()
Write-Host "On sheet A-7.1 - ready for screenshot"
