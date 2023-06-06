from qgis.PyQt.QtCore import (
    Qt,
    QSize
)
from qgis.PyQt.QtGui import (
    QColor,
    QPixmap
)
from qgis.PyQt.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QApplication
)

from koordinates.gui.detail_widgets.svg_framed_button import SvgFramedButton
from koordinates.gui.detail_widgets.thumbnail_label_widget import \
    PublisherThumbnailLabel
from koordinates.gui.gui_utils import FONT_FAMILIES
from ...api import (
    Dataset,
    PublisherType
)
from ..user_avatar_generator import UserAvatarGenerator


class HeaderWidget(QFrame):
    """
    A styled header widget for showing dataset details in a styled
    themed by the publisher
    """

    def __init__(self, dataset: Dataset, parent=None):
        super().__init__(parent)
        self.dataset = dataset

        self.setFixedHeight(72)
        self.setFrameShape(QFrame.NoFrame)

        self.publisher = self.dataset.publisher()

        self.publisher_theme = self.publisher.theme \
            if self.publisher else None
        background_color = self.publisher_theme.background_color() \
            if self.publisher_theme else None
        background_color = background_color or QColor('#555657')

        self.setStyleSheet(
            'HeaderWidget {{ background-color: {}; }}'.format(
                background_color.name()))

        hl = QHBoxLayout()
        hl.setContentsMargins(15, 0, 15, 0)

        logo_widget = PublisherThumbnailLabel(self.publisher, QSize(145, 35))
        hl.addWidget(logo_widget)

        url_frame = QFrame()
        url_frame.setFrameShape(QFrame.NoFrame)
        if background_color:
            url_frame.setStyleSheet(
                """QFrame {
                    border-radius: 6px;
                    background-color: rgba(255,255,255,0.1);
                }""")
        url_frame.setFixedHeight(35)
        url_layout = QHBoxLayout()
        url_layout.setContentsMargins(12, 7, 12, 7)

        url_label = QLabel(self.dataset.url_canonical() or '')
        if background_color:
            url_label.setStyleSheet(
                """QLabel {
                    background-color: none;
                    color: rgba(255,255,255,0.3)
                }""")
        url_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        url_label.setCursor(Qt.CursorShape.IBeamCursor)
        url_label.setMinimumWidth(10)
        url_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        url_layout.addWidget(url_label, 1)

        url_copy = SvgFramedButton(
            'copy.svg', 19, 19, 11, 14,
            border_color='rgba(255,255,255,0.3)' if background_color
            else None,
            hover_border_color='rgba(255,255,255,0.5)' if background_color
            else None
        )

        url_copy.clicked.connect(self._copy_url)
        url_layout.addWidget(url_copy)
        url_frame.setLayout(url_layout)

        hl.addWidget(url_frame, 1)

        font_scale = self.screen().logicalDotsPerInch() / 92
        org_font_size = 10
        if font_scale > 1:
            org_font_size = int(12 / font_scale)

        publisher_site = self.dataset.publisher().site \
            if self.dataset.publisher() else None
        publisher_site_name = publisher_site.name() if publisher_site else ''

        org_details_label = QLabel()
        org_details_label.setStyleSheet('padding-left: 10px;')
        publisher_name = self.dataset.publisher().name() \
            if self.dataset.publisher() else ''
        org_details_label.setText(
            f"""<p style="line-height: 130%;
            font-size: {org_font_size}pt;
            color: rgba(255,255,255,0.7);
            font-family: {FONT_FAMILIES}" """
            f"""><b>{publisher_name}</b><br>"""
            f"""<span style="
        font-size: {org_font_size}pt;
        font-family: {FONT_FAMILIES};
        color: rgba(255,255,255,0.8);"
        >via {publisher_site_name}</span></p>"""
        )

        hl.addWidget(org_details_label)

        self.setLayout(hl)

    def _copy_url(self):
        url = self.dataset.url_canonical()
        QApplication.clipboard().setText(url)
