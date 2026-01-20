$pipeName = 'RevitMCPBridge2026'
$centuryGothicTypeId = 1244683

$notes = @(
    @{id=2229821; text='8 IN'},
    @{id=2229822; text='4 IN INSUL.'},
    @{id=2229823; text='6 IN CONC. DECK'},
    @{id=2229824; text='8 IN'},
    @{id=2229825; text='8 IN MIN. TURN-UP'},
    @{id=2229826; text='4 IN INSUL.'},
    @{id=2229827; text='8 IN'},
    @{id=2229828; text='42 IN MIN.'},
    @{id=2229829; text='6 IN SLAB'},
    @{id=2229830; text='8 IN'},
    @{id=2229831; text='42 IN MIN.'},
    @{id=2229832; text='6 IN SLAB'},
    @{id=2229833; text='6 IN CONC.'},
    @{id=2229834; text='8 IN'}
)

$successCount = 0
foreach ($note in $notes) {
    $noteId = $note.id
    $text = $note.text
    $request = '{"method": "modifyTextNote", "params": {"elementId": ' + $noteId + ', "text": "' + $text + '", "textTypeId": ' + $centuryGothicTypeId + '}}'

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
            Write-Host "Updated note $noteId to Century Gothic"
        } else {
            Write-Host "Failed note $noteId : $($result.error)"
        }
    } catch {
        Write-Host "Error on note $noteId : $_"
    }
}

Write-Host "`nTotal updated: $successCount / 14"
