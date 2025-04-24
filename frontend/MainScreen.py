from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTextEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QAction,
    QDesktopWidget, QFrame, QLineEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, 
    QSizePolicy, QHeaderView, QPushButton, QStyledItemDelegate, 
    QFileDialog, QGraphicsView, QGraphicsScene, QDialog, QApplication, QGraphicsProxyWidget,
    QMessageBox, QStyle
)
from PyQt5.QtGui import (
    QPalette, QColor, QFont, QIntValidator, 
    QDoubleValidator, QRegExpValidator, QRegularExpressionValidator,
    QPixmap, QImage, QIcon, QTransform, QPainter, QMovie
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRegExp, QRegularExpression, QSize, QRectF, QUrl, QEvent

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

import os
import cv2
from pathlib import Path
from functools import partial
import shutil

os.environ["QT_MEDIA_BACKEND"] = "windowsmediafoundation"

from frontend.PreviewWindowImage import PreviewWindowImage
from frontend.PreviewWindowVideo import PreviewWindowVideo
from frontend.PreviewWindowDataset import PreviewWindowDataset
from ParameterDialog import ParameterDialog
from backend.ProcessingClass import ProcessingClass

PROJECT_ROOT = Path(__file__).parent.parent
MODEL_PATH = PROJECT_ROOT / 'mobile_net_model.h5'
YOLO_RAW_PATH = PROJECT_ROOT / 'yolo_raw.pt'
YOLO_BEST_PATH = PROJECT_ROOT / 'yolo_best.pt'
OUTPUT_PATH = PROJECT_ROOT / 'temp'

class ProcessingWorker(QThread):
    finished = pyqtSignal(str, dict)  # cигнал с результатами
    error = pyqtSignal(str)  # cигнал об ошибке

    def __init__(self, processor, settings):
        super().__init__()
        self.processor = processor
        self.settings = settings

    def run(self):
        try:
            if self.settings['file_type'] == 'Обработка изображения':
                if self.settings['process_type'] == 'Автоматическая обработка':
                    if self.settings['defects_type'] == 'Исправить основной дефект':
                        processed_path, result = self.processor.recovery_image(
                            processing_mode='automatic',
                            defect_mode='one_defect')
                    elif self.settings['defects_type'] == 'Исправить все дефекты':
                        processed_path, result = self.processor.recovery_image(
                            processing_mode='automatic',
                            defect_mode='all_defects')
                elif self.settings['process_type'] == 'Ручная обработка':
                    if self.settings['defects_type'] == 'Исправить основной дефект':
                        processed_path, result = self.processor.recovery_image(
                            processing_mode='manual',
                            defect_mode='one_defect')
                    elif self.settings['defects_type'] == 'Исправить все дефекты':
                        processed_path, result = self.processor.recovery_image(
                            processing_mode='manual',
                            defect_mode='all_defects')
            if self.settings['file_type'] == 'Обработка датасета':
                if self.settings['process_type'] == 'Автоматическая обработка':
                    if self.settings['defects_type'] == 'Исправить основной дефект':
                        processed_path, result = self.processor.recovery_dataset(
                            processing_mode='automatic',
                            defect_mode='one_defect')
                    elif self.settings['defects_type'] == 'Исправить все дефекты':
                        processed_path, result = self.processor.recovery_dataset(
                            processing_mode='automatic',
                            defect_mode='all_defects')
                    elif self.settings['defects_type'] == 'Исправить самый частый дефект':
                        processed_path, result = self.processor.recovery_dataset(
                            processing_mode='automatic',
                            defect_mode='often_defect')
                elif self.settings['process_type'] == 'Ручная обработка':
                    if self.settings['defects_type'] == 'Исправить основной дефект':
                        processed_path, result = self.processor.recovery_dataset(
                            processing_mode='manual',
                            defect_mode='one_defect')
                    elif self.settings['defects_type'] == 'Исправить все дефекты':
                        processed_path, result = self.processor.recovery_dataset(
                            processing_mode='manual',
                            defect_mode='all_defects')
                    elif self.settings['defects_type'] == 'Исправить самый частый дефект':
                        processed_path, result = self.processor.recovery_dataset(
                            processing_mode='manual',
                            defect_mode='often_defect')
                print(f"[DEBUG] Dataset processed - Path: {processed_path}, Result: {result}")
            elif self.settings['file_type'] == 'Обработка видео':
                if self.settings['process_type'] == 'Автоматическая обработка':
                    if self.settings['defects_type'] == 'Исправить основной дефект':
                        processed_path, result = self.processor.recovery_video(
                            processing_mode='automatic',
                            defect_mode='one_defect')
                    elif self.settings['defects_type'] == 'Исправить все дефекты':
                        processed_path, result = self.processor.recovery_video(
                            processing_mode='automatic',
                            defect_mode='all_defects')
                    elif self.settings['defects_type'] == 'Исправить самый частый дефект':
                        processed_path, result = self.processor.recovery_video(
                            processing_mode='automatic',
                            defect_mode='often_defect')
                if self.settings['process_type'] == 'Ручная обработка':
                    if self.settings['defects_type'] == 'Исправить основной дефект':
                        processed_path, result = self.processor.recovery_video(
                            processing_mode='manual',
                            defect_mode='one_defect')
                    elif self.settings['defects_type'] == 'Исправить все дефекты':
                        processed_path, result = self.processor.recovery_video(
                            processing_mode='manual',
                            defect_mode='all_defects')
                    elif self.settings['defects_type'] == 'Исправить самый частый дефект':
                        processed_path, result = self.processor.recovery_video(
                            processing_mode='manual',
                            defect_mode='often_defect')
            
            print(f"[DEBUG] Emitting finished: {processed_path}")
            self.finished.emit(processed_path, result)
        except Exception as e:
            print(self.processor.get_input_path())
            print(f"[ERROR] Worker failed: {str(e)}")
            self.error.emit(str(e))

    # def __del__(self):
    #     """
    #     Освобождаем ресурсы при удалении worker.
    #     """
    #     if hasattr(self.processor, 'cleanup'):
    #         self.processor.cleanup()

class DetectingWorker(QThread):
    finished = pyqtSignal(str, str)  # cигнал с результатами
    error = pyqtSignal(str)  # cигнал об ошибке

    def __init__(self, processor, settings):
        super().__init__()
        self.processor = processor
        self.settings = settings

    def run(self):
        try:
            if self.settings['file_type'] == 'Обработка изображения':
                detected_path = self.processor.detect_image(detect_type='raw')
                detected_processed_path = self.processor.detect_image(detect_type='best')
            elif self.settings['file_type'] == 'Обработка видео':
                detected_path = self.processor.detect_video(detect_type='raw')
                detected_processed_path = self.processor.detect_video(detect_type='best')
            elif self.settings['file_type'] == 'Обработка датасета':
                detected_path = self.processor.detect_dataset(detect_type='raw')
                detected_processed_path = self.processor.detect_dataset(detect_type='best')
            
            print(f"[DEBUG] Emitting finished: {detected_path, detected_processed_path}")
            self.finished.emit(detected_path, detected_processed_path)
        except Exception as e:
            print(self.processor.get_input_path())
            print(f"[ERROR] Worker failed: {str(e)}")
            self.error.emit(str(e))

    # def __del__(self):
    #     """
    #     Освобождаем ресурсы при удалении worker.
    #     """
    #     if hasattr(self.processor, 'cleanup'):
    #         self.processor.cleanup()

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

        # шрифт
        self.font = QFont()
        self.font.setPointSize(10)

        # словарь для хранения кнопок с параметрами
        self.gear_buttons = {}

        # стили для кнопок-шестеренок (с параметрами)
        self.gear_buttons_style = {
            'normal': """
                QPushButton {
                    border: none;
                    background: transparent;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: #e0e0e0;
                    border-radius: 2px;
                }
            """,
            'disabled': """
                 QPushButton {
                    border: none;
                    background: transparent;
                    padding: 0px;
                    color: #c0c0c0;
                }
            """
        }

        # стиль основных кнопок
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

        # создаем экземпляр класса-обработчика
        self.processor = ProcessingClass(
            model_path=MODEL_PATH,
            yolo_raw_path=YOLO_RAW_PATH,
            yolo_best_path=YOLO_BEST_PATH,
            output_path=OUTPUT_PATH
        )
        # получаем словари методов и разрешенных параметров
        self.auto_methods = self.processor.get_auto_methods()
        self.manual_methods = self.processor.get_manual_methods()
        self.allowed_params_values = self.processor.get_allowed_params()

        # для управления обработкой
        # self.right_movie = None
        # self.left_movie = None
        # self.left_gif_overley = None
        # self.right_gif_overley = None
        # self.processing_overlay = None
        # self.processing_label = None
        # self.processing_spinner = None
        # self.processing_timer = QTimer()
        # self.processing_timer.timeout.connect(self.update_spinner)

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
        self.file_type.currentTextChanged.connect(self.set_download_buttons_text)
        self.file_type.currentTextChanged.connect(self.set_defects_types)
        left_layout.addWidget(self.file_type)
        # self.set_download_buttons_text()

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
        self.file_widget.installEventFilter(self)
        self.file_layout = QVBoxLayout(self.file_widget)
        left_layout.addWidget(self.file_widget)

        # кнопка загрузки
        self.create_load_button()

        # кнопка для скачивания исходного размеченного файла
        self.download_detect_button = QPushButton()
        self.download_detect_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.download_detect_button.setFixedHeight(50)
        self.download_detect_button.setStyleSheet(self.buttons_style)
        self.download_detect_button.setFont(self.font)
        self.download_detect_button.clicked.connect(lambda: self.download_files(self.detected_path))
        self.set_download_buttons_text()
        left_layout.addWidget(self.download_detect_button)

        # выпадающий список для выбора способа исправления дефектов
        self.defects_processing_type = QComboBox()
        self.defects_processing_type.addItem("Исправить основной дефект")
        self.defects_processing_type.addItem("Исправить все дефекты")
        if self.file_type.currentText() != "Обработка изображения":
            self.defects_processing_type.addItem("Исправить самый частый дефект")
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
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # изначально правая сторона пустая
        self.clear_right_side()

        # self.add_right_side_additional_elements()

        # распределение пространства на правой стороне
        self.right_layout.setStretch(0, 1)  # process_title
        self.right_layout.setStretch(1, 6)  # result_widget (область результата)
        self.right_layout.setStretch(2, 4)  # results_table
        self.right_layout.setStretch(3, 1)  # detect_button
        self.right_layout.setStretch(4, 1)  # download_buttons_widget
        # right_layout.setStretch(5, 1)  # compare_button

        main_layout.addWidget(self.right_widget, stretch=50)

        # обновляем состояние всех кнопок
        self.update_buttons_state()


    # def closeEvent(self, event):
    #     """
    #     Событие закрытия окна.
    #     """
    #     self.clear_temp_folder()


    # =========================================================================
    # ОБЩИЕ ФУНКЦИИ
    # =========================================================================

    def center(self) -> None:
        """
        Устанавливает окно по центру экрана.
        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def sync_widgets_heights(self):
        """
        Устанавливает высоту области отображения справа по высоте слева
        """
        self.result_widget.setMinimumHeight(self.file_widget.height())
        self.result_widget.setMaximumHeight(self.file_widget.height())
        self.result_widget.updateGeometry()

    def eventFilter(self, obj, event):
        if hasattr(self, 'result_widget') and self.result_widget:
            if obj == self.file_widget and event.type() == QEvent.Resize:
                self.sync_widgets_heights()
        return super().eventFilter(obj, event)

    def show_errors(self, text, parent_layout):
        error_widget = QLabel()
        error_widget.setText(text)
        error_widget.setStyleSheet("color: red;")
        error_widget.setAlignment(Qt.AlignCenter)
        parent_layout.addWidget(error_widget)
    
    def update_buttons_state(self):
        """
        Обновляет состояние всех кнопок.
        """
        if hasattr(self, 'process_button'):
            self.process_button.setEnabled(hasattr(self, 'file_path') and self.file_path is not None)
        if hasattr(self, 'detect_button'):
            self.detect_button.setEnabled(hasattr(self, 'processed_path') and self.processed_path is not None)
        if hasattr(self, 'download_detect_button'):
            self.download_detect_button.setEnabled(hasattr(self, 'detected_path') and self.detected_path is not None)
        if hasattr(self, 'download_process_button'):
            self.download_process_button.setEnabled(hasattr(self, 'processed_path') and self.processed_path is not None)
        if hasattr(self, 'download_process_detect_button'):
            self.download_process_detect_button.setEnabled(hasattr(self, 'detected_processed_path') and self.detected_processed_path is not None)

    def set_defects_types(self):
        """
        Устанавливает список способов испраления дефектов 
        (добавляет опцию исправления самого частого дефекта для видео и датасета).
        """
        if self.file_type.currentText() != "Обработка изображения":
            self.defects_processing_type.addItem("Исправить самый частый дефект")
        else:
            item = self.defects_processing_type.findText("Исправить самый частый дефект")
            self.defects_processing_type.removeItem(item)
    
    def set_download_buttons_text(self):
        """
        Устанавливает нужный текст на кнопках скачивания.
        """
        # кнопка для скачивания обработанного файла
        if hasattr(self, 'download_process_button'):
            if self.file_type.currentText() == 'Обработка изображения':
                self.download_process_button.setText("Скачать\nобработанное\nизображение")
            elif self.file_type.currentText() == 'Обработка видео':
                self.download_process_button.setText("Скачать\nобработанное\nвидео")
            elif self.file_type.currentText() == 'Обработка датасета':
                self.download_process_button.setText("Скачать\nобработанный\nдатасет")

        # кнопка для скачивания обработанного и размеченного файла
        if hasattr(self, 'download_process_detect_button'):
            if self.file_type.currentText() == 'Обработка изображения':
                self.download_process_detect_button.setText("Скачать\nразмеченное\nизображение")
            elif self.file_type.currentText() == 'Обработка видео':
                self.download_process_detect_button.setText("Скачать\nразмеченное\nвидео")
            elif self.file_type.currentText() == 'Обработка датасета':
                self.download_process_detect_button.setText("Скачать\nразмеченный\nдатасет")

        # кнопка для скачивания исходного размеченного файла
        if hasattr(self, 'download_detect_button'):
            if self.file_type.currentText() == 'Обработка изображения':
                self.download_detect_button.setText("Скачать размеченное изображение")
            elif self.file_type.currentText() == 'Обработка видео':
                self.download_detect_button.setText("Скачать размеченное видео")
            elif self.file_type.currentText() == 'Обработка датасета':
                self.download_detect_button.setText("Скачать размеченный датасет")

    def download_files(self, path):
        """
        Реализует скачивание файлов.
        """
        downloads_dir = os.path.expanduser("~/Downloads")
        file_name = os.path.basename(path)
        save_path = os.path.join(downloads_dir, file_name)
        counter = 1
        base_name, ext = os.path.splitext(file_name)
        
        # обработка случая, когда path - это папка
        if os.path.isdir(path):
            while os.path.exists(save_path):
                save_path = os.path.normpath(os.path.join(downloads_dir, f"{base_name}_{counter}"))
                counter += 1
            try:
                shutil.copytree(path, save_path)
                display_path = save_path.replace("\\", "/")
                QMessageBox.information(self, "Успех", f"Папка сохранена в:\n{display_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить папку:\n{str(e)}")
        
        # обработка случая, когда path - это файл
        else:
            while os.path.exists(save_path):
                save_path = os.path.normpath(os.path.join(downloads_dir, f"{base_name}_{counter}{ext}"))
                counter += 1
            try:
                shutil.copy2(path, save_path)
                display_path = save_path.replace("\\", "/")
                QMessageBox.information(self, "Успех", f"Файл сохранен в:\n{display_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def clear_temp_folder(self):
        """
        Очищает папку с файлами.
        """
        for file_name in os.listdir(OUTPUT_PATH):
            file_path = os.path.join(OUTPUT_PATH, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    
    
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
            # передаем путь к файлу в объект класса-обработчика
            self.processor.set_input_path(self.file_path)
            # обновляем состояние кнопок
            self.update_buttons_state()

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
                self.display_dataset(file_path=file_path, close=close, side=side)
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
        overlay_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
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
        elif type == 'dataset':
            view_button.clicked.connect(lambda: self.view_content_dataset(side))
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
        if side == 'left':
            layout = self.file_layout
            # удаляем обработчик
            if hasattr(self, 'left_show_label'):
                self.left_show_label.resizeEvent = None
            # очищаем ссылки на левые виджеты
            for attr in ['left_show_label', 'left_show_container', 
                        'left_overlay_widget', 'left_view_button',
                        'left_close_button', 'left_play_button']:
                if hasattr(self, attr):
                    delattr(self, attr)
        elif side == 'right':
            layout = self.result_layout
            # удаляем обработчик
            if hasattr(self, 'right_show_label'):
                self.right_show_label.resizeEvent = None
            # очищаем ссылки на правые виджеты
            for attr in ['right_show_label', 'right_show_container',
                        'right_overlay_widget', 'right_view_button',
                        'right_play_button']:
                if hasattr(self, attr):
                    delattr(self, attr)

        if layout:
            # удаляем все виджеты из layout
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget: 
                    widget.deleteLater()

            # удаляем ссылку на layout
            del layout
    
    def clear(self):
        """
        Удаляет отображаемый файл из области по кнопке закрытия.
        Так как пользователь может закрыть только исходный файл, то есть левый,
        здесь используются объекты конкретно левой стороны.
        """
        # освобождаем ресурсы из-под объекта-обработчика
        # if hasattr(self, 'processor'):
        #     self.processor.cleanup()
        #     del self.processor

        # останавливаем таймер, если он существует
        if hasattr(self, 'left_video_timer') and self.left_video_timer:
            self.left_video_timer.stop()
            del self.left_video_timer
        
        # освобождаем ресурсы VideoCapture, если есть
        if hasattr(self, 'left_cap') and self.left_cap:
            self.left_cap.release()
            del self.left_cap
        
        # останавливаем таймер, если он существует
        if hasattr(self, 'right_video_timer') and self.right_video_timer:
            self.right_video_timer.stop()
            del self.right_video_timer
        
        # освобождаем ресурсы VideoCapture, если есть
        if hasattr(self, 'right_cap') and self.right_cap:
            self.right_cap.release()
            del self.right_cap

        # удаляем виджеты из области отображения файлов
        if hasattr(self, 'file_layout'):
            self.delete_files_widgets('left')
        if hasattr(self, 'result_layout'):
            self.delete_files_widgets('right')

        # освобождает пути к обработанным и размеченным файлам
        if hasattr(self, 'processed_path'):
            del self.processed_path
        if hasattr(self, 'detected_path'):
            del self.detected_path
        if hasattr(self, 'detect_processed_path'):
            del self.detect_processed_path

        # очищаем правую сторону
        self.clear_right_side()

        # очищаем временную папку
        self.clear_temp_folder()

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
            self.left_show_label.setStyleSheet("background-color: white;")
            self.left_show_container = show_container
            self.file_layout.addWidget(self.left_show_container)
        elif side == 'right': 
            self.right_show_label = show_label
            self.right_show_label.setStyleSheet("background-color: white;")
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
        if hasattr(self, 'left_overlay_widget') and self.left_overlay_widget and \
           hasattr(self, 'left_show_label') and self.left_show_label:
            left_label_width = self.left_show_label.width()
            self.left_overlay_widget.move(left_label_width - self.left_overlay_widget.width() - 10, 10)
        if hasattr(self, 'right_overlay_widget') and self.right_overlay_widget and \
           hasattr(self, 'right_show_label') and self.right_show_label:
            right_label_width = self.right_show_label.width()
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
            # error_widget = QLabel()
            # error_widget.setText("Ошибка: не удалось загрузить изображение")
            # error_widget.setStyleSheet("color: red;")
            # error_widget.setAlignment(Qt.AlignCenter)
            # self.file_layout.addWidget(error_widget)
            self.show_errors(
                text="Ошибка: не удалось загрузить изображение", 
                parent_layout=self.file_layout
            )
            return

        # создаем элементы показа картинки
        self.create_show_elements(side=side)

        # создаем кнопки закрытия и просмотра
        self.create_service_buttons(type='image', close=close, side=side)

        print(self.left_show_label)
        
        # устанавливаем обработчик изменения размера изображения
        if side == 'left' and hasattr(self, 'left_show_label'):
            self.left_show_label.resizeEvent = lambda e: self.update_image_display(original_pixmap, side)
        elif side == 'right' and hasattr(self, 'right_show_label'): 
            print('right_handler')
            self.right_show_label.resizeEvent = lambda e: self.update_image_display(original_pixmap, side)

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
            if hasattr(self, 'detected_path') and self.detected_path:
                self.preview_window = PreviewWindowImage(self.detected_path)
                self.preview_window.show()
            elif hasattr(self, 'file_path') and self.file_path:
                self.preview_window = PreviewWindowImage(self.file_path)
                self.preview_window.show()
        elif side == 'right':
            if hasattr(self, 'detected_processed_path') and self.detected_processed_path:
                self.preview_window = PreviewWindowImage(self.detected_processed_path)
                self.preview_window.show()
            elif hasattr(self, 'processed_path') and self.processed_path:
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
            # error_widget = QLabel()
            # error_widget.setText("Ошибка: файл не найден")
            # error_widget.setStyleSheet("color: red;")
            # error_widget.setAlignment(Qt.AlignCenter)
            # self.file_layout.addWidget(error_widget)
            self.show_errors(
                text="Ошибка: файл не найден", 
                parent_layout=self.file_layout
            )
            return
        
        # загружаем видео с помощью OpenCV VideoCapture
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            # error_widget = QLabel()
            # error_widget.setText("Ошибка: не удалось открыть видео")
            # error_widget.setStyleSheet("color: red;")
            # error_widget.setAlignment(Qt.AlignCenter)
            # self.file_layout.addWidget(error_widget)
            self.show_errors(
                text="Ошибка: не удалось открыть видео", 
                parent_layout=self.file_layout
            )
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
            if hasattr(self, 'detected_path') and self.detected_path:
                self.preview_window = PreviewWindowVideo(self.detected_path)
                self.preview_window.show()
            elif hasattr(self, 'file_path') and self.file_path:
                self.preview_window = PreviewWindowVideo(self.file_path)
                self.preview_window.show()
        elif side == 'right': 
            if hasattr(self, 'detected_processed_path') and self.detected_processed_path:
                self.preview_window = PreviewWindowVideo(self.detected_processed_path)
                self.preview_window.show()
            elif hasattr(self, 'processed_path') and self.processed_path:
                self.preview_window = PreviewWindowVideo(self.processed_path)
                self.preview_window.show()

    # =========================================================================
    # ФУНКЦИИ ДЛЯ ОТОБРАЖЕНИЯ ДАТАСЕТА
    # =========================================================================

    def display_dataset(self, file_path, close, side):
        """
        Отображает иконку датасета в маленьком окошке.
        Параметр close определяет наличие кнопки закрытия.
        """
        # cоздаем иконку папки для представления датасета
        folder_icon = QPixmap("icons/folder_4.png")
        folder_pixmap = folder_icon.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # создаем элементы показа
        self.create_show_elements(side=side)

        # создаем кнопки закрытия и просмотра
        self.create_service_buttons(type='dataset', close=close, side=side)

        # добавляем иконку папки на виджет для отображения
        if side == 'left' and hasattr(self, 'left_show_label'):
            self.left_show_label.setAlignment(Qt.AlignCenter)
            self.left_show_label.setPixmap(folder_pixmap)
        elif side == 'right' and hasattr(self, 'right_show_label'):
            self.right_show_label.setAlignment(Qt.AlignCenter)
            self.right_show_label.setPixmap(folder_pixmap)

        # устанавливаем обработчики изменения размеров лейбла
        if side == 'left' and hasattr(self, 'left_show_label'):
            self.left_show_label.resizeEvent = lambda e: self.update_buttons_position()
        elif side == 'right' and hasattr(self, 'right_show_label'): 
            print('right_handler')
            self.right_show_label.resizeEvent = lambda e: self.update_buttons_position()

    def view_content_dataset(self, side):
        """
        Открывает окно просмотра с содержимым датасета.
        """        
        if side == 'left': 
            if hasattr(self, 'detected_path') and self.detected_path:
                self.preview_window = PreviewWindowDataset(self.detected_path)
                self.preview_window.show()
            elif hasattr(self, 'file_path') and self.file_path:
                self.preview_window = PreviewWindowDataset(self.file_path)
                self.preview_window.show()
        elif side == 'right': 
            if hasattr(self, 'detected_processed_path') and self.detected_processed_path:
                self.preview_window = PreviewWindowDataset(self.detected_processed_path)
                self.preview_window.show()
            elif hasattr(self, 'processed_path') and self.processed_path:
                self.preview_window = PreviewWindowDataset(self.processed_path)
                self.preview_window.show()


    # =========================================================================
    # ФУНКЦИИ ДЛЯ ЗАПОЛНЕНИЯ ПРАВОЙ СТОРОНЫ
    # =========================================================================
    
    def clear_right_side(self):
        """
        Очищает правую часть интерфейса.
        """
        # удаляем все виджеты из right_layout
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # удаляем ссылки на виджеты
        for attr in ['results_table', 'detect_button', 
                'download_process_button', 'download_process_detect_button']:
            if hasattr(self, attr):
                delattr(self, attr)
                
        # for i in reversed(range(self.right_layout.count())):
        #     widget = self.right_layout.itemAt(i).widget()
        #     if widget:
        #         widget.deleteLater()

        # if hasattr(self, 'result_layout'): self.delete_files_widgets('right')
        
    def upper_right_side(self):
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
        self.right_layout.addWidget(self.process_title)

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
        # self.result_widget.setMinimumHeight(200)
        # self.result_widget.setMinimumHeight(self.file_widget.height())
        # self.result_widget.setMaximumHeight(self.file_widget.height())
        self.sync_widgets_heights()
        self.result_layout = QVBoxLayout(self.result_widget)
        self.right_layout.addWidget(self.result_widget)

        self.right_layout.addStretch()


    def add_right_side_additional_elements(self):
        """
        Добавляет остальные элементы правой части после успешной обработки
        """
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
        self.results_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
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
        self.right_layout.addWidget(self.results_table)

        # кнопка для обнаружения объектов
        self.detect_button = QPushButton("Найти объекты")
        self.detect_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.detect_button.setFixedHeight(50)
        self.detect_button.setStyleSheet(self.buttons_style)
        self.detect_button.setFont(self.font)
        self.detect_button.clicked.connect(self.detect_objects)
        self.right_layout.addWidget(self.detect_button)

        # создаем контейнер под кнопки скачивания
        right_download_buttons_widget = QWidget()
        right_download_buttons_layout = QHBoxLayout(right_download_buttons_widget)
        right_download_buttons_layout.setContentsMargins(0, 0, 0, 0)  # убираем отступы
        right_download_buttons_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # кнопка для скачивания обработанного файла
        self.download_process_button = QPushButton()
        self.download_process_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.download_process_button.setFixedHeight(100)
        self.download_process_button.setStyleSheet(self.buttons_style)
        self.download_process_button.setFont(self.font)
        self.download_process_button.clicked.connect(lambda: self.download_files(self.processed_path))
        self.set_download_buttons_text()
        right_download_buttons_layout.addWidget(self.download_process_button)

        # кнопка для скачивания обработанного и размеченного файла
        self.download_process_detect_button = QPushButton()
        self.download_process_detect_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.download_process_detect_button.setFixedHeight(100)
        self.download_process_detect_button.setStyleSheet(self.buttons_style)
        self.download_process_detect_button.setFont(self.font)
        self.download_process_detect_button.clicked.connect(lambda: self.download_files(self.detected_processed_path))
        # self.process_button.clicked.connect(self.detect_objects)
        self.set_download_buttons_text()
        right_download_buttons_layout.addWidget(self.download_process_detect_button)

        self.right_layout.addWidget(right_download_buttons_widget)

        self.update_buttons_state()

        # кнопка для параллельного просмотра исходной версии и итоговой
        # self.compare_button = QPushButton("Сравнить с исходным")
        # self.compare_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.compare_button.setFixedHeight(40)
        # self.compare_button.setStyleSheet("background-color: gray; border-radius: 10px; padding: 10px;")
        # self.compare_button.setFont(self.font)
        # # self.process_button.clicked.connect(self.detect_objects)
        # right_layout.addWidget(self.compare_button)


    # =========================================================================
    # ФУНКЦИИ ДЛЯ ЗАПОЛНЕНИЯ ТАБЛИЦ
    # =========================================================================

    def update_gear_buttons(self, defect_key):
        # нужный словарь
        if self.process_type.currentText() == 'Ручная обработка':
            methods_dict = self.manual_methods  
        else:
            methods_dict = self.auto_methods

        # ключ метода
        method_key = next(
            key
            for key, method in methods_dict[defect_key]['methods'].items() 
            if method['checked']
        )
        
        # обновляем кнопку
        if defect_key in self.gear_buttons:
            gear_btn = self.gear_buttons[defect_key]
            if method_key == "no_process":
                gear_btn.setEnabled(False)
                gear_btn.setStyleSheet(self.gear_buttons_style['disabled'])
            else:
                gear_btn.setEnabled(True)
                gear_btn.setStyleSheet(self.gear_buttons_style['normal'])
    
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
        for row, defect_key in enumerate(self.auto_methods.keys()):
            # первый столбец - название дефекта
            item = QTableWidgetItem(self.auto_methods[defect_key]['defect_name'])
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
            self.gear_buttons[defect_key] = gear_btn

            self.update_gear_buttons(defect_key)
            
            # для автоматического режима
            if self.process_type.currentText() == 'Автоматическая обработка':
                # метод обработки
                method_name = next(
                    method['method_name'] 
                    for method in self.auto_methods[defect_key]['methods'].values() 
                    if method['checked']
                )
                method_label = QLabel(method_name)
                method_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(method_label, stretch=1)
                
                # кнопка шестерёнки (только просмотр)
                gear_btn.clicked.connect(
                    partial(self.__handle_gear_click, defect_key, method_name, False)
                )

            # для ручного режима   
            else:
                # выпадающий список методов
                combo = QComboBox()
                combo.addItems([
                    method['method_name'] 
                    for method in self.manual_methods[defect_key]['methods'].values()
                ])
                cheked_method_name = next(
                    method['method_name'] 
                    for method in self.manual_methods[defect_key]['methods'].values() 
                    if method['checked']
                )
                combo.setCurrentText(cheked_method_name)
                combo.setStyleSheet("QComboBox { padding: 2px; }")
                layout.addWidget(combo, stretch=1)
                
                # кнопка шестерёнки (редактирование)
                gear_btn.clicked.connect(
                    partial(self.__handle_combo_gear_click, defect_key, combo)
                )
                # при изменении выбора обновляем текущий метод
                combo.currentTextChanged.connect(
                    partial(self.update_current_method, defect_key)
                )
            
            # добавляем кнопку шестеренки в лайаут
            layout.addWidget(gear_btn)
            # устанавливаем контейнер в таблицу
            self.methods_table.setCellWidget(row, 1, container)
        
        # настройки внешнего вида таблицы
        self.methods_table.resizeRowsToContents()
        self.methods_table.setMinimumHeight(160)

    def __handle_gear_click(self, defect_en, method_name, editable):
        """
        Обработчик клика по шестеренке в автоматическом режиме.
        """
        self.show_parameters(defect_en, self.auto_methods, method_name, editable)

    def __handle_combo_gear_click(self, defect_en, combo):
        """
        Обработчик клика по шестеренке в ручном режиме.
        """
        method_name = combo.currentText()
        self.show_parameters(defect_en, self.manual_methods, method_name, True)
    
    def update_current_method(self, defect_key, method_name):
        """
        Обновляет текущий выбранный метод для дефекта (для ручного режима).
        """
        # обновляем словарь manual_methods
        for method_key, method_data in self.manual_methods[defect_key]['methods'].items():
            method_data['checked'] = (method_data['method_name'] == method_name)

        self.update_gear_buttons(defect_key)

        # if hasattr(self, 'current_methods'):
        #     self.current_methods[defect_key] = method_name
        # else:
        #     self.current_methods = {defect_key: method_name}
    
    def show_parameters(self, defect_key, methods_dict, method_name, editable):
        """
        Показывает параметры для выбранного метода обработки дефекта.
        """
        print(defect_key)
        print(method_name)
        print(methods_dict[defect_key])
        # получаем ключ выбранного метода
        checked_method_key = next(
            key 
            for key, method in methods_dict[defect_key]['methods'].items() 
            if method['checked']    
        )
        # получаем параметры для выбранного метода
        params = methods_dict[defect_key]['methods'][checked_method_key]['params']
        
        dialog = ParameterDialog(method_name, params, self.allowed_params_values, editable)
        if dialog.exec_() == QDialog.Accepted and editable:
            # сохраняем обновленные параметры
            methods_dict[defect_key]['methods'][checked_method_key]['params'] = dialog.get_parameters()

    
    def update_results_table(self):
        """
        Обновляет таблицу результатов в соответствии с полученным 
        с бэкенда словарем.
        """
        if hasattr(self, 'result'):
            # полная очистка таблицы
            self.results_table.clearContents()
            
            # заполняем таблицу
            for row, defect_key in enumerate(self.auto_methods.keys()):                
                # получаем значения для этого дефекта
                detected, fixed = self.result.get(defect_key, [0, 0])
                
                # создаем ячейки
                item_defect = QTableWidgetItem(self.auto_methods[defect_key]['defect_name'])
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

    def show_processing(self, side, message='', show=True):
        """
        Общая функция для отображения спиннера в процессе обработки/распонавания.
        """
        if side == 'left':
            container_attr = 'left_processing_container'
            movie_attr = 'left_movie'
            label_attr = 'left_processing_label'
            widget = self.file_widget
            layout = self.file_layout
        else:
            container_attr = 'right_processing_container'
            movie_attr = 'right_movie'
            label_attr = 'right_processing_label'
            widget = self.result_widget
            layout = self.result_layout

        if show:
            # удаляем предыдущие элементы, если они есть
            if hasattr(self, container_attr):
                getattr(self, container_attr).deleteLater()
                delattr(self, container_attr)
            
            # создаем основной контейнер
            container = QWidget(widget)
            setattr(self, container_attr, container)
            container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # главный layout контейнера
            main_layout = QVBoxLayout(container)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # центрирующий виджет
            center_widget = QWidget()
            center_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            center_layout = QVBoxLayout(center_widget)
            center_layout.setContentsMargins(0, 0, 0, 0)
            center_layout.setSpacing(0)  # минимальное расстояние между гифкой и текстом
            
            # виджет с гифкой
            gif_widget = QWidget()
            gif_widget.setFixedSize(200, 200)
            gif_layout = QVBoxLayout(gif_widget)
            gif_layout.setContentsMargins(0, 0, 0, 0)
            gif_layout.setAlignment(Qt.AlignCenter)
            
            # создаем и настраиваем QMovie
            movie = QMovie("icons/loading.gif")
            movie.setScaledSize(QSize(200, 200))
            setattr(self, movie_attr, movie)
            
            # лейбл для отображения гифки
            spinner = QLabel()
            spinner.setAlignment(Qt.AlignCenter)
            spinner.setMovie(movie)
            movie.start()
            gif_layout.addWidget(spinner)
            
            # текст под гифкой
            label = QLabel(message)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #333333;
                    font-weight: bold;
                }
            """)
            label.setWordWrap(True)
            label.setMinimumWidth(300)
            # label.setMinimumHeight(40)
            setattr(self, label_attr, label)
            
            # добавляем гифку и текст в центр
            center_layout.addStretch()
            center_layout.addWidget(gif_widget, 0, Qt.AlignCenter)
            center_layout.addWidget(label, 0, Qt.AlignCenter)
            center_layout.addStretch()
            
            # добавляем центрирующий виджет в основной layout
            main_layout.addWidget(center_widget)
            
            layout.addWidget(container)
            container.show()
        else:
            # останавливаем и удаляем QMovie
            if hasattr(self, movie_attr):
                getattr(self, movie_attr).stop()
                getattr(self, movie_attr).deleteLater()
                delattr(self, movie_attr)
            
            # удаляем контейнер и метку
            if hasattr(self, container_attr):
                getattr(self, container_attr).deleteLater()
                delattr(self, container_attr)
            if hasattr(self, label_attr):
                delattr(self, label_attr)


    def processing(self):
        # очищаем правую сторону
        self.clear_right_side()
        # добавляем заголовок и область под результат обработки
        self.upper_right_side()

        # передаем на бэкенд текущие параметры для ручной обработки
        self.processor.set_manual_methods(self.manual_methods)

        # блокируем кнопку закрытия
        self.left_close_button.setEnabled(False)

        # создаем и настраиваем спиннер
        self.show_processing(
            side='right', 
            message='Идет обработка...', 
            show=True
        )
        
        # подготавливаем настройки для обработчика
        settings = {
            'file_type': self.file_type.currentText(),
            'process_type': self.process_type.currentText(),
            'defects_type': self.defects_processing_type.currentText()
        }
        
        # создаем и запускаем поток с обработкой
        self.worker = ProcessingWorker(self.processor, settings)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.worker.start()

    def on_processing_finished(self, processed_path, result):
        """
        Вызывается при успешном завершении процесса обработки.
        """
        # завершаем показ спиннера
        self.show_processing(
            side='right',
            show=False
        )
        # получаем результаты
        self.processed_path = processed_path
        self.result = result
        
        # обновляем интерфейс
        if self.processed_path:
            self.update_display(file_path=self.processed_path, close=False, side='right')
            self.add_right_side_additional_elements()
            self.update_results_table()
            self.update_buttons_state()
            self.left_close_button.setEnabled(True)

    def on_processing_error(self):
        """
        Вызывается, когда в процессе обработки возникает ошибка.
        """
        self.show_processing(
            side='right',
            show=False
        )
        self.show_errors(
            text="Ошибка в процессе исправления дефектов",
            parent_layout=self.result_layout
        )

    
    # =========================================================================
    # РАСПОЗНАВАНИЕ ОБЪЕКТОВ
    # =========================================================================

    def detect_objects(self):
        # удаляем виджеты из области отображения файлов
        if hasattr(self, 'file_layout'):
            self.delete_files_widgets('left')
        if hasattr(self, 'result_layout'):
            self.delete_files_widgets('right')

        # создаем и настраиваем спиннер
        self.show_processing(
            side='left', 
            message='Распознавание объектов...', 
            show=True
        )
        self.show_processing(
            side='right', 
            message='Распознавание объектов...', 
            show=True
        )
        
        # подготавливаем настройки для распознавателя
        settings = {
            'file_type': self.file_type.currentText(),
        }
        
        # создаем и запускаем поток с распознаванием
        self.detect_worker = DetectingWorker(self.processor, settings)
        self.detect_worker.finished.connect(self.on_detecting_finished)
        self.detect_worker.error.connect(self.on_detecting_error)
        self.detect_worker.start()

    def on_detecting_finished(self, detected_path, detected_processed_path):
        """
        Вызывается при успешном завершении распознавания объектов.
        """
        # убираем спиннер
        self.show_processing(
            side='left', 
            show=False
        )
        self.show_processing(
            side='right',  
            show=False
        )
        # получаем результаты
        self.detected_path = detected_path
        self.detected_processed_path = detected_processed_path

        # очищаем области отображения файлов
        if hasattr(self, 'file_layout'):
            self.delete_files_widgets('left')
        if hasattr(self, 'result_layout'):
            self.delete_files_widgets('right')

        # отображаем исходный размеченный файл слева
        if self.detected_path and os.path.exists(self.detected_path):
            if self.file_type.currentText() == 'Обработка изображения':
                self.display_image(file_path=self.detected_path, close=True, side='left')
            elif self.file_type.currentText() == 'Обработка видео':
                self.display_video(file_path=self.detected_path, close=True, side='left')
            elif self.file_type.currentText() == 'Обработка датасета':
                self.display_dataset(file_path=self.detected_path, close=True, side='left')
        
        # отображаем обработанный размеченный файл справа
        if self.detected_processed_path and os.path.exists(self.detected_processed_path):
            if self.file_type.currentText() == 'Обработка изображения':
                self.display_image(file_path=self.detected_processed_path, close=False, side='right')
            elif self.file_type.currentText() == 'Обработка видео':
                self.display_video(file_path=self.detected_processed_path, close=False, side='right')
            elif self.file_type.currentText() == 'Обработка датасета':
                self.display_dataset(file_path=self.detected_processed_path, close=False, side='right')
        
        # обновляем состояние кнопок
        self.update_buttons_state()

    def on_detecting_error(self):
        """
        Вызывается, когда в процессе распознавания возникает ошибка.
        """
        self.show_processing(
            side='left', 
            show=False
        )
        self.show_processing(
            side='right',  
            show=False
        )
        self.show_errors(
            text="Ошибка в процессе распознавания объектов",
            parent_layout=self.file_layout
        )
        self.show_errors(
            text="Ошибка в процессе распознавания объектов",
            parent_layout=self.result_layout
        )