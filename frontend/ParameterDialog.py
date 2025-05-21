from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QDialog, QFormLayout,
    QSpinBox, QDoubleSpinBox, QScrollArea
)
from PyQt5.QtCore import QTimer

class ParameterDialog(QDialog):
    def __init__(self, method_name, parameters_config, params_mapping, allowed_params_values, editable=False, parent=None):
        super().__init__(parent)
        self.method_name = method_name
        self.params_mapping = params_mapping
        self.parameters_config = parameters_config
        self.allowed_params_values = allowed_params_values
        self.editable = editable

        self.setWindowTitle(f"Параметры: {method_name}")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        # приводим параметры к виду 'param = value'
        self.original_parameters = {name: config['value'] for name, config in parameters_config.items()}
        self.current_parameters = {name: config['value'] for name, config in parameters_config.items()}
        # глубокое копирование параметров
        # self.original_parameters = {k: v[:] if isinstance(v, list) else v for k, v in parameters.items()}
        # self.current_parameters = {k: v[:] if isinstance(v, list) else v for k, v in parameters.items()}
        
        # начальная инициализация
        self.init_ui()
        # зависимости параметров (когда наличие одного зависит от другого)
        self.dependencies = {
            'sigma': {
                'source': 'estimate_noise',
                'condition': ['gaussian'],
                'widget_type': 'float'
            },
            'wavelet_sigma': {
                'source': 'wavelet_estimate_noise',
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
                self.create_parameter_row(parameter_name)
        
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

                # заменяем русские названия на английские
                current_value = next(k for k, v in self.params_mapping.items() if v == current_value)
                # print(f"Проверка зависимости: {dependent} <- {config['source']} = {current_value} (должно быть в {config['condition']})")
                
                # определяем по условию, должен ли зависимый виджет отображаться
                should_show = current_value in config['condition']
                label, widget = self.rows[dependent]
                label.setVisible(should_show)
                widget.setVisible(should_show)
        
        # автоматическое обновление размеров виджета в соответствии с содержимым
        self.content_widget.adjustSize()
    
    def create_parameter_row(self, name):
        """
        Создание строки параметра.
        """
        config = self.parameters_config[name]
        value = config['value']
        display_name = config['name']
        widget_type = config['type']

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # берется значение по ключу name, а если его нет, то берется value
        # original_value = self.original_parameters.get(name, value)
        
        # if isinstance(original_value, str):
        #     widget = QComboBox()
        #     items = self.allowed_params_values[name]
        #     widget.addItems(items)
        #     widget.setCurrentText(str(original_value))
        #     widget_type = 'combo'
            
        #     if name in ['estimate_noise', 'mask_mode', 'wavelet_estimate_noise']:
        #         widget.currentTextChanged.connect(self.force_update_dependencies)

        if widget_type == 'combo':
            widget = QComboBox()
            items = self.allowed_params_values[name]
            translated_items = [self.params_mapping[item] for item in items]
            widget.addItems(translated_items)
            # widget.setCurrentText(str(self.params_mapping[original_value]))
            widget.setCurrentText(self.params_mapping.get(str(value), str(value)))

            for item in config.get('options', []):
                widget.addItem(self.params_mapping.get(item, item), item)
            widget.setCurrentText(self.params_mapping.get(str(value), str(value)))
            
            if name in ['estimate_noise', 'mask_mode', 'wavelet_estimate_noise']:
                widget.currentTextChanged.connect(self.force_update_dependencies)

        elif widget_type == 'int':
            widget = QSpinBox()
            min_val, max_val = config['bounds']            
            widget.setRange(min_val, max_val)
            widget.setValue(int(value))
        
        elif widget_type == 'float':
            widget = QDoubleSpinBox()
            min_val, max_val = config['bounds']
            widget.setRange(min_val, max_val)
            widget.setValue(float(value))

        elif widget_type == 'tuple' and len(value) == 2:
            min_val, max_val = config['bounds']

            label_left = QLabel("(")
            spin1 = QSpinBox()
            spin1.setRange(min_val, max_val)
            spin1.setValue(value[0])
            spin1.setEnabled(self.editable)

            label_comma = QLabel(",")

            spin2 = QSpinBox()
            spin2.setRange(min_val, max_val)
            spin2.setValue(value[1])
            spin2.setEnabled(self.editable)
            label_right = QLabel(")")
    
            row_layout.addWidget(label_left)
            row_layout.addWidget(spin1)
            row_layout.addWidget(label_comma)
            row_layout.addWidget(spin2)
            row_layout.addWidget(label_right)
    
            widget = (spin1, spin2)
        else:
            widget = QLineEdit(str(value))
            widget_type = 'text'

        if widget_type != 'tuple':
            row_layout.addWidget(widget)
            row_layout.addStretch()
            widget.setEnabled(self.editable)

        label = QLabel(display_name)
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
        # self.current_parameters = self.get_parameters()
        current_config = self.get_parameters()
        self.current_parameters = {name: config['value'] for name, config in current_config.items()}
        self.accept()
    
    def get_parameters(self):
        """
        Получение текущих значений параметров в виде структурированного конфига
        (аналогично входному parameters_config)
        """
        params_config = {}
        for name, (widget, widget_type) in self.widgets.items():
            if name in self.parameters_config:
                param_config = self.parameters_config[name].copy()

                if widget_type == 'combo':
                    current_value = next(k for k, v in self.params_mapping.items() if v == widget.currentText())
                    param_config['value'] = current_value
                elif widget_type == 'int':
                    param_config['value'] = int(widget.value())
                elif widget_type == 'float':
                    param_config['value'] = float(widget.value())
                elif widget_type == 'tuple':
                    param_config['value'] = (widget[0].value(), widget[1].value())
                else:
                    param_config['value'] = widget.text()
                
                params_config[name] = param_config
        
        return params_config
    
    # def get_parameters(self):
    #     """
    #     Получение текущих значений параметров.
    #     """
    #     params = {}
    #     for name, (widget, widget_type) in self.widgets.items():
    #         if name in self.original_parameters:
    #             if widget_type == 'combo':
    #                 params[name] = widget.currentData()
    #             elif widget_type == 'int':
    #                 params[name] = int(widget.value())
    #             elif widget_type == 'float':
    #                 params[name] = float(widget.value())
    #             elif widget_type == 'tuple':
    #                 params[name] = (widget[0].value(), widget[1].value())
    #             else:
    #                 params[name] = widget.text()
    #     return params