from PyQt5.QtWidgets import QLayout
from PyQt5.QtCore import Qt, QSize, QRect, QPoint

class QFlowLayout(QLayout):
    """
    Этот класс используется для корректного расположения виджетов, с 
    переносом их на новую строку.
    """
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        # устанавливаем отступы от краев
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        # устанавливаем пространство между элементами (-1 - берется значение по умолчанию из Qt)
        self.setSpacing(spacing)
        # список элементов
        self.itemList = []
    
    def addItem(self, item):
        """
        Добавляет новый элемент.
        """
        self.itemList.append(item)
    
    def count(self):
        """
        Вовзращает длину списка элементов.
        """
        return len(self.itemList)
    
    def itemAt(self, index):
        """
        Получение элемента по индексу.
        """
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None
    
    def takeAt(self, index):
        """
        Удаляет и возвращает элемент по индексу.
        """
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None
    
    def expandingDirections(self):
        """
        Запрещает расширение для лайаута.
        """
        return Qt.Orientations(Qt.Orientation(0))
    
    def hasHeightForWidth(self):
        """
        Определяет, зависит ли высота лайаута от ширины
        (True - высота рассчитывается на основе ширины).
        """
        return True
    
    def heightForWidth(self, width):
        """
        Вычисление высоты на основе ширины.
        """
        return self.doLayout(QRect(0, 0, width, 0), True)
    
    def setGeometry(self, rect):
        """
        Отвечает за размещение элементов.
        """
        super().setGeometry(rect)
        self.doLayout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        """
        Вычисляет минимальный размер элемента.
        """
        size = QSize()
        
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size
    
    def doLayout(self, rect, testOnly):
        """
        Отвечает за размещение элементов.
        rect - область, в которой нужно разместить объекты,
        testOnly - выполнять ли перемещения элементов.
        """
        # начальные координаты
        x = rect.x()
        y = rect.y()
        # высота текущей строки
        line_height = 0
        
        for item in self.itemList:
            spaceX = self.spacing()
            spaceY = self.spacing()
            # вычисляет координаты следующего элемента в строке
            nextX = x + item.sizeHint().width() + spaceX
            # если элемент вылезает за границы, переносит на след. строку
            if nextX - spaceX > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                line_height = 0
            
            # элементы перемещаются в соответствии с их значением высоты
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            
            x = nextX
            line_height = max(line_height, item.sizeHint().height())
        
        return y + line_height - rect.y()