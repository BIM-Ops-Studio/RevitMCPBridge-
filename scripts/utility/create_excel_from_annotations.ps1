# Create Excel file using square footage from text annotations on the floor plan

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
Write-Host "CREATING EXCEL FROM FLOOR PLAN ANNOTATIONS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get active view
Write-Host "Getting active view..." -ForegroundColor Yellow
$viewResult = Send-RevitCommand -Method "getActiveView" -Params @{}

if (-not $viewResult.success) {
    Write-Host "ERROR: Could not get active view" -ForegroundColor Red
    Write-Host $viewResult.error -ForegroundColor Red
    exit 1
}

$viewId = $viewResult.viewId
$viewName = $viewResult.viewName
$levelName = $viewResult.level

Write-Host "Active View: $viewName" -ForegroundColor Green
Write-Host "Level: $levelName" -ForegroundColor Green
Write-Host "View ID: $viewId`n" -ForegroundColor Green

# Get all text notes from the view
Write-Host "Reading text annotations from view..." -ForegroundColor Yellow
$textResult = Send-RevitCommand -Method "getTextNotesInView" -Params @{ viewId = $viewId }

if (-not $textResult.success) {
    Write-Host "ERROR: Could not get text notes" -ForegroundColor Red
    Write-Host $textResult.error -ForegroundColor Red
    exit 1
}

Write-Host "Found $($textResult.textNoteCount) text annotations`n" -ForegroundColor Green

# Get all rooms for the level
Write-Host "Getting rooms from Revit..." -ForegroundColor Yellow
$roomsResult = Send-RevitCommand -Method "getRooms" -Params @{}

if (-not $roomsResult.success) {
    Write-Host "ERROR: Failed to get rooms" -ForegroundColor Red
    exit 1
}

$levelRooms = $roomsResult.rooms | Where-Object { $_.level -eq $levelName }
Write-Host "Found $($levelRooms.Count) rooms on $levelName`n" -ForegroundColor Green

# Parse text notes to extract square footage
# Looking for patterns like "810 SF", "810 square foot", "810 sq ft", etc.
$squareFootages = @{}

foreach ($note in $textResult.textNotes) {
    $text = $note.text

    # Try to match patterns like "810 SF", "810 square foot", "810 sq ft"
    if ($text -match '(\d+)\s*(SF|square\s*foot|sq\s*ft|SqFt)') {
        $sqft = [int]$matches[1]

        # Try to find room number in the text (like "01", "02", etc.)
        if ($text -match '\b0?(\d{1,2})\b') {
            $roomNum = "{0:D2}" -f [int]$matches[1]
            if (-not $squareFootages.ContainsKey($roomNum)) {
                $squareFootages[$roomNum] = $sqft
                Write-Host "Found: Room $roomNum = $sqft SF" -ForegroundColor Cyan
            }
        }
    }
}

Write-Host "`nParsed $($squareFootages.Count) square footage values from annotations`n" -ForegroundColor Green

# Create Excel data
$excelData = @()
foreach ($room in $levelRooms) {
    $roomNum = "{0:D2}" -f [int]$room.number

    # Use square footage from annotation if available, otherwise use room area
    if ($squareFootages.ContainsKey($roomNum)) {
        $sqft = $squareFootages[$roomNum]
        Write-Host "Using annotation value for Room $roomNum : $sqft SF" -ForegroundColor White
    } else {
        $sqft = [math]::Round([double]$room.area, 0)
        Write-Host "No annotation found for Room $roomNum, using room area: $sqft SF" -ForegroundColor Yellow
    }

    $excelData += [PSCustomObject]@{
        'Room Number' = $roomNum
        'Room Name' = $room.name
        'Square Footage' = $sqft
    }
}

# Sort by room number
$excelData = $excelData | Sort-Object { [int]$_.'Room Number' }

Write-Host "`nSample data:" -ForegroundColor Cyan
$excelData | Select-Object -First 5 | Format-Table
Write-Host ""

# Create Excel file
$excelPath = "D:\RevitMCPBridge2026\${levelName}_Room_List_From_Annotations.xlsx"

Write-Host "Creating Excel file: $excelPath" -ForegroundColor Yellow

# Create Excel COM object
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

# Create new workbook
$workbook = $excel.Workbooks.Add()
$worksheet = $workbook.Worksheets.Item(1)
$worksheet.Name = "$levelName Rooms"

# Set page setup for 8.5x11
$worksheet.PageSetup.Orientation = 1  # Portrait
$worksheet.PageSetup.PaperSize = 1    # Letter (8.5x11)
$worksheet.PageSetup.FitToPagesWide = 1
$worksheet.PageSetup.LeftMargin = 36
$worksheet.PageSetup.RightMargin = 36
$worksheet.PageSetup.TopMargin = 36
$worksheet.PageSetup.BottomMargin = 36

# Add title
$worksheet.Cells.Item(1, 1) = "TYPICAL FLOOR PLAN - $levelName"
$worksheet.Cells.Item(1, 1).Font.Size = 16
$worksheet.Cells.Item(1, 1).Font.Bold = $true
$worksheet.Cells.Item(1, 1).HorizontalAlignment = -4108

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
Write-Host "Values from annotations: $($squareFootages.Count)" -ForegroundColor Green
Write-Host ""
