$pipeName = 'RevitMCPBridge2026'
$centuryGothicTypeId = 1244683

# Use modifyTextNote2 with textNoteId parameter (not elementId)
$noteIds = @(2229821, 2229822, 2229823, 2229824, 2229825, 2229826, 2229827, 2229828, 2229829, 2229830, 2229831, 2229832, 2229833, 2229834)

$successCount = 0
foreach ($noteId in $noteIds) {
    # modifyTextNote2 uses textNoteId, not elementId
    $request = '{"method": "modifyTextNote2", "params": {"textNoteId": ' + $noteId + ', "textTypeId": ' + $centuryGothicTypeId + '}}'

    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(5000)
        $writer = New-Object System.IO.StreamWriter($pipe)
        $reader = New-Object System.IO.StreamReader($pipe)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $response = $reader.ReadLine()
        $pipe.Close()

        $result = $response | ConvertFrom-Json
        if ($result.success) {
            $successCount++
            Write-Host "Changed type for note $noteId"
        } else {
            Write-Host "Failed note $noteId : $($result.error)"
        }
    } catch {
        Write-Host "Error on note $noteId : $_"
    }
}

Write-Host "`nTotal type changes: $successCount / 14"
