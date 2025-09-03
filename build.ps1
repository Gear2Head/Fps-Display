#requires -Version 5
param(
	[string]$Python = "python",
	[string]$OutputDir = "dist"
)

$ErrorActionPreference = "Stop"

Write-Host "Installing build dependencies..." -ForegroundColor Cyan
& $Python -m pip install --upgrade pip | Out-Host
& $Python -m pip install pyinstaller -q | Out-Host

Write-Host "Building single-file exe..." -ForegroundColor Cyan
$specArgs = @(
	"--onefile",
	"--windowed",
	"--name",
	"OSD-Overlay",
	"--add-data",
	"config.json;.",
	"app.py"
)

& $Python -m PyInstaller $specArgs | Out-Host

Write-Host "Build completed. Output in: $OutputDir" -ForegroundColor Green
