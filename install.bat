@echo off
echo ========================================
echo BatchReelMaker V9 - Installation Script
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as administrator - proceeding with installation...
) else (
    echo WARNING: This script should be run as administrator for proper installation.
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo.
echo Installing BatchReelMaker V9...

REM Create program directory
if not exist "C:\Program Files\BatchReelMaker_V9" (
    echo Creating program directory...
    mkdir "C:\Program Files\BatchReelMaker_V9"
)

REM Check if executable exists
if not exist "BatchReelMaker_V9.exe" (
    echo ERROR: BatchReelMaker_V9.exe not found in current directory.
    echo Please run this script from the same directory as the executable.
    pause
    exit /b 1
)

REM Copy executable
echo Copying executable...
copy "BatchReelMaker_V9.exe" "C:\Program Files\BatchReelMaker_V9\" >nul
if %errorLevel% neq 0 (
    echo ERROR: Failed to copy executable.
    pause
    exit /b 1
)

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\BatchReelMaker V9.lnk'); $Shortcut.TargetPath = 'C:\Program Files\BatchReelMaker_V9\BatchReelMaker_V9.exe'; $Shortcut.WorkingDirectory = 'C:\Program Files\BatchReelMaker_V9\'; $Shortcut.Description = 'BatchReelMaker V9 - Video Reel Creator'; $Shortcut.Save()"

REM Create start menu shortcut
echo Creating start menu shortcut...
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\BatchReelMaker_V9" (
    mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\BatchReelMaker_V9"
)
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\BatchReelMaker_V9\BatchReelMaker V9.lnk'); $Shortcut.TargetPath = 'C:\Program Files\BatchReelMaker_V9\BatchReelMaker_V9.exe'; $Shortcut.WorkingDirectory = 'C:\Program Files\BatchReelMaker_V9\'; $Shortcut.Description = 'BatchReelMaker V9 - Video Reel Creator'; $Shortcut.Save()"

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo BatchReelMaker V9 has been installed to:
echo C:\Program Files\BatchReelMaker_V9\
echo.
echo Shortcuts created:
echo - Desktop: BatchReelMaker V9
echo - Start Menu: BatchReelMaker_V9\BatchReelMaker V9
echo.
echo You can now run BatchReelMaker V9 from the desktop shortcut
echo or search for it in the Start Menu.
echo.
pause
