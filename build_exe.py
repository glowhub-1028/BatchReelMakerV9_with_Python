#!/usr/bin/env python3
"""
PyInstaller build script for BatchReelMaker V9
This script creates a standalone executable with FFmpeg bundled.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_ffmpeg():
    """Check if FFmpeg is available in the system PATH"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, check=True)
        print("✓ FFmpeg found in system PATH")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ FFmpeg not found in system PATH")
        return False

def download_ffmpeg():
    """Download FFmpeg for Windows if not available"""
    print("Downloading FFmpeg for Windows...")
    
    # Create ffmpeg directory
    ffmpeg_dir = Path("ffmpeg")
    ffmpeg_dir.mkdir(exist_ok=True)
    
    # Download FFmpeg from official builds
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    try:
        import urllib.request
        import zipfile
        
        print(f"Downloading from: {ffmpeg_url}")
        zip_path = ffmpeg_dir / "ffmpeg.zip"
        
        # Download the file
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(ffmpeg_dir)
        
        # Find the extracted directory
        extracted_dirs = [d for d in ffmpeg_dir.iterdir() if d.is_dir()]
        if extracted_dirs:
            ffmpeg_bin_dir = extracted_dirs[0] / "bin"
            if ffmpeg_bin_dir.exists():
                # Copy ffmpeg.exe to the main directory
                ffmpeg_exe = ffmpeg_bin_dir / "ffmpeg.exe"
                if ffmpeg_exe.exists():
                    shutil.copy2(ffmpeg_exe, "ffmpeg.exe")
                    print("✓ FFmpeg downloaded and extracted successfully")
                    return True
        
        print("✗ Failed to extract FFmpeg properly")
        return False
        
    except Exception as e:
        print(f"✗ Error downloading FFmpeg: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building BatchReelMaker V9 executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable
        "--windowed",                   # Hide console window
        "--name=BatchReelMaker_V9",     # Name of the executable
        "--icon=icon.ico",              # Icon (if available)
        "--add-data=ffmpeg.exe;.",      # Include FFmpeg
        "--hidden-import=moviepy",
        "--hidden-import=moviepy.editor",
        "--hidden-import=moviepy.video",
        "--hidden-import=moviepy.audio",
        "--hidden-import=moviepy.tools",
        "--hidden-import=imageio",
        "--hidden-import=imageio_ffmpeg",
        "--hidden-import=numpy",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=proglog",
        "--hidden-import=decorator",
        "--hidden-import=tqdm",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=certifi",
        "--hidden-import=charset_normalizer",
        "--hidden-import=idna",
        "--collect-all=moviepy",
        "--collect-all=imageio",
        "--collect-all=proglog",
        "--collect-all=decorator",
        "--collect-all=tqdm",
        "app.py"
    ]
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Executable built successfully!")
        print(f"Output: dist/BatchReelMaker_V9.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error building executable: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def create_installer():
    """Create a simple installer script"""
    installer_script = """@echo off
echo Installing BatchReelMaker V9...
echo.

REM Create program directory
if not exist "C:\\Program Files\\BatchReelMaker_V9" mkdir "C:\\Program Files\\BatchReelMaker_V9"

REM Copy executable
copy "BatchReelMaker_V9.exe" "C:\\Program Files\\BatchReelMaker_V9\\"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\BatchReelMaker V9.lnk'); $Shortcut.TargetPath = 'C:\\Program Files\\BatchReelMaker_V9\\BatchReelMaker_V9.exe'; $Shortcut.Save()"

echo.
echo Installation completed!
echo BatchReelMaker V9 has been installed to C:\\Program Files\\BatchReelMaker_V9\\
echo A desktop shortcut has been created.
echo.
pause
"""
    
    with open("install.bat", "w") as f:
        f.write(installer_script)
    
    print("✓ Installer script created: install.bat")

def main():
    """Main build process"""
    print("=" * 50)
    print("BatchReelMaker V9 - Build Script")
    print("=" * 50)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✓ PyInstaller installed")
    
    # Check/Download FFmpeg
    if not check_ffmpeg():
        if not download_ffmpeg():
            print("Warning: FFmpeg not available. The application may not work properly.")
            print("Please install FFmpeg manually and ensure it's in your system PATH.")
    
    # Build the executable
    if build_executable():
        create_installer()
        print("\n" + "=" * 50)
        print("BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("Files created:")
        print("- dist/BatchReelMaker_V9.exe (Main executable)")
        print("- install.bat (Installer script)")
        print("\nTo install:")
        print("1. Run install.bat as administrator")
        print("2. Or manually copy BatchReelMaker_V9.exe to your desired location")
    else:
        print("\n" + "=" * 50)
        print("BUILD FAILED!")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
