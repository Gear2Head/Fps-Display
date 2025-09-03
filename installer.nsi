!include "MUI2.nsh"

!define APPNAME "OSD Overlay"
!define COMPANY "YourCompany"
!define VERSION "1.0.0"
!define OUTFILE "OSD-Overlay-Setup.exe"
!define INSTALLDIR "$PROGRAMFILES64\\${COMPANY}\\${APPNAME}"

Name "${APPNAME}"
OutFile "${OUTFILE}"
InstallDir "${INSTALLDIR}"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Turkish"

Section "Install"
	SetOutPath "$INSTDIR"
	File /r "dist\\OSD-Overlay.exe"
	CreateShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\OSD-Overlay.exe"
SectionEnd

Section "Uninstall"
	Delete "$DESKTOP\\${APPNAME}.lnk"
	Delete "$INSTDIR\\OSD-Overlay.exe"
	RMDir "$INSTDIR"
SectionEnd
