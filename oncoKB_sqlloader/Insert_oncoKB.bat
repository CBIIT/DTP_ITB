REM Emily: loop through each oncokb files in archive folder and upload the data to Oracle tables
@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
echo %DATE% %TIME%
set DATESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%
set TIMESTAMP=%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set UserName=
set Password=
set DBServer=DTPSTG.NCIFCRF.GOV
set FilePath="C:\Temp\test_sqlldr\sqlloader_files"
echo exit | sqlplus "%UserName%"/"%Password%"@"%DBServer%" @"%FilePath%"\sql\clean_oncoKB_table.sql 
echo %DATESTAMP%_%TIMESTAMP%
IF NOT EXIST "%FilePath%\archive%DATESTAMP%_%TIMESTAMP%" md "%FilePath%\archive%DATESTAMP%_%TIMESTAMP%"
IF NOT EXIST "%FilePath%\log%DATESTAMP%_%TIMESTAMP%" md "%FilePath%\log%DATESTAMP%_%TIMESTAMP%"
IF NOT EXIST "%FilePath%\archive" md "%FilePath%\archive"
IF NOT EXIST "%FilePath%\log" md "%FilePath%\log"
for /F "delims=" %%F in ('dir /b "%FilePath%\archive\*.oncoKB.txt"') do (
echo %%F
set "FileName=%%F"
echo file name is !FileName!
powershell -Command "(gc %FilePath%\oncoKB_org.ctl) -replace ':FILE', '!FileName!' | Out-File -encoding ASCII %FilePath%\oncoKB_org.ctl"
sqlldr "%UserName%"/"%Password%"@"%DBServer%" CONTROL='%FilePath%\oncoKB_org.ctl' LOG='%FilePath%\log\oncoKB_org_!FileName!.log' BAD='%FilePath%\log\oncoKB_org_!FileName!.bad' "DATA=%FilePath%\archive\%%F" DIRECT=true skip=1
move "%FilePath%\archive\%%F" "%FilePath%\archive%DATESTAMP%_%TIMESTAMP%"
powershell -Command "(gc %FilePath%\oncoKB_org.ctl) -replace  '!FileName!', ':FILE' | Out-File -encoding ASCII %FilePath%\oncoKB_org.ctl"
)
echo move "%FilePath%\log\.*" "%FilePath%\log%DATESTAMP%_%TIMESTAMP%"
move %FilePath%\log\ %FilePath%\log%DATESTAMP%_%TIMESTAMP%
echo exit |sqlplus "%UserName%"/"%Password%"@"%DBServer%" @"%FilePath%\sql\run_insert_oncoKB.sql" 
pause
echo %DATE% %TIME%
