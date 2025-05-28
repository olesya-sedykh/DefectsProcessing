from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QDesktopWidget, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize

class PreviewWindowImage(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Просмотр изображения")
        self.resize(800, 600)
        self.center()
        
        self.image_path = image_path
        self.original_pixmap = QPixmap(image_path)
        
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setMinimumSize(1, 1)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.image_label)
        
        self.update_image()

    def update_image(self):
        """
        Обновляет изображение с учетом текущего размера окна.
        """
        if not self.original_pixmap.isNull():
            # получаем доступный размер (с небольшим отступом)
            available_size = self.image_label.size() - QSize(10, 10)
            
            # масштабируем с сохранением пропорций
            scaled_pixmap = self.original_pixmap.scaled(
                available_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """
        Обработчик изменения размера окна.
        """
        super().resizeEvent(event)
        self.update_image()

    def center(self) -> None:
        """
        Устанавливает окно по центру экрана.
        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())