from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton, 
                            QSizePolicy, QHBoxLayout)
from PyQt5.QtGui import QImage, QPixmap, QCursor
from PyQt5.QtCore import Qt, QTimer
import cv2
import os

class PreviewWindowVideo(QWidget):
    def __init__(self, video_path):
        super().__init__()
        self.setWindowTitle("Просмотр видео")
        self.setGeometry(100, 100, 800, 600)
        self.video_path = video_path
        self.cap = None
        self.is_playing = False
        self.video_width = 0  # Переименовываем переменные
        self.video_height = 0
        
        self.setup_ui()
        self.setMouseTracking(True)
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMouseTracking(True)
        
        self.play_button = QPushButton("▶", self)
        self.play_button.setFixedSize(60, 60)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 150);
                border-radius: 30px;
                border: none;
                font-size: 24px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 200);
            }
        """)
        self.play_button.hide()
        self.play_button.clicked.connect(self.toggle_play)
        
        self.close_button = QPushButton("×", self)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border-radius: 15px;
                border: 1px solid gray;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        self.close_button.clicked.connect(self.close)
        
        self.layout.addWidget(self.video_label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.load_video()
        
    def load_video(self):
        if not os.path.exists(self.video_path):
            self.show_error("Файл не найден")
            return
            
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            self.show_error("Не удалось открыть видео")
            return
            
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Используем новое имя
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.toggle_play()
        
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            q_img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
            self.video_label.setPixmap(
                QPixmap.fromImage(q_img).scaled(
                    self.video_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
            )
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
    def toggle_play(self):
        if self.is_playing:
            self.timer.stop()
            self.play_button.setText("▶")
            self.play_button.show()
        else:
            self.timer.start(int(1000 / self.fps))
            self.play_button.setText("❚❚")
            self.play_button.hide()
        self.is_playing = not self.is_playing
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_play()
            
    def enterEvent(self, event):
        if not self.is_playing:
            self.play_button.show()
        self.update_button_positions()
        
    def leaveEvent(self, event):
        if not self.is_playing:
            self.play_button.hide()
            
    def resizeEvent(self, event):
        self.update_button_positions()
        super().resizeEvent(event)
        
    def update_button_positions(self):
        """Исправленный метод с правильными именами переменных"""
        # Используем self.width() и self.height() - методы QWidget
        self.play_button.move(
            (self.width() - self.play_button.width()) // 2,
            (self.height() - self.play_button.height()) // 2
        )
        
        self.close_button.move(
            self.width() - self.close_button.width() - 10,
            10
        )
        
    def show_error(self, message):
        error_label = QLabel(message, self)
        error_label.setStyleSheet("color: red; font-size: 16px;")
        error_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(error_label)
        
    def closeEvent(self, event):
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
        super().closeEvent(event)