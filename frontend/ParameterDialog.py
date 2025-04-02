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

class ParameterDialog(QDialog):
    def __init__(self, method_name, parameters, editable=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Параметры: {method_name}")
        self.setModal(True)
        self.setMinimumWidth(300)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QFormLayout(content)
        
        self.widgets = {}
        
        for name, value in parameters.items():
            if isinstance(value, int):
                widget = QSpinBox()
                widget.setRange(0, 1000)
                widget.setValue(value)
            elif isinstance(value, float):
                widget = QDoubleSpinBox()
                widget.setRange(0.0, 1000.0)
                widget.setSingleStep(0.1)
                widget.setValue(value)
            else:
                widget = QLineEdit(str(value))
            
            widget.setEnabled(editable)
            layout.addRow(name, widget)
            self.widgets[name] = widget
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        
        if editable:
            buttons = QWidget()
            buttons_layout = QHBoxLayout(buttons)
            buttons_layout.addStretch()
            
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(self.accept)
            buttons_layout.addWidget(ok_button)
            
            cancel_button = QPushButton("Отмена")
            cancel_button.clicked.connect(self.reject)
            buttons_layout.addWidget(cancel_button)
            
            main_layout.addWidget(buttons)
    
    def get_parameters(self):
        params = {}
        for name, widget in self.widgets.items():
            if isinstance(widget, QSpinBox):
                params[name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[name] = widget.value()
            else:
                params[name] = widget.text()
        return params