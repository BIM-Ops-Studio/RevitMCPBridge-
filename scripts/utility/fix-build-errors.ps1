# PowerShell script to fix build errors in MCP Bridge source

Write-Host "Fixing MCP Bridge build errors..." -ForegroundColor Green

# Fix Point/Rect references in RevitMCPBridgeApp.cs
$appFile = "src\RevitMCPBridgeApp.cs"
$content = Get-Content $appFile -Raw

# Add using statement for System.Windows
if ($content -notmatch "using System\.Windows;") {
    $content = $content -replace "(using System;)", "`$1`nusing System.Windows;"
}

# Fix TaskDialog ambiguity
$content = $content -replace "TaskDialog\.Show", "Autodesk.Revit.UI.TaskDialog.Show"

Set-Content $appFile $content

# Fix issues in MCPServer.cs
$serverFile = "src\MCPServer.cs"
$content = Get-Content $serverFile -Raw

# Add using statement for System.Linq
if ($content -notmatch "using System\.Linq;") {
    $content = $content -replace "(using System;)", "`$1`nusing System.Linq;"
}

# Fix IntegerValue (deprecated in Revit 2024+)
$content = $content -replace "\.IntegerValue", ".Value"

# Fix nullable Guid
$content = $content -replace "element\.VersionGuid\?\.ToString\(\)", "element.VersionGuid.ToString()"

Set-Content $serverFile $content

# Fix command files
$commandFiles = @(
    "src\Commands\QueryRevitCommand.cs",
    "src\Commands\ExecuteCommandCommand.cs", 
    "src\Commands\SettingsCommand.cs"
)

foreach ($file in $commandFiles) {
    $content = Get-Content $file -Raw
    
    # Fix TaskDialog references
    $content = $content -replace "TaskDialog\.Show", "Autodesk.Revit.UI.TaskDialog.Show"
    $content = $content -replace "new TaskDialog", "new Autodesk.Revit.UI.TaskDialog"
    
    # Fix Control reference in SettingsCommand.cs
    if ($file -like "*SettingsCommand*") {
        $content = $content -replace "new Control\[\]", "new System.Windows.Forms.Control[]"
    }
    
    # Remove PurgeUnused (not available in API)
    if ($file -like "*ExecuteCommandCommand*") {
        $content = $content -replace "doc\.PurgeUnused\(\);", "// PurgeUnused not available in API"
    }
    
    Set-Content $file $content
}

Write-Host "Build errors fixed!" -ForegroundColor Green
Write-Host ""
Write-Host "Now run: dotnet build --configuration Release" -ForegroundColor Yellow