$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
try {
    $pipe.Connect(30000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    Write-Output "=== CAPTURING SHEET IMAGES ==="

    # Sheet IDs are also view IDs - try exportViewImage
    $sheets = @(
        @{ id = 1240478; name = "AD-001" },
        @{ id = 1240493; name = "AD-002" }
    )

    foreach ($sheet in $sheets) {
        Write-Output ("Capturing " + $sheet.name + "...")
        $filePath = "D:\\RevitMCPBridge2026\\sheet_" + $sheet.name + "_verify.png"
        $json = '{"method":"exportViewImage","params":{"viewId":' + $sheet.id + ',"filePath":"' + $filePath.Replace("\", "\\") + '","width":1920,"height":1080}}'
        $writer.WriteLine($json)
        $response = $reader.ReadLine()
        $result = $response | ConvertFrom-Json
        if ($result.success) {
            Write-Output ("  SUCCESS: " + $result.filePath)
        } else {
            Write-Output ("  Failed: " + $result.error)
        }
    }

    Write-Output ""
    Write-Output "=== CAPTURE COMPLETE ==="

} catch {
    Write-Output ("Error: " + $_.Exception.Message)
} finally {
    if ($pipe) { $pipe.Dispose() }
}
