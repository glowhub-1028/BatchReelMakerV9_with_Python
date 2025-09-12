import sys
import os
import json
import gc
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                             QPushButton, QCheckBox, QSpinBox, QTableWidget, 
                             QTableWidgetItem, QFileDialog, QMessageBox, 
                             QProgressBar, QGroupBox, QHeaderView, QComboBox,
                             QListWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

import moviepy.editor as mp
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_audioclips, vfx
import numpy as np
from PIL import Image

# Pillow 10+ compatibility: restore removed constants used by MoviePy
try:
    _Resampling = getattr(Image, 'Resampling', None)
    if _Resampling is not None:
        if not hasattr(Image, 'ANTIALIAS'):
            Image.ANTIALIAS = _Resampling.LANCZOS
        if not hasattr(Image, 'BICUBIC'):
            Image.BICUBIC = _Resampling.BICUBIC
        if not hasattr(Image, 'BILINEAR'):
            Image.BILINEAR = _Resampling.BILINEAR
except Exception:
    pass


class OverlayItem:
    """Represents an overlay item with timing and display properties"""
    def __init__(self, filename: str = "", start_time: str = "00:00:00", 
                 duration: int = 5, show_timer: bool = False):
        self.filename = filename
        self.start_time = start_time
        self.duration = duration
        self.show_timer = show_timer
    
    def to_dict(self) -> Dict:
        return {
            'filename': self.filename,
            'start_time': self.start_time,
            'duration': self.duration,
            'show_timer': self.show_timer
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OverlayItem':
        return cls(
            filename=data.get('filename', ''),
            start_time=data.get('start_time', '00:00:00'),
            duration=data.get('duration', 5),
            show_timer=data.get('show_timer', False)
        )


class VideoProcessor(QThread):
    """Thread for processing videos to avoid GUI freezing"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
    
    def run(self):
        try:
            self.status_updated.emit("Starting video processing...")
            
            # Load base image
            self.status_updated.emit("Loading base image...")
            base_image_path = self.config['folder_a']
            if not os.path.exists(base_image_path):
                raise FileNotFoundError(f"Base image folder not found: {base_image_path}")
            
            # Get first image from folder
            image_files = [f for f in os.listdir(base_image_path) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            if not image_files:
                raise FileNotFoundError(f"No image files found in: {base_image_path}")
            
            base_image_file = os.path.join(base_image_path, image_files[0])
            self.progress_updated.emit(10)
            
            # Load audio
            self.status_updated.emit("Loading audio...")
            audio_folder = self.config['folder_b']
            if not os.path.exists(audio_folder):
                raise FileNotFoundError(f"Audio folder not found: {audio_folder}")
            
            audio_files = [f for f in os.listdir(audio_folder) 
                          if f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac'))]
            if not audio_files:
                raise FileNotFoundError(f"No audio files found in: {audio_folder}")
            
            audio_file = os.path.join(audio_folder, audio_files[0])
            self.progress_updated.emit(20)
            
            # Load overlays
            self.status_updated.emit("Loading overlays...")
            overlay_folder = self.config['overlay_folder']
            overlays = []
            
            if os.path.exists(overlay_folder):
                for overlay_item in self.config['overlays']:
                    overlay_path = os.path.join(overlay_folder, overlay_item['filename'])
                    if os.path.exists(overlay_path):
                        overlays.append({
                            'path': overlay_path,
                            'start_time': self._time_to_seconds(overlay_item['start_time']),
                            'duration': overlay_item['duration'],
                            'show_timer': overlay_item['show_timer']
                        })
            
            self.progress_updated.emit(30)
            
            # Load alarm sound
            alarm_audio = None
            if self.config['alarm_file'] and os.path.exists(self.config['alarm_file']):
                self.status_updated.emit("Loading alarm sound...")
                alarm_audio = AudioFileClip(self.config['alarm_file'])
            
            self.progress_updated.emit(40)
            
            # Create base video clip with memory optimization
            self.status_updated.emit("Creating base video...")
            base_clip = ImageClip(base_image_file)
            
            # Optimize memory usage by reducing image size if too large
            max_dimension = 1920  # Maximum width/height to prevent memory issues
            if base_clip.size[0] > max_dimension or base_clip.size[1] > max_dimension:
                scale_factor = min(max_dimension / base_clip.size[0], max_dimension / base_clip.size[1])
                new_width = int(base_clip.size[0] * scale_factor)
                new_height = int(base_clip.size[1] * scale_factor)
                base_clip = base_clip.resize((new_width, new_height))
                self.status_updated.emit(f"Resized base image to {new_width}x{new_height} to optimize memory usage")
            
            # Process audio
            self.status_updated.emit("Processing audio...")
            audio_clip = AudioFileClip(audio_file)
            
            # Loop audio if specified
            if self.config['music_loops'] > 1:
                audio_clips = [audio_clip] * self.config['music_loops']
                audio_clip = concatenate_audioclips(audio_clips)
            
            # Set base clip duration to match audio
            base_clip = base_clip.set_duration(audio_clip.duration)
            
            # Apply fade-in effect if enabled (AFTER setting duration)
            if self.config['fade_in']:
                self.status_updated.emit("Applying fade-in effect to base image...")
                base_clip = base_clip.fadein(5)
            
            self.progress_updated.emit(60)
            
            # Add overlays
            self.status_updated.emit("Adding overlays...")
            overlay_clips = []
            alarm_clips = []
            base_w, base_h = base_clip.size
            
            for overlay in overlays:
                # Skip if no valid duration or file
                if overlay['duration'] <= 0 or not os.path.exists(overlay['path']):
                    self.status_updated.emit(f"Skipping overlay (invalid): {overlay['path']}")
                    continue

                # Create overlay clip with transparency support and ensure it fits inside the base video
                overlay_clip = (ImageClip(overlay['path'], transparent=True)
                               .set_duration(overlay['duration'])
                               .set_start(overlay['start_time'])
                               .set_position(("center", "center")))
                
                # Apply fade-in and fade-out effects to the overlay's opacity mask
                # This creates smooth transparency transitions without affecting the RGB content
                if overlay_clip.mask is not None:
                    # Apply fades to the existing mask
                    overlay_clip = overlay_clip.set_mask(overlay_clip.mask.fadein(5).fadeout(5))
                else:
                    # Create a mask if none exists and apply fades
                    from moviepy.video.VideoClip import VideoClip
                    mask_clip = VideoClip(lambda t: 1.0, duration=overlay['duration'])
                    mask_clip = mask_clip.fadein(5).fadeout(5)
                    overlay_clip = overlay_clip.set_mask(mask_clip)
                
                ow, oh = overlay_clip.size
                
                # Additional memory optimization: limit overlay size
                max_overlay_dimension = 1024  # Maximum overlay dimension
                if ow > max_overlay_dimension or oh > max_overlay_dimension:
                    scale_factor = min(max_overlay_dimension / ow, max_overlay_dimension / oh)
                    overlay_clip = overlay_clip.resize(scale_factor)
                    ow, oh = overlay_clip.size
                    self.status_updated.emit(f"Resized overlay for memory optimization: {overlay['path']}")
                
                # scale down if larger than base video (keep 90% margins)
                max_w = int(base_w * 0.9)
                max_h = int(base_h * 0.9)
                scale = min(max_w / ow, max_h / oh, 1.0)
                if scale < 1.0:
                    overlay_clip = overlay_clip.resize(scale)
                    self.status_updated.emit(f"Resized overlay to fit: {overlay['path']} (scale={scale:.2f})")
                
                self.status_updated.emit(
                    f"Overlay added with fade effects: {overlay['path']}"
                )
                
                overlay_clips.append(overlay_clip)
                
                # Add alarm sound at overlay start time
                if alarm_audio:
                    alarm_clip = alarm_audio.set_start(overlay['start_time'])
                    alarm_clips.append(alarm_clip)
                
                # Clean up memory periodically
                if len(overlay_clips) % 3 == 0:  # Every 3 overlays
                    gc.collect()
            
            self.progress_updated.emit(70)
            
            # Combine all clips
            self.status_updated.emit("Compositing final video...")
            video_clips = [base_clip] + overlay_clips
            final_video = CompositeVideoClip(video_clips, size=base_clip.size)
            
            # Combine audio
            audio_clips = [audio_clip] + alarm_clips
            final_audio = concatenate_audioclips(audio_clips)
            
            final_video = final_video.set_audio(final_audio)
            
            self.progress_updated.emit(80)
            
            # Clean up memory before export
            gc.collect()
            
            # Export video
            self.status_updated.emit("Exporting video...")
            output_folder = self.config['folder_c']
            os.makedirs(output_folder, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_folder, f"BatchReelMaker_V9_{timestamp}.mp4")
            
            final_video.write_videofile(
                output_path,
                fps=self.config['frame_rate'],
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                preset='ultrafast',  # Faster encoding, less memory usage
                threads=2,  # Limit threads to reduce memory usage
                bitrate='2000k'  # Control bitrate to manage memory
            )
            
            self.progress_updated.emit(100)
            
            # Final memory cleanup
            gc.collect()
            
            self.status_updated.emit("Video processing completed successfully!")
            self.finished.emit(True, output_path)
            
        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")
            self.finished.emit(False, str(e))
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert time string (HH:MM:SS) to seconds"""
        try:
            time_parts = time_str.split(':')
            if len(time_parts) == 3:
                hours, minutes, seconds = map(int, time_parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(time_parts) == 2:
                minutes, seconds = map(int, time_parts)
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except:
            return 0.0


class BatchReelMakerV9(QMainWindow):
    """Main application window for BatchReelMaker V9"""
    
    def __init__(self):
        super().__init__()
        self.overlays = []
        self.video_processor = None
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("BatchReelMaker V9")
        self.setGeometry(100, 100, 1000, 800)
        
        # Set application icon
        icon = QIcon("icon.ico")
        self.setWindowIcon(icon)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("BatchReelMaker V9")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Folder selection group
        folder_group = QGroupBox("Folder Selection")
        folder_layout = QGridLayout(folder_group)
        
        # Folder A (Images)
        self.folder_a_edit = QLineEdit()
        self.folder_a_edit.setPlaceholderText("Select folder with base images...")
        folder_a_btn = QPushButton("Browse")
        folder_a_btn.clicked.connect(lambda: self.browse_folder(self.folder_a_edit))
        folder_layout.addWidget(QLabel("Folder A (Images):"), 0, 0)
        folder_layout.addWidget(self.folder_a_edit, 0, 1)
        folder_layout.addWidget(folder_a_btn, 0, 2)
        
        # Folder B (Audio)
        self.folder_b_edit = QLineEdit()
        self.folder_b_edit.setPlaceholderText("Select folder with audio files...")
        folder_b_btn = QPushButton("Browse")
        folder_b_btn.clicked.connect(lambda: self.browse_folder(self.folder_b_edit))
        folder_layout.addWidget(QLabel("Folder B (Audio):"), 1, 0)
        folder_layout.addWidget(self.folder_b_edit, 1, 1)
        folder_layout.addWidget(folder_b_btn, 1, 2)
        
        # Overlay Folder
        self.overlay_folder_edit = QLineEdit()
        self.overlay_folder_edit.setPlaceholderText("Select folder with overlay images...")
        overlay_folder_btn = QPushButton("Browse")
        overlay_folder_btn.clicked.connect(self.browse_overlay_folder)
        folder_layout.addWidget(QLabel("Overlay Folder:"), 2, 0)
        folder_layout.addWidget(self.overlay_folder_edit, 2, 1)
        folder_layout.addWidget(overlay_folder_btn, 2, 2)
        
        # Folder C (Output)
        self.folder_c_edit = QLineEdit()
        self.folder_c_edit.setPlaceholderText("Select output folder...")
        folder_c_btn = QPushButton("Browse")
        folder_c_btn.clicked.connect(lambda: self.browse_folder(self.folder_c_edit))
        folder_layout.addWidget(QLabel("Folder C (Output):"), 3, 0)
        folder_layout.addWidget(self.folder_c_edit, 3, 1)
        folder_layout.addWidget(folder_c_btn, 3, 2)
        
        main_layout.addWidget(folder_group)
        
        # File previews under folder selection
        preview_group = QGroupBox("Folder Previews")
        preview_layout = QGridLayout(preview_group)
        
        self.images_list = QListWidget()
        self.audios_list = QListWidget()
        
        preview_layout.addWidget(QLabel("Images in Folder A:"), 0, 0)
        preview_layout.addWidget(self.images_list, 1, 0)
        preview_layout.addWidget(QLabel("Audio in Folder B:"), 0, 1)
        preview_layout.addWidget(self.audios_list, 1, 1)
        
        main_layout.addWidget(preview_group)
        
        # Settings group
        settings_group = QGroupBox("Video Settings")
        settings_layout = QGridLayout(settings_group)
        
        # Music loops
        self.music_loops_spin = QSpinBox()
        self.music_loops_spin.setRange(1, 100)
        self.music_loops_spin.setValue(1)
        settings_layout.addWidget(QLabel("Music Loops:"), 0, 0)
        settings_layout.addWidget(self.music_loops_spin, 0, 1)
        
        # Fade-in checkbox
        self.fade_in_checkbox = QCheckBox("Fade-in effect (5s)")
        self.fade_in_checkbox.setChecked(True)
        settings_layout.addWidget(self.fade_in_checkbox, 0, 2)
        
        # Frame rate
        self.frame_rate_spin = QSpinBox()
        self.frame_rate_spin.setRange(15, 60)
        self.frame_rate_spin.setValue(30)
        settings_layout.addWidget(QLabel("Frame Rate:"), 1, 0)
        settings_layout.addWidget(self.frame_rate_spin, 1, 1)
        
        # Alarm file
        self.alarm_file_edit = QLineEdit()
        self.alarm_file_edit.setPlaceholderText("Select alarm sound file...")
        alarm_file_btn = QPushButton("Browse")
        alarm_file_btn.clicked.connect(self.browse_alarm_file)
        settings_layout.addWidget(QLabel("Alarm File:"), 2, 0)
        settings_layout.addWidget(self.alarm_file_edit, 2, 1)
        settings_layout.addWidget(alarm_file_btn, 2, 2)
        
        main_layout.addWidget(settings_group)
        
        # Overlays table
        overlay_group = QGroupBox("Overlays Management")
        overlay_layout = QVBoxLayout(overlay_group)
        
        # Table
        self.overlay_table = QTableWidget()
        self.overlay_table.setColumnCount(4)
        self.overlay_table.setHorizontalHeaderLabels(["File Name", "Start Time (HH:MM:SS)", "Duration (s)", "Show Timer"])
        
        # Set column widths
        header = self.overlay_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        overlay_layout.addWidget(self.overlay_table)
        
        # Overlay buttons
        overlay_btn_layout = QHBoxLayout()
        add_overlay_btn = QPushButton("Add Overlay")
        add_overlay_btn.clicked.connect(self.add_overlay)
        remove_overlay_btn = QPushButton("Remove Overlay")
        remove_overlay_btn.clicked.connect(self.remove_overlay)
        clear_overlays_btn = QPushButton("Clear All")
        clear_overlays_btn.clicked.connect(self.clear_overlays)
        
        overlay_btn_layout.addWidget(add_overlay_btn)
        overlay_btn_layout.addWidget(remove_overlay_btn)
        overlay_btn_layout.addWidget(clear_overlays_btn)
        overlay_btn_layout.addStretch()
        
        overlay_layout.addLayout(overlay_btn_layout)
        main_layout.addWidget(overlay_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Action buttons
        action_layout = QHBoxLayout()
        convert_btn = QPushButton("Convert All")
        convert_btn.setFont(QFont("Arial", 12, QFont.Bold))
        convert_btn.clicked.connect(self.convert_all)
        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.close)
        
        action_layout.addWidget(convert_btn)
        action_layout.addWidget(quit_btn)
        main_layout.addLayout(action_layout)
        
        # Connect table signals
        self.overlay_table.itemChanged.connect(self.on_table_item_changed)
        
        # Auto-refresh previews when folder paths change
        self.folder_a_edit.textChanged.connect(lambda _: self.refresh_previews())
        self.folder_b_edit.textChanged.connect(lambda _: self.refresh_previews())
        
        # Refresh overlay filenames when overlay folder path changes
        self.overlay_folder_edit.textChanged.connect(lambda _: self.refresh_overlay_dropdowns())
    
    def browse_folder(self, line_edit: QLineEdit):
        """Browse for a folder and update the line edit"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)
            self.refresh_previews()
    
    def browse_alarm_file(self):
        """Browse for an alarm sound file"""
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Alarm File", "", 
            "Audio Files (*.mp3 *.wav *.m4a *.aac)"
        )
        if file:
            self.alarm_file_edit.setText(file)

    def browse_overlay_folder(self):
        """Browse for overlay folder and refresh overlay filename dropdowns"""
        folder = QFileDialog.getExistingDirectory(self, "Select Overlay Folder")
        if folder:
            self.overlay_folder_edit.setText(folder)
            self.refresh_overlay_dropdowns()

    def refresh_overlay_dropdowns(self):
        """Populate filename dropdowns in the overlay table from the selected overlay folder"""
        overlay_folder = self.overlay_folder_edit.text()
        if not overlay_folder or not os.path.exists(overlay_folder):
            return
        image_files = [f for f in os.listdir(overlay_folder)
                       if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
        for row in range(self.overlay_table.rowCount()):
            filename_widget = self.overlay_table.cellWidget(row, 0)
            if isinstance(filename_widget, QComboBox):
                current = filename_widget.currentText()
                filename_widget.blockSignals(True)
                filename_widget.clear()
                filename_widget.addItems(image_files)
                # Restore previous selection if still available
                if current:
                    idx = filename_widget.findText(current)
                    if idx >= 0:
                        filename_widget.setCurrentIndex(idx)
                filename_widget.blockSignals(False)

    def refresh_previews(self):
        """Refresh images and audios list widgets based on selected folders"""
        # Images
        self.images_list.clear()
        folder_a = self.folder_a_edit.text()
        if folder_a and os.path.exists(folder_a):
            imgs = [f for f in os.listdir(folder_a)
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
            self.images_list.addItems(sorted(imgs))
        
        # Audios
        self.audios_list.clear()
        folder_b = self.folder_b_edit.text()
        if folder_b and os.path.exists(folder_b):
            auds = [f for f in os.listdir(folder_b)
                    if f.lower().endswith((".mp3", ".wav", ".m4a", ".aac"))]
            self.audios_list.addItems(sorted(auds))
    
    def add_overlay(self):
        """Add a new overlay to the table"""
        row = self.overlay_table.rowCount()
        self.overlay_table.insertRow(row)
        
        # File name (combo box with files from overlay folder)
        filename_combo = QComboBox()
        if self.overlay_folder_edit.text():
            overlay_folder = self.overlay_folder_edit.text()
            if os.path.exists(overlay_folder):
                image_files = [f for f in os.listdir(overlay_folder) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
                filename_combo.addItems(image_files)
        self.overlay_table.setCellWidget(row, 0, filename_combo)
        
        # Start time
        start_time_item = QTableWidgetItem("00:00:00")
        self.overlay_table.setItem(row, 1, start_time_item)
        
        # Duration
        duration_item = QTableWidgetItem("5")
        self.overlay_table.setItem(row, 2, duration_item)
        
        # Show timer checkbox
        timer_checkbox = QCheckBox()
        timer_checkbox.setChecked(False)
        self.overlay_table.setCellWidget(row, 3, timer_checkbox)
        
        # Add to overlays list
        overlay_item = OverlayItem()
        self.overlays.append(overlay_item)
    
    def remove_overlay(self):
        """Remove selected overlay from the table"""
        current_row = self.overlay_table.currentRow()
        if current_row >= 0:
            self.overlay_table.removeRow(current_row)
            if current_row < len(self.overlays):
                self.overlays.pop(current_row)
    
    def clear_overlays(self):
        """Clear all overlays"""
        self.overlay_table.setRowCount(0)
        self.overlays.clear()
    
    def on_table_item_changed(self, item):
        """Handle table item changes"""
        row = item.row()
        if row < len(self.overlays):
            overlay = self.overlays[row]
            
            if item.column() == 1:  # Start time
                overlay.start_time = item.text()
            elif item.column() == 2:  # Duration
                try:
                    overlay.duration = int(item.text())
                except ValueError:
                    item.setText("5")
                    overlay.duration = 5
    
    def get_overlays_from_table(self) -> List[Dict]:
        """Extract overlay data from the table"""
        overlays = []
        for row in range(self.overlay_table.rowCount()):
            filename_widget = self.overlay_table.cellWidget(row, 0)
            filename = filename_widget.currentText() if filename_widget else ""
            
            start_time = self.overlay_table.item(row, 1).text() if self.overlay_table.item(row, 1) else "00:00:00"
            
            duration_item = self.overlay_table.item(row, 2)
            duration = int(duration_item.text()) if duration_item and duration_item.text().isdigit() else 5
            
            timer_widget = self.overlay_table.cellWidget(row, 3)
            show_timer = timer_widget.isChecked() if timer_widget else False
            
            overlays.append({
                'filename': filename,
                'start_time': start_time,
                'duration': duration,
                'show_timer': show_timer
            })
        
        return overlays
    
    def validate_inputs(self) -> bool:
        """Validate all input fields"""
        if not self.folder_a_edit.text():
            QMessageBox.warning(self, "Validation Error", "Please select Folder A (Images)")
            return False
        
        if not self.folder_b_edit.text():
            QMessageBox.warning(self, "Validation Error", "Please select Folder B (Audio)")
            return False
        
        if not self.folder_c_edit.text():
            QMessageBox.warning(self, "Validation Error", "Please select Folder C (Output)")
            return False
        
        return True
    
    def convert_all(self):
        """Start the video conversion process"""
        if not self.validate_inputs():
            return
        
        # Prepare configuration
        config = {
            'folder_a': self.folder_a_edit.text(),
            'folder_b': self.folder_b_edit.text(),
            'overlay_folder': self.overlay_folder_edit.text(),
            'folder_c': self.folder_c_edit.text(),
            'music_loops': self.music_loops_spin.value(),
            'fade_in': self.fade_in_checkbox.isChecked(),
            'frame_rate': self.frame_rate_spin.value(),
            'alarm_file': self.alarm_file_edit.text(),
            'overlays': self.get_overlays_from_table()
        }
        
        # Start processing in background thread
        self.video_processor = VideoProcessor(config)
        self.video_processor.progress_updated.connect(self.progress_bar.setValue)
        self.video_processor.status_updated.connect(self.status_label.setText)
        self.video_processor.finished.connect(self.on_conversion_finished)
        
        # Update UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting conversion...")
        
        self.video_processor.start()
    
    def on_conversion_finished(self, success: bool, message: str):
        """Handle conversion completion"""
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Success", f"Video created successfully!\nOutput: {message}")
            self.status_label.setText("Conversion completed successfully!")
        else:
            QMessageBox.critical(self, "Error", f"Conversion failed: {message}")
            self.status_label.setText("Conversion failed!")
    
    def save_config(self):
        """Save current configuration to file"""
        config = {
            'folder_a': self.folder_a_edit.text(),
            'folder_b': self.folder_b_edit.text(),
            'overlay_folder': self.overlay_folder_edit.text(),
            'folder_c': self.folder_c_edit.text(),
            'music_loops': self.music_loops_spin.value(),
            'fade_in': self.fade_in_checkbox.isChecked(),
            'frame_rate': self.frame_rate_spin.value(),
            'alarm_file': self.alarm_file_edit.text(),
            'overlays': self.get_overlays_from_table()
        }
        
        try:
            with open('batchreelmaker_config.json', 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists('batchreelmaker_config.json'):
                with open('batchreelmaker_config.json', 'r') as f:
                    config = json.load(f)
                
                self.folder_a_edit.setText(config.get('folder_a', ''))
                self.folder_b_edit.setText(config.get('folder_b', ''))
                self.overlay_folder_edit.setText(config.get('overlay_folder', ''))
                self.folder_c_edit.setText(config.get('folder_c', ''))
                self.music_loops_spin.setValue(config.get('music_loops', 1))
                self.fade_in_checkbox.setChecked(config.get('fade_in', True))
                self.frame_rate_spin.setValue(config.get('frame_rate', 30))
                self.alarm_file_edit.setText(config.get('alarm_file', ''))
                
                # Load overlays
                overlays = config.get('overlays', [])
                for overlay in overlays:
                    self.add_overlay()
                    row = self.overlay_table.rowCount() - 1
                    
                    # Set filename
                    filename_combo = self.overlay_table.cellWidget(row, 0)
                    if filename_combo:
                        index = filename_combo.findText(overlay.get('filename', ''))
                        if index >= 0:
                            filename_combo.setCurrentIndex(index)
                    
                    # Set start time
                    start_time_item = QTableWidgetItem(overlay.get('start_time', '00:00:00'))
                    self.overlay_table.setItem(row, 1, start_time_item)
                    
                    # Set duration
                    duration_item = QTableWidgetItem(str(overlay.get('duration', 5)))
                    self.overlay_table.setItem(row, 2, duration_item)
                    
                    # Set show timer
                    timer_checkbox = self.overlay_table.cellWidget(row, 3)
                    if timer_checkbox:
                        timer_checkbox.setChecked(overlay.get('show_timer', False))
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.save_config()
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("BatchReelMaker V9")
    app.setApplicationVersion("9.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = BatchReelMakerV9()
    window.show()
    
    # Start application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
