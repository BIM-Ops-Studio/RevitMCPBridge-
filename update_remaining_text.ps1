$pipeName = 'RevitMCPBridge2026'
$centuryGothicTypeId = 1244683

# Text notes still using Schedule Default
$noteIds = @(2223266, 2223267, 2223268, 2223269, 2223270, 2223271, 2223272, 2223250, 2223251, 2223252, 2223253, 2223254, 2223255, 2223256, 2223257, 2223258, 2223259, 2223260, 2223261)

Write-Host "Changing $($noteIds.Count) text notes to Century Gothic..."

$successCount = 0
foreach ($noteId in $noteIds) {
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
            Write-Host "  Changed note $noteId"
        } else {
            Write-Host "  Failed note $noteId : $($result.error)"
        }
    } catch {
        Write-Host "  Error on note $noteId : $_"
    }
}

Write-Host "`nTotal changed: $successCount / $($noteIds.Count)"
