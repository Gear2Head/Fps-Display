#requires -Version 5
param(
	[string]$RepoUrl = "https://github.com/Gear2Head/Fps-Display.git",
	[string]$Tag = "v1.0.0",
	[switch]$CreateRelease
)

$ErrorActionPreference = "Stop"

# Ensure git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
	throw "git bulunamadi. https://git-scm.com/ yukleyin."
}

# Initialize repo if needed
if (-not (Test-Path .git)) {
	git init
	git add .
	git commit -m "Initial commit"
	git branch -M main
	git remote add origin $RepoUrl
}

# Push current state
git add .
 git commit -m "Setup" -m "Automated commit" --allow-empty
 git push -u origin main

# Tag and push
if ($Tag) {
	git tag -f $Tag
	git push -f origin $Tag
}

# If we have a local installer, compute sha256 and write to launcher_config.json
$setup = Join-Path $PWD "OSD-Overlay-Setup.exe"
if (Test-Path $setup) {
	$sha = (certutil -hashfile $setup SHA256 | Select-String -Pattern '^[0-9A-F]{64}$').Matches.Value
	if ($sha) {
		$json = Get-Content launcher_config.json -Raw | ConvertFrom-Json
		$json.sha256 = $sha
		($json | ConvertTo-Json -Depth 5) | Set-Content launcher_config.json -Encoding UTF8
		git add launcher_config.json
		git commit -m "Update launcher sha256"
		git push
	}
}

if ($CreateRelease) {
	Write-Host "Actions workflow release olusturacak (tag ile). GitHub Actions sekmesini izleyin." -ForegroundColor Cyan
}
