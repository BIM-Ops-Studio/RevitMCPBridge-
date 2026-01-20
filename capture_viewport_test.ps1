$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    Write-Output "=== CAPTURING SHEET VIA captureViewport ==="

    # First, set the active view to AD-001
    $json = '{"method":"setActiveView","params":{"viewId":1240478}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "Set active view: $response"

    # Now capture the viewport
    $json = '{"method":"captureViewport","params":{"outputPath":"D:\\RevitMCPBridge2026\\sheet_AD001_captured.png","width":1920,"height":1080}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "Capture result: $response"

    # Try AD-002
    $json = '{"method":"setActiveView","params":{"viewId":1240493}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "Set active view AD-002: $response"

    $json = '{"method":"captureViewport","params":{"outputPath":"D:\\RevitMCPBridge2026\\sheet_AD002_captured.png","width":1920,"height":1080}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "Capture AD-002: $response"

} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
