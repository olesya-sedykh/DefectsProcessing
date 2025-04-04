from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTextEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QAction,
    QDesktopWidget, QFrame, QLineEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, 
    QSizePolicy, QHeaderView, QPushButton, QStyledItemDelegate, 
    QFileDialog, QGraphicsView, QGraphicsScene, QDialog, QApplication, QGraphicsProxyWidget
)
from PyQt5.QtGui import (
    QPalette, QColor, QFont, QIntValidator, 
    QDoubleValidator, QRegExpValidator, QRegularExpressionValidator,
    QPixmap, QImage, QIcon, QTransform, QPainter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRegExp, QRegularExpression, QSize, QRectF, QUrl

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

import os
import cv2

os.environ["QT_MEDIA_BACKEND"] = "windowsmediafoundation"

from PreviewWindow import PreviewWindow
from ParameterDialog import ParameterDialog

class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = "Исправление дефектов"
        self.width = 1200
        self.height = 800
        self.background_color = 'white'

        self.setWindowTitle(self.title)
        self.setGeometry(150, 150, self.width, self.height)
        self.setStyleSheet(f"background-color: {self.background_color};")
        self.center()

        # шрифт
        self.font = QFont()
        self.font.setPointSize(10)

        # главный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # горизонтальный layout для разделения на левую и правую части
        main_layout = QHBoxLayout(central_widget)

        # =========================================================================
        # ЛЕВАЯ СТОРОНА
        # =========================================================================

        # левая часть
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # выпадающий список для выбора вида обрабатываемого файла
        self.file_type = QComboBox()
        self.file_type.addItem("Обработка изображения")
        self.file_type.addItem("Обработка датасета")
        self.file_type.addItem("Обработка видео")
        # self.file_type.setFixedHeight(40)
        self.file_type.setMinimumHeight(40)
        self.file_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.file_type.setFont(self.font)
        left_layout.addWidget(self.file_type)

        # область для загрузки и отображения файлов
        self.file_widget = QWidget()
        self.file_widget.setStyleSheet("background-color: lightgray; border-radius: 20px;")
        # self.file_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.file_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.file_layout = QVBoxLayout(self.file_widget)
        left_layout.addWidget(self.file_widget)
        # left_layout.addStretch(60)

        # кнопка загрузки
        self.create_load_button()

        # выпадающий список для выбора способа исправления дефектов
        self.defects_processing_type = QComboBox()
        self.defects_processing_type.addItem("Исправить все дефекты")
        self.defects_processing_type.addItem("Исправить основной дефект")
        # self.defects_processing_type.setFixedHeight(40)
        self.defects_processing_type.setMinimumHeight(40)
        self.defects_processing_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.defects_processing_type.setFont(self.font)
        left_layout.addWidget(self.defects_processing_type)
        
        # выпадающий список для выбора способа обработки
        self.process_type = QComboBox()
        self.process_type.addItem("Автоматическая обработка")
        self.process_type.addItem("Ручная обработка")
        # self.process_type.setFixedHeight(40)
        self.process_type.setMinimumHeight(40)
        self.process_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.process_type.setFont(self.font)
        left_layout.addWidget(self.process_type)
        self.process_type.currentIndexChanged.connect(self.update_methods_table)

        # таблица с методами исправления дефектов
        self.methods_table = QTableWidget()
        self.methods_table.setRowCount(4)
        self.methods_table.setColumnCount(2)
        self.methods_table.setHorizontalHeaderLabels(["Дефект", "Метод обработки"])
        self.methods_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # растяжение столбцов по ширине таблицы
        self.methods_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.methods_table.horizontalHeader().setStretchLastSection(True)
        self.methods_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.methods_table.verticalHeader().setVisible(False)
        # self.methods_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.methods_table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.methods_table.setEditTriggers(QTableWidget.NoEditTriggers) # запрет редактирования
        self.methods_table.setStyleSheet("""
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 5px;
                font-weight: bold;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
            }
        """)
        self.methods_table.setShowGrid(True)
        self.methods_table.setGridStyle(Qt.SolidLine)
        self.methods_table.resizeRowsToContents()
        
        # методы для автоматической обработки
        self.automatic_methods = [
            "Фильтр Лапласа",
            "Алгоритм CLAHE",
            "Адаптивный метод",
            "Фильтр среднего значения"
        ]
        
        # методы для ручной обработки
        self.manual_options = {
            "Размытие": ["Фильтр Лапласа", "Фильтр Гаусса", "Фильтр Собеля"],
            "Низкая контрастность": ["Алгоритм CLAHE", "Гистограммное выравнивание", "Гамма-коррекция"],
            "Блики": ["Адаптивный метод", "Метод на основе морфологии", "Пороговая обработка"],
            "Шум": ["Фильтр среднего значения", "Медианный фильтр", "Фильтр Гаусса"]
        }
        
        # параметры по умолчанию для методов
        self.method_parameters = {
            "Фильтр Лапласа": {"Размер ядра": 3, "Масштаб": 1.0, "Дельта": 0},
            "Алгоритм CLAHE": {"Лимит контраста": 2.0, "Размер тайла": 8},
            "Адаптивный метод": {"Размер блока": 11, "Константа": 2},
            "Фильтр среднего значения": {"Размер ядра": 5},
            "Фильтр Гаусса": {"Размер ядра": 3, "Сигма": 1.0},
            "Фильтр Собеля": {"Размер ядра": 3, "Масштаб": 1.0, "Дельта": 0},
            "Гистограммное выравнивание": {},
            "Гамма-коррекция": {"Гамма": 1.0},
            "Метод на основе морфологии": {"Размер ядра": 3, "Операция": "Открытие"},
            "Пороговая обработка": {"Порог": 127, "Максимальное значение": 255},
            "Медианный фильтр": {"Размер ядра": 3}
        }
        
        print("Before update")
        self.update_methods_table()
        print("After update")

        left_layout.addWidget(self.methods_table)

        # кнопка для обработки дефектов
        self.process_button = QPushButton("Исправить дефекты")
        self.process_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.process_button.setStyleSheet("background-color: gray; border-radius: 10px; padding: 10px;")
        self.process_button.setFont(self.font)
        # self.process_button.clicked.connect(self.processing)
        left_layout.addWidget(self.process_button)

        # распределение размеров элементов по высоте для левой стороны
        left_layout.setStretch(0, 10)
        left_layout.setStretch(1, 35)  # 30% для file_widget (первый добавленный элемент)
        left_layout.setStretch(2, 10)   # 5% для defects_processing_type
        left_layout.setStretch(3, 10)   # 5% для process_type
        left_layout.setStretch(4, 25)  # 60% для methods_table
        left_layout.setStretch(5, 10)

        main_layout.addWidget(left_widget, stretch=50)

        # разделитель между левой и правой частью
        main_separator = QFrame()
        main_separator.setFrameShape(QFrame.VLine)  # Вертикальная линия
        main_layout.addWidget(main_separator)

        # =========================================================================
        # ПРАВАЯ СТОРОНА
        # =========================================================================

        # правая сторона
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        main_layout.addWidget(right_widget, stretch=50)

    def center(self) -> None:
        """
        Устанавливает окно по центру экрана.
        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def load_file(self):
        """
        Открывает диалоговое окно для загрузки файла или выбора папки
        в зависимости от выбранного типа обработки.
        """
        processing_type = self.file_type.currentText()

        if processing_type == "Обработка изображения":
            options = QFileDialog.Options()
            self.file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите файл изображения",
                "",
                "Images (*.png *.jpg);;All Files (*)",
                options=options
            )
        elif processing_type == "Обработка видео":
            options = QFileDialog.Options()
            self.file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите файл видео",
                "",
                "Videos (*.mp4 *.avi);;All Files (*)",
                options=options
            )
        elif processing_type == "Обработка датасета":
            self.file_path = QFileDialog.getExistingDirectory(
                self,
                "Выберите папку с датасетом"
            )

        if self.file_path:
            self.update_display()

    def update_display(self):
        """
        Определяет заполнение области после загрузки файла.
        """
        if self.file_path:
            processing_type = self.file_type.currentText()
            if processing_type == "Обработка изображения":
                self.display_image()
                # self.load_button.hide()
                # self.view_button.show()
            elif processing_type == "Обработка датасета":
                self.display_dataset()
                # self.load_button.hide()
                # self.view_button.show()
            elif processing_type == "Обработка видео":
                self.display_video()
                # self.load_button.hide()
                # self.view_button.show()

    # =========================================================================
    # ФУНКЦИИ ДЛЯ ОТОБРАЖЕНИЯ КАРТИНКИ
    # =========================================================================
    
    def display_image(self):
        """
        Отображает изображение.
        """
        # загружаем изображение
        self.original_pixmap = QPixmap(self.file_path) # self.original_pixmap - это непосредственно изображение
        if self.original_pixmap.isNull():
            error_widget = QLabel()
            error_widget.setText("Ошибка: не удалось загрузить изображение")
            error_widget.setStyleSheet("color: red;")
            error_widget.setAlignment(Qt.AlignCenter)
            self.file_layout.addWidget(error_widget)
            return
        
        # удаление предыдущих виджетов, чтобы они не накапливались
        self.delete_files_widgets()

        # контейнер для изображения
        self.image_container = QWidget() # "рамка" (область) для изоражения
        self.image_container_layout = QVBoxLayout(self.image_container) # правила размещения внутри области (по вертикали)
        # self.image_container.setLayout(QVBoxLayout()) # правила размещения внутри области (по вертикали)
        self.image_container.layout().setContentsMargins(0, 0, 0, 0) # содержимое должно занимать все пространство
        
        # QLabel для изображения
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored) # игнорировать рекомендуемые размеры
        self.image_label.setStyleSheet("background-color: #f0f0f0;")
        
        # создаем overlay виджет для кнопок
        self.overlay_widget = QWidget(self.image_label) # создаем виджет поверх виджета для картинки
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False) # именно этот, а не родительский, виджет будет реагировать на мышь
        overlay_layout = QHBoxLayout(self.overlay_widget) # расположение по горизонтали
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_widget.setStyleSheet("background: transparent; border: none;") # делаем прозрачным фон виджета для кнопок
        # overlay_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
        # кнопка просмотра (глаз)
        self.view_button = QPushButton("👁")
        self.view_button.setFixedSize(30, 30)
        self.view_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border-radius: 15px;
                border: 1px solid gray;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        self.view_button.clicked.connect(self.view_content)
        
        # кнопка закрытия (крестик)
        self.close_button = QPushButton("×")
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
        self.close_button.clicked.connect(self.clear_image)
        
        # добавляем кнопки в виджет
        overlay_layout.addWidget(self.view_button)
        overlay_layout.addWidget(self.close_button)
        
        # устанавливаем размер виджета для кнопок (подгоняет размер под содержимое)
        self.overlay_widget.adjustSize()
        
        # добавляем элементы в контейнер для изображения
        self.image_container_layout.addWidget(self.image_label)
        self.file_layout.addWidget(self.image_container)
        
        # устанавливаем обработчик изменения размера изображения
        self.image_label.resizeEvent = lambda e: self.update_image_display()

    def update_cropped_image(self):
        """
        Обновляет отображаемую часть изображения (среднюю часть).
        """
        if hasattr(self, 'original_pixmap'): # если в принципе изображение есть
            # получаем текущие размеры виджета для изображения
            width = self.image_label.width()
            height = self.image_label.height()
            
            # размеры самого изображения
            img_width = self.original_pixmap.width()
            img_height = self.original_pixmap.height()
            
            # координаты для вырезания центральной части
            crop_x = max(0, (img_width - width) // 2)
            crop_y = max(0, (img_height - height) // 2)
            crop_width = min(width, img_width)
            crop_height = min(height, img_height)
            
            # вырезаем и масштабируем
            cropped = self.original_pixmap.copy(crop_x, crop_y, crop_width, crop_height) # создает вырезанное изображение, принимает координаты левого верхнего угла и длину/ширину
            scaled = cropped.scaled(
                width, height, # необходимые размеры
                Qt.IgnoreAspectRatio, # растягивает по заданным размерам
                Qt.SmoothTransformation # сглаживание
            )
            self.image_label.setPixmap(scaled)

    def update_buttons_position(self):
        """
        Обновляет позицию кнопок в правом верхнем углу.
        """
        if hasattr(self, 'overlay_widget'):
            img_width = self.image_label.width()
            self.overlay_widget.move(img_width - 75, 10)  # 75 = 30+30+15 отступ

    def update_image_display(self):
        """
        Обработчик изменения размера изображения (или окна).
        """
        # обрезаем изображение для отображения
        self.update_cropped_image()
        # обновляем позицию кнопок
        self.update_buttons_position()

    def create_load_button(self):
        # контейнер для кнопки загрузки
        self.load_button_container = QWidget()
        load_button_layout = QVBoxLayout(self.load_button_container)

        # растяжение перед кнопкой (прижимает кнопку к нижнему краю)
        load_button_layout.addStretch()

        # горизонтальный layout для центрирования кнопки
        button_horizontal_layout = QHBoxLayout()

        # пространство слева от кнопки
        button_horizontal_layout.addStretch()

        # кнопка загрузки
        self.load_button = QPushButton('Загрузить\nфайл')
        self.load_button.setFixedSize(130, 150)
        self.load_button.setStyleSheet("background-color: gray; border-radius: 10px; padding: 10px;")
        self.load_button.setFont(self.font)
        self.load_button.clicked.connect(self.load_file)
        button_horizontal_layout.addWidget(self.load_button)

        # пространство справа от кнопки
        button_horizontal_layout.addStretch()

        # добавляем горизонтальный layout в вертикальный
        load_button_layout.addLayout(button_horizontal_layout)

        # добавляем контейнер с кнопкой в file_layout
        self.file_layout.addWidget(self.load_button_container)
    
    def delete_files_widgets(self):
        """
        Удаляет виджеты из области отображения файлов.
        """
        # удаление предыдущих виджетов, чтобы они не накапливались
        for i in reversed(range(self.file_layout.count())):
            widget = self.file_layout.itemAt(i).widget()
            if widget: 
                widget.deleteLater()
    
    def clear_image(self):
        """
        Удаляет изображение из области по кнопке закрытия.
        """
        if hasattr(self, 'overlay_widget'):
            self.delete_files_widgets()

        # опять создаем контейнер для кнопки загрузки и саму кнопку
        self.create_load_button()

    def view_content(self):
        """
        Открывает окно просмотра с полным изображением.
        """
        if hasattr(self, 'file_path') and self.file_path:
            self.preview_window = PreviewWindow(self.file_path)
            self.preview_window.show()

    # =========================================================================
    # ФУНКЦИИ ДЛЯ ОТОБРАЖЕНИЯ ВИДЕО
    # =========================================================================

    def display_video(self):
        """
        Отображает видео в маленьком окошке с использованием OpenCV.
        """
        # Проверяем существование файла
        if not os.path.exists(self.file_path):
            error_widget = QLabel()
            error_widget.setText("Ошибка: файл не найден")
            error_widget.setStyleSheet("color: red;")
            error_widget.setAlignment(Qt.AlignCenter)
            self.file_layout.addWidget(error_widget)
            return
        
        # Удаление предыдущих виджетов
        self.delete_files_widgets()

        # Контейнер для видео
        self.video_container = QWidget()
        self.video_container_layout = QVBoxLayout(self.video_container)
        self.video_container_layout.setContentsMargins(0, 0, 0, 0)

        # Виджет для отображения видео (теперь это QLabel)
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #f0f0f0;")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Инициализация OpenCV VideoCapture
        self.cap = cv2.VideoCapture(self.file_path)
        if not self.cap.isOpened():
            error_widget = QLabel()
            error_widget.setText("Ошибка: не удалось открыть видео")
            error_widget.setStyleSheet("color: red;")
            error_widget.setAlignment(Qt.AlignCenter)
            self.file_layout.addWidget(error_widget)
            return

        # Таймер для обновления кадров
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_frame)
        self.is_playing = False

        # Overlay виджет для кнопок
        self.overlay_widget = QWidget(self.video_label)
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        overlay_layout = QHBoxLayout(self.overlay_widget)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_widget.setStyleSheet("background: transparent; border: none;")
        
        # Кнопка просмотра
        self.view_button = QPushButton("👁")
        self.view_button.setFixedSize(30, 30)
        self.view_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border-radius: 15px;
                border: 1px solid gray;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        self.view_button.clicked.connect(self.view_content)
        
        # Кнопка закрытия
        self.close_button = QPushButton("×")
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
        self.close_button.clicked.connect(self.clear_video)
        
        # Центральная кнопка воспроизведения
        self.play_button = QPushButton("▶")
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
        self.play_button.clicked.connect(self.toggle_play_video)
        
        # Добавляем кнопки в overlay
        overlay_layout.addWidget(self.view_button)
        overlay_layout.addWidget(self.close_button)
        
        # Центральный layout для кнопки play
        self.center_layout = QHBoxLayout()
        self.center_layout.addStretch()
        self.center_layout.addWidget(self.play_button)
        self.center_layout.addStretch()
        
        # Добавляем элементы в контейнер
        self.video_container_layout.addWidget(self.video_label)
        self.video_container_layout.addLayout(self.center_layout)
        self.file_layout.addWidget(self.video_container)
        
        # Устанавливаем обработчик изменения размера
        self.video_label.resizeEvent = lambda e: self.update_buttons_position()
        
        # Обновляем позиции элементов
        self.update_buttons_position()
        
        # Начинаем воспроизведение
        self.toggle_play_video()

    def update_frame(self):
        """Обновляет текущий кадр видео"""
        ret, frame = self.cap.read()
        if ret:
            # Конвертируем кадр из BGR (OpenCV) в RGB (Qt)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # Масштабируем изображение под размер виджета
            self.video_label.setPixmap(pixmap.scaled(
                self.video_label.size(), 
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        else:
            # Если видео закончилось, возвращаемся в начало
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def toggle_play_video(self):
        """Переключает воспроизведение видео"""
        if self.is_playing:
            self.video_timer.stop()
            self.play_button.setText("▶")
        else:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.video_timer.start(int(1000 / fps))  # Обновляем с частотой кадров видео
            self.play_button.setText("❚❚")
        self.is_playing = not self.is_playing

    def update_buttons_position(self):
        """Обновляет позицию кнопок управления"""
        if hasattr(self, 'overlay_widget') and hasattr(self, 'video_label'):
            label_width = self.video_label.width()
            self.overlay_widget.move(label_width - 75, 10)  # 75 = 30+30+15 отступ
            
            # Центрируем кнопку play
            if hasattr(self, 'play_button'):
                self.play_button.move(
                    self.video_label.width() // 2 - 30,
                    self.video_label.height() // 2 - 30
                )

    def clear_video(self):
        """Очищает видео и освобождает ресурсы"""
        if hasattr(self, 'video_timer'):
            self.video_timer.stop()
        if hasattr(self, 'cap'):
            self.cap.release()
        self.delete_files_widgets()
        self.create_load_button()


    # def update_methods_table(self):
    #     """
    #     Обновляет заполнение таблицы.
    #     """
    #     processing_type = self.process_type.currentText()
    #     print('processing_type', processing_type)

    #     # полное очищение таблицы перед новым заполнением
    #     self.methods_table.clearContents()

    #     # заполнение строк таблицы дефектами
    #     defects = ["Размытие", "Низкая контрастность", "Блики", "Шум"]
    #     for row, defect in enumerate(defects):
    #         item = QTableWidgetItem(defect) # создание ячейки
    #         item.setTextAlignment(Qt.AlignCenter) # выравнивание ячейки
    #         font = item.font()
    #         font.setBold(True)  # делаем текст жирным
    #         item.setFont(font)
    #         self.methods_table.setItem(row, 0, item) # помещение ячейки в таблицу в строку row, столбец 0
        
    #     for row in range(self.methods_table.rowCount()):
    #         # в случае автоматической обработки просто показываем названия методов
    #         if self.process_type.currentIndex() == 0:
    #             method_item = QTableWidgetItem(self.automatic_methods[row])
    #             method_item.setTextAlignment(Qt.AlignCenter)
    #             self.methods_table.setItem(row, 1, method_item)
            
    #         # в случае ручной обработки для каждого дефекта можно выбрать метод
    #         else:
    #             defect = self.methods_table.item(row, 0).text()
    #             combo = QComboBox()
    #             combo.addItems(self.manual_options[defect])
    #             combo.setCurrentIndex(0)
    #             self.methods_table.setCellWidget(row, 1, combo)
        
    #     self.methods_table.resizeRowsToContents()

    def update_methods_table(self):
        """
        Обновляет таблицу методов с кнопками параметров для каждого метода
        """
        print('Режим обработки:', self.process_type.currentText())
        
        # Полная очистка таблицы
        self.methods_table.clearContents()
        
        # Стиль для кнопок шестерёнок
        gear_style = """
            QPushButton {
                border: none;
                background: transparent;
                padding: 0px;
            }
            QPushButton:hover {
                background: #e0e0e0;
                border-radius: 2px;
            }
        """
        
        # Заполняем таблицу
        defects = ["Размытие", "Низкая контрастность", "Блики", "Шум"]
        for row, defect in enumerate(defects):
            # Ячейка с дефектом (первый столбец)
            item = QTableWidgetItem(defect)
            item.setTextAlignment(Qt.AlignCenter)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            self.methods_table.setItem(row, 0, item)
            
            # Создаем контейнер для второго столбца
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(5, 0, 5, 0)
            layout.setSpacing(5)
            
            if self.process_type.currentIndex() == 0:  # Автоматический режим
                # Метод обработки
                method_label = QLabel(self.automatic_methods[row])
                method_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(method_label, stretch=1)
                
                # Кнопка шестерёнки (только просмотр)
                gear_btn = QPushButton()
                gear_btn.setText("⚙")
                gear_btn.setFont(QFont("Arial", 10))
                gear_btn.setFixedSize(24, 24)
                gear_btn.setStyleSheet(gear_style)
                gear_btn.clicked.connect(lambda _, r=row: self.show_parameters(r, False))
                layout.addWidget(gear_btn)
                
            else:  # Ручной режим
                # Выпадающий список методов
                combo = QComboBox()
                combo.addItems(self.manual_options[defect])
                combo.setCurrentIndex(0)
                combo.setStyleSheet("QComboBox { padding: 2px; }")
                layout.addWidget(combo, stretch=1)
                
                # Кнопка шестерёнки (редактирование)
                gear_btn = QPushButton()
                gear_btn.setText("⚙")
                gear_btn.setFont(QFont("Arial", 10))
                gear_btn.setFixedSize(24, 24)
                gear_btn.setStyleSheet(gear_style)
                gear_btn.clicked.connect(lambda _, r=row: self.show_parameters(r, True))
                layout.addWidget(gear_btn)
            
            # Устанавливаем контейнер в таблицу
            self.methods_table.setCellWidget(row, 1, container)
        
        # Настройки внешнего вида таблицы
        self.methods_table.resizeRowsToContents()
        self.methods_table.setMinimumHeight(160)  # Минимальная высота для 4 строк

    def show_parameters(self, row, editable):
        """Shows parameters dialog for the selected method"""
        defect = self.methods_table.item(row, 0).text()
        
        if self.process_type.currentText() == "Автоматическая обработка":
            method_name = self.automatic_methods[row]
        else:
            combo = self.methods_table.cellWidget(row, 1).findChild(QComboBox)
            method_name = combo.currentText()
        
        parameters = self.method_parameters.get(method_name, {}).copy()
        
        dialog = ParameterDialog(method_name, parameters, editable)
        if dialog.exec_() == QDialog.Accepted and editable:
            # Save changed parameters for manual processing
            self.method_parameters[method_name] = dialog.get_parameters()