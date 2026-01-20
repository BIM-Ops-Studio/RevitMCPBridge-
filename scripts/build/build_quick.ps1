# Quick build script
$msbuildPath = "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"

if (Test-Path $msbuildPath) {
    & $msbuildPath RevitMCPBridge2026.csproj /p:Configuration=Release /v:minimal
} else {
    Write-Host "ERROR: MSBuild not found at $msbuildPath" -ForegroundColor Red
    exit 1
}
