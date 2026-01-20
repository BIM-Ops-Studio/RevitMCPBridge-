$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    $sheets = @(1240478, 1240493, 1240508)
    
    foreach ($sheetId in $sheets) {
        $json = '{"method":"changeTitleBlock","params":{"sheetId":' + $sheetId + ',"titleBlockId":1254808}}'
        $writer.WriteLine($json)
        $response = $reader.ReadLine()
        $result = $response | ConvertFrom-Json
        if ($result.success) {
            Write-Output ("Sheet " + $result.sheetNumber + ": Changed to " + $result.newTitleBlock)
        } else {
            Write-Output ("Sheet $sheetId failed: " + $result.error)
        }
    }
    
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
