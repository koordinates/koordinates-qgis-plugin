import platform

from qgis.PyQt.QtCore import (
    Qt,
    QUrl
)
from qgis.PyQt.QtGui import (
    QDesktopServices
)
from qgis.PyQt.QtWidgets import (
    QFrame,
    QLabel,
    QHBoxLayout
)

from ..gui_utils import FONT_FAMILIES
from ..svg_label import SvgLabel


class AttachmentWidget(QFrame):
    """
    A widget for showing file attachment details
    """

    def __init__(self, attachment):
        super().__init__()

        self.setStyleSheet("""AttachmentWidget {
        border: 1px solid #dddddd;
        border-radius: 3px;
         }
         """)

        self.attachment = attachment
        label = QLabel()

        base_font_size = 11
        if platform.system() == 'Darwin':
            base_font_size = 12

        title = attachment.get('document', {}).get('title')

        label.setText(
            f"""<span style="font-family: {FONT_FAMILIES};
            font-weight: 500;
            font-size: {base_font_size}pt;">{title}</span>"""
        )
        hl = QHBoxLayout()
        hl.addWidget(label, 1)

        download_frame = QFrame()
        download_frame.setStyleSheet("""QFrame {
        border: 1px solid #dddddd;
        border-radius: 3px;
        }

        QFrame:hover { background-color: #f8f8f8; }
        """)

        file_details = attachment.get('document', {}).get('extension',
                                                          '').upper()
        file_details += ' ' + attachment.get('document', {}).get(
            'file_size_formatted', '')

        download_label = QLabel()
        download_label.setText(
            f"""<span style="font-family: {FONT_FAMILIES};
            font-size: {base_font_size}pt;">{file_details}</span>"""
        )
        download_label.setStyleSheet('border: none')

        download_layout = QHBoxLayout()
        download_layout.addWidget(download_label)

        download_icon = SvgLabel('arrow-down.svg', 16, 16)
        download_layout.addWidget(download_icon)

        download_frame.setLayout(download_layout)
        download_frame.setCursor(Qt.PointingHandCursor)

        download_frame.mousePressEvent = self._download

        hl.addWidget(download_frame)

        self.setLayout(hl)

    def _download(self, event):
        url = self.attachment['url_download']
        QDesktopServices.openUrl(QUrl(url))
