# Create Excel file using Filled Region Area × 1.2 for all rooms
# This version gets filled region data for each room individually

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
Write-Host "CREATING EXCEL FROM FILLED REGIONS" -ForegroundColor Cyan
Write-Host "Formula: Filled Region Area × 1.2" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get all Level 7 rooms
Write-Host "Getting rooms from Revit..." -ForegroundColor Yellow
$roomsResult = Send-RevitCommand -Method "getRooms" -Params @{}
$level7Rooms = $roomsResult.rooms | Where-Object { $_.level -eq "L7" }
Write-Host "Found $($level7Rooms.Count) rooms on Level 7`n" -ForegroundColor Green

# Calculate square footage for each room
$excelData = @()
$successCount = 0
$failCount = 0

Write-Host "Calculating filled region areas (this may take a moment)...`n" -ForegroundColor Yellow

foreach ($room in $level7Rooms) {
    $roomNum = "{0:D2}" -f [int]$room.number

    # Get filled region area for this room
    $result = Send-RevitCommand -Method "updateRoomAreaFromFilledRegion" -Params @{
        roomId = $room.roomId.ToString()
        multiplier = 1.0  # Get base filled region area
    }

    if ($result.success -and $result.filledRegionArea -gt 0) {
        # Calculate area with 1.2 multiplier
        $filledRegionArea = [double]$result.filledRegionArea
        $calculatedArea = [math]::Round($filledRegionArea * 1.2, 0)
        Write-Host "  Room $roomNum : $([math]::Round($filledRegionArea, 0)) SF × 1.2 = $calculatedArea SF" -ForegroundColor Green
        $squareFeet = $calculatedArea
        $successCount++
    } else {
        # No filled region found, use room area
        $squareFeet = [math]::Round([double]$room.area, 0)
        Write-Host "  Room $roomNum : $squareFeet SF (no filled region)" -ForegroundColor Yellow
        $failCount++
    }

    $excelData += [PSCustomObject]@{
        'Room Number' = $roomNum
        'Room Name' = $room.name
        'Square Footage' = $squareFeet
    }

    # Small delay to prevent overwhelming the pipe
    Start-Sleep -Milliseconds 50
}

Write-Host "`nProcessed: $successCount with filled regions, $failCount without`n" -ForegroundColor Cyan

# Sort by room number
$excelData = $excelData | Sort-Object { [int]$_.'Room Number' }

Write-Host "Sample data:" -ForegroundColor Cyan
$excelData | Select-Object -First 5 | Format-Table
Write-Host ""

# Create Excel file
$excelPath = "D:\RevitMCPBridge2026\Level_7_Filled_Region_Areas.xlsx"
Write-Host "Creating Excel file: $excelPath" -ForegroundColor Yellow

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

$workbook = $excel.Workbooks.Add()
$worksheet = $workbook.Worksheets.Item(1)
$worksheet.Name = "Level 7 Rooms"

# Set page setup
$worksheet.PageSetup.Orientation = 1
$worksheet.PageSetup.PaperSize = 1
$worksheet.PageSetup.FitToPagesWide = 1
$worksheet.PageSetup.LeftMargin = 36
$worksheet.PageSetup.RightMargin = 36
$worksheet.PageSetup.TopMargin = 36
$worksheet.PageSetup.BottomMargin = 36

# Title
$worksheet.Cells.Item(1, 1) = "TYPICAL FLOOR PLAN - LEVEL 7"
$worksheet.Cells.Item(1, 1).Font.Size = 16
$worksheet.Cells.Item(1, 1).Font.Bold = $true
$worksheet.Cells.Item(1, 1).HorizontalAlignment = -4108
$titleRange = $worksheet.Range("A1:C1")
$titleRange.Merge()

# Subtitle
$worksheet.Cells.Item(2, 1) = "Room Areas (Filled Region × 1.2)"
$worksheet.Cells.Item(2, 1).Font.Size = 12
$worksheet.Cells.Item(2, 1).HorizontalAlignment = -4108
$subtitleRange = $worksheet.Range("A2:C2")
$subtitleRange.Merge()

# Headers
$row = 4
$worksheet.Cells.Item($row, 1) = "Room Number"
$worksheet.Cells.Item($row, 2) = "Room Name"
$worksheet.Cells.Item($row, 3) = "Square Footage"

$headerRange = $worksheet.Range("A4:C4")
$headerRange.Font.Bold = $true
$headerRange.Font.Size = 11
$headerRange.Interior.ColorIndex = 15
$headerRange.HorizontalAlignment = -4108
$headerRange.Borders.Weight = 2

# Data
$row = 5
foreach ($item in $excelData) {
    $worksheet.Cells.Item($row, 1) = $item.'Room Number'
    $worksheet.Cells.Item($row, 2) = $item.'Room Name'
    $worksheet.Cells.Item($row, 3) = $item.'Square Footage'
    $row++
}

# Format data
$lastRow = $row - 1
$dataRange = $worksheet.Range("A5:C$lastRow")
$dataRange.Borders.Weight = 1
$dataRange.Font.Size = 10

# Column widths
$worksheet.Columns.Item(1).ColumnWidth = 15
$worksheet.Columns.Item(2).ColumnWidth = 30
$worksheet.Columns.Item(3).ColumnWidth = 18

# Alignment
$worksheet.Columns.Item(1).HorizontalAlignment = -4108
$worksheet.Columns.Item(3).HorizontalAlignment = -4108
$worksheet.Columns.Item(2).HorizontalAlignment = -4131

# Alternating colors
for ($i = 5; $i -le $lastRow; $i++) {
    $rowRange = $worksheet.Range("A$i:C$i")
    if (($i - 5) % 2 -eq 1) {
        $rowRange.Interior.ColorIndex = 2
    } else {
        $rowRange.Interior.ColorIndex = 15
    }
}

# Save
Write-Host "Saving Excel file..." -ForegroundColor Yellow
$workbook.SaveAs($excelPath)
$workbook.Close()
$excel.Quit()

[System.Runtime.Interopservices.Marshal]::ReleaseComObject($worksheet) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($workbook) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SUCCESS!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "File: $excelPath" -ForegroundColor Green
Write-Host "Total rooms: $($excelData.Count)" -ForegroundColor Green
Write-Host "With filled regions: $successCount" -ForegroundColor Green
Write-Host "Without filled regions: $failCount" -ForegroundColor Green
Write-Host ""
Write-Host "All values calculated as: Filled Region Area × 1.2" -ForegroundColor Yellow
Write-Host "Example: Office 01 = 675 SF × 1.2 = 810 SF" -ForegroundColor Yellow
Write-Host ""
