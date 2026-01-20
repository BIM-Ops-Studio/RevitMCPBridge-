# PowerShell script to test DLL contents
Write-Host "Testing MCP Bridge DLL..." -ForegroundColor Green

$dllPath = "$env:APPDATA\Autodesk\Revit\Addins\2026\RevitMCPBridge2026.dll"

if (Test-Path $dllPath) {
    Write-Host "DLL found at: $dllPath" -ForegroundColor Yellow
    
    try {
        # Load the assembly
        $assembly = [System.Reflection.Assembly]::LoadFrom($dllPath)
        
        Write-Host "`nAssembly loaded successfully!" -ForegroundColor Green
        Write-Host "Full Name: $($assembly.FullName)"
        
        # Get all types
        $types = $assembly.GetTypes()
        Write-Host "`nTypes found in assembly:" -ForegroundColor Yellow
        foreach ($type in $types) {
            Write-Host "  - $($type.FullName)"
            if ($type.GetInterface("Autodesk.Revit.UI.IExternalApplication")) {
                Write-Host "    [IExternalApplication]" -ForegroundColor Green
            }
        }
        
        # Look specifically for our app class
        $appClass = $types | Where-Object { $_.Name -eq "RevitMCPBridgeApp" }
        if ($appClass) {
            Write-Host "`nFound RevitMCPBridgeApp class!" -ForegroundColor Green
            Write-Host "Full name: $($appClass.FullName)"
            Write-Host "Namespace: $($appClass.Namespace)"
        } else {
            Write-Host "`nERROR: RevitMCPBridgeApp class not found!" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "`nERROR loading assembly: $_" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: DLL not found at $dllPath" -ForegroundColor Red
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")