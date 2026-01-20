# Create Excel file for Level 1 rooms only
# 2-digit room numbers in ascending order

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
Write-Host "CREATING LEVEL 1 ROOM LIST EXCEL FILE" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get all rooms from Revit
Write-Host "Getting all rooms from Revit..." -ForegroundColor Yellow
$result = Send-RevitCommand -Method "getRooms" -Params @{}

if (-not $result.success) {
    Write-Host "ERROR: Failed to get rooms" -ForegroundColor Red
    Write-Host $result.error -ForegroundColor Red
    exit 1
}

# Filter for Level 1 rooms only - by level name "L1"
$level1Rooms = $result.rooms | Where-Object {
    $_.level -eq "L1"
}

Write-Host "Found $($level1Rooms.Count) Level 1 rooms" -ForegroundColor Green
Write-Host ""

# Get filled regions to calculate the correct square footage
Write-Host "Getting filled regions for area calculation..." -ForegroundColor Yellow
$filledRegionsResult = Send-RevitCommand -Method "getFilledRegions" -Params @{}

# Prepare data for Excel
$excelData = @()
foreach ($room in $level1Rooms) {
    # Format room number as 2 digits with leading zero
    $roomNum = "{0:D2}" -f [int]$room.number

    # Find matching filled region for this room
    $matchingRegion = $filledRegionsResult.filledRegions | Where-Object {
        $_.name -eq $room.number
    }

    if ($matchingRegion) {
        # Calculate adjusted area: filled region area × 1.2
        $adjustedArea = [math]::Round([double]$matchingRegion.area * 1.2, 0)
    } else {
        # Fallback to room area if no filled region found
        $adjustedArea = [math]::Round([double]$room.area, 0)
    }

    $excelData += [PSCustomObject]@{
        'Room Number' = $roomNum
        'Room Name' = $room.name
        'Square Footage' = $adjustedArea
    }
}

# Sort by room number (numeric)
$excelData = $excelData | Sort-Object { [int]$_.'Room Number' }

Write-Host "Sample rooms:" -ForegroundColor Cyan
$excelData | Select-Object -First 5 | Format-Table
Write-Host ""

# Create Excel file
$excelPath = "D:\RevitMCPBridge2026\Level_1_Room_List.xlsx"

Write-Host "Creating Excel file: $excelPath" -ForegroundColor Yellow

# Create Excel COM object
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

# Create new workbook
$workbook = $excel.Workbooks.Add()
$worksheet = $workbook.Worksheets.Item(1)
$worksheet.Name = "Level 1 Rooms"

# Set page setup for 8.5x11
$worksheet.PageSetup.Orientation = 1  # Portrait
$worksheet.PageSetup.PaperSize = 1    # Letter (8.5x11)
$worksheet.PageSetup.FitToPagesWide = 1
$worksheet.PageSetup.FitToPagesTall = 0  # Auto
$worksheet.PageSetup.LeftMargin = 36   # 0.5 inch
$worksheet.PageSetup.RightMargin = 36
$worksheet.PageSetup.TopMargin = 36
$worksheet.PageSetup.BottomMargin = 36

# Add title
$worksheet.Cells.Item(1, 1) = "TYPICAL FLOOR PLAN - LEVEL 1"
$worksheet.Cells.Item(1, 1).Font.Size = 16
$worksheet.Cells.Item(1, 1).Font.Bold = $true
$worksheet.Cells.Item(1, 1).HorizontalAlignment = -4108  # xlCenter

# Merge title cells
$titleRange = $worksheet.Range("A1:C1")
$titleRange.Merge()

# Add subtitle
$worksheet.Cells.Item(2, 1) = "Room Areas"
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
$headerRange.Interior.ColorIndex = 15  # Light gray
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
$worksheet.Columns.Item(1).ColumnWidth = 15  # Room Number
$worksheet.Columns.Item(2).ColumnWidth = 30  # Room Name
$worksheet.Columns.Item(3).ColumnWidth = 18  # Square Footage

# Center align Room Number and Square Footage
$worksheet.Columns.Item(1).HorizontalAlignment = -4108
$worksheet.Columns.Item(3).HorizontalAlignment = -4108

# Left align Room Name
$worksheet.Columns.Item(2).HorizontalAlignment = -4131  # xlLeft

# Add alternating row colors
for ($i = 5; $i -le $lastRow; $i++) {
    if (($i - 5) % 2 -eq 1) {
        $rowRange = $worksheet.Range("A$i:C$i")
        $rowRange.Interior.ColorIndex = 2  # White
    } else {
        $rowRange = $worksheet.Range("A$i:C$i")
        $rowRange.Interior.ColorIndex = 15  # Light gray
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
Write-Host "Total Level 1 rooms: $($excelData.Count)" -ForegroundColor Green
Write-Host ""
Write-Host "File is formatted for 8.5x11 printing" -ForegroundColor Cyan
Write-Host "Room numbers: 01, 02, 03, etc. (ascending order)" -ForegroundColor Cyan
