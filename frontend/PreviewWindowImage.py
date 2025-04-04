from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class PreviewWindowImage(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Просмотр изображения")
        self.setGeometry(100, 100, 800, 600)

        # Загружаем изображение
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

        # Layout для окна просмотра
        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)
        self.setLayout(layout)