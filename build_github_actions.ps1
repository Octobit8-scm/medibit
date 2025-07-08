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
# Add additional binaries if they exist - try multiple possible paths
$pyzbarPaths = @(
  "venv\Lib\site-packages\pyzbar",
  "venv\Lib\site-packages\pyzbar-0.1.9-py3.11.egg\pyzbar",
  "venv\Lib\site-packages\pyzbar-0.1.9-py3.11.egg\pyzbar\lib",
  "venv\Lib\site-packages\pyzbar\lib",
  "venv\Lib\site-packages\pyzbar\*.dll"
)

$dllsFound = $false
foreach ($pyzbarPath in $pyzbarPaths) {
  if (Test-Path "$pyzbarPath\libiconv.dll") {
    Copy-Item "$pyzbarPath\libiconv.dll" "dist\"
    Write-Host "Copied libiconv.dll from $pyzbarPath" -ForegroundColor Yellow
    $dllsFound = $true
  }
  if (Test-Path "$pyzbarPath\libzbar-64.dll") {
    Copy-Item "$pyzbarPath\libzbar-64.dll" "dist\"
    Write-Host "Copied libzbar-64.dll from $pyzbarPath" -ForegroundColor Yellow
    $dllsFound = $true
  }
}

# Also try to find DLLs in the current directory or Python installation
if (-not $dllsFound) {
  Write-Host "Searching for pyzbar DLLs in alternative locations..." -ForegroundColor Yellow
  $pythonPath = python -c "import sys; print(sys.prefix)" 2>$null
  if ($pythonPath) {
    $altPaths = @(
      "$pythonPath\Lib\site-packages\pyzbar",
      "$pythonPath\DLLs",
      "C:\Windows\System32"
    )
    foreach ($altPath in $altPaths) {
      if (Test-Path "$altPath\libiconv.dll") {
        Copy-Item "$altPath\libiconv.dll" "dist\"
        Write-Host "Copied libiconv.dll from $altPath" -ForegroundColor Yellow
      }
      if (Test-Path "$altPath\libzbar-64.dll") {
        Copy-Item "$altPath\libzbar-64.dll" "dist\"
        Write-Host "Copied libzbar-64.dll from $altPath" -ForegroundColor Yellow
      }
    }
  }
}

Write-Host "=== Step 4: Create distribution package ===" -ForegroundColor Green
# Create a zip archive for distribution
$version = "1.0.0"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zipName = "MedibitPharmacy-v$version-$timestamp.zip"

# Copy additional files to dist
$filesToCopy = @(
  "config.json",
  "pharmacy_inventory.db",
  "README.txt",
  "RELEASE_NOTES.txt",
  "license.txt"
)

foreach ($file in $filesToCopy) {
  if (Test-Path $file) {
    Copy-Item $file "dist\"
    Write-Host "Copied $file" -ForegroundColor Yellow
  }
  else {
    Write-Host "File not found: $file" -ForegroundColor Red
  }
}

# List what's in the dist directory before creating zip
Write-Host "Files in dist directory:" -ForegroundColor Cyan
Get-ChildItem "dist\" | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor White }

# Create zip archive
Compress-Archive -Path "dist\*" -DestinationPath $zipName -Force
Write-Host "Created distribution package: $zipName" -ForegroundColor Green

# List contents of the zip file
Write-Host "Contents of zip file:" -ForegroundColor Cyan
$zipContents = Get-ChildItem $zipName | ForEach-Object { 
  [System.IO.Compression.ZipFile]::OpenRead($_.FullName).Entries | Select-Object Name 
}
$zipContents | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor White }

Write-Host ""
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Executable: dist\main.exe" -ForegroundColor Cyan
Write-Host "Distribution package: $zipName" -ForegroundColor Cyan 