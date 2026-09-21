!include "MUI2.nsh"

Name "Fanzy Projects"
OutFile "{{ROOT}}\dist\FanzyProjects-{{VERSION}}-windows-installer.exe"
InstallDir "$PROGRAMFILES64\Fanzy Projects"
RequestExecutionLevel admin
Unicode true

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Spanish"

Section "install"
    SetOutPath "$INSTDIR"
    File /r "{{ROOT}}\dist\fanzyprojects\*.*"
    CreateShortcut "$SMPROGRAMS\Fanzy Projects.lnk" "$INSTDIR\fanzyprojects.exe"
    CreateShortcut "$DESKTOP\Fanzy Projects.lnk" "$INSTDIR\fanzyprojects.exe"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Fanzy Projects" \
        "DisplayName" "Fanzy Projects"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Fanzy Projects" \
        "UninstallString" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\Fanzy Projects.lnk"
    Delete "$DESKTOP\Fanzy Projects.lnk"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Fanzy Projects"
SectionEnd