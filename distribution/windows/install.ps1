#Requires -RunAsAdministrator

# Scholarr Windows Installer Script
# Installation path: C:\ProgramData\Scholarr
# Data path: C:\Users\[User]\AppData\Local\Scholarr

param(
    [switch]$SkipPythonCheck = $false
)

function Write-Header {
    param([string]$Text)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Status {
    param([string]$Text)
    Write-Host "➜ $Text" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "✗ ERROR: $Text" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "! WARNING: $Text" -ForegroundColor Yellow
}

# Verify admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error-Custom "This installer must be run as Administrator"
    exit 1
}

Write-Header "Scholarr v0.1.0 - Windows Installer"

# Check Python 3.11+ is installed
Write-Status "Checking Python 3.11+ installation..."
$pythonPath = $null
$pythonVersion = $null

# Try to find Python
$pythonExe = Get-Command python -ErrorAction SilentlyContinue
if ($pythonExe) {
    $pythonPath = $pythonExe.Source
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Status "Found Python at: $pythonPath"
    Write-Status "Version: $pythonVersion"
} else {
    if ($SkipPythonCheck) {
        Write-Warning-Custom "Python not found in PATH. Please install Python 3.11+ manually."
        $pythonPath = Read-Host "Enter full path to python.exe"
    } else {
        Write-Error-Custom "Python 3.11+ is required but not found"
        Write-Host "`nPlease install Python from: https://www.python.org/downloads/"
        exit 1
    }
}

# Verify Python version is 3.11+
$pythonVersion -match "(\d+)\.(\d+)" | Out-Null
if ($Matches[1] -lt 3 -or ($Matches[1] -eq 3 -and $Matches[2] -lt 11)) {
    Write-Error-Custom "Python 3.11 or later is required. Found: $pythonVersion"
    exit 1
}
Write-Status "Python version OK ($($Matches[1]).$($Matches[2]))"

# Create installation directory
Write-Status "Creating installation directory..."
$installPath = "C:\ProgramData\Scholarr"
if (-not (Test-Path $installPath)) {
    New-Item -ItemType Directory -Path $installPath | Out-Null
}

$dataPath = "$env:LOCALAPPDATA\Scholarr"
if (-not (Test-Path $dataPath)) {
    New-Item -ItemType Directory -Path "$dataPath\config" | Out-Null
    New-Item -ItemType Directory -Path "$dataPath\library" | Out-Null
    New-Item -ItemType Directory -Path "$dataPath\inbox" | Out-Null
}

Write-Status "Installation path: $installPath"
Write-Status "Data path: $dataPath"

# Create virtual environment
Write-Status "Creating Python virtual environment..."
& $pythonPath -m venv "$installPath\venv"
if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to create virtual environment"
    exit 1
}

# Activate virtualenv
$activateScript = "$installPath\venv\Scripts\Activate.ps1"
& $activateScript

# Upgrade pip
Write-Status "Upgrading pip..."
& "$installPath\venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel | Out-Null

# Install Scholarr
Write-Status "Installing Scholarr..."
if (Test-Path "pyproject.toml") {
    & "$installPath\venv\Scripts\pip.exe" install -e . 2>&1 | Select-Object -Last 5
} else {
    & "$installPath\venv\Scripts\pip.exe" install scholarr==0.1.0 2>&1 | Select-Object -Last 5
}

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to install Scholarr"
    exit 1
}

# Create environment file
Write-Status "Creating configuration file..."
$envFile = "$dataPath\config\scholarr.env"
$secretKey = (New-Object System.Guid).Guid

@"
# Scholarr Environment Configuration
# Generated during installation: $(Get-Date)

SCHOLARR_ENVIRONMENT=production
SCHOLARR_LOG_LEVEL=info
SCHOLARR_DATABASE_URL=mysql+aiomysql://scholarr:scholarr_password@localhost:3306/scholarr
SCHOLARR_SECRET_KEY=$secretKey
"@ | Set-Content $envFile

# Create batch wrapper script for running Scholarr
Write-Status "Creating launcher script..."
$launcherScript = "$installPath\scholarr.bat"
@"
@echo off
cd /d "$installPath"
venv\Scripts\activate.bat
uvicorn scholarr.app:app --host 0.0.0.0 --port 8787 --log-level info
"@ | Set-Content $launcherScript

# Create Windows service using NSSM if available, otherwise create scheduled task
Write-Status "Setting up Scholarr service..."

$nssmPath = "C:\ProgramData\NSSM\nssm.exe"
$useNssm = $false

if (Test-Path $nssmPath) {
    $useNssm = $true
    Write-Status "Using NSSM to create Windows service..."

    & $nssmPath install Scholarr "$installPath\venv\Scripts\python.exe" "-m uvicorn scholarr.app:app --host 0.0.0.0 --port 8787"
    & $nssmPath set Scholarr AppDirectory "$installPath"
    & $nssmPath set Scholarr AppEnvironmentExtra "SCHOLARR_DATABASE_URL=mysql+aiomysql://scholarr:scholarr_password@localhost:3306/scholarr"
    & $nssmPath start Scholarr
} else {
    Write-Warning-Custom "NSSM not installed. Creating startup shortcut instead."
    Write-Host "`nTo create a Windows service, download and install NSSM from: https://nssm.cc/"

    # Create Start Menu shortcut
    $startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Scholarr.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($startMenuPath)
    $shortcut.TargetPath = "$installPath\scholarr.bat"
    $shortcut.WorkingDirectory = $installPath
    $shortcut.IconLocation = "C:\Windows\System32\cmd.exe,0"
    $shortcut.Save()

    Write-Status "Created Start Menu shortcut"
}

# Create Start Menu shortcut for launching application
Write-Status "Creating application shortcuts..."
$appShortcut = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Scholarr App.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($appShortcut)
$shortcut.TargetPath = "http://localhost:8787"
$shortcut.Save()

# Create uninstaller script
Write-Status "Creating uninstaller..."
$uninstallerScript = "$installPath\uninstall.ps1"
@"
#Requires -RunAsAdministrator

`$nssmPath = "C:\ProgramData\NSSM\nssm.exe"
if (Test-Path `$nssmPath) {
    & `$nssmPath stop Scholarr
    & `$nssmPath remove Scholarr confirm
}

Remove-Item -Path "$installPath" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$appShortcut" -ErrorAction SilentlyContinue
Remove-Item -Path "$startMenuPath" -ErrorAction SilentlyContinue

Write-Host "Scholarr has been uninstalled."
"@ | Set-Content $uninstallerScript

Write-Header "Installation Complete!"

Write-Host "Installation path: $installPath"
Write-Host "Data path: $dataPath"
Write-Host "Configuration file: $envFile"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Set up MySQL database (or update credentials in: $envFile)"
Write-Host "2. Review configuration at: $envFile"
Write-Host "3. Start Scholarr:"
Write-Host "   - If using NSSM: Service should be running"
Write-Host "   - Otherwise: Double-click 'Scholarr' in Start Menu"
Write-Host "4. Open browser to: http://localhost:8787"
Write-Host ""

# Option to start immediately
$startNow = Read-Host "Start Scholarr now? (Y/n)"
if ($startNow -eq "" -or $startNow.ToLower() -eq "y") {
    if ($useNssm) {
        Write-Status "Service is running"
    } else {
        Write-Status "Starting Scholarr..."
        Start-Process -FilePath $launcherScript
    }

    Write-Status "Opening browser..."
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8787"
}

Write-Host "`nTo uninstall, run: PowerShell -File `"$uninstallerScript`""
