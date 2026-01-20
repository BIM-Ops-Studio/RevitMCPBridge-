# Get all doors and their marks for mapping
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
$pipe.Connect(20000)
$writer = New-Object System.IO.StreamWriter($pipe)
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($pipe)

Write-Host "=== GETTING ALL DOOR MARKS ===" -ForegroundColor Cyan

# Get doors from model
$json = '{"method":"getDoors","params":{}}'
$writer.WriteLine($json)
$response = $reader.ReadLine()
$result = $response | ConvertFrom-Json

if ($result.success) {
    Write-Host "Found $($result.doorCount) doors" -ForegroundColor Green

    # Group by mark pattern
    $numeric = @()
    $letter = @()
    $other = @()

    foreach ($door in $result.doors) {
        $doorInfo = @{
            id = $door.doorId
            mark = $door.mark
            level = $door.level
            toRoom = $door.toRoom
            typeName = $door.typeName
        }

        if ($door.mark -match '^\d+$') {
            $numeric += $doorInfo
        } elseif ($door.mark -match '^[A-Za-z]+$') {
            $letter += $doorInfo
        } else {
            $other += $doorInfo
        }
    }

    Write-Host "`nNumeric marks ($($numeric.Count) doors):"
    $numeric | Sort-Object { [int]$_.mark } | ForEach-Object {
        Write-Host "  Mark $($_.mark): ID=$($_.id), Room=$($_.toRoom)"
    }

    Write-Host "`nLetter marks ($($letter.Count) doors):"
    $letter | ForEach-Object {
        Write-Host "  Mark $($_.mark): ID=$($_.id), Room=$($_.toRoom)"
    }

    Write-Host "`nOther marks ($($other.Count) doors):"
    $other | Select-Object -First 10 | ForEach-Object {
        Write-Host "  Mark '$($_.mark)': ID=$($_.id), Room=$($_.toRoom)"
    }
}

$pipe.Close()
