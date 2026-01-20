# Extract all wall geometry from current Revit document
$pipeName = 'RevitMCPBridge2026'
$wallIds = @(
    # Exterior CMU walls
    1946509, 1946577, 1946691, 1946751, 1946817, 1946869, 1946938, 1947064,
    # Interior partitions
    1948066, 1948260, 1948338, 1948441, 1948500, 1948604, 1949292, 1949620,
    1949756, 1949891, 1950244, 1950457, 1950593, 1950706, 1950828, 1950932,
    1951210, 1951475, 1951626, 1951760, 1951973, 1952173, 1952605, 1952712,
    1952823, 1974542, 1975148, 2021077, 2021101, 2021217, 2021239,
    # Upper level CMU
    1961188, 1961691, 1961827, 1961915,
    # Foundation walls
    2021920, 2022230, 2022370, 2022512, 2022703, 2022846, 2022995, 2073966,
    # Stone veneer
    2097545, 2097688, 2097815, 2097985, 2098091, 2098215, 2098333
)

$allWalls = @()

foreach ($wallId in $wallIds) {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $writer = New-Object System.IO.StreamWriter($pipe)
    $reader = New-Object System.IO.StreamReader($pipe)
    $writer.AutoFlush = $true

    $request = '{"method":"getWallInfo","params":{"wallId":' + $wallId + '}}'
    $writer.WriteLine($request)
    $response = $reader.ReadLine()
    $pipe.Close()

    $wallData = $response | ConvertFrom-Json
    if ($wallData.success) {
        $allWalls += $wallData
        Write-Host "Extracted wall $wallId - $($wallData.wallType)"
    } else {
        Write-Host "Failed to extract wall $wallId"
    }
}

# Save to JSON file
$output = @{
    extractedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    sourceDocument = "1700 West Sheffield Road"
    wallCount = $allWalls.Count
    walls = $allWalls
}

$output | ConvertTo-Json -Depth 10 | Out-File "D:\RevitMCPBridge2026\avon_park_walls.json" -Encoding UTF8
Write-Host "`nExtracted $($allWalls.Count) walls to avon_park_walls.json"
