from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    QSize,
    QUrl
)
from qgis.PyQt.QtSvg import QSvgWidget
from qgis.PyQt.QtGui import (
    QDesktopServices,
    QFontMetrics
)
from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QLabel
)

from .action_button import ActionButton
from .gui_utils import GuiUtils


class ActionDialog(QDialog):

    def __init__(self, title: str, message: str, action: str,
                 url: Optional[str] = None, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        layout = QVBoxLayout()
        hl = QHBoxLayout()
        koordinates_logo_widget = QSvgWidget(
            GuiUtils.get_icon_svg('koordinates_logo.svg'))
        koordinates_logo_widget.setFixedSize(QSize(100, 28))
        hl.addWidget(koordinates_logo_widget)
        hl.addStretch()

        layout.addLayout(hl)
        layout.addSpacing(16)

        font = self.font()
        font.setPointSize(font.pointSize() - 1)
        message_label = QLabel(
            """<div style="line-height: 1.2;">{}</div>""".format(message))
        message_label.setWordWrap(True)
        message_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        message_label.setFont(font)
        layout.addWidget(message_label)

        layout.addSpacing(22)

        hl = QHBoxLayout()

        button = ActionButton()
        button.setText(action)
        button.setFixedHeight(32)
        button.setFont(self.font())
        button.setStyleSheet(
            button.styleSheet() + """
            QToolButton { padding-left: 10px; padding-right: 10px }
            """
        )

        if url:
            def open_url():
                QDesktopServices.openUrl(QUrl(url))

            button.clicked.connect(open_url)
        hl.addWidget(button)
        hl.addStretch()

        layout.addLayout(hl)

        fm = QFontMetrics(message_label.font())

        layout.setContentsMargins(fm.width('x') * 7,
                                  fm.width('x') * 5,
                                  fm.width('x') * 7,
                                  fm.width('x') * 7)

        self.setLayout(layout)

        self.window().setFixedWidth(fm.width('x') * 70)
