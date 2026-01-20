# Get door schedule data from Revit
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(15000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== GETTING DOOR SCHEDULE DATA ===" -ForegroundColor Cyan

# First get all schedules to find door schedule
$json = '{"method":"getSchedules","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "`nAvailable Schedules:" -ForegroundColor Yellow
    foreach ($sched in $result.result.schedules) {
        if ($sched.name -like "*Door*" -or $sched.name -like "*Window*") {
            Write-Host "  ID: $($sched.id) - $($sched.name)"
        }
    }
}

$pipe.Close()
