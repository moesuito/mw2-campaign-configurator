$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (!(Test-Path -LiteralPath ".\.venv")) {
    py -m venv .venv
}

.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python .\scripts\create_icon.py
.\.venv\Scripts\pyinstaller --onefile --windowed --name MW2CampaignConfigurator --icon .\assets\app.ico --add-data "assets;assets" .\src\mw2_campaign_configurator.py --noconfirm

Get-Item .\dist\MW2CampaignConfigurator.exe

$makensis = "C:\Program Files (x86)\NSIS\makensis.exe"
if (Test-Path -Path $makensis) {
    Write-Host "Compiling NSIS Installer..."
    & $makensis .\scripts\installer.nsi
    Get-Item .\dist\MW2CampaignConfiguratorSetup.exe
} else {
    Write-Warning "NSIS (makensis.exe) not found at standard path '$makensis'. Installer creation skipped."
}

