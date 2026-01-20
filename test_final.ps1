$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(15000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    # Import a wall detail for sheet AD-002
    Write-Output "=== Importing from Wall Details ==="
    $json = '{"method":"importDetailToDocument","params":{"detailPath":"D:\\Revit Detail Libraries\\Revit Details\\03 - Wall Details\\1HR BOTTOM OF WALL DETAIL.rvt"}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output $response
    
    $data = $response | ConvertFrom-Json
    $viewId = $data.viewId
    
    # Place on sheet AD-002 (Wall Details - ID 1240493)
    Write-Output "`n=== Placing on sheet AD-002 ==="
    $json = '{"method":"placeViewOnSheet","params":{"viewId":' + $viewId + ',"sheetId":1240493,"x":1.5,"y":1.0}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output $response
    
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
