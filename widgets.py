"""Petits widgets graphiques personnalisés (aucune logique réseau)."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

import config as c


class DashedSeparator(QWidget):
    """Trait horizontal en pointillés. lines=2 dessine un double trait."""

    def __init__(self, lines=1, parent=None):
        super().__init__(parent)
        self.lines = lines
        self.setFixedHeight(lines + (lines - 1) * c.SEPARATOR_LINE_GAP)

    def paintEvent(self, _event):
        painter = QPainter(self)
        pen = QPen(QColor(c.SEPARATOR_COLOR), 1)
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([c.SEPARATOR_DASH, c.SEPARATOR_GAP])
        painter.setPen(pen)
        for i in range(self.lines):
            y = i * (1 + c.SEPARATOR_LINE_GAP)
            painter.drawLine(0, y, self.width(), y)
        painter.end()