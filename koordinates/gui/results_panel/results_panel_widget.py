from typing import Optional

from qgis.PyQt.QtWidgets import (
    QWidget
)


class ResultsPanelWidget(QWidget):
    """
    Base class for results panel widgets
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

    def cancel_active_requests(self):
        """
        Cancels any active request
        """
        pass
