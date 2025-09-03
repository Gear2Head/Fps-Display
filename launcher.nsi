!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "WinVer.nsh"
!include "InetC.nsh" ; Require inetc plugin

!define APPNAME "OSD Overlay Launcher"
!define OUTFILE "OSD-Overlay-Launcher.exe"
!define CONFIG "launcher_config.json"

Name "${APPNAME}"
OutFile "${OUTFILE}"
RequestExecutionLevel admin
ShowInstDetails nevershow

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Turkish"

Section
	SetOutPath $TEMP
	File "${CONFIG}"
	
	Var /GLOBAL URL
	Var /GLOBAL SAVEAS
	Var /GLOBAL SHA256
	
	ClearErrors
	FileOpen $0 "$TEMP\\${CONFIG}" r
	IfErrors 0 +3
		MessageBox MB_ICONSTOP "Yapilandirma dosyasi bulunamadi."
		Abort
	
	StrCpy $URL ""
	StrCpy $SAVEAS "OSD-Overlay-Setup.exe"
	StrCpy $SHA256 ""
	
	loop:
		FileRead $0 $1
		IfErrors done
		${IfThen} $1 ~ StrStr $1 \"installerUrl\" + 0 ${|}
			StrCpy $2 $1
			StrReplace $2 $2 '"' ''
			StrReplace $2 $2 ' ' ''
			StrCpy $URL $2 0 14
		${|}
		${EndIf}
		${IfThen} $1 ~ StrStr $1 \"saveAs\" + 0 ${|}
			StrCpy $3 $1
			StrReplace $3 $3 '"' ''
			StrReplace $3 $3 ' ' ''
			StrCpy $SAVEAS $3 0 7
		${|}
		${EndIf}
		${IfThen} $1 ~ StrStr $1 \"sha256\" + 0 ${|}
			StrCpy $4 $1
			StrReplace $4 $4 '"' ''
			StrReplace $4 $4 ' ' ''
			StrCpy $SHA256 $4 0 7
		${|}
		${EndIf}
		Goto loop
	done:
	FileClose $0

	${If} $URL == ""
		MessageBox MB_ICONSTOP "Gecerli installerUrl bulunamadi."
		Abort
	${EndIf}

	inetc::get /POPUP /SILENT /RESUME "$URL" "$TEMP\\$SAVEAS"
	Pop $0
	${If} $0 != "OK"
		MessageBox MB_ICONSTOP "Indirme basarisiz: $0"
		Abort
	${EndIf}

	; SHA256 dogrulama (istege bagli)
	${If} $SHA256 != ""
		nsExec::ExecToStack 'cmd /c certutil -hashfile "$TEMP\\$SAVEAS" SHA256'
		Pop $R0 ; rc
		Pop $R1 ; satir1 (SHA256 hash)
		Pop $R2
		StrCpy $R1 $R1 64 0
		StrCmp $R1 $SHA256 0 +3
			; esit
			Goto verified
		MessageBox MB_ICONSTOP "Dosya imza dogrulamasi basarisiz!" /SD IDOK
		Abort
		verified:
	${EndIf}

	ExecWait '"$TEMP\\$SAVEAS"'
SectionEnd
