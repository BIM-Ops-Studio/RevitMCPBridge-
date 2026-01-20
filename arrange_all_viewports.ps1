$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    # Get viewports on AD-001
    $json = '{"method":"getViewportsOnSheet","params":{"sheetId":1240478}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "AD-001 viewports:"
    Write-Output $response
    Write-Output ""

    # Get viewports on AD-002
    $json = '{"method":"getViewportsOnSheet","params":{"sheetId":1240493}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "AD-002 viewports:"
    Write-Output $response
    Write-Output ""

    # Get viewports on AD-003
    $json = '{"method":"getViewportsOnSheet","params":{"sheetId":1240508}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "AD-003 viewports:"
    Write-Output $response

} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
