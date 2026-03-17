# Scholarr Windows Installer
# Installs to C:\Scholarr with optional Windows Service
# Uses SQLite — no database server needed

$Version = "0.2.0"
$InstallPath = "C:\Scholarr"
$DataPath = "$env:LOCALAPPDATA\Scholarr"

Write-Host ""
Write-Host "  Scholarr v$Version - Windows Installer" -ForegroundColor Cyan
Write-Host "  ----------------------------------------" -ForegroundColor Cyan
Write-Host ""

# Find Python
$Python = $null
foreach ($p in @("python3", "python")) {
    $cmd = Get-Command $p -ErrorAction SilentlyContinue
    if ($cmd) {
        $ver = & $cmd.Source -c "import sys;print(sys.version_info.minor)" 2>$null
        if ([int]$ver -ge 11) {
            $Python = $cmd.Source
            break
        }
    }
}

if (-not $Python) {
    Write-Host "  ERROR: Python 3.11+ required. Download from python.org" -ForegroundColor Red
    exit 1
}

$PyVer = & $Python --version
Write-Host "  Python: $PyVer"

# Create directories
Write-Host "  Creating directories..."
New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
New-Item -ItemType Directory -Path "$DataPath\data" -Force | Out-Null
New-Item -ItemType Directory -Path "$DataPath\uploads" -Force | Out-Null
New-Item -ItemType Directory -Path "$DataPath\backups" -Force | Out-Null
New-Item -ItemType Directory -Path "$DataPath\config" -Force | Out-Null

# Virtual environment
Write-Host "  Creating virtual environment..."
& $Python -m venv "$InstallPath\venv"
& "$InstallPath\venv\Scripts\python.exe" -m pip install --upgrade pip -q

# Install Scholarr
Write-Host "  Installing Scholarr..."
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
if (Test-Path "$RepoRoot\pyproject.toml") {
    & "$InstallPath\venv\Scripts\pip.exe" install -e $RepoRoot -q
} else {
    & "$InstallPath\venv\Scripts\pip.exe" install scholarr -q
}

# Generate config
$ApiKey = & "$InstallPath\venv\Scripts\python.exe" -c "import secrets;print(secrets.token_urlsafe(32))"
$DbPath = "$DataPath\data\scholarr.db" -replace '\\', '/'
$ConfigFile = "$DataPath\config\scholarr.env"
@"
SCHOLARR_API_KEY=$ApiKey
SCHOLARR_DATABASE_URL=sqlite+aiosqlite:///$DbPath
SCHOLARR_DATA_DIR=$DataPath\data
SCHOLARR_UPLOAD_DIR=$DataPath\uploads
SCHOLARR_BACKUP_DIR=$DataPath\backups
SCHOLARR_LOG_LEVEL=info
SCHOLARR_PORT=8787
"@ | Set-Content $ConfigFile

# Launcher batch file
@"
@echo off
title Scholarr
cd /d "$InstallPath"
for /f "tokens=*" %%a in ($ConfigFile) do set %%a
venv\Scripts\uvicorn.exe scholarr.app:create_app --factory --host 127.0.0.1 --port 8787
"@ | Set-Content "$InstallPath\scholarr.bat"

# Launcher PowerShell script
@"
`$env:Path = "$InstallPath\venv\Scripts;" + `$env:Path
Get-Content "$ConfigFile" | ForEach-Object {
    if (`$_ -match '^([^#]\S+?)=(.*)$') {
        [Environment]::SetEnvironmentVariable(`$Matches[1], `$Matches[2], 'Process')
    }
}
& "$InstallPath\venv\Scripts\uvicorn.exe" scholarr.app:create_app --factory --host 127.0.0.1 --port 8787
"@ | Set-Content "$InstallPath\Start-Scholarr.ps1"

# Start Menu shortcut
Write-Host "  Creating shortcuts..."
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Scholarr.lnk")
$Shortcut.TargetPath = "$InstallPath\scholarr.bat"
$Shortcut.WorkingDirectory = $InstallPath
$Shortcut.Description = "Scholarr Academic Manager"
$Shortcut.Save()

# Desktop shortcut
$Desktop = $Shell.CreateShortcut("$env:USERPROFILE\Desktop\Scholarr.lnk")
$Desktop.TargetPath = "$InstallPath\scholarr.bat"
$Desktop.WorkingDirectory = $InstallPath
$Desktop.Description = "Scholarr Academic Manager"
$Desktop.Save()

# Uninstaller
@"
Write-Host "Uninstalling Scholarr..."
Remove-Item -Path "$InstallPath" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Scholarr.lnk" -ErrorAction SilentlyContinue
Remove-Item -Path "$env:USERPROFILE\Desktop\Scholarr.lnk" -ErrorAction SilentlyContinue
Write-Host "Scholarr uninstalled. Data preserved at: $DataPath"
"@ | Set-Content "$InstallPath\Uninstall-Scholarr.ps1"

Write-Host ""
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  API Key: $ApiKey"
Write-Host "  Config:  $ConfigFile"
Write-Host "  Data:    $DataPath"
Write-Host ""
Write-Host "  Start: Double-click 'Scholarr' on Desktop or Start Menu"
Write-Host "  Open:  http://localhost:8787"
Write-Host ""

$Start = Read-Host "  Start Scholarr now? (Y/n)"
if ($Start -eq "" -or $Start.ToLower() -eq "y") {
    Start-Process "$InstallPath\scholarr.bat"
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:8787"
}
