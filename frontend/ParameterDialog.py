from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QDialog, QFormLayout,
    QSpinBox, QDoubleSpinBox, QScrollArea
)
from PyQt5.QtCore import QTimer

class ParameterDialog(QDialog):
    def __init__(self, method_name, parameters, allowed_params_values, editable=False, parent=None):
        super().__init__(parent)
        self.method_name = method_name
        self.allowed_params_values = allowed_params_values
        self.editable = editable

        self.setWindowTitle(f"Параметры: {method_name}")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        # глубокое копирование параметров
        self.original_parameters = {k: v[:] if isinstance(v, list) else v for k, v in parameters.items()}
        self.current_parameters = {k: v[:] if isinstance(v, list) else v for k, v in parameters.items()}
        
        # начальная инициализация
        self.init_ui()
        # зависимости параметров (когда наличие одного зависит от другого)
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

        # self.setup_dependencies()
        
    def init_ui(self):
        """
        Начальная инициализация.
        """
        # полная очистка предыдущего состояния
        if hasattr(self, 'scroll_area'):
            self.scroll_area.deleteLater()
        
        # создание области под параметры
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # создание виджета самой формы
        self.content_widget = QWidget()
        self.content_layout = QFormLayout(self.content_widget)
        self.content_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.widgets = {}
        self.rows = {}
        
        # список полей ввода в нужном порядке
        param_order = ['mask_mode', 'gradient_method', 'gradient_threshold'] + \
                     [p for p in self.current_parameters.keys() if p not in ['mask_mode', 'gradient_method', 'gradient_threshold']]
        
        for parameter_name in param_order:
            # берем лишь те параметры из списка, которые нам нужны в текущий момент
            if parameter_name in self.current_parameters:
                self.create_parameter_row(parameter_name, self.current_parameters[parameter_name])
        
        # добавляем виджет формы в область
        self.scroll_area.setWidget(self.content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll_area)
        
        # добавляем кнопки согласия и отмены
        if self.editable:
            self.add_control_buttons(main_layout)
        
        # принудительное обновление после полной инициализации
        QTimer.singleShot(100, self.force_update_dependencies)
    
    def force_update_dependencies(self):
        """
        Принудительное обновление всех зависимостей.
        """
        for dependent, config in self.dependencies.items():
            if dependent in self.widgets and config['source'] in self.widgets:
                source_widget = self.widgets[config['source']][0]
                # сохраняем значение главного виджета
                if isinstance(source_widget, QComboBox):
                    current_value = source_widget.currentText()
                else:
                    current_value = str(source_widget.value())
                # print(f"Проверка зависимости: {dependent} <- {config['source']} = {current_value} (должно быть в {config['condition']})")
                
                # определяем по условию, должен ли зависимый виджет отображаться
                should_show = current_value in config['condition']
                label, widget = self.rows[dependent]
                label.setVisible(should_show)
                widget.setVisible(should_show)
        
        # автоматическое обновление размеров виджета в соответствии с содержимым
        self.content_widget.adjustSize()
    
    def create_parameter_row(self, name, value):
        """
        Создание строки параметра.
        """
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # берется значение по ключу name, а если его нет, то берется value
        original_value = self.original_parameters.get(name, value)
        
        if isinstance(original_value, str):
            widget = QComboBox()
            items = self.allowed_params_values[name]
            widget.addItems(items)
            widget.setCurrentText(str(original_value))
            widget_type = 'combo'
            
            if name == 'estimate_noise' or name == 'mask_mode':
                widget.currentTextChanged.connect(self.force_update_dependencies)
            # elif name == 'mask_mode':
            #     widget.currentTextChanged.connect(self.on_mask_mode_changed)
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
        elif isinstance(original_value, tuple) and len(value) == 2:
            label_left = QLabel("(")
            spin1 = QSpinBox()
            spin1.setRange(0, 1000)
            spin1.setValue(original_value[0])
            spin1.setEnabled(self.editable)

            label_comma = QLabel(",")

            spin2 = QSpinBox()
            spin2.setRange(0, 1000)
            spin2.setValue(original_value[1])
            spin2.setEnabled(self.editable)
            label_right = QLabel(")")
    
            row_layout.addWidget(label_left)
            row_layout.addWidget(spin1)
            row_layout.addWidget(label_comma)
            row_layout.addWidget(spin2)
            row_layout.addWidget(label_right)
    
            widget = (spin1, spin2)
            widget_type = 'tuple'
        else:
            widget = QLineEdit(str(value))
            widget_type = 'text'

        if not isinstance(value, tuple):
            row_layout.addWidget(widget)
            row_layout.addStretch()
            widget.setEnabled(self.editable)

        label = QLabel(name)
        self.content_layout.addRow(label, row_widget)
        self.widgets[name] = (widget, widget_type)
        self.rows[name] = (label, row_widget)
    
    def add_control_buttons(self, layout):
        """
        Добавление кнопок управления.
        """
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
        """
        Сохранение параметров и закрытие.
        """
        self.current_parameters = self.get_parameters()
        self.accept()
    
    def get_parameters(self):
        """
        Получение текущих параметров.
        """
        params = {}
        for name, (widget, widget_type) in self.widgets.items():
            if name in self.original_parameters:
                original_value = self.original_parameters[name]
                
                if widget_type == 'combo':
                    params[name] = str(widget.currentText())
                elif widget_type == 'int':
                    params[name] = int(widget.value())
                elif widget_type == 'float':
                    params[name] = float(widget.value())
                elif widget_type == 'tuple':
                    print('TUPLE_WIDGET', widget)
                    params[name] = (widget[0].value(), widget[1].value())
                else:
                    params[name] = widget.text()
        return params