from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTextEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QAction,
    QDesktopWidget, QFrame, QLineEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, 
    QSizePolicy, QHeaderView, QPushButton, QStyledItemDelegate, 
    QFileDialog, QGraphicsView, QGraphicsScene, QDialog, QFormLayout,
    QSpinBox, QDoubleSpinBox, QScrollArea
)
from PyQt5.QtGui import (
    QPalette, QColor, QFont, QIntValidator, 
    QDoubleValidator, QRegExpValidator, QRegularExpressionValidator,
    QPixmap, QImage, QIcon, QTransform
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRegExp, QRegularExpression, QSize, QRectF

# class ParameterDialog(QDialog):
#     def __init__(self, method_name, parameters, editable=False, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle(f"Параметры: {method_name}")
#         self.setModal(True)
#         self.setMinimumWidth(300)
        
#         scroll = QScrollArea()
#         scroll.setWidgetResizable(True)
#         content = QWidget()
#         layout = QFormLayout(content)
        
#         self.widgets = {}
        
#         for name, value in parameters.items():
#             row_widget = QWidget()
#             row_layout = QHBoxLayout(row_widget)
#             row_layout.setContentsMargins(0, 0, 0, 0)

#             if isinstance(value, int):
#                 widget = QSpinBox()
#                 widget.setRange(0, 1000)
#                 widget.setValue(value)
#                 widget_type == 'int'
#             elif isinstance(value, float):
#                 widget = QDoubleSpinBox()
#                 widget.setRange(0.0, 1000.0)
#                 widget.setSingleStep(0.1)
#                 widget.setValue(value)
#                 widget_type = 'float'
#             elif isinstance(value, list):
#                 widget = QComboBox()
#                 widget.addItems(value)
#                 widget.setCurrentIndex(0)
#                 widget_type = 'combo'
#             elif isinstance(value, tuple) and len(value) == 2:
#                 label_left = QLabel("(")
#                 spin1 = QSpinBox()
#                 spin1.setRange(0, 1000)
#                 spin1.setValue(value[0])
#                 label_comma = QLabel(",")
#                 spin2 = QSpinBox()
#                 spin2.setRange(0, 1000)
#                 spin2.setValue(value[1])
#                 label_right = QLabel(")")
                
#                 row_layout.addWidget(label_left)
#                 row_layout.addWidget(spin1)
#                 row_layout.addWidget(label_comma)
#                 row_layout.addWidget(spin2)
#                 row_layout.addWidget(label_right)
                
#                 widget = (spin1, spin2)
#                 widget_type = 'tuple'

#             if not isinstance(value, tuple):
#                 row_layout.addWidget(widget)
#                 row_layout.addStretch()
            
#             widget.setEnabled(editable)
#             layout.addRow(name, widget)
#             self.widgets[name] = widget

#             if name == 'estimate_noise':
#                 widget.currentTextChanged.connect(lambda: self.update_dependencies('sigma', 'estimate_noise', 'gaussian'))
        
#         scroll.setWidget(content)
        
#         main_layout = QVBoxLayout(self)
#         main_layout.addWidget(scroll)
        
#         if editable:
#             buttons = QWidget()
#             buttons_layout = QHBoxLayout(buttons)
#             buttons_layout.addStretch()
            
#             ok_button = QPushButton("OK")
#             ok_button.clicked.connect(self.accept)
#             buttons_layout.addWidget(ok_button)
            
#             cancel_button = QPushButton("Отмена")
#             cancel_button.clicked.connect(self.reject)
#             buttons_layout.addWidget(cancel_button)
            
#             main_layout.addWidget(buttons)
    
#     def update_dependencies(self, dependent_widget_name, main_widget_name, condition_name):
#         """
#         Обновляет видимость зависимых параметров.
#         Принимает в качестве параметров название зависимого параметра,
#         название того параметра, от которого он зависит, и название условия 
#         (значения основного параметра, который определяет видимость)
#         """
#         if dependent_widget_name in self.widgets:
#             dependent_widget, _ = self.widgets[dependent_widget_name]
#             main_widget, _ = self.widgets[main_widget_name]
#             dependent_widget.setVisible(main_widget.currentText() == condition_name)
    
#     def get_parameters(self):
#         params = {}
#         for name, (widget, widget_type) in self.widgets.items():
#             if widget_type == 'tuple':
#                 params[name] = (widget[0].value(), widget[1].value())
#             elif widget_type == 'int':
#                 params[name] = widget.value()
#             elif widget_type == 'float':
#                 params[name] = widget.value()
#             elif widget_type == 'combo':
#                 params[name] = widget.currentText()
#             else:
#                 params[name] = widget.text()
#         return params



# class ParameterDialog(QDialog):
#     def __init__(self, method_name, parameters, editable=False, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle(f"Параметры: {method_name}")
#         self.setModal(True)
#         self.setMinimumWidth(300)
        
#         scroll = QScrollArea()
#         scroll.setWidgetResizable(True)
#         content = QWidget()
#         layout = QFormLayout(content)
        
#         self.widgets = {}
#         self.rows = {}

#         self.dependencies = {
#             'sigma': {'source': 'estimate_noise', 'condition': ['gaussian']},
#             'gradient_method': {'source': 'mask_mode', 'condition': ['gradient', 'combine']},
#             'gradient_threshold': {'source': 'mask_mode', 'condition': ['gradient', 'combine']},
#         }
        
#         for name, value in parameters.items():
#             row_widget = QWidget()
#             row_layout = QHBoxLayout(row_widget)
#             row_layout.setContentsMargins(0, 0, 0, 0)

#             if isinstance(value, int):
#                 widget = QSpinBox()
#                 widget.setRange(0, 1000)
#                 widget.setValue(value)
#                 widget_type = 'int'  # Исправлено с == на =
#             elif isinstance(value, float):
#                 widget = QDoubleSpinBox()
#                 widget.setRange(0.0, 1000.0)
#                 widget.setSingleStep(0.1)
#                 widget.setValue(value)
#                 widget_type = 'float'
#             elif isinstance(value, list):
#                 widget = QComboBox()
#                 widget.addItems(value)
#                 widget.setCurrentIndex(0)
#                 widget_type = 'combo'
#             elif isinstance(value, tuple) and len(value) == 2:
#                 label_left = QLabel("(")
#                 spin1 = QSpinBox()
#                 spin1.setRange(0, 1000)
#                 spin1.setValue(value[0])
#                 label_comma = QLabel(",")
#                 spin2 = QSpinBox()
#                 spin2.setRange(0, 1000)
#                 spin2.setValue(value[1])
#                 label_right = QLabel(")")
                
#                 row_layout.addWidget(label_left)
#                 row_layout.addWidget(spin1)
#                 row_layout.addWidget(label_comma)
#                 row_layout.addWidget(spin2)
#                 row_layout.addWidget(label_right)
                
#                 widget = (spin1, spin2)
#                 widget_type = 'tuple'

#                 spin1.setEnabled(editable)
#                 spin2.setEnabled(editable)
#             else:
#                 widget = QLineEdit(str(value))
#                 widget_type = 'text'

#             if not isinstance(value, tuple):
#                 row_layout.addWidget(widget)
#                 row_layout.addStretch()
#                 widget.setEnabled(editable)

#             layout.addRow(name, row_widget)
#             self.widgets[name] = (widget, widget_type)

#             label = QLabel(name)
#             self.rows[name] = (label, row_widget)

#             self.init_dependencies()
        
#         scroll.setWidget(content)
        
#         main_layout = QVBoxLayout(self)
#         main_layout.addWidget(scroll)
        
#         if editable:
#             buttons = QWidget()
#             buttons_layout = QHBoxLayout(buttons)
#             buttons_layout.addStretch()
            
#             ok_button = QPushButton("OK")
#             ok_button.clicked.connect(self.accept)
#             buttons_layout.addWidget(ok_button)
            
#             cancel_button = QPushButton("Отмена")
#             cancel_button.clicked.connect(self.reject)
#             buttons_layout.addWidget(cancel_button)
            
#             main_layout.addWidget(buttons)
    
#     def init_dependencies(self):
#         """
#         Вызывает функцию, скрывающую и показывающую параметры, используя информацию
#         о зависимостях из self.dependencies. В этом словаре хранятся названия зависимых
#         виджетов; виджетов, от которых они зависят (главных); и значений главных виджетов,
#         определяющих наличие зависимых виджетов.
#         """
#         for dep, config in self.dependencies.items():
#             if dep in self.widgets and config['source'] in self.widgets:
#                 source_widget, _ = self.widgets[config['source']]
#                 source_widget.currentTextChanged.connect(
#                     lambda text, d=dep, c=config: self.update_dependencies(d, c['source'], c['condition'])
#                 )
#                 self.update_dependencies(dep, config['source'], config['condition'])
    
#     def update_dependencies(self, dependent_widget_name, main_widget_name, conditions):
#         """
#         Обновляет видимость зависимых параметров.
#         """
#         if dependent_widget_name in self.rows and main_widget_name in self.widgets:
#             label, row_widget = self.rows[dependent_widget_name]
#             main_widget, _ = self.widgets[main_widget_name]
            
#             # Получаем текущее значение главного виджета
#             if isinstance(main_widget, QComboBox):
#                 current_value = main_widget.currentText()
#             else:
#                 current_value = str(main_widget.value())

#             # Проверяем условие видимости
#             should_show = current_value in conditions
            
#             # Устанавливаем видимость всей строки
#             label.setVisible(should_show)
#             row_widget.setVisible(should_show)
    
#     def get_parameters(self):
#         params = {}
#         for name, (widget, widget_type) in self.widgets.items():
#             if widget_type == 'tuple':
#                 params[name] = (widget[0].value(), widget[1].value())
#             elif widget_type == 'int':
#                 params[name] = widget.value()
#             elif widget_type == 'float':
#                 params[name] = widget.value()
#             elif widget_type == 'combo':
#                 params[name] = widget.currentText()
#             else:
#                 params[name] = widget.text()
#         return params
    



class ParameterDialog(QDialog):
    def __init__(self, method_name, parameters, editable=False, parent=None):
        super().__init__(parent)
        self.method_name = method_name
        self.editable = editable
        self.setWindowTitle(f"Параметры: {method_name}")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        # Глубокое копирование параметров
        self.original_parameters = {k: v[:] if isinstance(v, list) else v for k, v in parameters.items()}
        self.current_parameters = {k: v[:] if isinstance(v, list) else v for k, v in parameters.items()}
        
        self.init_ui()
        self.setup_dependencies()
        
    def init_ui(self):
        # Полная очистка предыдущего состояния
        if hasattr(self, 'scroll_area'):
            self.scroll_area.deleteLater()
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.content_widget = QWidget()
        self.layout = QFormLayout(self.content_widget)
        self.layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.widgets = {}
        self.rows = {}
        
        # Создаем виджеты в фиксированном порядке
        param_order = ['mask_mode', 'gradient_method', 'gradient_threshold'] + \
                     [p for p in self.current_parameters.keys() if p not in ['mask_mode', 'gradient_method', 'gradient_threshold']]
        
        for name in param_order:
            if name in self.current_parameters:
                self.create_parameter_row(name, self.current_parameters[name])
        
        self.scroll_area.setWidget(self.content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll_area)
        
        if self.editable:
            self.add_control_buttons(main_layout)
        
        # Принудительное обновление после полной инициализации
        QTimer.singleShot(100, self.force_update_dependencies)
    
    def setup_dependencies(self):
        """Явная настройка зависимостей с проверкой"""
        self.dependencies = {
            'sigma': {
                'source': 'estimate_noise',
                'condition': ['gaussian'],
                'widget_type': 'float'
            },
            'gradient_method': {
                'source': 'mask_mode',
                'condition': ['gradient', 'combine'],
                'widget_type': 'combo'
            },
            'gradient_threshold': {
                'source': 'mask_mode',
                'condition': ['gradient', 'combine'],
                'widget_type': 'int'
            }
        }
        
        # Проверка доступности всех виджетов
        for dep, config in self.dependencies.items():
            if dep not in self.widgets:
                print(f"Ошибка: виджет для '{dep}' не создан")
            if config['source'] not in self.widgets:
                print(f"Ошибка: источник '{config['source']}' для '{dep}' не найден")
    
    def force_update_dependencies(self):
        """Принудительное обновление всех зависимостей"""
        for dep, config in self.dependencies.items():
            if dep in self.widgets and config['source'] in self.widgets:
                source_widget = self.widgets[config['source']][0]
                current_value = source_widget.currentText() if isinstance(source_widget, QComboBox) else str(source_widget.value())
                print(f"Проверка зависимости: {dep} <- {config['source']} = {current_value} (должно быть в {config['condition']})")
                
                should_show = current_value in config['condition']
                label, widget = self.rows[dep]
                label.setVisible(should_show)
                widget.setVisible(should_show)
        
        self.content_widget.adjustSize()
    
    def create_parameter_row(self, name, value):
        """Создание строки параметра с сохранением всех вариантов для комбобоксов"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # Получаем оригинальное значение для определения типа
        original_value = self.original_parameters.get(name, value)
        
        if isinstance(original_value, list):
            widget = QComboBox()
            widget.addItems(original_value)
            # Устанавливаем текущее значение, если оно есть в списке
            if str(value) in original_value:
                widget.setCurrentText(str(value))
            widget_type = 'combo'
            
            if name == 'estimate_noise':
                widget.currentTextChanged.connect(self.force_update_dependencies)
            elif name == 'mask_mode':
                widget.currentTextChanged.connect(self.on_mask_mode_changed)
        elif isinstance(original_value, int):
            widget = QSpinBox()
            widget.setRange(0, 1000)
            widget.setValue(int(value))
            widget_type = 'int'
        elif isinstance(original_value, float):
            widget = QDoubleSpinBox()
            widget.setRange(-1000.0, 1000.0)
            widget.setSingleStep(0.1)
            widget.setValue(float(value))
            widget_type = 'float'
        else:
            widget = QLineEdit(str(value))
            widget_type = 'text'

        row_layout.addWidget(widget)
        row_layout.addStretch()
        widget.setEnabled(self.editable)

        label = QLabel(name)
        self.layout.addRow(label, row_widget)
        self.widgets[name] = (widget, widget_type)
        self.rows[name] = (label, row_widget)
    
    def on_mask_mode_changed(self, value):
        """Специальный обработчик для mask_mode"""
        print(f"mask_mode изменён на: {value}")
        self.force_update_dependencies()
    
    def add_control_buttons(self, layout):
        """Добавление кнопок управления"""
        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.save_and_close)
        buttons_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addWidget(buttons)
    
    def save_and_close(self):
        """Сохранение параметров и закрытие"""
        self.current_parameters = self.get_parameters()
        self.accept()
    
    def get_parameters(self):
        """Получение текущих параметров с сохранением всех вариантов для комбобоксов"""
        params = {}
        for name, (widget, widget_type) in self.widgets.items():
            if name in self.original_parameters:
                original_value = self.original_parameters[name]
                
                if isinstance(original_value, list):
                    # Для комбобоксов сохраняем весь список и текущий выбор
                    params[name] = original_value.copy()  # Сохраняем все варианты
                    if widget_type == 'combo':
                        selected = widget.currentText()
                        # Перемещаем выбранный элемент на первое место
                        if selected in params[name]:
                            params[name].remove(selected)
                            params[name].insert(0, selected)
                elif isinstance(original_value, int):
                    params[name] = int(widget.value())
                elif isinstance(original_value, float):
                    params[name] = float(widget.value())
                else:
                    params[name] = widget.text()
        return params