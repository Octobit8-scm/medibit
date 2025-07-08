# Build Script for GitHub Actions
# Creates EXE and zip archive instead of installer

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

Write-Host "=== Step 4: Create distribution package ===" -ForegroundColor Green
# Create a zip archive for distribution
$version = "1.0.0"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zipName = "MedibitPharmacy-v$version-$timestamp.zip"

# Copy additional files to dist
if (Test-Path "config.json") {
  Copy-Item "config.json" "dist\"
  Write-Host "Copied config.json" -ForegroundColor Yellow
}
if (Test-Path "pharmacy_inventory.db") {
  Copy-Item "pharmacy_inventory.db" "dist\"
  Write-Host "Copied pharmacy_inventory.db" -ForegroundColor Yellow
}
if (Test-Path "README.txt") {
  Copy-Item "README.txt" "dist\"
  Write-Host "Copied README.txt" -ForegroundColor Yellow
}
if (Test-Path "RELEASE_NOTES.txt") {
  Copy-Item "RELEASE_NOTES.txt" "dist\"
  Write-Host "Copied RELEASE_NOTES.txt" -ForegroundColor Yellow
}

# Create zip archive
Compress-Archive -Path "dist\*" -DestinationPath $zipName -Force
Write-Host "Created distribution package: $zipName" -ForegroundColor Green

Write-Host ""
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Executable: dist\main.exe" -ForegroundColor Cyan
Write-Host "Distribution package: $zipName" -ForegroundColor Cyan 