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
from pathlib import Path

os.environ["QT_MEDIA_BACKEND"] = "windowsmediafoundation"

from frontend.PreviewWindowImage import PreviewWindowImage
from frontend.PreviewWindowVideo import PreviewWindowVideo
from ParameterDialog import ParameterDialog
from backend.ProcessingClass import ProcessingClass

PROJECT_ROOT = Path(__file__).parent.parent
MODEL_PATH = PROJECT_ROOT / 'mobile_net_model.h5'
OUTPUT_PATH = PROJECT_ROOT / 'temp'

class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = "Исправление дефектов"
        self.width = 1200
        self.height = 900
        self.background_color = 'white'

        self.setWindowTitle(self.title)
        self.setGeometry(150, 150, self.width, self.height)
        self.setStyleSheet(f"background-color: {self.background_color};")
        self.center()

        self.defects = ["Размытие", "Контрастность", "Блики", "Шум"]

        # шрифт
        self.font = QFont()
        self.font.setPointSize(10)

        # стиль кнопок
        self.buttons_style = """
            QPushButton {
                background-color: #F5F5F5;
                border: 2px solid #96C896;
                padding: 10px;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #e0dede;
            }
            QPushButton:disabled {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                color: #B0B0B0;
            }
            QPushButton:pressed {
                background-color: #C8E6C8;
            }
        """

        # главный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # горизонтальный layout для разделения на левую и правую части
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)  # отступы по краям
        main_layout.setSpacing(10)  # расстояние между элементами

        # =========================================================================
        # ЛЕВАЯ СТОРОНА
        # =========================================================================

        # левая часть
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # выпадающий список для выбора вида обрабатываемого файла
        self.file_type = QComboBox()
        self.file_type.addItem("Обработка изображения")
        self.file_type.addItem("Обработка датасета")
        self.file_type.addItem("Обработка видео")
        self.file_type.setFixedHeight(45)
        self.file_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.file_type.setFont(self.font)
        left_layout.addWidget(self.file_type)

        # область для загрузки и отображения файлов
        self.file_widget = QWidget()
        self.file_widget.setObjectName("file_widget")
        self.file_widget.setStyleSheet("""
            QWidget#file_widget {
                background-color: white;
                border-radius: 20px;
                border: 2px solid #96C896;
            }
        """)
        self.file_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.file_widget.setMinimumHeight(200)
        self.file_layout = QVBoxLayout(self.file_widget)
        left_layout.addWidget(self.file_widget)

        # кнопка загрузки
        self.create_load_button()

        # кнопка для скачивания исходной размеченной картинки
        self.download_detect_button = QPushButton("Скачать размеченное изображение")
        self.download_detect_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.download_detect_button.setFixedHeight(50)
        self.download_detect_button.setStyleSheet(self.buttons_style)
        self.download_detect_button.setFont(self.font)
        left_layout.addWidget(self.download_detect_button)

        # выпадающий список для выбора способа исправления дефектов
        self.defects_processing_type = QComboBox()
        self.defects_processing_type.addItem("Исправить все дефекты")
        self.defects_processing_type.addItem("Исправить основной дефект")
        self.defects_processing_type.setFixedHeight(45)
        self.defects_processing_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.defects_processing_type.setFont(self.font)
        left_layout.addWidget(self.defects_processing_type)
        
        # выпадающий список для выбора способа обработки
        self.process_type = QComboBox()
        self.process_type.addItem("Автоматическая обработка")
        self.process_type.addItem("Ручная обработка")
        self.process_type.setMinimumHeight(45)
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
            "Адаптивное восстановление",
            "Нелокальное среднее"
        ]
        
        # методы для ручной обработки
        self.manual_options = {
            "Размытие": ["Фильтр Лапласа", "Повышение резкости"],
            "Контрастность": ["Алгоритм CLAHE", "Гистограммное выравнивание"],
            "Блики": ["Восстановление с помощью маски", "Адаптивное восстановление"],
            "Шум": ["Фильтр среднего значения", "Медианный фильтр", "Фильтр Гаусса", "Вейвлет-обработка", "Нелокальное среднее"]
        }
        
        # параметры по умолчанию для методов
        self.method_parameters = {
            "Фильтр Лапласа": {
                "alpha": 6
            },
            "Повышение резкости": {
                "sigma": 3, 
                "alpha": 5.5, 
                "betta": -4.5
            },

            "Гистограммное выравнивание": {
                "color_space": ["hsv", "yuv"]
            },
            "Алгоритм CLAHE": {
                "color_space": ['hsv', 'rgb', 'yuv'], 
                "clip_limit": 6.5, 
                "tile_grid_size": (12, 12)
            },

            "Восстановление с помощью маски": {
                "mask_mode": ['brightness', 'gradient', 'combine'], 
                "color_space_mask": ['hsv', 'gray', 'yuv'],
                "color_space": ['yuv', 'rgb', 'hsv'],
                "threshold": 160,
                "inpaint_radius": 3,
                "inpaint_method": ['inpaint_ns', 'ipaint_telea'],
                'gradient_method': ['sobel', 'scharr', 'laplacian'],
                'gradient_threshold': 100
            },
            "Адаптивное восстановление": {
                "mask_mode": ['brightness', 'gradient', 'combine'],
                "color_space_mask": ['hsv', 'gray', 'yuv'],
                "color_space": ['yuv', 'rgb', 'hsv'],
                "adaptive_method": ['gaussian', 'mean'],
                "block_size": 7,
                "C": 5,
                "inpaint_radius": 3,
                "inpaint_method": ['inpaint_ns', 'ipaint_telea'],
                'gradient_method': ['sobel', 'scharr', 'laplacian'],
                'gradient_threshold': 100
            },

            "Фильтр среднего значения": {
                "estimate_noise": ['function', 'gaussian'], 
                "sigma": 3
            },
            "Медианный фильтр": {
                "estimate_noise": ['function', 'gaussian'], 
                "sigma": 3
            },
            "Фильтр Гаусса": {
                "estimate_noise": ['function', 'gaussian'], 
                "sigma": 3
            },
            "Вейвлет-обработка": {
                "type": ['haar', 'db2', 'db4', 'sym2', 'bior1.3'], 
                "mode": ['hard', 'soft'], 
                "number_of_levels": 3, 
                "estimate_noise": ['function', 'gaussian', 'wavelet'], 
                "sigma": 3
            },
            "Нелокальное среднее": {
                "h": 10, 
                "template_window_size": 7, 
                "search_window_size": 21
            }
        }
        
        self.update_methods_table()

        left_layout.addWidget(self.methods_table)

        # кнопка для обработки дефектов
        self.process_button = QPushButton("Исправить дефекты")
        self.process_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.process_button.setFixedHeight(50)
        self.process_button.setStyleSheet(self.buttons_style)
        self.process_button.setFont(self.font)
        self.process_button.clicked.connect(self.processing)
        left_layout.addWidget(self.process_button)

        # распределение размеров элементов по высоте для левой стороны
        left_layout.setStretch(0, 1)   # file_type (выпадающий список)
        left_layout.setStretch(1, 5)   # file_widget (область загрузки)
        left_layout.setStretch(2, 1)   # download_detect_button
        left_layout.setStretch(3, 1)   # defects_processing_type
        left_layout.setStretch(4, 1)   # process_type
        left_layout.setStretch(5, 3)   # methods_table
        left_layout.setStretch(6, 1)   # process_button

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
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # заголовок
        self.process_title = QLabel("Результат обработки")
        self.process_title.setAlignment(Qt.AlignCenter)
        self.process_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.process_title.setFixedHeight(45)
        self.process_title.setStyleSheet("""
            background-color: #F5F5F5;  /* Светло-серый как в таблицах */
            border-radius: 10px; 
            padding: 10px;
            border-bottom: 2px solid #E0E0E0;  /* Тонкая линия снизу */
            color: #555555;  /* Темно-серый текст */
        """)
        self.process_title.setFont(self.font)
        right_layout.addWidget(self.process_title)

        # область отображения результата обработки
        self.result_widget = QWidget()
        self.result_widget.setObjectName("result_widget")
        self.result_widget.setStyleSheet("""
            QWidget#result_widget {
                background-color: white;
                border-radius: 20px;
                border: 2px solid #96C896;
            }
        """)
        self.result_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_widget.setMinimumHeight(200)
        self.result_layout = QVBoxLayout(self.result_widget)
        right_layout.addWidget(self.result_widget)

        # таблица с результатами обработки
        self.results_table = QTableWidget()
        self.results_table.setRowCount(4)
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["", "Обнаружено", "Исправлено"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # растяжение столбцов по ширине таблицы
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers) # запрет редактирования
        self.results_table.setStyleSheet("""
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
        self.results_table.setShowGrid(True)
        self.results_table.setGridStyle(Qt.SolidLine)
        self.results_table.setMinimumHeight(270)
        self.results_table.resizeRowsToContents()
        right_layout.addWidget(self.results_table)

        # кнопка для обнаружения объектов
        self.detect_button = QPushButton("Найти объекты")
        self.detect_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.detect_button.setFixedHeight(50)
        self.detect_button.setStyleSheet(self.buttons_style)
        self.detect_button.setFont(self.font)
        # self.process_button.clicked.connect(self.detect_objects)
        right_layout.addWidget(self.detect_button)

        # создаем контейнер под кнопки скачивания
        right_download_buttons_widget = QWidget()
        right_download_buttons_layout = QHBoxLayout(right_download_buttons_widget)
        right_download_buttons_layout.setContentsMargins(0, 0, 0, 0)  # убираем отступы
        right_download_buttons_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # кнопка для скачивания обработанной картинки
        self.download_process_button = QPushButton("Скачать\nобработанное\nизображение")
        self.download_process_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.download_process_button.setFixedHeight(100)
        self.download_process_button.setStyleSheet(self.buttons_style)
        self.download_process_button.setFont(self.font)
        # self.process_button.clicked.connect(self.detect_objects)
        right_download_buttons_layout.addWidget(self.download_process_button)

        # кнопка для скачивания обработанной и размеченной картинки
        self.download_process_detect_button = QPushButton("Скачать\nразмеченное\nизображение")
        self.download_process_detect_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.download_process_detect_button.setFixedHeight(100)
        self.download_process_detect_button.setStyleSheet(self.buttons_style)
        self.download_process_detect_button.setFont(self.font)
        # self.process_button.clicked.connect(self.detect_objects)
        right_download_buttons_layout.addWidget(self.download_process_detect_button)

        right_layout.addWidget(right_download_buttons_widget)

        # кнопка для параллельного просмотра исходной версии и итоговой
        # self.compare_button = QPushButton("Сравнить с исходным")
        # self.compare_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.compare_button.setFixedHeight(40)
        # self.compare_button.setStyleSheet("background-color: gray; border-radius: 10px; padding: 10px;")
        # self.compare_button.setFont(self.font)
        # # self.process_button.clicked.connect(self.detect_objects)
        # right_layout.addWidget(self.compare_button)

        right_layout.setStretch(0, 1)  # process_title
        right_layout.setStretch(1, 6)  # result_widget (область результата)
        right_layout.setStretch(2, 4)  # results_table
        right_layout.setStretch(3, 1)  # detect_button
        right_layout.setStretch(4, 1)  # download_buttons_widget
        # right_layout.setStretch(5, 1)  # compare_button

        main_layout.addWidget(right_widget, stretch=50)

        # обновляем состояние всех кнопок
        self.update_buttons_state()

    def center(self) -> None:
        """
        Устанавливает окно по центру экрана.
        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_buttons_state(self):
        """
        Обновляет состояние всех кнопок.
        """
        self.detect_button.setEnabled(hasattr(self, 'processed_path') and self.processed_path is not None)
        self.download_detect_button.setEnabled(hasattr(self, 'detect_path') and self.detect_path is not None)
        self.download_process_button.setEnabled(hasattr(self, 'processed_path') and self.processed_path is not None)
        self.download_process_detect_button.setEnabled(hasattr(self, 'detect_path') and self.detect_path is not None)

    
    # =========================================================================
    # ОБЩИЕ ФУНКЦИИ ДЛЯ ОТОБРАЖЕНИЯ
    # =========================================================================

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
            # отображаем файл
            self.update_display(file_path=self.file_path, close=True, side='left')
            # создаем экземпляр класса-обработчика
            self.processor = ProcessingClass(
                input_path=self.file_path,
                model_path=MODEL_PATH,
                output_path=OUTPUT_PATH
            )

    def update_display(self, file_path, close, side):
        """
        Определяет заполнение области после загрузки файла.
        Параметр close определяет наличие кнопки закрытия. Если файл загружается
        первый раз, то она нужна. Если загружаемый файл - результат обработки, то нет.
        """
        if self.file_path:
            processing_type = self.file_type.currentText()
            if processing_type == "Обработка изображения":
                self.display_image(file_path=file_path, close=close, side=side)
            elif processing_type == "Обработка датасета":
                self.display_dataset()
            elif processing_type == "Обработка видео":
                self.display_video(file_path=file_path, close=close, side=side)

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
        self.load_button.setFixedSize(200, 170)
        self.load_button.setStyleSheet(
            self.buttons_style +
            """
            QPushButton {
                border-radius: 15px;
            }
            """
        )
        self.load_button.setFont(self.font)
        self.load_button.clicked.connect(self.load_file)
        button_horizontal_layout.addWidget(self.load_button)

        # пространство справа от кнопки
        button_horizontal_layout.addStretch()

        # добавляем горизонтальный layout в вертикальный
        load_button_layout.addLayout(button_horizontal_layout)

        # пространство сверху от кнопки, чтобы сделать ее по центру по вертикали
        load_button_layout.addStretch()

        # добавляем контейнер с кнопкой в file_layout
        self.file_layout.addWidget(self.load_button_container)

    def create_service_buttons(self, type, close, side):
        """
        Создает окружение для кнопок и сами кнопки закрытия и просмотра.
        Параметр type определяет тип файла.
        Параметр close определяет наличие кнопки закрытия. Если файл загружается
        первый раз, то она нужна. Если загружаемый файл - результат обработки, то нет
        """
        # создаем overlay виджет для кнопок
        if side == 'left': overlay_widget = QWidget(self.left_show_label) # создаем виджет поверх виджета для картинки или видео
        elif side == 'right': overlay_widget = QWidget(self.right_show_label)
        overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False) # именно этот, а не родительский, виджет будет реагировать на мышь
        overlay_layout = QHBoxLayout(overlay_widget) # расположение по горизонтали
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_widget.setStyleSheet("background: transparent; border: none;") # делаем прозрачным фон виджета для кнопок
        # overlay_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
        # кнопка просмотра (глаз)
        view_button = QPushButton("👁")
        view_button.setFixedSize(30, 30)
        view_button.setStyleSheet("""
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
        if type == 'image':
            view_button.clicked.connect(lambda: self.view_content_image(side))
        elif type == 'video':
            view_button.clicked.connect(lambda: self.view_content_video(side))
        overlay_layout.addWidget(view_button)
        
        # кнопка закрытия (крестик)
        if close:
            close_button = QPushButton("×")
            close_button.setFixedSize(30, 30)
            close_button.setStyleSheet("""
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
            close_button.clicked.connect(self.clear)
            overlay_layout.addWidget(close_button)

        if side == 'left':
            self.left_overlay_widget = overlay_widget
            self.left_view_button = view_button
            self.left_close_button = close_button
        elif side == 'right':
            self.right_overlay_widget = overlay_widget
            self.right_view_button = view_button
        
        # устанавливаем размер виджета для кнопок (подгоняет размер под содержимое)
        overlay_widget.adjustSize()
    
    def delete_files_widgets(self, side):
        """
        Удаляет виджеты из области отображения файлов.
        """
        if side == 'left': layout = self.file_layout
        elif side == 'right': layout = self.result_layout
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget: 
                widget.deleteLater()
    
    def clear(self):
        """
        Удаляет отображаемый файл из области по кнопке закрытия.
        Так как пользователь может закрыть только исходный файл, то есть левый,
        здесь используются объекты конкретно левой стороны.
        """
        # освобождаем ресурсы из-под объекта-обработчика
        if hasattr(self, 'processor'):
            self.processor.cleanup()
            del self.processor

        # останавливаем таймер, если он существует
        if hasattr(self, 'left_video_timer') and self.left_video_timer:
            self.left_video_timer.stop()
        
        # освобождаем ресурсы VideoCapture, если есть
        if hasattr(self, 'cap') and self.left_cap:
            self.left_cap.release()

        # удаляем виджеты из области отображения файлов
        if hasattr(self, 'file_layout'):
            self.delete_files_widgets('left')

        if hasattr(self, 'processed_path'):
            del self.processed_path
        if hasattr(self, 'detect_path'):
            del self.detect_path
        if hasattr(self, 'detect_processed_path'):
            del self.detect_processed_path

        # опять создаем контейнер для кнопки загрузки и саму кнопку
        self.create_load_button()

    def create_show_elements(self, side):
        """
        Подготавливает элементы для отображения файла.
        """
        # удаление предыдущих виджетов, чтобы они не накапливались
        self.delete_files_widgets(side=side)

        # контейнер для изображения
        show_container = QWidget() # "рамка" (область) для изоражения
        show_container_layout = QVBoxLayout(show_container) # правила размещения внутри области (по вертикали)
        show_container_layout.setContentsMargins(0, 0, 0, 0) # содержимое должно занимать все пространство
        
        # QLabel для изображения
        show_label = QLabel()
        show_label.setAlignment(Qt.AlignCenter)
        show_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored) # игнорировать рекомендуемые размеры
        show_label.setStyleSheet("background-color: #f0f0f0;")

        # добавляем элемент показа в контейнер
        show_container_layout.addWidget(show_label)
        # добавляем контейнер в лайаут для отображения файла
        if side == 'left': 
            self.left_show_label = show_label
            self.left_show_container = show_container
            self.file_layout.addWidget(self.left_show_container)
        elif side == 'right': 
            self.right_show_label = show_label
            self.right_show_container = show_container
            self.result_layout.addWidget(self.right_show_container)

    def update_cropped_image(self, pixmap, side):
        """
        Обновляет отображаемую часть изображения или кадра (среднюю часть).
        """        
        if side == 'left': show_label = self.left_show_label
        elif side == 'right': show_label = self.right_show_label
        
        # получаем текущие размеры виджета для изображения
        width = show_label.width()
        height = show_label.height()
        
        # размеры самого изображения
        img_width = pixmap.width()
        img_height = pixmap.height()
        
        # координаты для вырезания центральной части
        crop_x = max(0, (img_width - width) // 2)
        crop_y = max(0, (img_height - height) // 2)
        crop_width = min(width, img_width)
        crop_height = min(height, img_height)
        
        # вырезаем и масштабируем
        cropped = pixmap.copy(crop_x, crop_y, crop_width, crop_height) # создает вырезанное изображение, принимает координаты левого верхнего угла и длину/ширину
        scaled = cropped.scaled(
            width, height, # необходимые размеры
            Qt.IgnoreAspectRatio, # растягивает по заданным размерам
            Qt.SmoothTransformation # сглаживание
        )
        show_label.setPixmap(scaled)

    def update_buttons_position(self):
        """
        Обновляет позиции кнопок управления (служебных кнопок).
        """
        if hasattr(self, 'left_overlay_widget') and self.left_overlay_widget:
            left_label_width = self.left_show_label.width() if hasattr(self, 'left_show_label') else 0
            self.left_overlay_widget.move(left_label_width - self.left_overlay_widget.width() - 10, 10)
        
        if hasattr(self, 'right_overlay_widget') and self.right_overlay_widget:
            right_label_width = self.right_show_label.width() if hasattr(self, 'right_show_label') else 0
            self.right_overlay_widget.move(right_label_width - self.right_overlay_widget.width() - 10, 10)


    # =========================================================================
    # ФУНКЦИИ ДЛЯ ОТОБРАЖЕНИЯ КАРТИНКИ
    # =========================================================================
    
    def display_image(self, file_path, close, side):
        """
        Отображает изображение.
        Параметр close определяет наличие кнопки закрытия. Если файл загружается
        первый раз, то она нужна. Если загружаемый файл - результат обработки, то нет
        """
        # загружаем изображение
        original_pixmap = QPixmap(file_path) # original_pixmap - это непосредственно изображение
        if original_pixmap.isNull():
            error_widget = QLabel()
            error_widget.setText("Ошибка: не удалось загрузить изображение")
            error_widget.setStyleSheet("color: red;")
            error_widget.setAlignment(Qt.AlignCenter)
            self.file_layout.addWidget(error_widget)
            return

        # создаем элементы показа картинки
        self.create_show_elements(side=side)

        # создаем кнопки закрытия и просмотра
        self.create_service_buttons(type='image', close=close, side=side)
        
        # устанавливаем обработчик изменения размера изображения
        if side == 'left': self.left_show_label.resizeEvent = lambda e: self.update_image_display(original_pixmap, side)
        elif side == 'right': self.right_show_label.resizeEvent = lambda e: self.update_image_display(original_pixmap, side)

    def update_image_display(self, pixmap, side):
        """
        Обработчик изменения размера изображения (или окна).
        """
        # обрезаем изображение для отображения
        self.update_cropped_image(pixmap, side)
        # обновляем позицию кнопок
        self.update_buttons_position()

    def view_content_image(self, side):
        """
        Открывает окно просмотра с полным изображением.
        """
        if side == 'left': 
            if hasattr(self, 'file_path') and self.file_path:
                self.preview_window = PreviewWindowImage(self.file_path)
                self.preview_window.show()
        elif side == 'right': 
            if hasattr(self, 'processed_path') and self.processed_path:
                self.preview_window = PreviewWindowImage(self.processed_path)
                self.preview_window.show()

    # =========================================================================
    # ФУНКЦИИ ДЛЯ ОТОБРАЖЕНИЯ ВИДЕО
    # =========================================================================

    def display_video(self, file_path, close, side):
        """
        Отображает видео в маленьком окошке с использованием OpenCV.
        """
        # проверяем существование файла
        if not os.path.exists(file_path):
            error_widget = QLabel()
            error_widget.setText("Ошибка: файл не найден")
            error_widget.setStyleSheet("color: red;")
            error_widget.setAlignment(Qt.AlignCenter)
            self.file_layout.addWidget(error_widget)
            return
        
        # загружаем видео с помощью OpenCV VideoCapture
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            error_widget = QLabel()
            error_widget.setText("Ошибка: не удалось открыть видео")
            error_widget.setStyleSheet("color: red;")
            error_widget.setAlignment(Qt.AlignCenter)
            self.file_layout.addWidget(error_widget)
            return

        # создаем элементы показа видео
        self.create_show_elements(side=side)

        # создаем кнопки закрытия и просмотра
        self.create_service_buttons('video', close=close, side=side)

        # таймер для обновления кадров
        video_timer = QTimer()
        is_playing = False

        # для левой и правой стороны создаем свой видео-объект, таймер и флаг для запуска/остановки
        if side == 'left':
            self.left_cap = cap
            self.left_video_timer = video_timer
            self.left_is_playing = is_playing
            show_label = self.left_show_label
        elif side == 'right':
            self.right_cap = cap
            self.right_video_timer = video_timer
            self.right_is_playing = is_playing
            show_label = self.right_show_label

        video_timer.timeout.connect(lambda: self.update_frame(side))
        
        # центральная кнопка воспроизведения
        play_button = QPushButton("▶", show_label)
        play_button.setFixedSize(60, 60)
        play_button.setStyleSheet("""
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
        play_button.clicked.connect(self.toggle_play_video)

        if side == 'left': self.left_play_button = play_button
        elif side == 'right': self.right_play_button = play_button

        # центрируем кнопку запуска после создания
        self.update_play_button_position(side)

        # обработчики событий мыши
        show_label.mousePressEvent = lambda event: self.on_video_click(side=side)
        show_label.enterEvent = lambda event: self.show_play_button(side=side)
        show_label.leaveEvent = lambda event: self.hide_play_button(side=side)

        # устанавливаем отслеживание мыши для окна показа, но убираем для кнопки, чтобы проходило сквозь кнопку
        play_button.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        show_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        # устанавливаем обработчик изменения размера
        show_label.resizeEvent = lambda e: self.update_video_display(side)
        
        # обновляем позиции элементов
        self.update_video_display(side)

    def update_play_button_position(self, side):
        """
        Центрирует кнопку воспроизведения.
        """
        if side == 'left': 
            if hasattr(self, 'left_play_button'):
                x = (self.left_show_label.width() - self.left_play_button.width()) // 2
                y = (self.left_show_label.height() - self.left_play_button.height()) // 2
                self.left_play_button.move(x, y)
        elif side == 'right': 
            if hasattr(self, 'right_play_button'):
                x = (self.right_show_label.width() - self.right_play_button.width()) // 2
                y = (self.right_show_label.height() - self.right_play_button.height()) // 2
                self.right_play_button.move(x, y)

    def update_video_display(self, side):
        """
        Обработчик изменения размера видео (или окна).
        """
        # обновляем позицию служебных кнопок
        self.update_buttons_position()
        # обновляем позицию кнопки запуска/останова
        self.update_play_button_position(side=side)
    
    def on_video_click(self, side):
        """
        Обработчик клика по видео.
        """
        self.toggle_play_video(side=side)

    def show_play_button(self, side):
        """
        Показывает кнопку при наведении мыши.
        """
        if side == 'left': self.left_play_button.show()
        elif side == 'right': self.right_play_button.show()
        self.update_play_button_position(side)

    def hide_play_button(self, side):
        """
        Скрывает кнопку, когда мышь уходит.
        """
        if side == 'left': 
            if self.left_is_playing:
                self.left_play_button.hide()
        elif side == 'right':
            if self.right_is_playing: 
                self.right_play_button.hide()

    def update_frame(self, side):
        """
        Обновляет текущий кадр видео.
        """
        if side == 'left': cap = self.left_cap
        elif side == 'right': cap = self.right_cap

        ret, frame = cap.read()
        if ret:
            # конвертируем кадр из BGR (OpenCV) в RGB (Qt)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)

            # масштабируем изображение (кадр) под размер виджета
            self.update_cropped_image(pixmap, side)
        else:
            # если видео закончилось, возвращаемся в начало
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def toggle_play_video(self, side):
        """
        Переключает воспроизведение видео (остановка\запуск).
        """
        if side == 'left':
            is_playing = self.left_is_playing
            video_timer = self.left_video_timer
            cap = self.left_cap
            play_button = self.left_play_button
        else:
            is_playing = self.right_is_playing
            video_timer = self.right_video_timer
            cap = self.right_cap
            play_button = self.right_play_button

        if is_playing:
            video_timer.stop()
            play_button.setText("▶")
        else:
            fps = cap.get(cv2.CAP_PROP_FPS)
            video_timer.start(int(1000 / fps))
            play_button.setText("❚❚")
        
        # обновляем флаг состояния
        if side == 'left':
            self.left_is_playing = not is_playing
        else:
            self.right_is_playing = not is_playing

    def view_content_video(self, side):
        """
        Открывает окно просмотра с полным видео.
        """
        if side == 'left': 
            if hasattr(self, 'file_path') and self.file_path:
                self.preview_window = PreviewWindowVideo(self.file_path)
                self.preview_window.show()
        elif side == 'right': 
            if hasattr(self, 'processed_path') and self.processed_path:
                self.preview_window = PreviewWindowVideo(self.processed_path)
                self.preview_window.show()


    # =========================================================================
    # ФУНКЦИИ ДЛЯ ЗАПОЛНЕНИЯ ТАБЛИЦ
    # =========================================================================

    def update_methods_table(self):
        """
        Обновляет таблицу методов с кнопками параметров для каждого метода.
        """
        # полная очистка таблицы
        self.methods_table.clearContents()
        
        # стиль для кнопок-шестерёнок
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
        
        # заполняем таблицу
        for row, defect in enumerate(self.defects):
            # первый столбец - название дефекта
            item = QTableWidgetItem(defect)
            item.setTextAlignment(Qt.AlignCenter)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            self.methods_table.setItem(row, 0, item)
            
            # создаем контейнер для второго столбца
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(5, 0, 5, 0)
            layout.setSpacing(5)

            # кнопка шестеренки
            gear_btn = QPushButton()
            gear_btn.setText("⚙")
            gear_btn.setFont(QFont("Arial", 10))
            gear_btn.setFixedSize(24, 24)
            gear_btn.setStyleSheet(gear_style)
            
            # для автоматического режима
            if self.process_type.currentIndex() == 0:
                # метод обработки
                method_label = QLabel(self.automatic_methods[row])
                method_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(method_label, stretch=1)
                
                # кнопка шестерёнки (только просмотр)
                gear_btn.clicked.connect(lambda _, r=row: self.show_parameters(r, False))
                layout.addWidget(gear_btn)

            # для ручного режима   
            else:
                # выпадающий список методов
                combo = QComboBox()
                combo.addItems(self.manual_options[defect])
                combo.setCurrentIndex(0)
                combo.setStyleSheet("QComboBox { padding: 2px; }")
                layout.addWidget(combo, stretch=1)
                
                # кнопка шестерёнки (редактирование)
                gear_btn.clicked.connect(lambda _, r=row: self.show_parameters(r, True))
                layout.addWidget(gear_btn)
            
            # устанавливаем контейнер в таблицу
            self.methods_table.setCellWidget(row, 1, container)
        
        # настройки внешнего вида таблицы
        self.methods_table.resizeRowsToContents()
        self.methods_table.setMinimumHeight(160)

    def show_parameters(self, row, editable):
        """
        Открывает диалоговое окошко для просмотра или ввода параметров.
        """       
        if self.process_type.currentText() == "Автоматическая обработка":
            method_name = self.automatic_methods[row]
        else:
            combo = self.methods_table.cellWidget(row, 1).findChild(QComboBox)
            method_name = combo.currentText()
        
        # Всегда используем текущие сохраненные параметры (если они есть)
        parameters = self.method_parameters.get(method_name, {}).copy()
        
        dialog = ParameterDialog(method_name, parameters, editable)
        if dialog.exec_() == QDialog.Accepted and editable:
            # Сохраняем новые параметры только если было редактирование
            self.method_parameters[method_name] = dialog.get_parameters()
        elif not editable:
            # Для просмотра просто показываем текущие сохраненные параметры
            pass

    
    def update_results_table(self):
        """
        Обновляет таблицу результатов в соответствии с полученным 
        с бэкенда словарем.
        """
        if hasattr(self, 'result'):
            # полная очистка таблицы
            self.results_table.clearContents()

            defect_mapping = {
                'blur': "Размытие",
                'contrast': "Контрастность",
                'glares': "Блики",
                'noise': "Шум"
            }
            
            # заполняем таблицу
            for row, defect_ru in enumerate(self.defects):
                # находим английский ключ для этого дефекта
                defect_en = next(key for key, value in defect_mapping.items() if value == defect_ru)
                
                # получаем значения для этого дефекта
                detected, fixed = self.result.get(defect_en, [0, 0])
                
                # создаем ячейки
                item_defect = QTableWidgetItem(defect_ru)
                item_detected = QTableWidgetItem(str(detected))
                item_fixed = QTableWidgetItem(str(fixed))
                
                # устанавливаем выравнивание по центру
                for item in [item_defect, item_detected, item_fixed]:
                    item.setTextAlignment(Qt.AlignCenter)
                
                # добавляем ячейки в таблицу
                self.results_table.setItem(row, 0, item_defect)
                self.results_table.setItem(row, 1, item_detected)
                self.results_table.setItem(row, 2, item_fixed)
            
            # настройки внешнего вида таблицы
            self.methods_table.resizeRowsToContents()


    # =========================================================================
    # ИСПРАВЛЕНИЕ ДЕФЕКТОВ
    # =========================================================================

    def processing(self):
        if self.file_type.currentText() == 'Обработка изображения':
            if self.process_type.currentText() == 'Автоматическая обработка':
                if self.defects_processing_type.currentText() == 'Исправить основной дефект':
                    self.processed_path, self.result = self.processor.recovery_image(
                        processing_mode='automatic',
                        defect_mode='one_defect')
                elif self.defects_processing_type.currentText() == 'Исправить все дефекты':
                    self.processed_path, self.result = self.processor.recovery_image(
                        processing_mode='automatic',
                        defect_mode='all_defects')
        elif self.file_type.currentText() == 'Обработка видео':
            if self.process_type.currentText() == 'Автоматическая обработка':
                if self.defects_processing_type.currentText() == 'Исправить основной дефект':
                    print('yes')
                    self.processed_path, self.result = self.processor.recovery_video(
                        processing_mode='automatic',
                        defect_mode='one_defect')
                elif self.defects_processing_type.currentText() == 'Исправить все дефекты':
                    print('yes')
                    self.processed_path, self.result = self.processor.recovery_video(
                        processing_mode='automatic',
                        defect_mode='all_defects')
        if self.processed_path:
            print(self.processed_path)
            print(self.result)
            self.update_display(file_path=self.processed_path, close=False, side='right')
            self.update_results_table()
            self.update_buttons_state()
            