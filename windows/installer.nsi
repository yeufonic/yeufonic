; Yeufonic for Windows: a small installer.  It carries our own files, shows the
; terms, and runs setup.ps1, which checks the PC and fetches the rest from each
; part's publisher.  Per user, into %LOCALAPPDATA%, so no administrator prompt.
;
; Built by windows/build.sh:  makensis /DVERSION=x.y.z /DSTAGE=<staged files> installer.nsi

Unicode true
!include "MUI2.nsh"
!include "Sections.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
!include "TextFunc.nsh"
!include "FileFunc.nsh"

!ifndef VERSION
  !error "VERSION is not defined"
!endif
!ifndef STAGE
  !error "STAGE is not defined"
!endif
!ifndef OUTFILE
  !define OUTFILE "Yeufonic-Setup-${VERSION}.exe"
!endif

; TEST_INSTALL is a test build that sets up for real (nothing skipped), so it needs no setup arguments of its own.
!ifdef TEST_INSTALL
  !ifndef SETUP_ARGS
    !define SETUP_ARGS ""
  !endif
!endif

; A test build (setup given -SkipModels or -CheckOnly) has its own name, shortcuts and
; uninstall entry, so trying it out on a PC with Yeufonic installed leaves that alone.
; LEGACY is the app's name before it was Yeufonic: an install of YuE2 Studio is taken
; over where it stands (see .onInit).  A test build takes over a YuE2 Studio test build.
!ifdef SETUP_ARGS
  !define APPNAME "Yeufonic (test)"
  !define REGNAME "YeufonicTest"
  !define LEGACY_APPNAME "YuE2 Studio (test)"
  !define LEGACY_REGNAME "YuE2StudioTest"
!else
  !define SETUP_ARGS ""
  !define APPNAME "Yeufonic"
  !define REGNAME "Yeufonic"
  !define LEGACY_APPNAME "YuE2 Studio"
  !define LEGACY_REGNAME "YuE2Studio"
!endif
!define LEGACY_REGKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${LEGACY_REGNAME}"
!define REGKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${REGNAME}"

Name "${APPNAME}"
OutFile "${OUTFILE}"
InstallDir "$LOCALAPPDATA\Programs\${REGNAME}"   ; where per-user programs go (VS Code, Discord)
InstallDirRegKey HKCU "Software\${REGNAME}" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
BrandingText "${APPNAME} ${VERSION}"

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "${APPNAME}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "FileDescription" "${APPNAME} installer"
VIAddVersionKey "LegalCopyright" "Copyright (c) 2026 Paul Shields. All rights reserved."

!define MUI_ICON "${STAGE}\yeufonic.ico"
!define MUI_UNICON "${STAGE}\yeufonic.ico"
; The logo on the Welcome and Finish pages, in place of NSIS's own picture (164 x 314).
!define MUI_WELCOMEFINISHPAGE_BITMAP "${STAGE}\installer-panel.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${STAGE}\installer-panel.bmp"
!define MUI_ABORTWARNING

;  An install already on this PC is updated in place: the pages say so, the folder
; page is skipped, and the Gemma choice made last time is kept (see .onInit).
Var Updating        ; 1 when this installer is updating an install already here
Var Legacy          ; 1 when that install is YuE2 Studio, the app's name before
Var OldVersion
Var WelcomeTitle
Var WelcomeText
Var InstHeader
Var InstSubtext
Var FinishText
Var ModelRadio     ; the model size section that is ticked (SecFull or SecSmall)
Var EngineRadio    ; the engine section that is ticked (SecComfy or SecCpp)
Var FullSize       ; the two model sizes' download sizes as the page first showed them (0 when installed),
Var SmallSize      ; put back when ComfyUI is chosen again after yue2.cpp, which needs neither
Var LyricsText      ; the Gemma option's description, which says when it is already here
Var PicturesText    ; the same for FLUX.2 klein
Var LorasText       ; the same for the style LoRAs
Var VoicesText      ; the same for recorded voices

!define MUI_WELCOMEPAGE_TITLE "$WelcomeTitle"
!define MUI_WELCOMEPAGE_TEXT "$WelcomeText"
!insertmacro MUI_PAGE_WELCOME
!define MUI_LICENSEPAGE_TEXT_TOP "Each part is used under its own terms."
!insertmacro MUI_PAGE_LICENSE "${STAGE}\terms.txt"
!define MUI_PAGE_CUSTOMFUNCTION_SHOW WiderComponents
!insertmacro MUI_PAGE_COMPONENTS
!define MUI_PAGE_CUSTOMFUNCTION_PRE SkipWhenUpdating
!insertmacro MUI_PAGE_DIRECTORY
!define MUI_PAGE_HEADER_TEXT "$InstHeader"
!define MUI_PAGE_HEADER_SUBTEXT "$InstSubtext"
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TEXT "$FinishText"
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Start ${APPNAME} now"
!define MUI_FINISHPAGE_RUN_FUNCTION StartNow
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

; This installer is 32-bit, and Windows shows a 32-bit program SysWOW64 wherever it
; asks for System32, on whichever thread asks, so the 32-bit PowerShell would start.
; Sysnative is the way through to the real one.  Shortcuts are opened by Explorer,
; which is 64-bit and has no Sysnative, so they name System32.
Var PowerShell      ; for running, from here
Var PowerShellLink  ; for shortcuts

!macro FindPowerShell
  StrCpy $PowerShellLink "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
  ${If} ${RunningX64}
    StrCpy $PowerShell "$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
  ${Else}
    StrCpy $PowerShell $PowerShellLink
  ${EndIf}
!macroend

Function un.onInit
  !insertmacro FindPowerShell
FunctionEnd

; Yeufonic's launcher (Yeufonic.exe in the install folder) is running while the app, its engine
; and its window are.  Replacing files under it half-works, so the person is asked to close it
; and the installer waits.  Nothing is stopped for them: a render or a training run would be
; lost.  A silent install has nobody to ask, and stops it as the section below always did.
Function WaitForYeufonicClosed
  ${If} ${Silent}
    Return
  ${EndIf}
  ${If} $PowerShell == ""
    Return
  ${EndIf}
  ${Do}
    ; The answer is PowerShell's exit code, 10 plus the number running, because the text it
    ; prints does not come back through nsExec intact (a "0" arrived as a "?").  Any other code
    ; means it could not ask, and that does not hold the install hostage.
    nsExec::Exec '"$PowerShell" -NoProfile -Command "exit (10 + @(Get-CimInstance Win32_Process | Where-Object { $$_.ExecutablePath -like $\'$INSTDIR\Yeufonic.exe$\' }).Count)"'
    Pop $0
    ${If} $0 <= 10
      ${Break}
    ${EndIf}
    MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "${APPNAME} is running.$\r$\n$\r$\nQuit it from its icon by the clock (right-click, then Quit) and give it a few seconds to finish, then choose Retry. Closing its window leaves it running. Anything it is working on, a render or a training run, stops when it quits.$\r$\n$\r$\nCancel leaves ${APPNAME} as it is." IDRETRY +2
    Abort
  ${Loop}
FunctionEnd

Function StartNow
  ExecShell "" "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
FunctionEnd

;  A control's place on its page, in the page's own coordinates: x, y, width and height.
!macro ControlRect PAGE CONTROL
  System::Call "*(i,i,i,i)p.R0"
  System::Call "user32::GetWindowRect(p${CONTROL},pR0)"
  System::Call "user32::MapWindowPoints(p0,p${PAGE},pR0,i2)"
  System::Call "*$R0(i.R1,i.R2,i.R3,i.R4)"
  System::Free $R0
  IntOp $R3 $R3 - $R1
  IntOp $R4 $R4 - $R2
!macroend
!define SWP_KEEP 0x14   ; SWP_NOZORDER | SWP_NOACTIVATE
!define TVM_GETNEXTITEM 0x110A
!define TVGN_CARET 0x9
!define TVM_GETITEM 0x113E  ; TVM_GETITEMW

; The components page leaves a third of its width to the words "Select components to install:", and its
; description box is too narrow for the longer descriptions, which then need scrolling (and the box empties
; as soon as the mouse leaves the component).  The label goes; the list and the description share its width,
; and the space needed sits under the list.
Function WiderComponents
  Push $9
  Push $R0
  Push $R1
  Push $R2
  Push $R3
  Push $R4
  Push $R5
  Push $R6
  Push $R7
  Push $R8
  Push $R9
  FindWindow $R9 "#32770" "" $HWNDPARENT
  GetDlgItem $R8 $R9 1022                      ; "Select components to install:"
  !insertmacro ControlRect $R9 $R8
  StrCpy $R5 $R1                               ; the left edge
  ShowWindow $R8 ${SW_HIDE}
  GetDlgItem $R8 $R9 1023                      ; "Space required"
  !insertmacro ControlRect $R9 $R8
  StrCpy $R6 $R4                               ; its height
  GetDlgItem $R8 $R9 1032                      ; the list
  !insertmacro ControlRect $R9 $R8
  IntOp $9 $R1 - $R5                           ; the width set free
  IntOp $R7 $9 * 2
  IntOp $R7 $R7 / 5                            ; two fifths of it to the list
  IntOp $9 $9 - $R7                            ; and the rest to the description
  IntOp $R3 $R3 + $R7
  IntOp $R4 $R4 - $R6
  IntOp $R4 $R4 - 6
  System::Call "user32::SetWindowPos(p$R8,p0,i$R5,i$R2,i$R3,i$R4,i${SWP_KEEP})"
  IntOp $R2 $R2 + $R4
  IntOp $R2 $R2 + 6
  GetDlgItem $R8 $R9 1023
  System::Call "user32::SetWindowPos(p$R8,p0,i$R5,i$R2,i$R3,i$R6,i${SWP_KEEP})"
  GetDlgItem $R8 $R9 1042                      ; the description's frame
  !insertmacro ControlRect $R9 $R8
  IntOp $R1 $R1 - $9
  IntOp $R3 $R3 + $9
  System::Call "user32::SetWindowPos(p$R8,p0,i$R1,i$R2,i$R3,i$R4,i${SWP_KEEP})"
  GetDlgItem $R8 $R9 1043                      ; and its text
  !insertmacro ControlRect $R9 $R8
  IntOp $R1 $R1 - $9
  IntOp $R3 $R3 + $9
  System::Call "user32::SetWindowPos(p$R8,p0,i$R1,i$R2,i$R3,i$R4,i${SWP_KEEP})"
  Pop $R9
  Pop $R8
  Pop $R7
  Pop $R6
  Pop $R5
  Pop $R4
  Pop $R3
  Pop $R2
  Pop $R1
  Pop $R0
  Pop $9
FunctionEnd

; An update goes where the app already is: a new folder would be a second install.
Function SkipWhenUpdating
  ${If} $Updating == 1
    Abort
  ${EndIf}
FunctionEnd

Section "${APPNAME}" SecCore
  SectionIn RO
  ; What setup.ps1 will put on disk for the app and its tools, so the page shows the real figure; the
  ; engine chosen below adds its own.
  AddSize 2700000
  SetOutPath "$INSTDIR"
  ; A running copy holds its files open.  Only its own programs are stopped, never
  ; this installer, which may be running from the same folder.
  Call WaitForYeufonicClosed
  nsExec::Exec '"$PowerShell" -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $$_.ExecutablePath -like $\'$INSTDIR\*$\' -and $$_.Name -in $\'Yeufonic.exe$\',$\'python.exe$\',$\'pythonw.exe$\',$\'ffmpeg.exe$\',$\'ffprobe.exe$\',$\'fluidsynth.exe$\',$\'yue-server.exe$\',$\'ollama.exe$\',$\'sd-server.exe$\' } | ForEach-Object { Stop-Process -Id $$_.ProcessId -Force }"'
  Pop $0
  RMDir /r "$INSTDIR\studio"
  File /r "${STAGE}\studio"
  File "${STAGE}\setup.ps1"
  File "${STAGE}\launcher.py"
  File "${STAGE}\Yeufonic.exe"
  File "${STAGE}\yeufonic.ico"
  File "${STAGE}\LICENSE.md"
  File "${STAGE}\THIRD_PARTY_NOTICES.md"
  File "${STAGE}\terms.txt"
  WriteRegStr HKCU "Software\${REGNAME}" "InstallDir" "$INSTDIR"
!ifdef TEST_MANIFEST
  ; A test build looks for updates at an address only the tester knows (see windows/build.sh).
  WriteINIStr "$INSTDIR\settings.ini" "yue2" "update_manifest" "${TEST_MANIFEST}"
!endif
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${REGKEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKCU "${REGKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${REGKEY}" "Publisher" "Yeufonic"
  WriteRegStr HKCU "${REGKEY}" "DisplayIcon" "$INSTDIR\yeufonic.ico"
  WriteRegStr HKCU "${REGKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${REGKEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "${REGKEY}" "URLInfoAbout" "https://yeufonic.com"
  WriteRegDWORD HKCU "${REGKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${REGKEY}" "NoRepair" 1
  WriteRegDWORD HKCU "${REGKEY}" "EstimatedSize" 36000000
  ${If} $Legacy == 1
    ; YuE2 Studio's own entries go: this install is Yeufonic's now, in the same folder.
    ; Its shortcuts and Start menu folder are replaced at the end, once setup is done.
    DeleteRegKey HKCU "${LEGACY_REGKEY}"
    DeleteRegKey HKCU "Software\${LEGACY_REGNAME}"
    Delete "$INSTDIR\yue2studio.ico"
  ${EndIf}
SectionEnd

; The engine: ComfyUI (everything) or yue2.cpp (less video memory, no training).  Radio buttons, handled in
; .onSelChange as the model sizes are.  No files here: setup.ps1 is told which, and settings.ini remembers it.
SectionGroup /e "Engine" SecEngineGroup
  Section "ComfyUI" SecComfy
    AddSize 4500000
  SectionEnd
  Section /o "yue2.cpp" SecCpp
    AddSize 6000000
  SectionEnd
SectionGroupEnd

; The YuE2 model comes in two sizes and an install has one of them (radio buttons, below).  No
; files here: setup.ps1 is told which to fetch, and takes the other away if it is there.
SectionGroup /e "YuE2 model size (ComfyUI)" SecModelGroup
  Section "Full quality" SecFull
    AddSize 7800000
  SectionEnd
  Section /o "Low memory" SecSmall
    AddSize 3960000
  SectionEnd
SectionGroupEnd

Section "Lyric drafts (Gemma 4)" SecLyrics
  AddSize 7900000
  ; No files: setup.ps1 is told whether to fetch Gemma.  Without it, lyric drafts and
  ; song analysis need an external LLM, set in Settings.
SectionEnd

Section /o "FLUX.2 [klein]" SecPictures
  AddSize 8060000
  ; No files: setup.ps1 is told whether to fetch FLUX.2 klein.  Without it, a take's picture is drawn
  ; by the external LLM's image model, if one is set up, or not at all.
SectionEnd

Section /o "Style LoRAs" SecLoras
  AddSize 3716400
  ; No files: setup.ps1 is told whether to fetch the style LoRAs gathered on Hugging Face.  Without them the
  ; picker holds the user's own and any they import.
SectionEnd

Section /o "Recorded voices" SecVoices
  AddSize 7000000
  ; No files: setup.ps1 is told whether to set up the voice service (RVC and its separator, in a Python of their
  ; own) and fetch its models.  Without it the editor has no Recorded voice field.
SectionEnd

Section "-Setup"
  ${If} ${SectionIsSelected} ${SecLyrics}
    StrCpy $1 ""
  ${Else}
    StrCpy $1 "-NoLyrics"
  ${EndIf}
  ${If} ${SectionIsSelected} ${SecCpp}
    StrCpy $1 "$1 -Engine yue2cpp"
    WriteRegStr HKCU "Software\${REGNAME}" "Engine" "yue2cpp"
  ${Else}
    StrCpy $1 "$1 -Engine comfyui"
    WriteRegStr HKCU "Software\${REGNAME}" "Engine" "comfyui"
  ${EndIf}
  ${If} ${SectionIsSelected} ${SecSmall}
    StrCpy $1 "$1 -Int8"
    WriteRegDWORD HKCU "Software\${REGNAME}" "SmallModel" 1
  ${Else}
    WriteRegDWORD HKCU "Software\${REGNAME}" "SmallModel" 0
  ${EndIf}
  ${If} ${SectionIsSelected} ${SecPictures}
    StrCpy $1 "$1 -Pictures"
    WriteRegDWORD HKCU "Software\${REGNAME}" "Pictures" 1
  ${Else}
    WriteRegDWORD HKCU "Software\${REGNAME}" "Pictures" 0
  ${EndIf}
  ${If} ${SectionIsSelected} ${SecVoices}
    StrCpy $1 "$1 -Voices"
    WriteRegDWORD HKCU "Software\${REGNAME}" "Voices" 1
  ${Else}
    WriteRegDWORD HKCU "Software\${REGNAME}" "Voices" 0
  ${EndIf}
  ${If} ${SectionIsSelected} ${SecLoras}
    StrCpy $1 "$1 -Loras"
    WriteRegDWORD HKCU "Software\${REGNAME}" "Loras" 1
  ${Else}
    WriteRegDWORD HKCU "Software\${REGNAME}" "Loras" 0
  ${EndIf}
  ; Remembered, so an update offers the same choice again.
  ${If} ${SectionIsSelected} ${SecLyrics}
    WriteRegDWORD HKCU "Software\${REGNAME}" "Lyrics" 1
  ${Else}
    WriteRegDWORD HKCU "Software\${REGNAME}" "Lyrics" 0
  ${EndIf}
  DetailPrint "Setting up. Its progress is in a separate window, which may be behind this one."
  ${If} $Updating == 1
    DetailPrint "Updating from $OldVersion to ${VERSION}: only what has changed is downloaded."
    ${If} ${SectionIsSelected} ${SecLyrics}
    ${AndIf} ${FileExists} "$INSTDIR\engine\ComfyUI\models\text_encoders\gemma4_e4b_it_int8_convrot.safetensors"
      DetailPrint "Gemma 4 is already here, so it is not downloaded again."
    ${EndIf}
    ${If} ${SectionIsSelected} ${SecPictures}
    ${AndIf} ${FileExists} "$INSTDIR\engine\ComfyUI\models\diffusion_models\flux-2-klein-4b-fp8.safetensors"
      DetailPrint "FLUX.2 klein is already here, so it is not downloaded again."
    ${EndIf}
  ${ElseIf} ${SectionIsSelected} ${SecCpp}
    DetailPrint "This takes a while: about 6 GB to download, more with lyric drafts or take pictures."
  ${Else}
    DetailPrint "This takes a while: about 24 GB to download."
  ${EndIf}
  ExecWait '"$PowerShell" -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\setup.ps1" -InstallDir "$INSTDIR" $1 ${SETUP_ARGS}' $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "Setup did not finish.$\r$\n$\r$\nThe details are in $INSTDIR\logs\install.log. Run this installer again to carry on from where it stopped." /SD IDOK
    Abort
  ${EndIf}
  SetOutPath "$INSTDIR"
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  ${If} $Legacy == 1
    Delete "$DESKTOP\${LEGACY_APPNAME}.lnk"
    RMDir /r "$SMPROGRAMS\${LEGACY_APPNAME}"
  ${EndIf}
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\Yeufonic.exe"
  ; The same with a console window that reports as it goes, for diagnosing.
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME} (with console).lnk" "$INSTDIR\venv\Scripts\python.exe" '"$INSTDIR\launcher.py" --console' "$INSTDIR\yeufonic.ico"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Repair ${APPNAME}.lnk" "$PowerShellLink" '-NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\setup.ps1" -InstallDir "$INSTDIR"' "$INSTDIR\yeufonic.ico"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall ${APPNAME}.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\Yeufonic.exe"
SectionEnd

LangString DESC_Core ${LANG_ENGLISH} "The app, the engine chosen below, and the YuE2 models."
LangString DESC_Engine ${LANG_ENGLISH} "Which engine runs YuE2. ComfyUI does everything, LoRA training included, best with 12 GB of video memory or more. yue2.cpp is smaller, for cards with less memory, and does not train LoRAs. Run this installer again to switch: your library, settings and LoRAs are kept."
LangString DESC_Comfy ${LANG_ENGLISH} "ComfyUI: everything Yeufonic does, LoRA training included. Works best with 12 GB of video memory or more."
LangString DESC_Cpp ${LANG_ENGLISH} "yue2.cpp: a smaller native engine for graphics cards with less memory. Songs, covers, instrumentals, Harmony and transcription, with your style LoRAs; no LoRA training. Lyric drafts and pictures below run beside it. Download size: about 6 GB."
LangString DESC_Full ${LANG_ENGLISH} "The full-quality YuE2 model (BF16), 7.8 GB. Recommended. It needs a graphics card with plenty of memory to run at full speed, and it is the one that LoRA training uses."
LangString DESC_Small ${LANG_ENGLISH} "A smaller YuE2 model (INT8), 4.0 GB, for graphics cards with 6 GB of memory or less, or if the full one is too slow on this PC. LoRA training works on both sizes. A size already downloaded is kept, so changing back costs nothing."
LangString DESC_Pictures ${LANG_ENGLISH} "FLUX.2 klein, which draws a picture of each take on this PC, shown behind its card. Leave it out if your external LLM can draw them, or if you do not want pictures. Download size: 8.2 GB."
LangString DESC_Loras ${LANG_ENGLISH} "39 style LoRAs by their authors: chanson, canzone, Bulgarian voices, qawwali, militant reggae, J-pop, dream pop, old school hip-hop and 16 concept sliders, each with its trigger word and suggested strengths. CC BY-NC 4.0, credited in the guide. Download size: 3.8 GB."
LangString DESC_Voices ${LANG_ENGLISH} "Recorded voices: train a singer's voice from recordings, your own sung into the built-in recorder or a corpus's songs, and have a take sung in it. Runs beside the engine, on the graphics card. Download size: about 4 GB."
LangString DESC_Lyrics ${LANG_ENGLISH} "Gemma 4, for lyric drafts and song analysis on this PC. Leave it out if you intend to configure an external LLM. This will save an 8 GB download."
; The section of the item highlighted in the list (the one last clicked, or moved to with the keys), or -1.
; The installer keeps each item's section in its lParam.
Function HighlightedSection
  Push $1
  Push $2
  Push $3
  StrCpy $0 -1
  FindWindow $1 "#32770" "" $HWNDPARENT
  GetDlgItem $1 $1 1032
  SendMessage $1 ${TVM_GETNEXTITEM} ${TVGN_CARET} 0 $2
  ${If} $2 != 0
    System::Call "*(i 4, p r2, i, i, p, i, i, i, i, p)p.r3"     ; TVITEM asking for lParam (TVIF_PARAM)
    SendMessage $1 ${TVM_GETITEM} 0 $3
    System::Call "*$3(i, p, i, i, p, i, i, i, i, p.r0)"
    System::Free $3
  ${EndIf}
  Pop $3
  Pop $2
  Pop $1
FunctionEnd

; Modern UI's own description function, except that moving off the list does not empty the box: it describes
; the highlighted item instead, so a long description can be read and scrolled, and what it says matches what
; is highlighted.
Function .onMouseOverSection
  ${If} $0 == -1
    Call HighlightedSection
  ${EndIf}
  ${If} $0 == -1
    ; nothing highlighted yet: the box keeps what it says
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} $(DESC_Core)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecEngineGroup} $(DESC_Engine)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecComfy} $(DESC_Comfy)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCpp} $(DESC_Cpp)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecModelGroup} $(DESC_Full)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecFull} $(DESC_Full)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecSmall} $(DESC_Small)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecLyrics} $LyricsText
  !insertmacro MUI_DESCRIPTION_TEXT ${SecPictures} $PicturesText
  !insertmacro MUI_DESCRIPTION_TEXT ${SecLoras} $LorasText
  !insertmacro MUI_DESCRIPTION_TEXT ${SecVoices} $VoicesText
  ${EndIf}
FunctionEnd

; The two sizes of the model are radio buttons: ticking one unticks the other, and one is always ticked.
; Written out here rather than with the radio-button macros, which take a variable holding the previous
; choice and untick *that section first*: with it unset they unticked the core section, and nothing installed.
; This touches the two model sections only. $ModelRadio is the one that was ticked before the click.
; The model size is ComfyUI's.  With yue2.cpp it is greyed out, kept as it was (so going back to ComfyUI finds it
; unchanged), and downloads nothing.
Function ModelSizeForEngine
  ${If} $EngineRadio == ${SecCpp}
    SectionSetSize ${SecFull} 0
    SectionSetSize ${SecSmall} 0
    !insertmacro SetSectionFlag ${SecFull} ${SF_RO}
    !insertmacro SetSectionFlag ${SecSmall} ${SF_RO}
  ${Else}
    SectionSetSize ${SecFull} $FullSize
    SectionSetSize ${SecSmall} $SmallSize
    !insertmacro ClearSectionFlag ${SecFull} ${SF_RO}
    !insertmacro ClearSectionFlag ${SecSmall} ${SF_RO}
  ${EndIf}
FunctionEnd

Function .onSelChange
  ; The engine first, as the model size below: one of the two always ticked.
  SectionGetFlags ${SecComfy} $0
  SectionGetFlags ${SecCpp} $1
  IntOp $0 $0 & ${SF_SELECTED}
  IntOp $1 $1 & ${SF_SELECTED}
  ${If} $0 != 0
  ${AndIf} $1 != 0
    ${If} $EngineRadio == ${SecComfy}
      !insertmacro UnselectSection ${SecComfy}
      StrCpy $EngineRadio ${SecCpp}
    ${Else}
      !insertmacro UnselectSection ${SecCpp}
      StrCpy $EngineRadio ${SecComfy}
    ${EndIf}
  ${ElseIf} $0 != 0
    StrCpy $EngineRadio ${SecComfy}
  ${ElseIf} $1 != 0
    StrCpy $EngineRadio ${SecCpp}
  ${Else}
    !insertmacro SelectSection $EngineRadio
  ${EndIf}
  Call ModelSizeForEngine
  SectionGetFlags ${SecFull} $0
  SectionGetFlags ${SecSmall} $1
  IntOp $0 $0 & ${SF_SELECTED}
  IntOp $1 $1 & ${SF_SELECTED}
  ${If} $0 != 0
  ${AndIf} $1 != 0
    ; Both are ticked: the one that was not the choice before is the new choice.
    ${If} $ModelRadio == ${SecFull}
      !insertmacro UnselectSection ${SecFull}
      StrCpy $ModelRadio ${SecSmall}
    ${Else}
      !insertmacro UnselectSection ${SecSmall}
      StrCpy $ModelRadio ${SecFull}
    ${EndIf}
  ${ElseIf} $0 != 0
    StrCpy $ModelRadio ${SecFull}
  ${ElseIf} $1 != 0
    StrCpy $ModelRadio ${SecSmall}
  ${Else}
    ; Neither: unticking the one that was ticked, or the group's own box. A size is always chosen.
    !insertmacro SelectSection $ModelRadio
  ${EndIf}
FunctionEnd

; After the sections, so their names can be used here.
Function .onInit
  !insertmacro FindPowerShell
  Call WaitForYeufonicClosed
!ifdef TEST_SMALL
  ; A test build that starts with the low-memory model chosen (the choice can still be changed).
  !insertmacro UnselectSection ${SecFull}
  !insertmacro SelectSection ${SecSmall}
!endif
  StrCpy $Updating 0
  StrCpy $Legacy 0
  StrCpy $R9 "${REGNAME}"     ; where the Gemma choice was remembered
  ReadRegStr $OldVersion HKCU "${REGKEY}" "DisplayVersion"
  ReadRegStr $0 HKCU "Software\${REGNAME}" "InstallDir"
  ; No Yeufonic here yet, but YuE2 Studio may be: then that install is taken over where
  ; it stands.  Its library records every file by its full path, so the folder is not
  ; moved, only renamed in the Apps list, the Start menu and the shortcuts.
  ${If} $0 == ""
    ReadRegStr $1 HKCU "Software\${LEGACY_REGNAME}" "InstallDir"
    ${If} $1 != ""
    ${AndIf} ${FileExists} "$1\launcher.py"
      StrCpy $Legacy 1
      StrCpy $0 $1
      StrCpy $R9 "${LEGACY_REGNAME}"
      ReadRegStr $OldVersion HKCU "${LEGACY_REGKEY}" "DisplayVersion"
      ${If} $OldVersion == ""
        StrCpy $OldVersion "?"
      ${EndIf}
    ${EndIf}
  ${EndIf}
  ${If} $OldVersion != ""
  ${AndIf} $0 != ""
  ${AndIf} ${FileExists} "$0\launcher.py"
    StrCpy $Updating 1
    StrCpy $INSTDIR $0
    ; The version the app's own files carry is the truth; the Apps list entry is
    ; only what the last installer managed to write there.
    ClearErrors
    FileOpen $2 "$INSTDIR\studio\VERSION" r
    ${IfNot} ${Errors}
      FileRead $2 $3
      FileClose $2
      ${TrimNewLines} "$3" $3
      ${If} $3 != ""
        StrCpy $OldVersion $3
      ${EndIf}
    ${EndIf}
  ${EndIf}

  ${If} $Updating == 1
    ${If} $Legacy == 1
      StrCpy $WelcomeTitle "${LEGACY_APPNAME} is now ${APPNAME}"
      StrCpy $WelcomeText "${LEGACY_APPNAME} $OldVersion is installed on this PC. It has been renamed ${APPNAME}, and this updates it to ${APPNAME} ${VERSION} where it is, in $INSTDIR.$\r$\n$\r$\nYour library, settings, LoRAs and models are kept, and only what has changed is downloaded. The ${LEGACY_APPNAME} shortcuts and Apps list entry are replaced by ${APPNAME} ones.$\r$\n$\r$\nIf ${LEGACY_APPNAME} is running, you are asked to quit it first."
      StrCpy $InstHeader "Updating ${LEGACY_APPNAME} to ${APPNAME}"
      StrCpy $FinishText "${LEGACY_APPNAME} $OldVersion is now ${APPNAME} ${VERSION}.$\r$\n$\r$\nYour library and settings are as you left them. Start it from the ${APPNAME} shortcut on the desktop or in the Start menu."
    ${ElseIf} $OldVersion == "${VERSION}"
      StrCpy $WelcomeTitle "Reinstall ${APPNAME} ${VERSION}"
      StrCpy $WelcomeText "${APPNAME} ${VERSION} is already installed on this PC. This installs it again over itself, which can repair a copy that has stopped working.$\r$\n$\r$\nYour library, settings, LoRAs and models are kept, and anything already in place is not downloaded again.$\r$\n$\r$\nIf ${APPNAME} is running, you are asked to quit it first."
      StrCpy $InstHeader "Reinstalling ${APPNAME}"
      StrCpy $FinishText "${APPNAME} ${VERSION} has been installed again.$\r$\n$\r$\nYour library and settings are as you left them."
    ${Else}
      StrCpy $WelcomeTitle "Update ${APPNAME}"
      StrCpy $WelcomeText "${APPNAME} $OldVersion is installed on this PC. This updates it to ${VERSION}.$\r$\n$\r$\nYour library, settings, LoRAs and models are kept, and only what has changed is downloaded, so it takes minutes rather than hours.$\r$\n$\r$\nIf ${APPNAME} is running, you are asked to quit it first."
      StrCpy $InstHeader "Updating ${APPNAME}"
      StrCpy $FinishText "${APPNAME} has been updated from $OldVersion to ${VERSION}.$\r$\n$\r$\nYour library and settings are as you left them."
    ${EndIf}
    StrCpy $InstSubtext "Only what has changed is downloaded. The setup window may be behind this one."
    StrCpy $LyricsText "$(DESC_Lyrics)"
    StrCpy $PicturesText "$(DESC_Pictures)"
    StrCpy $LorasText "$(DESC_Loras)"
    StrCpy $VoicesText "$(DESC_Voices)"
    ; Recorded voices as chosen last time: kept, and brought up to date, if they are here.
    ReadRegDWORD $2 HKCU "Software\$R9" "Voices"
    ${If} ${FileExists} "$INSTDIR\voice\venv\Scripts\python.exe"
      !insertmacro SelectSection ${SecVoices}
      SectionSetSize ${SecVoices} 0
      SectionSetText ${SecVoices} "Recorded voices (installed)"
      StrCpy $VoicesText "Recorded voices are already on this PC: only what has changed is downloaded. Leave it ticked to keep them up to date. Unticking it does not remove them."
    ${ElseIf} $2 == 1
      !insertmacro SelectSection ${SecVoices}
    ${EndIf}
    ; The style LoRAs as chosen last time: ticked again if they were chosen, and nothing downloaded for those here.
    ReadRegDWORD $2 HKCU "Software\$R9" "Loras"
    ${If} $2 == 1
      !insertmacro SelectSection ${SecLoras}
      ${If} ${FileExists} "$INSTDIR\engine\ComfyUI\models\loras\chnsn_cabaret.safetensors"
        SectionSetSize ${SecLoras} 0
        SectionSetText ${SecLoras} "Style LoRAs (installed)"
        StrCpy $LorasText "The style LoRAs are already on this PC: only any that are missing are downloaded. Unticking them does not remove them."
      ${EndIf}
    ${EndIf}
    ; FLUX.2 klein as chosen last time: kept if it is here, ticked again if it was chosen.
    ReadRegDWORD $2 HKCU "Software\$R9" "Pictures"
    ${If} ${FileExists} "$INSTDIR\engine\ComfyUI\models\diffusion_models\flux-2-klein-4b-fp8.safetensors"
      !insertmacro SelectSection ${SecPictures}
      SectionSetSize ${SecPictures} 0
      SectionSetText ${SecPictures} "FLUX.2 [klein] (installed)"
      StrCpy $PicturesText "FLUX.2 klein is already on this PC, so nothing is downloaded for it. Leave it ticked to keep drawing take pictures here. Unticking it does not remove it."
    ${ElseIf} $2 == 1
      !insertmacro SelectSection ${SecPictures}
    ${EndIf}
    ; Only the app itself is new: the engine and the models are already here.
    SectionSetSize ${SecCore} 100000
    ; The model sizes on disk: each one here downloads nothing, and both are kept.  The one in use stays chosen:
    ; the one chosen last time, or the low-memory one when it is the only one here.
    ${If} ${FileExists} "$INSTDIR\engine\ComfyUI\models\checkpoints\yue2_3b_bf16.safetensors"
      SectionSetSize ${SecFull} 0
      SectionSetText ${SecFull} "Full quality (installed)"
    ${EndIf}
    ${If} ${FileExists} "$INSTDIR\engine\ComfyUI\models\checkpoints\yue2_3b_int8_convrot.safetensors"
      SectionSetSize ${SecSmall} 0
      SectionSetText ${SecSmall} "Low memory (installed)"
    ${EndIf}
    ReadRegDWORD $1 HKCU "Software\$R9" "SmallModel"
    ${If} $1 == 1
    ${OrIfNot} ${FileExists} "$INSTDIR\engine\ComfyUI\models\checkpoints\yue2_3b_bf16.safetensors"
      ${If} ${FileExists} "$INSTDIR\engine\ComfyUI\models\checkpoints\yue2_3b_int8_convrot.safetensors"
        !insertmacro UnselectSection ${SecFull}
        !insertmacro SelectSection ${SecSmall}
      ${EndIf}
    ${EndIf}
    ; Gemma as chosen last time: kept if it is here, left out if it was left out.
    ReadRegDWORD $1 HKCU "Software\$R9" "Lyrics"
    ${If} ${FileExists} "$INSTDIR\engine\ComfyUI\models\text_encoders\gemma4_e4b_it_int8_convrot.safetensors"
      ; Already downloaded: said plainly, so nobody fears another 8 GB.
      SectionSetSize ${SecLyrics} 0
      SectionSetText ${SecLyrics} "Gemma 4 (installed)"
      StrCpy $LyricsText "Gemma 4 is already on this PC, so nothing is downloaded for it. Leave it ticked to keep using it for lyric drafts and song analysis. Unticking it does not remove it."
    ${ElseIf} ${FileExists} "$INSTDIR\engine\ComfyUI\models\ollama\manifests\*.*"
      ; Gemma for yue2.cpp, in Ollama's folder.
      SectionSetSize ${SecLyrics} 0
      SectionSetText ${SecLyrics} "Gemma 4 (installed)"
    ${ElseIf} $1 != 1
      ; Left out when installing, most likely for an external LLM: it stays out
      ; unless ticked now, and the page says why it is not ticked.
      !insertmacro UnselectSection ${SecLyrics}
      StrCpy $LyricsText "Gemma 4 was left out when ${APPNAME} was installed, so lyric drafts and song analysis use the external LLM set in Settings. It stays out unless you tick it; ticking it downloads about 8 GB."
    ${EndIf}
  ${Else}
    StrCpy $WelcomeTitle "Install ${APPNAME}"
    StrCpy $LyricsText "$(DESC_Lyrics)"
    StrCpy $PicturesText "$(DESC_Pictures)"
    StrCpy $LorasText "$(DESC_Loras)"
    StrCpy $VoicesText "$(DESC_Voices)"
    ${If} ${FileExists} "$INSTDIR\models-kept\*.*"
    ${OrIf} ${FileExists} "$INSTDIR\data\*.*"
      StrCpy $WelcomeText "${APPNAME} writes and covers songs with the YuE2 music model, on this PC.$\r$\n$\r$\nWhat you kept when ${APPNAME} was uninstalled is in $INSTDIR, and this install picks it up: your library, and any models you kept are not downloaded again.$\r$\n$\r$\nIt checks that this PC can run YuE2, then downloads the rest from each part's publisher. A separate window shows the setup's progress; it may open behind this one."
    ${Else}
      StrCpy $WelcomeText "${APPNAME} writes and covers songs with the YuE2 music model, on this PC.$\r$\n$\r$\nThis installer is small. It checks that this PC can run YuE2 (an NVIDIA RTX 30-series card or newer), then downloads the rest from each part's publisher: about 24 GB with the ComfyUI engine (less with yue2.cpp), most of it the models. A download that breaks off carries on where it stopped when you run the installer again.$\r$\n$\r$\nA separate window shows the setup's progress; it may open behind this one.$\r$\n$\r$\nYou need about 40 GB of free space with ComfyUI, less with yue2.cpp."
    ${EndIf}
    StrCpy $InstHeader "Installing ${APPNAME}"
    StrCpy $InstSubtext "The setup window shows its progress, and may be behind this one."
    StrCpy $FinishText "${APPNAME} has been installed on this PC."
  ${EndIf}
  ; The engine as chosen last time, and which one is ticked to begin with, for .onSelChange.
  ReadRegStr $2 HKCU "Software\$R9" "Engine"
  ${If} $2 == "yue2cpp"
    !insertmacro UnselectSection ${SecComfy}
    !insertmacro SelectSection ${SecCpp}
  ${EndIf}
!ifdef TEST_CPP
  !insertmacro UnselectSection ${SecComfy}
  !insertmacro SelectSection ${SecCpp}
!endif
  SectionGetFlags ${SecCpp} $0
  IntOp $0 $0 & ${SF_SELECTED}
  ${If} $0 != 0
    StrCpy $EngineRadio ${SecCpp}
  ${Else}
    StrCpy $EngineRadio ${SecComfy}
  ${EndIf}
  SectionGetSize ${SecFull} $FullSize
  SectionGetSize ${SecSmall} $SmallSize
  Call ModelSizeForEngine
  ; Which model size is ticked to begin with, for .onSelChange.
  SectionGetFlags ${SecSmall} $0
  IntOp $0 $0 & ${SF_SELECTED}
  ${If} $0 != 0
    StrCpy $ModelRadio ${SecSmall}
  ${Else}
    StrCpy $ModelRadio ${SecFull}
  ${EndIf}
FunctionEnd

Var KeepLibrary
Var KeepModels

Section "Uninstall"
  nsExec::Exec '"$PowerShell" -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $$_.ExecutablePath -like $\'$INSTDIR\*$\' -and $$_.Name -in $\'Yeufonic.exe$\',$\'python.exe$\',$\'pythonw.exe$\',$\'ffmpeg.exe$\',$\'ffprobe.exe$\',$\'yue-server.exe$\',$\'ollama.exe$\',$\'sd-server.exe$\' } | ForEach-Object { Stop-Process -Id $$_.ProcessId -Force }"'
  Pop $0
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APPNAME}"
  DeleteRegKey HKCU "${REGKEY}"

  ; Two questions, because they are not alike: the library is the user's own work and
  ; small, so it is kept unless they say otherwise; the models are many GB that can be
  ; downloaded again, so they go unless they say otherwise.  Nothing is left behind
  ; by pressing Enter through this.
  StrCpy $KeepLibrary 0
  StrCpy $KeepModels 0
  MessageBox MB_YESNO|MB_ICONQUESTION "Keep your library?$\r$\n$\r$\nYour songs, takes, spaces and corpora, and the LoRAs you trained or installed. Kept, they stay in $INSTDIR, and installing ${APPNAME} again picks them up." /SD IDYES IDNO +2
    StrCpy $KeepLibrary 1
  ${GetSize} "$INSTDIR\engine\ComfyUI\models" "/S=0M" $0 $1 $2
  IntOp $0 $0 / 1000
  ${If} $0 > 0
    MessageBox MB_YESNO|MB_ICONQUESTION|MB_DEFBUTTON2 "Also keep the downloaded models, about $0 GB?$\r$\n$\r$\nKept, installing ${APPNAME} again does not download them. Not kept, the space is freed now." /SD IDNO IDNO +2
      StrCpy $KeepModels 1
  ${EndIf}

  ${If} $KeepLibrary == 0
  ${AndIf} $KeepModels == 0
    RMDir /r "$INSTDIR"
    DeleteRegKey HKCU "Software\${REGNAME}"
  ${Else}
    ; What is kept goes where setup.ps1 looks for it on a reinstall.
    ${If} $KeepModels == 1
      Rename "$INSTDIR\engine\ComfyUI\models" "$INSTDIR\models-kept"
    ${Else}
      CreateDirectory "$INSTDIR\models-kept"
      Rename "$INSTDIR\engine\ComfyUI\models\loras" "$INSTDIR\models-kept\loras"
    ${EndIf}
    ${If} $KeepLibrary == 0
      RMDir /r "$INSTDIR\data"
      RMDir /r "$INSTDIR\models-kept\loras"
      Delete "$INSTDIR\settings.ini"
    ${EndIf}
    RMDir /r "$INSTDIR\engine"
    RMDir /r "$INSTDIR\engine-cpp"
    RMDir /r "$INSTDIR\voice"
    RMDir /r "$INSTDIR\venv"
    RMDir /r "$INSTDIR\python"
    RMDir /r "$INSTDIR\tools"
    RMDir /r "$INSTDIR\downloads"
    RMDir /r "$INSTDIR\studio"
    RMDir /r "$INSTDIR\state"
    RMDir /r "$INSTDIR\logs"
    Delete "$INSTDIR\setup.ps1"
    Delete "$INSTDIR\launcher.py"
    Delete "$INSTDIR\Yeufonic.exe"
    ; The page's window's browser profiles: sizes and places, nothing of the user's.
    RMDir /r "$INSTDIR\browsers"
    RMDir /r "$INSTDIR\browser"
    Delete "$INSTDIR\terms.txt"
    Delete "$INSTDIR\LICENSE.md"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\THIRD_PARTY_NOTICES.md"
    Delete "$INSTDIR\yeufonic.ico"
    Delete "$INSTDIR\yue2studio.ico"
    Delete "$INSTDIR\Uninstall.exe"
    ; The folder stays remembered, so installing again goes back to it.
    ${GetSize} "$INSTDIR" "/S=0M" $0 $1 $2
    ${If} $0 >= 1000
      IntOp $0 $0 / 1000
      StrCpy $0 "about $0 GB"
    ${ElseIf} $0 < 1
      StrCpy $0 "under 1 MB"
    ${Else}
      StrCpy $0 "$0 MB"
    ${EndIf}
    MessageBox MB_OK|MB_ICONINFORMATION "What you kept is in $INSTDIR ($0).$\r$\n$\r$\nInstalling ${APPNAME} again picks it up. To remove it instead, delete that folder." /SD IDOK
  ${EndIf}
SectionEnd
