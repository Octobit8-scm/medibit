# Build and Installer Script for Medibit Pharmacy
# PowerShell version for GitHub Actions compatibility

Write-Host "=== Step 1: Clean previous build ===" -ForegroundColor Green
# Clean previous build
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "main.spec") { Remove-Item -Force "main.spec" }

Write-Host "=== Step 2: Build EXE with PyInstaller ===" -ForegroundColor Green
# Build EXE with PyInstaller
$pyinstallerArgs = @(
  "--noconfirm",
  "--onefile",
  "--windowed",
  "--icon=medibit.ico",
  "--version-file=version.txt",
  "src/main.py"
)

# Add images directory if it exists and contains files
$imagesPath = "src/public/images"
if (Test-Path $imagesPath) {
  $imageFiles = Get-ChildItem -Path $imagesPath -File
  if ($imageFiles.Count -gt 0) {
    $pyinstallerArgs += @("--add-binary", "src/public/images/*;public/images")
    Write-Host "Adding images directory to build..." -ForegroundColor Yellow
  }
  else {
    Write-Host "Images directory is empty, skipping..." -ForegroundColor Yellow
  }
}
else {
  Write-Host "Images directory not found, skipping..." -ForegroundColor Yellow
}

$result = & pyinstaller @pyinstallerArgs
if ($LASTEXITCODE -ne 0) {
  Write-Host "PyInstaller build failed!" -ForegroundColor Red
  exit 1
}

Write-Host "=== Step 3: Add additional binaries if they exist ===" -ForegroundColor Green
# Add additional binaries if they exist
$pyzbarPath = "venv\Lib\site-packages\pyzbar"
if (Test-Path "$pyzbarPath\libiconv.dll") {
  Copy-Item "$pyzbarPath\libiconv.dll" "dist\"
  Write-Host "Copied libiconv.dll" -ForegroundColor Yellow
}
if (Test-Path "$pyzbarPath\libzbar-64.dll") {
  Copy-Item "$pyzbarPath\libzbar-64.dll" "dist\"
  Write-Host "Copied libzbar-64.dll" -ForegroundColor Yellow
}

Write-Host "=== Step 4: Build installer with Inno Setup ===" -ForegroundColor Green
# Build installer with Inno Setup
$innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\iscc.exe"
if (Test-Path $innoSetupPath) {
  $result = & $innoSetupPath "installer.iss"
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Inno Setup build failed!" -ForegroundColor Red
    exit 1
  }
}
else {
  Write-Host "Inno Setup not found at: $innoSetupPath" -ForegroundColor Yellow
  Write-Host "Skipping installer creation..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Build and installer creation complete!" -ForegroundColor Green
Write-Host "Output: dist\MedibitPharmacySetup.exe" -ForegroundColor Cyan 