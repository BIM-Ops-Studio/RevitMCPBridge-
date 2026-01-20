Write-Output "=== REVIT 2025 ==="
try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2025", [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(3000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $request = '{"method":"getAssistanceSummary","params":{}}'
    $writer.WriteLine($request)
    $writer.Flush()
    $response = $reader.ReadLine()
    $pipe.Close()
    $data = $response | ConvertFrom-Json
    Write-Output "Project: $($data.context.document)"
    Write-Output "Sheet: $($data.context.sheetNumber) - $($data.context.activeView)"
    Write-Output "Learning: $($data.learning.status) ($($data.learning.observations) observations)"
} catch {
    Write-Output "Connection failed: $($_.Exception.Message)"
}

Write-Output ""
Write-Output "=== REVIT 2026 ==="
try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(3000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $request = '{"method":"getAssistanceSummary","params":{}}'
    $writer.WriteLine($request)
    $writer.Flush()
    $response = $reader.ReadLine()
    $pipe.Close()
    $data = $response | ConvertFrom-Json
    Write-Output "Project: $($data.context.document)"
    Write-Output "Sheet: $($data.context.sheetNumber) - $($data.context.activeView)"
    Write-Output "Learning: $($data.learning.status) ($($data.learning.observations) observations)"
} catch {
    Write-Output "Connection failed: $($_.Exception.Message)"
}
