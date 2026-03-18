rem  Place this batch file and the accompanying self-extracting archives
rem  in the directory you want to install Trade Wars 2002 v2
rem  Run this batch file to setup a new game

echo off

if exist EXTERN.EXE goto upgrade

echo Now INSTALLING your Trade Wars 2002 v2
md ANSI
cd ANSI
..\twsupp 
cd ..
twpgm
erase twsupp.exe > nul
erase 2002V2b1.exe  > nul
erase twpgm.exe >nul
fixbb
bigbang 
extern 
 
goto end


:upgrade
echo Now UPGRADING your Trade Wars 2002 to version 2.xx
cd ANSI
..\twsupp -o
cd ..
twpgm -o
erase twsupp.exe
erase twpgm.exe

:end
cls
type install.dir
ECHO Cracked by ÄÍþCONTOURþÍÄ '94 Run TWCRACK.COM to complete the crackpatch!
