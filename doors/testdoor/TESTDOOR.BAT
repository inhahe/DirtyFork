@ECHO OFF
REM DirtyFork Test Door - runs under DOSBox, communicates via CTTY COM1
REM Usage: TESTDOOR.BAT [node] [args...]

REM Redirect all console I/O to the serial port
CTTY COM1

ECHO.
ECHO ============================================================
ECHO   DirtyFork Test Door v1.0 (DOS/DOSBox)
ECHO ============================================================
ECHO.
ECHO COMMAND LINE: %0 %1 %2 %3 %4 %5 %6 %7 %8 %9
ECHO.
ECHO DRIVES AVAILABLE:
IF EXIST C:\NUL ECHO   C:\ mounted (dropfile dir)
IF EXIST D:\NUL ECHO   D:\ mounted (door dir)
ECHO.
ECHO DROPFILES ON C:\
IF EXIST C:\DOOR.SYS ECHO   DOOR.SYS found
IF NOT EXIST C:\DOOR.SYS ECHO   DOOR.SYS NOT found
IF EXIST C:\DOOR32.SYS ECHO   DOOR32.SYS found
IF NOT EXIST C:\DOOR32.SYS ECHO   DOOR32.SYS NOT found
IF EXIST C:\CALLINFO.BBS ECHO   CALLINFO.BBS found
IF NOT EXIST C:\CALLINFO.BBS ECHO   CALLINFO.BBS NOT found
IF EXIST C:\DORINFO1.DEF ECHO   DORINFO1.DEF found
IF NOT EXIST C:\DORINFO1.DEF ECHO   DORINFO1.DEF NOT found
ECHO.
ECHO ============================================================
ECHO   DOOR.SYS CONTENTS:
ECHO ============================================================
IF EXIST C:\DOOR.SYS TYPE C:\DOOR.SYS
IF NOT EXIST C:\DOOR.SYS ECHO   (not found)
ECHO.
ECHO ============================================================
ECHO   DOOR32.SYS CONTENTS:
ECHO ============================================================
IF EXIST C:\DOOR32.SYS TYPE C:\DOOR32.SYS
IF NOT EXIST C:\DOOR32.SYS ECHO   (not found)
ECHO.
ECHO ============================================================
ECHO   FILES ON D:\ (door directory):
ECHO ============================================================
DIR D:\ /W
ECHO.
ECHO ============================================================
ECHO   Press any key to exit the test door...
ECHO ============================================================
PAUSE > NUL

REM Restore console to local
CTTY CON
