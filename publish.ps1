#requires -Version 5
param(
	[string]$Owner,
	[string]$Repo,
	[string]$Tag,
	[string]$Token = $env:GITHUB_TOKEN,
	[string]$ArtifactsDir = "dist",
	[string]$StableSetupName = "OSD-Overlay-Setup.exe"
)

$ErrorActionPreference = "Stop"
if (-not $Token) { throw "GITHUB_TOKEN gerekli" }
if (-not $Owner -or -not $Repo -or -not $Tag) { throw "Owner/Repo/Tag gerekli" }

$upload = {
	param($releaseId, $filePath)
	$fn = [System.IO.Path]::GetFileName($filePath)
	$mime = "application/octet-stream"
	$uri = "https://uploads.github.com/repos/$Owner/$Repo/releases/$releaseId/assets?name=$fn"
	$bytes = [System.IO.File]::ReadAllBytes($filePath)
	Invoke-RestMethod -Headers @{ Authorization = "token $Token" } -Method POST -Uri $uri -ContentType $mime -Body $bytes | Out-Null
}

Write-Host "Creating (or reusing) release $Tag" -ForegroundColor Cyan
$rel = Invoke-RestMethod -Headers @{ Authorization = "token $Token" } -Method POST -Uri "https://api.github.com/repos/$Owner/$Repo/releases" -Body (@{
	tag_name=$Tag; name=$Tag; draft=$false; prerelease=$false
} | ConvertTo-Json)
$rid = $rel.id

Write-Host "Uploading artifacts from $ArtifactsDir" -ForegroundColor Cyan
Get-ChildItem $ArtifactsDir -File | ForEach-Object { & $upload $rid $_.FullName }

# Ayrica versiyonsuz sabit isimli bir kopya uretip yukleyin
$setup = Join-Path $ArtifactsDir "OSD-Overlay-Setup-1.0.0.exe"
if (Test-Path $setup) {
	Copy-Item $setup (Join-Path $ArtifactsDir $StableSetupName) -Force
	& $upload $rid (Join-Path $ArtifactsDir $StableSetupName)
}

Write-Host "Done. Latest URL ornegi:" -ForegroundColor Green
Write-Host "https://github.com/$Owner/$Repo/releases/latest/download/$StableSetupName"
