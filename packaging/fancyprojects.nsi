!include "MUI2.nsh"

Name "Fancy Projects"
OutFile "{{ROOT}}\dist\FancyProjects-{{VERSION}}-windows-installer.exe"
InstallDir "$PROGRAMFILES64\Fancy Projects"
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
    File /r "{{ROOT}}\dist\fancyprojects\*.*"
    CreateShortcut "$SMPROGRAMS\Fancy Projects.lnk" "$INSTDIR\fancyprojects.exe"
    CreateShortcut "$DESKTOP\Fancy Projects.lnk" "$INSTDIR\fancyprojects.exe"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Fancy Projects" \
        "DisplayName" "Fancy Projects"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Fancy Projects" \
        "UninstallString" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\Fancy Projects.lnk"
    Delete "$DESKTOP\Fancy Projects.lnk"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Fancy Projects"
SectionEnd