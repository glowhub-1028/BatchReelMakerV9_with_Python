# BatchReelMaker V9

A modern desktop application for creating video reels with overlays, audio, and effects. Built with Python, PyQt5, and MoviePy.

## Features

- **Base Image Support**: Use images as the background for your videos
- **Audio Looping**: Loop background music multiple times
- **Overlay Management**: Add multiple overlays with precise timing control
- **Fade Effects**: Smooth fade-in/fade-out transitions for overlays
- **Alarm Sounds**: Add sound effects when overlays appear
- **Modern GUI**: Clean, intuitive interface built with PyQt5
- **Configuration Persistence**: Settings are automatically saved and restored

## Requirements

- Windows 10/11 (64-bit)
- Python 3.8 or higher
- FFmpeg (automatically handled by the build script)

## Installation

### Option 1: Run from Source

1. **Clone or download the project**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python app.py
   ```

### Option 2: Build Standalone Executable

1. **Run the build script**:
   ```bash
   python build_exe.py
   ```
2. **Install the application**:
   - Run `install.bat` as administrator, OR
   - Manually copy `dist/BatchReelMaker_V9.exe` to your desired location

## Usage

### 1. Folder Setup

- **Folder A (Images)**: Contains your base background images
- **Folder B (Audio)**: Contains your background music files
- **Overlay Folder**: Contains overlay images to display during the video
- **Folder C (Output)**: Where the final videos will be saved

### 2. Video Settings

- **Music Loops**: Number of times to repeat the background music
- **Fade-in Effect**: Enable 5-second fade-in for the base image
- **Frame Rate**: Video output frame rate (default: 30 fps)
- **Alarm File**: Sound effect to play when overlays appear

### 3. Overlay Management

Use the table to configure overlays:

- **File Name**: Select from available overlay images
- **Start Time**: When the overlay should appear (HH:MM:SS format)
- **Duration**: How long the overlay should stay visible (in seconds)
- **Show Timer**: Placeholder for future timer display feature

### 4. Creating Videos

1. Configure all settings and overlays
2. Click "Convert All" to start processing
3. Monitor progress in the status bar
4. Find your output video in Folder C

## File Formats Supported

### Images
- PNG, JPG, JPEG, BMP, GIF
- **PNG with transparency** recommended for overlays for best fade effects

### Audio
- MP3, WAV, M4A, AAC

### Output
- MP4 (H.264 codec, AAC audio)

## Technical Details

### Architecture
- **GUI Framework**: PyQt5
- **Video Processing**: MoviePy with FFmpeg backend
- **Image Processing**: Pillow (PIL)
- **Audio Processing**: MoviePy audio capabilities

### Video Processing Pipeline
1. Load base image and apply fade-in effect
2. Load and loop background audio
3. Process overlays with fade transitions
4. Insert alarm sounds at overlay start times
5. Composite all elements into final video
6. Export as MP4 with specified frame rate

### Configuration
Settings are automatically saved to `batchreelmaker_config.json` and restored on startup.

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - The build script will automatically download FFmpeg
   - Ensure you have internet connection during build

2. **Video processing fails**
   - Check that all input files exist and are valid
   - Ensure sufficient disk space for output
   - Verify audio/video file formats are supported

3. **GUI not responding during processing**
   - Video processing runs in a background thread
   - The progress bar shows current status
   - Wait for completion or check error messages

### Performance Tips

- Use compressed image formats (JPG) for faster loading
- Keep overlay images reasonably sized
- Close other applications during video processing
- Use SSD storage for better I/O performance

## Development

### Project Structure
```
BatchReelMaker_V9/
├── app.py              # Main application
├── requirements.txt    # Python dependencies
├── build_exe.py       # PyInstaller build script
├── README.md          # This file
└── batchreelmaker_config.json  # User settings (auto-generated)
```

### Building from Source
```bash
# Install development dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Build executable
python build_exe.py
```

### Customization
- Modify `app.py` to change GUI layout or functionality
- Update `requirements.txt` for different dependency versions
- Customize `build_exe.py` for different packaging options

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all requirements are met
3. Ensure input files are in supported formats
4. Check system resources during processing

## Version History

### V9.1
- Memory optimization improvements
- Automatic image resizing for large files
- Garbage collection during processing
- Optimized video export settings
- Fixed MoviePy compatibility issues

### V9.0
- Initial release
- PyQt5 GUI with modern interface
- MoviePy video processing
- Overlay management system
- Configuration persistence
- Standalone executable support
