<#
.SYNOPSIS
    Installs RevitMCPBridge2026 to Revit 2026 Add-ins folder.

.DESCRIPTION
    This script:
    1. Builds the project (optional)
    2. Copies DLL and add-in manifest to Revit add-ins folder
    3. Verifies installation

.PARAMETER NoBuild
    Skip building, just deploy existing DLL.

.PARAMETER RevitYear
    Revit version year (default: 2026)

.EXAMPLE
    .\Install-RevitMCPBridge.ps1

.EXAMPLE
    .\Install-RevitMCPBridge.ps1 -NoBuild
#>

param(
    [switch]$NoBuild,
    [string]$RevitYear = "2026"
)

$ErrorActionPreference = "Stop"

# Configuration
$ProjectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$DllPath = Join-Path $ProjectRoot "bin\Release\RevitMCPBridge2026.dll"
$AddinPath = Join-Path $ProjectRoot "RevitMCPBridge2026.addin"
$ConfigPath = Join-Path $ProjectRoot "appsettings.json"
$CsprojPath = Join-Path $ProjectRoot "RevitMCPBridge2026.csproj"
$TargetFolder = "$env:APPDATA\Autodesk\Revit\Addins\$RevitYear"

Write-Host "========================================"
Write-Host "RevitMCPBridge2026 Installer"
Write-Host "========================================"
Write-Host ""
Write-Host "Project Root: $ProjectRoot"
Write-Host "Target Folder: $TargetFolder"
Write-Host ""

# Step 1: Build (unless -NoBuild)
if (-not $NoBuild) {
    Write-Host "[1/4] Building project..."

    # Find MSBuild
    $msbuildPaths = @(
        "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
        "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
        "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
        "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
    )

    $msbuild = $null
    foreach ($path in $msbuildPaths) {
        if (Test-Path $path) {
            $msbuild = $path
            break
        }
    }

    if (-not $msbuild) {
        Write-Error "MSBuild not found. Please install Visual Studio 2022."
        exit 1
    }

    Write-Host "   Using MSBuild: $msbuild"

    Push-Location $ProjectRoot
    try {
        & $msbuild $CsprojPath /p:Configuration=Release /v:minimal /nologo
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Build failed with exit code $LASTEXITCODE"
            exit 1
        }
        Write-Host "   Build succeeded" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "[1/4] Skipping build (-NoBuild specified)"
}

# Step 2: Verify DLL exists
Write-Host "[2/4] Verifying build output..."
if (-not (Test-Path $DllPath)) {
    Write-Error "DLL not found at: $DllPath"
    Write-Host "   Run without -NoBuild to build first."
    exit 1
}

$dllInfo = Get-Item $DllPath
Write-Host "   DLL found: $($dllInfo.Length / 1KB) KB, modified $($dllInfo.LastWriteTime)"

# Step 3: Create target folder if needed
Write-Host "[3/4] Preparing target folder..."
if (-not (Test-Path $TargetFolder)) {
    Write-Host "   Creating folder: $TargetFolder"
    New-Item -ItemType Directory -Path $TargetFolder -Force | Out-Null
}

# Check if Revit is running
$revitProcess = Get-Process -Name "Revit" -ErrorAction SilentlyContinue
if ($revitProcess) {
    Write-Host ""
    Write-Warning "Revit is currently running!"
    Write-Host "   The add-in may not be updated until you restart Revit."
    Write-Host ""
    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne "y") {
        Write-Host "Installation cancelled."
        exit 0
    }
}

# Step 4: Copy files
Write-Host "[4/4] Installing files..."

try {
    # Copy DLL
    Copy-Item -Path $DllPath -Destination $TargetFolder -Force
    Write-Host "   Copied: RevitMCPBridge2026.dll"

    # Copy addin manifest
    Copy-Item -Path $AddinPath -Destination $TargetFolder -Force
    Write-Host "   Copied: RevitMCPBridge2026.addin"

    # Copy configuration file (only if doesn't exist - preserve user settings)
    $targetConfig = Join-Path $TargetFolder "appsettings.json"
    if (-not (Test-Path $targetConfig)) {
        if (Test-Path $ConfigPath) {
            Copy-Item -Path $ConfigPath -Destination $TargetFolder -Force
            Write-Host "   Copied: appsettings.json (default config)"
        }
    }
    else {
        Write-Host "   Skipped: appsettings.json (user config preserved)"
    }

    # Also copy dependencies if they exist
    $depsFolder = Join-Path $ProjectRoot "bin\Release"
    $deps = @("Newtonsoft.Json.dll", "Serilog.dll", "Serilog.Sinks.File.dll")
    foreach ($dep in $deps) {
        $depPath = Join-Path $depsFolder $dep
        if (Test-Path $depPath) {
            Copy-Item -Path $depPath -Destination $TargetFolder -Force
            Write-Host "   Copied: $dep"
        }
    }
}
catch {
    Write-Error "Failed to copy files: $_"
    exit 1
}

# Verify installation
Write-Host ""
Write-Host "========================================"
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "Installed to: $TargetFolder"
Write-Host ""
Write-Host "Files installed:"
Get-ChildItem -Path $TargetFolder -Filter "RevitMCPBridge*" | ForEach-Object {
    Write-Host "   - $($_.Name)"
}
Write-Host ""
Write-Host "Next steps:"
Write-Host "   1. Start Revit 2026"
Write-Host "   2. Open a project"
Write-Host "   3. Run smoke test: python tests/smoke_test.py"
Write-Host ""
