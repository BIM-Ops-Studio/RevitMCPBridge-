# Build RevitMCPBridge2026
$msbuildPath = "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"

if (-not (Test-Path $msbuildPath)) {
    $msbuildPath = "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
}

if (-not (Test-Path $msbuildPath)) {
    Write-Host "MSBuild not found! Please install Visual Studio or Build Tools." -ForegroundColor Red
    exit 1
}

& $msbuildPath "RevitMCPBridge2026.csproj" /p:Configuration=Release /v:minimal
