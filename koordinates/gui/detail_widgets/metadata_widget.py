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


class MetadataWidget(QFrame):
    """
    A widget for showing dataset metadata documents
    """

    def __init__(self, source, metadata):
        super().__init__()

        self.setStyleSheet("""MetadataWidget {
        border: 1px solid #dddddd;
        border-radius: 3px;
         }
         """)

        self.metadata = metadata
        label = QLabel()

        base_font_size = 11
        if platform.system() == 'Darwin':
            base_font_size = 12

        title = 'ISO 19115/19139 Metadata' if source == 'iso' \
            else 'Dublin Core Metadata'

        label.setText(
            f"""<span style="font-family: {FONT_FAMILIES};
            font-weight: 500;
            font-size: {base_font_size}pt;">{title}</span>"""
        )
        hl = QHBoxLayout()
        hl.addWidget(label, 1)

        download_xml_frame = QFrame()
        download_xml_frame.setStyleSheet("""QFrame {
        border: 1px solid #dddddd;
        border-radius: 3px;
         }

         QFrame:hover { background-color: #f8f8f8; }
         """)

        download_xml_label = QLabel()
        download_xml_label.setText(
            f"""<span style="font-family: {FONT_FAMILIES};
            font-size: {base_font_size}pt;">XML</span>"""
        )
        download_xml_label.setStyleSheet('border: none')

        download_xml_layout = QHBoxLayout()
        download_xml_layout.addWidget(download_xml_label)

        download_icon = SvgLabel('arrow-down.svg', 16, 16)
        download_xml_layout.addWidget(download_icon)

        download_xml_frame.setLayout(download_xml_layout)
        download_xml_frame.setCursor(Qt.PointingHandCursor)

        download_xml_frame.mousePressEvent = self._download_xml

        hl.addWidget(download_xml_frame)

        download_pdf_frame = QFrame()
        download_pdf_frame.setStyleSheet("""QFrame {
        border: 1px solid #dddddd;
        border-radius: 3px;
         }

         QFrame:hover { background-color: #f8f8f8; }
         """)

        download_pdf_label = QLabel()
        download_pdf_label.setText(
            f"""<span style="font-family: {FONT_FAMILIES};
            font-size: {base_font_size}pt;">PDF</span>"""
        )
        download_pdf_label.setStyleSheet('border: none')

        download_pdf_layout = QHBoxLayout()
        download_pdf_layout.addWidget(download_pdf_label)

        download_icon = SvgLabel('arrow-down.svg', 16, 16)
        download_pdf_layout.addWidget(download_icon)

        download_pdf_frame.setLayout(download_pdf_layout)
        download_pdf_frame.setCursor(Qt.PointingHandCursor)

        download_pdf_frame.mousePressEvent = self._download_pdf

        hl.addWidget(download_pdf_frame)

        self.setLayout(hl)

    def _download_xml(self, event):
        QDesktopServices.openUrl(QUrl(self.metadata))

    def _download_pdf(self, event):
        QDesktopServices.openUrl(QUrl(self.metadata + '?format=pdf'))
