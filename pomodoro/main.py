#!/usr/bin/env python3
"""
🍅 Professional Pomodoro Timer with YouTube Audio Integration

Features:
- Customizable work/break intervals
- YouTube audio downloading and playback
- Modern PySide6 GUI interface
- VLC media player integration
- Persistent configuration settings
- AI Agent GitHub management integration

This project is automatically managed by an AI Agent that handles:
- Intelligent commit messages
- Automated GitHub synchronization
- Code quality checks
- Release management
- Documentation updates

Created: October 2025
Auto-managed by: AI Agent Development Environment
Repository: https://github.com/Z124415-JACK-TAYLOR-GORMAN/pomodoro-timer-pro
"""

import sys
import vlc
import yt_dlp
import shutil
import json
import os
import random
from threading import Thread
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QLineEdit,
    QFileDialog,
    QCheckBox,
    QListWidget,
    QGroupBox,
    QFrame,
)
from PySide6.QtCore import Qt, QTimer, QObject, Signal, QByteArray
from PySide6.QtGui import QKeyEvent, QFont, QPixmap, QPainter, QPainterPath

# --- START: Reworked Pathing ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
CONFIG_FILE = os.path.join(project_root, "config.json")
AUDIO_FOLDER = os.path.join(project_root, "audio")
VIDEO_FOLDER = os.path.join(project_root, "video")
# --- END: Reworked Pathing ---


# --- START: Enhanced Video Window ---
class VideoWindow(QWidget):
    """A separate window for video playback that forwards key presses."""
    keyPressed = Signal(QKeyEvent)
    windowShown = Signal() # Signal emitted when the window is first shown
    windowHidden = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pomodoro Video Player")
        self.setGeometry(700, 100, 480, 270)
        self.setLayout(QVBoxLayout())
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.layout().addWidget(self.video_frame)
        self.layout().setContentsMargins(0,0,0,0)
        self._allow_close = False

    def allow_close(self):
        self._allow_close = True

    def keyPressEvent(self, event: QKeyEvent):
        """Forward key events to the main window for centralized handling."""
        self.keyPressed.emit(event)

    def showEvent(self, event):
        """Emit a signal the first time the window is made visible."""
        super().showEvent(event)
        self.windowShown.emit()

    def closeEvent(self, event):
        if self._allow_close:
            event.accept()
        else:
            self.hide()
            self.windowHidden.emit()
            event.ignore()
# --- END: Enhanced Video Window ---


class Downloader(QObject):
    progress = Signal(int)
    finished = Signal(str, str, str) # file, title, original_url

    def __init__(self, url, audio_only):
        super().__init__()
        self.url = url
        self.audio_only = audio_only

    def run(self):
        if not shutil.which('ffmpeg'):
            print("ffmpeg not found. Please install ffmpeg to download audio from YouTube.")
            self.finished.emit(None, None, self.url)
            return

        try:
            folder = AUDIO_FOLDER if self.audio_only else VIDEO_FOLDER
            if not os.path.exists(folder): os.makedirs(folder)

            ydl_opts = {
                'format': 'bestaudio/best' if self.audio_only else 'bestvideo[height<=1080][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'verbose': True,
            }
            if self.audio_only:
                ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                filename = ydl.prepare_filename(info)
                title = info.get('title', os.path.basename(filename))
                self.finished.emit(filename, title, self.url)
        except Exception as e:
            print(f"Error downloading youtube video: {e}")
            self.finished.emit(None, None, self.url)

    def progress_hook(self, d):
        """Robustly calculate download percentage from raw byte values."""
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            if total_bytes and downloaded_bytes:
                percentage = (downloaded_bytes / total_bytes) * 100
                self.progress.emit(int(percentage))


class PomodoroTimer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pomodoro Timer")
        self.setGeometry(100, 100, 420, 850)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        self.setStyleSheet('''
            QMainWindow { background-color: #FFFFFF; }
            QLabel { color: #333333; }
            QPushButton {
                background-color: #FFA500; color: #FFFFFF; border: none;
                padding: 10px 20px; border-radius: 15px; font-size: 16px;
            }
            QPushButton:hover { background-color: #FFC107; }
            QSlider::groove:horizontal {
                border: 1px solid #FFA500; height: 10px; background: #FFFFFF;
                margin: 2px 0; border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #FFA500; border: 1px solid #FFA500;
                width: 18px; margin: -2px 0; border-radius: 9px;
            }
            QLineEdit, QGroupBox {
                border: 2px solid #FFA500; border-radius: 15px;
                padding: 10px; font-size: 14px;
            }
            QGroupBox { margin-top: 10px; }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top center;
                padding: 0 3px;
            }
            QPushButton#ModeButton {
                background-color: transparent; border: none;
                font-size: 18px; font-weight: bold;
            }
            QPushButton#TransportButton { font-size: 24px; }
        ''')

        self.work_playlist = []
        self.break_playlist = []
        self.download_queue = []
        self.video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm']
        self.is_vlc_attached = False

        self.create_widgets()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.work_time = 25 * 60
        self.break_time = 5 * 60
        self.remaining_work_time = self.work_time
        self.remaining_break_time = self.break_time
        self.current_time = self.remaining_work_time
        self.is_work_time = True
        self.is_paused = True

        vlc_args = [
            '--no-xlib',
            '--avcodec-hw=none',
            '--vout=gl'
        ]
        self.vlc_instance = vlc.Instance(vlc_args)

        self.media_player = self.vlc_instance.media_player_new()
        self.video_window = VideoWindow()
        self.video_window.windowShown.connect(self.attach_vlc_to_window)
        self.video_window.windowHidden.connect(self.on_video_window_hidden)
        
        self.current_media_path = None
        self.work_media_pos = {}
        self.break_media_pos = {}

        events = self.media_player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.media_finished)

        self.start_button.clicked.connect(self.start_timer)
        self.pause_button.clicked.connect(self.pause_timer)
        self.reset_button.clicked.connect(self.reset_timer)
        self.browse_button.clicked.connect(self.browse_file)
        self.work_media_button.clicked.connect(self.add_to_work_playlist)
        self.break_media_button.clicked.connect(self.add_to_break_playlist)
        self.reset_work_playlist_button.clicked.connect(self.reset_work_playlist)
        self.reset_break_playlist_button.clicked.connect(self.reset_break_playlist)
        self.work_slider.valueChanged.connect(self.set_work_time)
        self.break_slider.valueChanged.connect(self.set_break_time)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.shuffle_work_button.clicked.connect(self.shuffle_work_playlist)
        self.shuffle_break_button.clicked.connect(self.shuffle_break_playlist)
        self.work_mode_button.clicked.connect(self.set_mode_work)
        self.break_mode_button.clicked.connect(self.set_mode_break)
        self.skip_back_button.clicked.connect(self.skip_back)
        self.skip_forward_button.clicked.connect(self.skip_forward)
        self.video_window.keyPressed.connect(self.keyPressEvent)
        self.always_on_top_checkbox.stateChanged.connect(self.toggle_always_on_top)

        self.load_session()
        self.update_mode_indicator()

    def on_video_window_hidden(self):
        self.is_vlc_attached = False

    def attach_vlc_to_window(self):
        if not self.is_vlc_attached:
            if sys.platform.startswith('linux'):
                self.media_player.set_xwindow(self.video_window.video_frame.winId())
            elif sys.platform == 'win32':
                self.media_player.set_hwnd(self.video_window.video_frame.winId())
            self.is_vlc_attached = True

    def create_widgets(self):
        self.timer_label = QLabel("25:00", self)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont("Arial", 80, QFont.Bold))
        self.layout.addWidget(self.timer_label)
        
        mode_layout = QHBoxLayout()
        self.work_mode_button = QPushButton("Work")
        self.work_mode_button.setObjectName("ModeButton")
        self.break_mode_button = QPushButton("Break")
        self.break_mode_button.setObjectName("ModeButton")
        mode_layout.addWidget(self.work_mode_button)
        mode_layout.addWidget(self.break_mode_button)
        self.layout.addLayout(mode_layout)

        work_slider_layout, self.work_slider = self.create_slider("Work Time: 25 min", 1, 60, 25)
        break_slider_layout, self.break_slider = self.create_slider("Break Time: 5 min", 1, 30, 5)
        self.layout.addLayout(work_slider_layout)
        self.layout.addLayout(break_slider_layout)

        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start", self)
        self.pause_button = QPushButton("Pause", self)
        self.reset_button = QPushButton("Reset", self)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.reset_button)
        self.layout.addLayout(control_layout)
        
        media_control_layout = QHBoxLayout()
        self.skip_back_button = QPushButton("⏪")
        self.skip_back_button.setObjectName("TransportButton")
        self.skip_forward_button = QPushButton("⏩")
        self.skip_forward_button.setObjectName("TransportButton")
        media_control_layout.addWidget(self.skip_back_button)
        media_control_layout.addWidget(self.skip_forward_button)
        self.layout.addLayout(media_control_layout)

        self.media_label = QLabel("Media:", self)
        self.media_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.layout.addWidget(self.media_label)

        self.youtube_input = QLineEdit(self)
        self.youtube_input.setPlaceholderText("Enter YouTube URL or local file path")
        self.layout.addWidget(self.youtube_input)

        media_options_layout = QHBoxLayout()
        self.audio_only_checkbox = QCheckBox("Audio Only", self)
        self.always_on_top_checkbox = QCheckBox("Video Always on Top", self)
        media_options_layout.addWidget(self.audio_only_checkbox)
        media_options_layout.addWidget(self.always_on_top_checkbox)
        self.layout.addLayout(media_options_layout)

        self.browse_button = QPushButton("Browse Local Files", self)
        self.layout.addWidget(self.browse_button)
        
        media_buttons_layout = QHBoxLayout()
        self.work_media_button = QPushButton("Add to Work Playlist", self)
        self.break_media_button = QPushButton("Add to Break Playlist", self)
        media_buttons_layout.addWidget(self.work_media_button)
        media_buttons_layout.addWidget(self.break_media_button)
        self.layout.addLayout(media_buttons_layout)

        work_groupbox = QGroupBox("Work Playlist")
        work_layout = QVBoxLayout()
        self.work_playlist_widget = QListWidget(self)
        work_layout.addWidget(self.work_playlist_widget)
        work_playlist_buttons = QHBoxLayout()
        self.reset_work_playlist_button = QPushButton("Reset", self)
        self.shuffle_work_button = QPushButton("Shuffle", self)
        work_playlist_buttons.addWidget(self.reset_work_playlist_button)
        work_playlist_buttons.addWidget(self.shuffle_work_button)
        work_layout.addLayout(work_playlist_buttons)
        work_groupbox.setLayout(work_layout)
        self.layout.addWidget(work_groupbox)

        break_groupbox = QGroupBox("Break Playlist")
        break_layout = QVBoxLayout()
        self.break_playlist_widget = QListWidget(self)
        break_layout.addWidget(self.break_playlist_widget)
        break_playlist_buttons = QHBoxLayout()
        self.reset_break_playlist_button = QPushButton("Reset", self)
        self.shuffle_break_button = QPushButton("Shuffle", self)
        break_playlist_buttons.addWidget(self.reset_break_playlist_button)
        break_playlist_buttons.addWidget(self.shuffle_break_button)
        break_layout.addLayout(break_playlist_buttons)
        break_groupbox.setLayout(break_layout)
        self.layout.addWidget(break_groupbox)

        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        self.layout.addLayout(volume_layout)

        self.status_label = QLabel("", self)
        self.layout.addWidget(self.status_label)

        bottom_layout = QHBoxLayout()

        donation_label = QLabel("<a href='https://linktr.ee/Mclunky'>Help Jack Gorman afford univerity with a donation! And find more of my work. I hope I helped!</a>")
        donation_label.setOpenExternalLinks(True)
        donation_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(donation_label)

        self.image_label = QLabel()
        image_path = os.path.join(script_dir, 'prof.png')
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            size = 100 # size of the circle
            rounded = QPixmap(size, size)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            # scale the image to fit the circle
            scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.end()
            self.image_label.setPixmap(rounded)
            self.image_label.setAlignment(Qt.AlignCenter)

        bottom_layout.addWidget(self.image_label)

        self.layout.addLayout(bottom_layout)

    def set_volume(self, value):
        self.media_player.audio_set_volume(value)

    def play_media(self, path):
        if path and os.path.exists(path):
            is_video = any(path.lower().endswith(ext) for ext in self.video_extensions)
            
            if is_video:
                main_geom = self.geometry()
                if not self.video_window.isVisible():
                    self.video_window.move(main_geom.right() + 10, main_geom.top())
                self.video_window.show()
            else:
                self.video_window.hide()

            self.current_media_path = path
            
            time_ms = self.work_media_pos.get(path, 0) if self.is_work_time else self.break_media_pos.get(path, 0)
            start_seconds = time_ms / 1000.0
            
            media = self.vlc_instance.media_new(path)
            if start_seconds > 0.5:
                media.add_option(f'start-time={start_seconds}')

            self.media_player.set_media(media)
            
            if not self.is_paused:
                self.media_player.play()

    def stop_media(self):
        self.media_player.stop()
        self.media_player.set_media(None)
        self.current_media_path = None
        self.video_window.hide()
        self.is_vlc_attached = False

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        
        if key == Qt.Key_Space:
            if self.media_player.get_media():
                if self.is_paused: self.start_timer()
                else: self.pause_timer()

        elif key == Qt.Key_Up:
            self.volume_slider.setValue(self.volume_slider.value() + 5)
        elif key == Qt.Key_Down:
            self.volume_slider.setValue(self.volume_slider.value() - 5)
        
        elif key == Qt.Key_Right and modifiers == Qt.ShiftModifier:
            self.skip_forward()
        elif key == Qt.Key_Left and modifiers == Qt.ShiftModifier:
            self.skip_back()

        elif key == Qt.Key_Right:
            self.media_player.set_time(self.media_player.get_time() + 5000)
        elif key == Qt.Key_Left:
            self.media_player.set_time(self.media_player.get_time() - 5000)
        else:
            super().keyPressEvent(event)
            
    # --- Omitted unchanged methods for brevity ---
    def create_slider(self, label_text, min_val, max_val, initial_val):
        layout = QVBoxLayout(); label = QLabel(label_text); slider = QSlider(Qt.Horizontal); slider.setRange(min_val, max_val); slider.setValue(initial_val); slider.valueChanged.connect(lambda value, l=label, text=label_text.split(':')[0]: l.setText(f'{text}: {value} min')); layout.addWidget(label); layout.addWidget(slider); return layout, slider
    def update_mode_indicator(self):
        if self.is_work_time: self.work_mode_button.setText("▶ Work"); self.work_mode_button.setStyleSheet("color: #FFA500; border: none; font-size: 18px; font-weight: bold;"); self.break_mode_button.setText("Break"); self.break_mode_button.setStyleSheet("color: #808080; border: none; font-size: 18px; font-weight: bold;")
        else: self.work_mode_button.setText("Work"); self.work_mode_button.setStyleSheet("color: #808080; border: none; font-size: 18px; font-weight: bold;"); self.break_mode_button.setText("▶ Break"); self.break_mode_button.setStyleSheet("color: #FFA500; border: none; font-size: 18px; font-weight: bold;")
    def switch_mode(self, to_work):
        if not self.is_paused: return
        self.stop_media(); self.is_work_time = to_work; self.current_time = self.remaining_work_time if to_work else self.remaining_break_time; self.update_display(); self.update_mode_indicator(); self.play_next_media()
        if self.media_player.get_media(): self.media_player.pause()
    def set_mode_work(self): self.switch_mode(True)
    def set_mode_break(self): self.switch_mode(False)
    def set_work_time(self, value):
        self.work_time = value * 60
        if self.is_work_time and self.is_paused: self.remaining_work_time = self.work_time; self.current_time = self.remaining_work_time; self.update_display()
    def set_break_time(self, value):
        self.break_time = value * 60
        if not self.is_work_time and self.is_paused: self.remaining_break_time = self.break_time; self.current_time = self.remaining_break_time; self.update_display()
    def start_timer(self):
        if self.is_paused:
            self.is_paused = False
            self.timer.start(1000)

        if self.current_media_path and any(self.current_media_path.lower().endswith(ext) for ext in self.video_extensions):
            if not self.video_window.isVisible():
                self.video_window.show()

        if self.media_player.get_media():
            self.media_player.play()
        else:
            self.play_next_media()
    def pause_timer(self):
        if not self.is_paused: self.is_paused = True; self.timer.stop()
        if self.current_media_path and self.media_player.is_playing():
            time_ms = self.media_player.get_time()
            if self.is_work_time: self.work_media_pos[self.current_media_path] = time_ms
            else: self.break_media_pos[self.current_media_path] = time_ms
        self.media_player.pause()
        if self.is_work_time: self.remaining_work_time = self.current_time
        else: self.remaining_break_time = self.current_time
    def reset_timer(self):
        self.is_paused = True
        self.timer.stop()
        self.is_work_time = True
        self.remaining_work_time = self.work_time
        self.remaining_break_time = self.break_time
        self.current_time = self.work_time
        self.update_display()
        self.update_mode_indicator()
        self.stop_media()
        self.work_playlist.clear()
        self.break_playlist.clear()
        self.work_media_pos.clear()
        self.break_media_pos.clear()
        self.update_playlists()
    def update_timer(self):
        self.current_time -= 1
        if self.current_time < 0:
            if self.current_media_path and self.media_player.is_playing():
                time_ms = self.media_player.get_time()
                if self.is_work_time: self.work_media_pos[self.current_media_path] = time_ms
                else: self.break_media_pos[self.current_media_path] = time_ms
            if self.is_work_time: self.is_work_time = False; self.current_time = self.break_time; self.remaining_break_time = self.break_time
            else: self.is_work_time = True; self.current_time = self.work_time; self.remaining_work_time = self.work_time
            self.update_mode_indicator(); self.play_next_media()
        else:
            if self.is_work_time: self.remaining_work_time = self.current_time
            else: self.remaining_break_time = self.current_time
        self.update_display()
    def update_display(self):
        mins, secs = divmod(self.current_time, 60)
        self.timer_label.setText(f'{mins:02d}:{secs:02d}')

    def browse_file(self):
        filepaths, _ = QFileDialog.getOpenFileNames(self, "Select Media Files")
        if filepaths:
            self.youtube_input.setText(",".join(filepaths))

    def add_to_playlist(self, playlist, widget):
        paths = self.youtube_input.text().split(",")
        for path in filter(None, map(str.strip, paths)):
            playlist.append(path)
            widget.addItem(os.path.basename(path))
            if path.startswith("http"):
                self.download_queue.append(path)
        self.youtube_input.clear()
        if self.download_queue:
            self.start_download()
    def add_to_work_playlist(self): self.add_to_playlist(self.work_playlist, self.work_playlist_widget)
    def add_to_break_playlist(self): self.add_to_playlist(self.break_playlist, self.break_playlist_widget)
    def start_download(self):
        if self.download_queue: url = self.download_queue.pop(0); self.status_label.setText(f'Downloading {url}...'); self.downloader = Downloader(url, self.audio_only_checkbox.isChecked()); self.thread = Thread(target=self.downloader.run); self.downloader.progress.connect(self.update_download_progress); self.downloader.finished.connect(self.download_finished); self.thread.start()
    def update_download_progress(self, percentage): self.status_label.setText(f'Downloading... {percentage}%')
    def download_finished(self, filename, title, original_url):
        if filename:
            self.status_label.setText(f"Downloaded '{title}'")
            for i, item in enumerate(self.work_playlist):
                if item == original_url: self.work_playlist[i] = filename; self.work_playlist_widget.item(i).setText(title); break
            for i, item in enumerate(self.break_playlist):
                if item == original_url: self.break_playlist[i] = filename; self.break_playlist_widget.item(i).setText(title); break
        else: self.status_label.setText(f"Download failed for {original_url}")
        self.start_download()
    def play_next_media(self): 
        playlist = self.work_playlist if self.is_work_time else self.break_playlist
        if playlist: 
            self.play_media(playlist[0])
        else: self.stop_media()
    def media_finished(self, event):
        playlist = self.work_playlist if self.is_work_time else self.break_playlist
        if playlist and self.current_media_path in playlist:
            if self.is_work_time: self.work_media_pos[self.current_media_path] = 0
            else: self.break_media_pos[self.current_media_path] = 0
            index = playlist.index(self.current_media_path)
            if index + 1 < len(playlist): self.play_media(playlist[index + 1])
            else: self.stop_media()
    def skip_forward(self):
        playlist = self.work_playlist if self.is_work_time else self.break_playlist
        if not self.current_media_path or self.current_media_path not in playlist: return
        if self.is_work_time: self.work_media_pos[self.current_media_path] = 0
        else: self.break_media_pos[self.current_media_path] = 0
        index = playlist.index(self.current_media_path)
        if index + 1 < len(playlist): self.play_media(playlist[index + 1])
        else: self.stop_media()
    def skip_back(self):
        playlist = self.work_playlist if self.is_work_time else self.break_playlist
        if not self.current_media_path or self.current_media_path not in playlist: return
        if self.media_player.get_time() > 3000: self.play_media(self.current_media_path)
        else:
            index = playlist.index(self.current_media_path)
            if index > 0:
                if self.is_work_time: self.work_media_pos[self.current_media_path] = 0
                else: self.break_media_pos[self.current_media_path] = 0
                self.play_media(playlist[index - 1])
            else: self.play_media(self.current_media_path)
    def update_playlists(self):
        self.work_playlist_widget.clear(); self.work_playlist_widget.addItems([os.path.basename(p) for p in self.work_playlist]); self.break_playlist_widget.clear(); self.break_playlist_widget.addItems([os.path.basename(p) for p in self.break_playlist])
    def shuffle_playlist(self, playlist): random.shuffle(playlist); self.update_playlists()
    def shuffle_work_playlist(self): self.shuffle_playlist(self.work_playlist)
    def shuffle_break_playlist(self): self.shuffle_playlist(self.break_playlist)
    def reset_work_playlist(self):
        if self.is_work_time and self.current_media_path in self.work_playlist: self.stop_media()
        self.work_playlist.clear(); self.work_media_pos.clear(); self.update_playlists()
    def reset_break_playlist(self):
        if not self.is_work_time and self.current_media_path in self.break_playlist: self.stop_media()
        self.break_playlist.clear(); self.break_media_pos.clear(); self.update_playlists()
    def toggle_always_on_top(self, state):
        current_flags = self.video_window.windowFlags()
        if state == Qt.Checked.value: self.video_window.setWindowFlags(current_flags | Qt.WindowStaysOnTopHint)
        else: self.video_window.setWindowFlags(current_flags & ~Qt.WindowStaysOnTopHint)
        if self.video_window.isVisible(): self.video_window.show(); self.is_vlc_attached = False; QTimer.singleShot(100, self.attach_vlc_to_window)
    def save_session(self):
        session = { "work_time": self.work_time, "break_time": self.break_time, "work_playlist": self.work_playlist, "break_playlist": self.break_playlist, "work_media_pos": self.work_media_pos, "break_media_pos": self.break_media_pos, "volume": self.volume_slider.value(), "always_on_top": self.always_on_top_checkbox.isChecked(), "main_window_geometry": self.saveGeometry().toBase64().data().decode('ascii'), "video_window_geometry": self.video_window.saveGeometry().toBase64().data().decode('ascii') };
        with open(CONFIG_FILE, "w") as f: json.dump(session, f, indent=4)
    def load_session(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    session = json.load(f)
                    self.work_time = session.get("work_time", 25 * 60)
                    self.break_time = session.get("break_time", 5 * 60)
                    self.work_slider.setValue(self.work_time // 60)
                    self.break_slider.setValue(self.break_time // 60)
                    self.remaining_work_time = self.work_time
                    self.remaining_break_time = self.break_time
                    self.work_playlist = session.get("work_playlist", [])
                    self.break_playlist = session.get("break_playlist", [])
                    self.work_media_pos = session.get("work_media_pos", {})
                    self.break_media_pos = session.get("break_media_pos", {})
                    volume = session.get("volume", 75)
                    self.volume_slider.setValue(volume)
                    self.set_volume(volume)
                    always_on_top = session.get("always_on_top", False)
                    self.always_on_top_checkbox.setChecked(always_on_top)
                    if geom := session.get("main_window_geometry"): self.restoreGeometry(QByteArray.fromBase64(geom.encode('ascii')))
                    if geom := session.get("video_window_geometry"): self.video_window.restoreGeometry(QByteArray.fromBase64(geom.encode('ascii')))
                    self.update_playlists()
                    self.current_time = self.remaining_work_time
                    self.update_display()
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not decode {CONFIG_FILE} or key missing. Starting fresh. Error: {e}")
                self.volume_slider.setValue(75)
    def closeEvent(self, event):
        self.save_session()
        self.video_window.allow_close()
        self.video_window.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PomodoroTimer()
    window.show()
    sys.exit(app.exec())