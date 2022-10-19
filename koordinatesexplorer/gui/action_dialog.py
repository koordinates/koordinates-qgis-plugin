from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    QSize,
    QUrl
)
from qgis.PyQt.QtSvg import QSvgWidget
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
    QLayout
)

from .action_button import ActionButton
from .gui_utils import GuiUtils


class ActionDialog(QDialog):

    def __init__(self, title: str, message: str, action: str,
                 url: Optional[str] = None, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addSpacing(28)
        hl = QHBoxLayout()
        koordinates_logo_widget = QSvgWidget(GuiUtils.get_icon_svg('koordinates_logo.svg'))
        koordinates_logo_widget.setFixedSize(QSize(161, 46))
        hl.addStretch()
        hl.addWidget(koordinates_logo_widget)
        hl.addStretch()

        layout.addLayout(hl)
        layout.addSpacing(25)

        hl = QHBoxLayout()
        hl.addStretch()
        font = self.font()
        font.setPointSize(font.pointSize() - 1)
        message_label = QLabel("""<div style="line-height: 1.2;">{}</div>""".format(message))
        message_label.setWordWrap(True)
        message_label.setFixedWidth(280)
        message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        message_label.setFont(font)
        hl.addWidget(message_label)
        hl.addStretch()

        layout.addLayout(hl)

        layout.addSpacing(22)

        hl = QHBoxLayout()
        hl.addStretch()

        button = ActionButton()
        button.setText(action)
        button.setFixedHeight(32)
        button.setFont(self.font())

        if url:
            def open_url():
                QDesktopServices.openUrl(QUrl(url))

            button.clicked.connect(open_url)
        hl.addWidget(button)
        hl.addStretch()

        layout.addLayout(hl)
        layout.addSpacing(22)

        self.setLayout(layout)

        self.window().layout().setSizeConstraint(QLayout.SetFixedSize)
