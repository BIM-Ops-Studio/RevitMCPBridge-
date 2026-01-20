$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    Write-Output "=== SHEET VERIFICATION TESTS ==="
    Write-Output ""

    # Test 1: Get title block dimensions to verify sheet size
    Write-Output "--- TEST 1: Title Block Dimensions ---"
    $json = '{"method":"getTitleblockDimensions","params":{"sheetId":1240478}}'
    $writer.WriteLine($json)
    $response = $reader.ReadLine()
    Write-Output "AD-001 title block: $response"
    Write-Output ""

    # Test 2: Check viewport bounds to ensure no overlaps
    Write-Output "--- TEST 2: Viewport Bounds Check ---"
    $sheets = @(
        @{ id = 1240478; name = "AD-001" },
        @{ id = 1240493; name = "AD-002" }
    )

    foreach ($sheet in $sheets) {
        $json = '{"method":"getViewportsOnSheet","params":{"sheetId":' + $sheet.id + '}}'
        $writer.WriteLine($json)
        $response = $reader.ReadLine()
        $result = $response | ConvertFrom-Json

        Write-Output ("Sheet " + $sheet.name + ":")
        if ($result.success -and $result.viewports) {
            foreach ($vp in $result.viewports) {
                $x = [math]::Round($vp.location[0], 2)
                $y = [math]::Round($vp.location[1], 2)
                Write-Output ("  - " + $vp.viewName + " at (" + $x + ", " + $y + ")")
            }
        }
        Write-Output ""
    }

    # Test 3: Export sheet images for visual verification
    Write-Output "--- TEST 3: Exporting Sheet Images ---"
    foreach ($sheet in $sheets) {
        $json = '{"method":"exportSheetImage","params":{"sheetId":' + $sheet.id + ',"filePath":"D:/RevitMCPBridge2026/verify_' + $sheet.name + '.png","resolution":150}}'
        $writer.WriteLine($json)
        $response = $reader.ReadLine()
        $result = $response | ConvertFrom-Json
        if ($result.success) {
            Write-Output ("  " + $sheet.name + " exported: " + $result.filePath)
        } else {
            Write-Output ("  " + $sheet.name + " export failed: " + $result.error)
        }
    }

    Write-Output ""
    Write-Output "=== VERIFICATION COMPLETE ==="

} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
