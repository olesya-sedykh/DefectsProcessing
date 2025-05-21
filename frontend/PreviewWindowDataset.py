from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTextEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QAction,
    QDesktopWidget, QFrame, QLineEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, 
    QSizePolicy, QHeaderView, QPushButton, QStyledItemDelegate, 
    QFileDialog, QGraphicsView, QGraphicsScene, QDialog, QApplication, QGraphicsProxyWidget,
    QMessageBox, QStyle, QScrollArea, QToolButton
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
        
    def keyPressEvent(self, event):
        """Обработка нажатий клавиш для листания изображений"""
        if self.fullscreen_viewer and self.fullscreen_viewer.isVisible():
            # Если открыто полноэкранное окно, передаем управление ему
            self.fullscreen_viewer.keyPressEvent(event)
        else:
            # Листание миниатюр (если нужно)
            super().keyPressEvent(event)
    
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
        self.setFocusPolicy(Qt.StrongFocus)
        
    def init_ui(self):
        """Инициализация интерфейса с простыми стрелочными кнопками"""
        self.setWindowTitle("Просмотр изображения")
        self.original_size = QSize(800, 600)
        self.resize(self.original_size)
        
        # Главный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Кнопка "Назад" (слева)
        self.prev_button = QToolButton()
        self.prev_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.prev_button.setIconSize(QSize(24, 24))
        self.prev_button.clicked.connect(self.show_prev_image)
        main_layout.addWidget(self.prev_button, alignment=Qt.AlignVCenter)
        
        # Область изображения (центр)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.image_label, stretch=1)
        
        # Кнопка "Вперед" (справа)
        self.next_button = QToolButton()
        self.next_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.next_button.setIconSize(QSize(24, 24))
        self.next_button.clicked.connect(self.show_next_image)
        main_layout.addWidget(self.next_button, alignment=Qt.AlignVCenter)
        
        # Простая стилизация кнопок
        self.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 20px;
                background: transparent;
            }
            QToolButton:hover {
                background: rgba(0, 0, 0, 20);
            }
        """)
    
    def load_image(self):
        """Загружает текущее изображение"""
        if 0 <= self.current_index < len(self.image_files):
            pixmap = QPixmap(self.image_files[self.current_index])
            if not pixmap.isNull():
                # Масштабируем под доступный размер QLabel
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            
            self.prev_button.setEnabled(self.current_index > 0)
            self.next_button.setEnabled(self.current_index < len(self.image_files) - 1)
    
    def show_prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()
    
    def show_next_image(self):
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.load_image()
    
    def keyPressEvent(self, event):
        """Обработка клавиш стрелок"""
        if event.key() == Qt.Key_Left:
            self.show_prev_image()
        elif event.key() == Qt.Key_Right:
            self.show_next_image()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
    
    def showEvent(self, event):
        """Устанавливаем фокус при показе окна"""
        self.setFocus()
        super().showEvent(event)
    
    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        self.load_image()