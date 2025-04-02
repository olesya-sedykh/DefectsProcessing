from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTextEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QAction,
    QDesktopWidget, QFrame, QLineEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, 
    QSizePolicy, QHeaderView, QPushButton, QStyledItemDelegate, 
    QFileDialog, QGraphicsView, QGraphicsScene, QDialog
)
from PyQt5.QtGui import (
    QPalette, QColor, QFont, QIntValidator, 
    QDoubleValidator, QRegExpValidator, QRegularExpressionValidator,
    QPixmap, QImage, QIcon, QTransform
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRegExp, QRegularExpression, QSize, QRectF

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
        font = QFont()
        font.setPointSize(10)

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
        self.file_type.setFont(font)
        left_layout.addWidget(self.file_type)

        # область для загрузки и отображения файлов
        self.file_widget = QWidget()
        self.file_widget.setStyleSheet("background-color: lightgray; border-radius: 20px;")
        # self.file_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.file_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.file_layout = QVBoxLayout(self.file_widget)
        left_layout.addWidget(self.file_widget)
        # left_layout.addStretch(60)

        # контейнер для кнопки загрузки
        load_button_container = QWidget()
        load_button_layout = QVBoxLayout(load_button_container)

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
        self.load_button.setFont(font)
        self.load_button.clicked.connect(self.load_file)
        button_horizontal_layout.addWidget(self.load_button)

        # пространство справа от кнопки
        button_horizontal_layout.addStretch()

        # добавляем горизонтальный layout в вертикальный
        load_button_layout.addLayout(button_horizontal_layout)

        # добавляем контейнер с кнопкой в file_layout
        self.file_layout.addWidget(load_button_container)

        # выпадающий список для выбора способа исправления дефектов
        self.defects_processing_type = QComboBox()
        self.defects_processing_type.addItem("Исправить все дефекты")
        self.defects_processing_type.addItem("Исправить основной дефект")
        # self.defects_processing_type.setFixedHeight(40)
        self.defects_processing_type.setMinimumHeight(40)
        self.defects_processing_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.defects_processing_type.setFont(font)
        left_layout.addWidget(self.defects_processing_type)
        
        # выпадающий список для выбора способа обработки
        self.process_type = QComboBox()
        self.process_type.addItem("Автоматическая обработка")
        self.process_type.addItem("Ручная обработка")
        # self.process_type.setFixedHeight(40)
        self.process_type.setMinimumHeight(40)
        self.process_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.process_type.setFont(font)
        left_layout.addWidget(self.process_type)
        self.process_type.currentIndexChanged.connect(self.update_methods_table)

        # таблица с методами исправления дефектов
        self.methods_table = QTableWidget()
        self.methods_table.setRowCount(4)
        self.methods_table.setColumnCount(2)
        self.methods_table.setHorizontalHeaderLabels(["Дефект", "Метод обработки"])
        self.methods_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # растяжение столбцоы по ширине таблицы
        self.methods_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.methods_table.verticalHeader().setVisible(False)
        self.methods_table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.methods_table.setEditTriggers(QTableWidget.NoEditTriggers) # запрет редактирования
        
        # заполнение строк таблицы дефектами
        defects = ["Размытие", "Низкая контрастность", "Блики", "Шум"]
        for row, defect in enumerate(defects):
            item = QTableWidgetItem(defect) # создание ячейки
            item.setTextAlignment(Qt.AlignCenter) # выравнивание ячейки
            self.methods_table.setItem(row, 0, item) # помещение ячейки в таблицу в строку row, столбец 0
        
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
        
        self.update_methods_table()
        left_layout.addWidget(self.methods_table)

        # распределение размеров элементов по высоте для левой стороны
        left_layout.setStretch(0, 10)
        left_layout.setStretch(1, 45)  # 30% для file_widget (первый добавленный элемент)
        left_layout.setStretch(2, 10)   # 5% для defects_processing_type
        left_layout.setStretch(3, 10)   # 5% для process_type
        left_layout.setStretch(4, 25)  # 60% для methods_table

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

    def display_image(self):
        # Очищаем file_widget от предыдущих виджетов
        for i in reversed(range(self.file_layout.count())):
            widget = self.file_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Создаем контейнер с абсолютным позиционированием
        self.image_container = QWidget()
        self.image_container.setLayout(QVBoxLayout())
        self.image_container.layout().setContentsMargins(0, 0, 0, 0)
        
        # Создаем QLabel для изображения
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        # Загружаем изображение
        self.original_pixmap = QPixmap(self.file_path)
        if self.original_pixmap.isNull():
            print("Не удалось загрузить изображение")
            return
        
        # Первоначальное отображение центральной части
        self.update_cropped_image()
        
        # Создаем кнопку просмотра
        self.view_button = QPushButton()
        self.view_button.setIcon(QIcon.fromTheme("view-refresh"))
        self.view_button.setIconSize(QSize(24, 24))
        self.view_button.setFixedSize(32, 32)
        self.view_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 150);
                border-radius: 16px;
                border: 1px solid gray;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 200);
            }
        """)
        self.view_button.clicked.connect(self.view_content)
        
        # Размещаем кнопку в правом нижнем углу
        self.button_container = QWidget(self.image_container)
        self.button_container.setAttribute(Qt.WA_TransparentForMouseEvents)
        button_layout = QHBoxLayout(self.button_container)
        button_layout.setContentsMargins(0, 0, 10, 10)
        button_layout.addStretch()
        button_layout.addWidget(self.view_button)
        
        # Добавляем элементы в контейнер
        self.image_container.layout().addWidget(self.image_label)
        self.file_layout.addWidget(self.image_container)
        
        # Устанавливаем обработчик изменения размера (только один раз!)
        if not hasattr(self, '_size_connected'):
            self.image_container.installEventFilter(self)
            self._size_connected = True

    def eventFilter(self, obj, event):
        """Обработчик изменения размера без рекурсии"""
        if event.type() == event.Resize and obj == self.image_container:
            self.update_cropped_image()
        return super().eventFilter(obj, event)

    def update_cropped_image(self):
        """Обновляет отображаемую центральную часть изображения"""
        if hasattr(self, 'original_pixmap'):
            # Получаем текущие размеры области отображения
            width = self.image_container.width()
            height = self.image_container.height()
            
            # Вычисляем область для вырезания (центральная часть)
            img_width = self.original_pixmap.width()
            img_height = self.original_pixmap.height()
            
            # Координаты для вырезания центральной части
            crop_x = max(0, (img_width - width) // 2)
            crop_y = max(0, (img_height - height) // 2)
            crop_width = min(width, img_width)
            crop_height = min(height, img_height)
            
            # Вырезаем и масштабируем
            cropped = self.original_pixmap.copy(crop_x, crop_y, crop_width, crop_height)
            scaled = cropped.scaled(
                width, height, 
                Qt.IgnoreAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)

    def view_content(self):
        """
        Открывает окно просмотра с полным изображением.
        """
        if hasattr(self, 'file_path') and self.file_path:
            self.preview_window = PreviewWindow(self.file_path)  # Создаем окно просмотра
            self.preview_window.show()  # Показываем окно


    def update_methods_table(self):
        """
        Обновляет заполнение таблицы.
        """
        processing_type = self.process_type.currentText()
        print('processing_type', processing_type)
        
        for row in range(self.methods_table.rowCount()):
            self.methods_table.setItem(row, 1, None)  # Удаляем QTableWidgetItem если был
            widget = self.methods_table.cellWidget(row, 1)
            if widget:
                widget.deleteLater()
            
            # в случае автоматической обработки просто показываем названия методов
            if self.process_type.currentIndex() == 0:
                method_item = QTableWidgetItem(self.automatic_methods[row])
                method_item.setTextAlignment(Qt.AlignCenter)
                self.methods_table.setItem(row, 1, method_item)
            
            # в случае ручной обработки для каждого дефекта можно выбрать метод
            else:
                defect = self.methods_table.item(row, 0).text()
                combo = QComboBox()
                combo.addItems(self.manual_options[defect])
                combo.setCurrentIndex(0)
                self.methods_table.setCellWidget(row, 1, combo)
        
        self.methods_table.resizeRowsToContents()

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