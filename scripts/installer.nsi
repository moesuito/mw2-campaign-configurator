; MW2 Campaign Configurator Installer Script
; For NSIS (Nullsoft Scriptable Install System)

!include "MUI2.nsh"

; Define variables / constants
!define APP_NAME "MW2 Campaign Configurator"
!define APP_VERSION "0.3.1"
!define EXE_NAME "MW2CampaignConfigurator.exe"
!define SETUP_NAME "MW2CampaignConfiguratorSetup.exe"
!define UNINSTALL_NAME "Uninstall.exe"
!define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\MW2CampaignConfigurator"

; General settings
Name "${APP_NAME}"
OutFile "..\dist\${SETUP_NAME}"
InstallDir "$APPDATA\MW2CampaignConfigurator"

; Request user execution level (no admin/UAC elevation needed)
RequestExecutionLevel user

; Interface configuration
!define MUI_ICON "..\assets\app.ico"
!define MUI_UNICON "..\assets\app.ico"
!define MUI_ABORTWARNING

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Sections
Section "${APP_NAME} (Required)" SecApp
  SectionIn RO
  
  SetOutPath "$INSTDIR"
  
  ; Copy files
  File "..\dist\${EXE_NAME}"
  
  ; Write uninstaller
  WriteUninstaller "$INSTDIR\${UNINSTALL_NAME}"
  
  ; Write registry keys for Control Panel Add/Remove Programs
  WriteRegStr HKCU "${REG_UNINSTALL}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "${REG_UNINSTALL}" "DisplayIcon" "$INSTDIR\${EXE_NAME}"
  WriteRegStr HKCU "${REG_UNINSTALL}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "${REG_UNINSTALL}" "Publisher" "moesuito"
  WriteRegStr HKCU "${REG_UNINSTALL}" "URLInfoAbout" "https://github.com/moesuito/mw2-campaign-configurator"
  WriteRegStr HKCU "${REG_UNINSTALL}" "UninstallString" "$INSTDIR\${UNINSTALL_NAME}"
  WriteRegDWORD HKCU "${REG_UNINSTALL}" "NoModify" 1
  WriteRegDWORD HKCU "${REG_UNINSTALL}" "NoRepair" 1
SectionEnd

Section "Desktop Shortcut" SecDesktop
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}"
SectionEnd

Section "Start Menu Shortcut" SecStartMenu
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk" "$INSTDIR\${UNINSTALL_NAME}"
SectionEnd

; Uninstaller Section
Section "Uninstall"
  ; Remove files
  Delete "$INSTDIR\${EXE_NAME}"
  Delete "$INSTDIR\${UNINSTALL_NAME}"
  
  ; Remove shortcuts
  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  
  ; Remove install directory (only if empty)
  RMDir "$INSTDIR"
  
  ; Remove registry keys
  DeleteRegKey HKCU "${REG_UNINSTALL}"
SectionEnd

; Descriptions of components
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecApp} "Installs the MW2 Campaign Configurator executable."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Creates a shortcut to the application on your Desktop."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Creates shortcuts in the Start Menu."
!insertmacro MUI_FUNCTION_DESCRIPTION_END
