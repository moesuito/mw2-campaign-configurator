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
