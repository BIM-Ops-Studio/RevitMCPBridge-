param(
    [string]$ScheduleId = "",
    [string]$SheetId = ""
)

$pipeName = "RevitMCPBridge2026"

if ($SheetId -ne "") {
    $request = '{"method":"autoPlaceSchedule","params":{"scheduleId":' + $ScheduleId + ',"targetSheetId":' + $SheetId + '}}'
} else {
    $request = '{"method":"autoPlaceSchedule","params":{"scheduleId":' + $ScheduleId + '}}'
}

try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(15000)

    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)

    $writer.WriteLine($request)
    $writer.Flush()

    $response = $reader.ReadLine()
    Write-Output $response

    $pipe.Close()
} catch {
    Write-Output ("Error: " + $_.Exception.Message)
}
