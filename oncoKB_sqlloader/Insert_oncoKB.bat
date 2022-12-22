@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
REM Emily: loop through each oncokb files in archive folder and upload the data to Oracle tables
echo %DATE% %TIME%
set DATESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%
set TIMESTAMP=%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set UserName=
set Password=
set DBServer=DTPSTG.NCIFCRF.GOV
set FilePath="C:\Temp\test_sqlldr\sqlloader-files"
echo exit | sqlplus "%UserName%"/"%Password%"@"%DBServer%" @"%FilePath%"\sql\clean_oncoKB_table.sql 
echo %DATESTAMP%_%TIMESTAMP%
for /F "delims=" %%F in ('dir /b "%FilePath%\archive\*.oncoKB.txt"') do (
echo %%F
set "FileName=%%F"
echo file name is !FileName!
IF NOT EXIST "%FilePath%\archive%DATESTAMP%_%TIMESTAMP%" md "%FilePath%\archive%DATESTAMP%_%TIMESTAMP%"
powershell -Command "(gc %FilePath%\onko_org.ctl) -replace ':FILE', '!FileName!' | Out-File -encoding ASCII %FilePath%\onko_org.ctl"
sqlldr "%UserName%"/"%Password%"@"%DBServer%" CONTROL='%FilePath%\onko_org.ctl' LOG='%FilePath%\log\onko_org.log' BAD='%FilePath%\log\onko_org.bad' "DATA=%FilePath%\archive\%%F" DIRECT=true skip=1
move "%FilePath%\archive\%%F" "%FilePath%\archive%DATESTAMP%_%TIMESTAMP%"
powershell -Command "(gc %FilePath%\onko_org.ctl) -replace  '!FileName!', ':FILE' | Out-File -encoding ASCII %FilePath%\onko_org.ctl"
)
echo exit |sqlplus "%UserName%"/"%Password%"@"%DBServer%" @"%FilePath%\sql\run_insert_oncoKB.sql" 
pause
echo %DATE% %TIME%
