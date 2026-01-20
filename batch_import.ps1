$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true
    
    $details = @(
        @{path="D:\Revit Detail Libraries\Revit Details\01 - Roof Details\ROOF CRICKET DIAGRAM.rvt"; sheet=1240478; x=0.5; y=1.8},
        @{path="D:\Revit Detail Libraries\Revit Details\01 - Roof Details\OVERFLOW SCUPPER.rvt"; sheet=1240478; x=2.0; y=1.8},
        @{path="D:\Revit Detail Libraries\Revit Details\03 - Wall Details\PARAPET WALL DTL.rvt"; sheet=1240493; x=0.8; y=1.2},
        @{path="D:\Revit Detail Libraries\Revit Details\03 - Wall Details\STUCCO BAND DETAIL.rvt"; sheet=1240493; x=2.2; y=1.2}
    )
    
    foreach ($d in $details) {
        # Import
        $importJson = '{"method":"importDetailToDocument","params":{"detailPath":"' + $d.path.Replace('\','\\') + '"}}'
        $writer.WriteLine($importJson)
        $response = $reader.ReadLine()
        $result = $response | ConvertFrom-Json
        
        if ($result.success) {
            Write-Output ("Imported: " + $result.viewName + " (" + $result.verifiedElementsInView + " elements)")
            
            # Place on sheet
            $placeJson = '{"method":"placeViewOnSheet","params":{"viewId":' + $result.viewId + ',"sheetId":' + $d.sheet + ',"x":' + $d.x + ',"y":' + $d.y + '}}'
            $writer.WriteLine($placeJson)
            $placeResponse = $reader.ReadLine()
            $placeResult = $placeResponse | ConvertFrom-Json
            
            if ($placeResult.success) {
                Write-Output ("  -> Placed on " + $placeResult.sheetNumber)
            } else {
                Write-Output ("  -> Place failed: " + $placeResult.error)
            }
        } else {
            Write-Output ("Failed: " + $d.path + " - " + $result.error)
        }
    }
    
    Write-Output "`nBatch complete!"
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
