from qgis.PyQt.QtWidgets import (
    QFrame,
    QSizePolicy
)


class HorizontalLine(QFrame):
    """
    A simple 1px styled horizontal line widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background-color: #eaeaea;")
