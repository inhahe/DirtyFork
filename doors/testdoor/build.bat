@echo off
REM Build testdoor.exe using Open Watcom v2 (16-bit DOS, small model)
set WATCOM_BIN=D:\visual studio projects\DirtyFork\tools\watcom\binnt64
set INCLUDE=D:\watcom_h

echo Compiling testdoor.c...
"%WATCOM_BIN%\wcc.exe" -ms -os -d0 -w4 -zq testdoor.c -fo=testdoor.obj
if errorlevel 1 goto fail

echo Linking...
"%WATCOM_BIN%\wlink.exe" @testdoor.lnk
if errorlevel 1 goto fail

echo Done: testdoor.exe
goto end

:fail
echo BUILD FAILED
exit /b 1

:end
