$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    # Test connection with getLevels
    $json = '{"method":"getLevels","params":{}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "MCP Connection OK"

    # Get active document info
    $json = '{"method":"getProjectInfo","params":{}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    $result = $response | ConvertFrom-Json
    Write-Output ("Project: " + $result.projectName)

} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
