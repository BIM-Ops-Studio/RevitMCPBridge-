# Extract all doors and windows with host info and locations
$pipeName = 'RevitMCPBridge2026'

# Door IDs from Avon Park (from getDoorSchedule)
$doorIds = @(
    1954558, 1956061, 1957955, 1960017, 1956277, 1956378, 1957449, 1956539,
    1956688, 1956829, 1956972, 1967050, 1957293, 1970477, 1957069, 1957247,
    1955620, 1957628, 1957747, 1955722, 1957799, 1955802, 1964323, 1956008,
    1957546, 1956198
)

# Window IDs from Avon Park (from getWindowSchedule)
$windowIds = @(
    1958469, 1958664, 1958692, 1958724, 1958958, 1959124, 1959320, 1959414,
    1959855, 1960086, 2017147, 2018742, 2018792, 2059859
)

$allDoors = @()
$allWindows = @()

Write-Host "Extracting $($doorIds.Count) doors..."
foreach ($doorId in $doorIds) {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    $request = '{"method":"getDoorWindowInfo","params":{"elementId":' + $doorId + '}}'
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    $doorData = $response | ConvertFrom-Json
    if ($doorData.success) {
        $allDoors += $doorData
        Write-Host "  Door $doorId - $($doorData.familyName) $($doorData.typeName)"
    } else {
        Write-Host "  Failed: $doorId - $($doorData.error)"
    }
}

Write-Host "`nExtracting $($windowIds.Count) windows..."
foreach ($windowId in $windowIds) {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    $request = '{"method":"getDoorWindowInfo","params":{"elementId":' + $windowId + '}}'
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    $windowData = $response | ConvertFrom-Json
    if ($windowData.success) {
        $allWindows += $windowData
        Write-Host "  Window $windowId - $($windowData.familyName) $($windowData.typeName)"
    } else {
        Write-Host "  Failed: $windowId - $($windowData.error)"
    }
}

# Save to JSON file
$output = @{
    extractedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    sourceDocument = "1700 West Sheffield Road"
    doorCount = $allDoors.Count
    windowCount = $allWindows.Count
    doors = $allDoors
    windows = $allWindows
}

$output | ConvertTo-Json -Depth 10 | Out-File "D:\RevitMCPBridge2026\avon_park_doors_windows.json" -Encoding UTF8
Write-Host "`nExtracted $($allDoors.Count) doors and $($allWindows.Count) windows to avon_park_doors_windows.json"
