from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTextEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QAction,
    QDesktopWidget, QFrame, QLineEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, 
    QSizePolicy, QHeaderView, QPushButton, QStyledItemDelegate, 
    QFileDialog, QGraphicsView, QGraphicsScene, QDialog, QApplication, QGraphicsProxyWidget,
    QMessageBox, QStyle, QScrollArea
)
from PyQt5.QtGui import (
    QPalette, QColor, QFont, QIntValidator, 
    QDoubleValidator, QRegExpValidator, QRegularExpressionValidator,
    QPixmap, QImage, QIcon, QTransform, QPainter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRegExp, QRegularExpression, QSize, QRectF, QUrl

from frontend.QFlowLayout import QFlowLayout

import os
import cv2
from pathlib import Path
from functools import partial
import shutil
import glob

class PreviewWindowDataset(QMainWindow):
    def __init__(self, dataset_path):
        super().__init__()
        self.dataset_path = dataset_path
        self.current_image_index = 0
        self.image_files = self.get_image_files()
        
        self.init_ui()
        
    def get_image_files(self):
        """
        Получает список изображений в датасете.
        """
        extensions = ['*.png', '*.jpg', '*.jpeg']
        image_files = []
        for ext in extensions:
            image_files.extend(glob.glob(os.path.join(self.dataset_path, ext)))
        return sorted(image_files)
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Просмотр датасета")
        self.resize(800, 650)
        
        # Главный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Виджет для миниатюр
        self.thumbnails_widget = QWidget()
        self.thumbnails_layout = QFlowLayout()
        self.thumbnails_widget.setLayout(self.thumbnails_layout)
        
        # Scroll area для миниатюр
        scroll = QScrollArea()
        scroll.setWidget(self.thumbnails_widget)
        scroll.setWidgetResizable(True)
        
        main_layout.addWidget(scroll)
        
        # Заполняем миниатюры
        self.load_thumbnails()
        
    def load_thumbnails(self):
        """Загружает миниатюры изображений"""
        # Очищаем предыдущие миниатюры
        for i in reversed(range(self.thumbnails_layout.count())): 
            self.thumbnails_layout.itemAt(i).widget().setParent(None)
        
        # Загружаем новые миниатюры
        for i, image_path in enumerate(self.image_files):
            thumbnail = ThumbnailWidget(image_path)
            thumbnail.doubleClicked.connect(lambda idx=i: self.show_full_image(idx))
            self.thumbnails_layout.addWidget(thumbnail)
    
    def show_full_image(self, index):
        """Показывает изображение в полном размере"""
        self.current_image_index = index
        self.image_viewer = ImageViewerWindow(self.image_files, self.current_image_index)
        self.image_viewer.show()


class ThumbnailWidget(QLabel):
    doubleClicked = pyqtSignal()
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.setFixedSize(150, 150)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 1px solid gray;")
        
        self.load_image()
        
    def load_image(self):
        """Загружает изображение для миниатюры"""
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(
                self.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
    
    def mouseDoubleClickEvent(self, event):
        """Обработчик двойного клика"""
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class ImageViewerWindow(QMainWindow):
    def __init__(self, image_files, current_index):
        super().__init__()
        self.image_files = image_files
        self.current_index = current_index
        
        self.init_ui()
        self.load_image()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Просмотр изображения")
        self.resize(800, 600)
        
        # Главный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Label для изображения
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        # Кнопки навигации
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        
        self.prev_button = QPushButton("← Назад")
        self.prev_button.clicked.connect(self.show_prev_image)
        nav_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Вперед →")
        self.next_button.clicked.connect(self.show_next_image)
        nav_layout.addWidget(self.next_button)
        
        layout.addWidget(nav_widget)
        
    def load_image(self):
        """Загружает текущее изображение"""
        if 0 <= self.current_index < len(self.image_files):
            pixmap = QPixmap(self.image_files[self.current_index])
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                ))
                
            # Обновляем состояние кнопок
            self.prev_button.setEnabled(self.current_index > 0)
            self.next_button.setEnabled(self.current_index < len(self.image_files) - 1)
    
    def show_prev_image(self):
        """Показывает предыдущее изображение"""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()
    
    def show_next_image(self):
        """Показывает следующее изображение"""
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.load_image()
    
    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key_Left:
            self.show_prev_image()
        elif event.key() == Qt.Key_Right:
            self.show_next_image()
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        self.load_image()
        super().resizeEvent(event)