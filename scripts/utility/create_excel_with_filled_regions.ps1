# Create Excel file using Filled Region Area × 1.2 for all rooms

function Send-RevitCommand {
    param([string]$Method, [hashtable]$Params)
    $pipeClient = $null; $writer = $null; $reader = $null
    try {
        $pipeClient = New-Object System.IO.Pipes.NamedPipeClientStream(".", "RevitMCPBridge2026", [System.IO.Pipes.PipeDirection]::InOut)
        $pipeClient.Connect(5000)
        $request = @{ method = $Method; params = $Params } | ConvertTo-Json -Compress
        $writer = New-Object System.IO.StreamWriter($pipeClient)
        $writer.AutoFlush = $true
        $writer.WriteLine($request)
        $reader = New-Object System.IO.StreamReader($pipeClient)
        $response = $reader.ReadLine()
        return $response | ConvertFrom-Json
    } finally {
        if ($reader) { try { $reader.Dispose() } catch {} }
        if ($writer) { try { $writer.Dispose() } catch {} }
        if ($pipeClient) { try { $pipeClient.Dispose() } catch {} }
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CREATING EXCEL WITH FILLED REGION × 1.2" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get all rooms from Level 7
Write-Host "Getting rooms from Revit..." -ForegroundColor Yellow
$roomsResult = Send-RevitCommand -Method "getRooms" -Params @{}

$level7Rooms = $roomsResult.rooms | Where-Object { $_.level -eq "L7" }
Write-Host "Found $($level7Rooms.Count) rooms on Level 7`n" -ForegroundColor Green

# Calculate square footage for each room using Filled Region × 1.2
$excelData = @()
$successCount = 0
$failCount = 0

Write-Host "Calculating areas (Filled Region × 1.2)..." -ForegroundColor Yellow

foreach ($room in $level7Rooms) {
    $roomNum = "{0:D2}" -f [int]$room.number

    # Get filled region area for this room (already multiplied by 1.2)
    $result = Send-RevitCommand -Method "updateRoomAreaFromFilledRegion" -Params @{
        roomId = $room.roomId.ToString()
        multiplier = 1.2
    }

    if ($result.success) {
        # The newArea is already calculated as filledRegionArea × 1.2
        $squareFeet = [math]::Round($result.newArea, 0)
        Write-Host "  Room $roomNum : $squareFeet SF (from filled region)" -ForegroundColor Green
        $successCount++
    } else {
        # Fallback to room area if no filled region
        $squareFeet = [math]::Round([double]$room.area, 0)
        Write-Host "  Room $roomNum : $squareFeet SF (no filled region, using room area)" -ForegroundColor Yellow
        $failCount++
    }

    $excelData += [PSCustomObject]@{
        'Room Number' = $roomNum
        'Room Name' = $room.name
        'Square Footage' = $squareFeet
    }
}

Write-Host "`nProcessed: $successCount rooms with filled regions, $failCount without`n" -ForegroundColor Cyan

# Sort by room number
$excelData = $excelData | Sort-Object { [int]$_.'Room Number' }

Write-Host "Sample data:" -ForegroundColor Cyan
$excelData | Select-Object -First 5 | Format-Table
Write-Host ""

# Create Excel file
$excelPath = "D:\RevitMCPBridge2026\L7_Rooms_With_Multiplier.xlsx"

Write-Host "Creating Excel file: $excelPath" -ForegroundColor Yellow

# Create Excel COM object
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

# Create new workbook
$workbook = $excel.Workbooks.Add()
$worksheet = $workbook.Worksheets.Item(1)
$worksheet.Name = "Level 7 Rooms"

# Set page setup for 8.5x11
$worksheet.PageSetup.Orientation = 1
$worksheet.PageSetup.PaperSize = 1
$worksheet.PageSetup.FitToPagesWide = 1
$worksheet.PageSetup.LeftMargin = 36
$worksheet.PageSetup.RightMargin = 36
$worksheet.PageSetup.TopMargin = 36
$worksheet.PageSetup.BottomMargin = 36

# Add title
$worksheet.Cells.Item(1, 1) = "TYPICAL FLOOR PLAN - LEVEL 7"
$worksheet.Cells.Item(1, 1).Font.Size = 16
$worksheet.Cells.Item(1, 1).Font.Bold = $true
$worksheet.Cells.Item(1, 1).HorizontalAlignment = -4108

# Merge title cells
$titleRange = $worksheet.Range("A1:C1")
$titleRange.Merge()

# Add subtitle
$worksheet.Cells.Item(2, 1) = "Room Areas (Filled Region × 1.2)"
$worksheet.Cells.Item(2, 1).Font.Size = 12
$worksheet.Cells.Item(2, 1).HorizontalAlignment = -4108
$subtitleRange = $worksheet.Range("A2:C2")
$subtitleRange.Merge()

# Add headers (row 4)
$row = 4
$worksheet.Cells.Item($row, 1) = "Room Number"
$worksheet.Cells.Item($row, 2) = "Room Name"
$worksheet.Cells.Item($row, 3) = "Square Footage"

# Format headers
$headerRange = $worksheet.Range("A4:C4")
$headerRange.Font.Bold = $true
$headerRange.Font.Size = 11
$headerRange.Interior.ColorIndex = 15
$headerRange.HorizontalAlignment = -4108
$headerRange.Borders.Weight = 2

# Add data
$row = 5
foreach ($item in $excelData) {
    $worksheet.Cells.Item($row, 1) = $item.'Room Number'
    $worksheet.Cells.Item($row, 2) = $item.'Room Name'
    $worksheet.Cells.Item($row, 3) = $item.'Square Footage'
    $row++
}

# Format data range
$lastRow = $row - 1
$dataRange = $worksheet.Range("A5:C$lastRow")
$dataRange.Borders.Weight = 1
$dataRange.Font.Size = 10

# Format columns
$worksheet.Columns.Item(1).ColumnWidth = 15
$worksheet.Columns.Item(2).ColumnWidth = 30
$worksheet.Columns.Item(3).ColumnWidth = 18

# Center align Room Number and Square Footage
$worksheet.Columns.Item(1).HorizontalAlignment = -4108
$worksheet.Columns.Item(3).HorizontalAlignment = -4108

# Left align Room Name
$worksheet.Columns.Item(2).HorizontalAlignment = -4131

# Add alternating row colors
for ($i = 5; $i -le $lastRow; $i++) {
    if (($i - 5) % 2 -eq 1) {
        $rowRange = $worksheet.Range("A$i:C$i")
        $rowRange.Interior.ColorIndex = 2
    } else {
        $rowRange = $worksheet.Range("A$i:C$i")
        $rowRange.Interior.ColorIndex = 15
    }
}

# Save and close
Write-Host "Saving Excel file..." -ForegroundColor Yellow
$workbook.SaveAs($excelPath)
$workbook.Close()
$excel.Quit()

# Release COM objects
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($worksheet) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($workbook) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SUCCESS!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Excel file created: $excelPath" -ForegroundColor Green
Write-Host "Total rooms: $($excelData.Count)" -ForegroundColor Green
Write-Host "Calculated with filled regions: $successCount" -ForegroundColor Green
Write-Host "Using room area (no filled region): $failCount" -ForegroundColor Green
Write-Host ""
Write-Host "Formula used: Filled Region Area × 1.2" -ForegroundColor Yellow
Write-Host "Example: Office 01 = 675 SF × 1.2 = 810 SF" -ForegroundColor Yellow
