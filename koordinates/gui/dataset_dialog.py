import locale
import os
import platform
import datetime
from typing import Dict, List, Tuple

from qgis.PyQt import uic
from qgis.PyQt.QtCore import (
    Qt,
    QSize,
    QRect
)
from qgis.PyQt.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QBrush,
    QColor
)
from qgis.PyQt.QtWidgets import (
    QFrame,
    QLabel,
    QHBoxLayout,
    QDialog,
    QVBoxLayout,
    QScrollArea,
)
from qgis.PyQt.QtSvg import QSvgWidget

from .action_button import (
    AddButton,
    CloneButton
)
from .dataset_utils import (
    DatasetGuiUtils,
    IconStyle
)
from .gui_utils import (
    GuiUtils,
    FONT_FAMILIES,
)
from .star_button import StarButton
from .svg_label import SvgLabel
from .thumbnails import downloadThumbnail
from ..api import (
    ApiUtils,
    DataType,
    PublicAccessType,
    Capability,
    KoordinatesClient,
    Dataset
)
from .detail_widgets import (
    HorizontalLine,
    StatisticWidget,
    HeaderWidget,
    DetailsTable,
    AttachmentWidget,
    MetadataWidget
)

pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, BASE = uic.loadUiType(GuiUtils.get_ui_file_path("datasetdialog.ui"))


class DatasetDialog(QDialog):
    """
    A dialog showing details of a dataset
    """

    def __init__(self, parent, dataset: Dataset):
        super().__init__(parent)

        self.dataset = dataset.details
        self.dataset_obj = dataset

        self.details = KoordinatesClient.instance().dataset_details(
            self.dataset_obj)

        if self.details.get('attachments'):
            self.attachments = KoordinatesClient.instance().get_json(self.details['attachments'])
        else:
            self.attachments = []

        self.setWindowTitle('Dataset Details - {}'.format(
            self.dataset_obj.title())
        )

        self.setStyleSheet('DatasetDialog {background-color: white; }')

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 20)

        self.header_widget = HeaderWidget(self.dataset_obj)
        layout.addWidget(self.header_widget)

        title_hl = QHBoxLayout()
        title_hl.setContentsMargins(20, 25, 20, 25)

        title_font_size = 18
        base_font_size = 10
        self.description_font_size = 11
        if platform.system() == 'Darwin':
            title_font_size = 20
            base_font_size = 12
            self.description_font_size = 14

        self.label_title = QLabel()
        self.label_title.setText(
            f"""<span style="font-family: {FONT_FAMILIES};
            font-weight: 500;
            font-size: {title_font_size}pt;">"""
            f"""{self.dataset_obj.title()}</span>"""
        )
        title_hl.addWidget(self.label_title)

        if self.dataset_obj.access == PublicAccessType.none:
            private_icon = QSvgWidget(GuiUtils.get_icon_svg('private.svg'))
            private_icon.setFixedSize(QSize(24, 24))
            private_icon.setToolTip(self.tr('Private'))
            title_hl.addWidget(private_icon)

        title_hl.addStretch()

        self.star_button = StarButton(self.dataset_obj)
        title_hl.addWidget(self.star_button)

        if Capability.Clone in self.dataset_obj.capabilities:
            self.clone_button = CloneButton(self.dataset_obj,
                                            close_parent_on_clone=True)
            title_hl.addWidget(self.clone_button)
        else:
            self.clone_button = None

        if Capability.Add in self.dataset_obj.capabilities:
            self.add_button = AddButton(self.dataset_obj)
            title_hl.addWidget(self.add_button)
        else:
            self.add_button = None

        layout.addLayout(title_hl)

        scroll_area_layout = QHBoxLayout()
        scroll_area_layout.setContentsMargins(20, 0, 20, 0)
        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)

        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(256, 195)

        thumbnail_svg = DatasetGuiUtils.thumbnail_icon_for_dataset(
            self.dataset_obj
        )
        if thumbnail_svg:
            self.setThumbnail(GuiUtils.get_svg_as_image(thumbnail_svg,
                                                        195, 195))
        else:
            thumbnail_url = self.dataset_obj.thumbnail_url()
            if thumbnail_url:
                downloadThumbnail(thumbnail_url, self)

        contents_layout = QVBoxLayout()
        contents_layout.setContentsMargins(0, 0, 15, 15)

        base_details_layout = QHBoxLayout()
        base_details_layout.setContentsMargins(0, 0, 0, 0)
        base_details_layout.addWidget(self.thumbnail_label)

        base_details_right_pane_layout = QHBoxLayout()
        base_details_right_pane_layout.setContentsMargins(12, 0, 0, 0)
        icon_name = DatasetGuiUtils.get_icon_for_dataset(self.dataset_obj,
                                                         IconStyle.Dark)
        icon_label = SvgLabel(icon_name, 24, 24)
        base_details_right_pane_layout.addWidget(icon_label)

        summary_label = QLabel()
        summary_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        description = DatasetGuiUtils.get_type_description(self.dataset_obj)
        subtitle = DatasetGuiUtils.get_subtitle(self.dataset_obj,
                                                short_format=False)

        summary_label.setText("""<p style="line-height: 130%;
        font-family: {};
        font-size: {}pt"><b>Data type</b><br>
        {},<br>{}</p>""".format(
            FONT_FAMILIES,
            base_font_size,
            description,
            subtitle))

        base_details_right_pane_layout.addSpacing(10)
        base_details_right_pane_layout.addWidget(summary_label, 1)

        base_details_right_pane_layout_vl = QVBoxLayout()
        base_details_right_pane_layout_vl.setContentsMargins(0, 0, 0, 0)
        base_details_right_pane_layout_vl.addLayout(base_details_right_pane_layout)

        if self.dataset_obj.repository():
            base_details_right_pane_layout = QHBoxLayout()
            base_details_right_pane_layout.setContentsMargins(12, 0, 0, 0)

            icon_label = SvgLabel(GuiUtils.get_icon_svg('repo-book.svg'), 24, 24)
            base_details_right_pane_layout.addWidget(icon_label)

            summary_label = QLabel()
            summary_label.setAlignment(Qt.AlignmentFlag.AlignTop)

            description = self.tr('Repository')
            subtitle = self.dataset_obj.repository().title()

            summary_label.setText("""<p style="line-height: 130%;
                    font-family: {};
                    font-size: {}pt"><b>{}</b><br>
                    {}</p>""".format(
                FONT_FAMILIES,
                base_font_size,
                description,
                subtitle))

            base_details_right_pane_layout.addSpacing(10)
            base_details_right_pane_layout.addWidget(summary_label, 1)
            base_details_right_pane_layout_vl.addLayout(base_details_right_pane_layout)

        base_details_right_pane_layout_vl.addStretch()

        base_details_layout.addLayout(base_details_right_pane_layout_vl)

        contents_layout.addLayout(base_details_layout)

        contents_layout.addSpacing(7)
        contents_layout.addWidget(HorizontalLine())
        contents_layout.addSpacing(7)

        statistics_layout = QHBoxLayout()
        statistics_layout.setContentsMargins(0, 0, 0, 0)

        first_published = self.dataset_obj.created_at_date()
        if first_published:
            statistics_layout.addWidget(
                StatisticWidget(
                    'Date Added',
                    'add.svg',
                    self.format_date(first_published)
                )
            )

        last_updated = self.dataset_obj.updated_at_date()
        if last_updated:
            statistics_layout.addWidget(
                StatisticWidget(
                    'Last Updated',
                    'history.svg',
                    self.format_date(last_updated)
                )
            )

        num_downloads = self.dataset_obj.number_downloads()
        statistics_layout.addWidget(
            StatisticWidget(
                'Exports',
                'arrow-down.svg',
                DatasetGuiUtils.format_count(num_downloads)
            )
        )

        num_views = self.dataset_obj.number_views()
        statistics_layout.addWidget(
            StatisticWidget(
                'Views',
                'eye.svg',
                DatasetGuiUtils.format_count(num_views)
            )
        )

        statistics_layout.addWidget(
            StatisticWidget('{} ID'.format(
                self.dataset_obj.datatype.identifier_string()),
                'layers.svg',
                str(self.dataset_obj.id))
        )

        contents_layout.addLayout(statistics_layout)

        contents_layout.addSpacing(7)
        contents_layout.addWidget(HorizontalLine())
        contents_layout.addSpacing(7)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        self.description_label.setOpenExternalLinks(True)
        self.description_label.setText(
            self.dialog_css() + self.dataset_obj.html_description())

        contents_layout.addWidget(self.description_label, 1)

        contents_layout.addSpacing(40)

        if self.attachments:
            heading = QLabel(
                """<b style="font-family: {}; font-size: {}pt; color: black">{}</b>""".format(
                    FONT_FAMILIES,
                    self.description_font_size,
                    'Attachments'))
            contents_layout.addWidget(heading)

            for attachment in self.attachments:
                contents_layout.addWidget(AttachmentWidget(attachment))

            contents_layout.addSpacing(40)

        if self.details.get('metadata') and (self.details['metadata'].get('iso') or
                                             self.details['metadata'].get('dc')):
            heading = QLabel(
                """<b style="font-family: {}; font-size: {}pt; color: black">{}</b>""".format(
                    FONT_FAMILIES,
                    self.description_font_size,
                    'Metadata'))
            contents_layout.addWidget(heading)

            for source in ('iso', 'dc'):
                if self.details['metadata'].get(source):
                    contents_layout.addWidget(
                        MetadataWidget(source, self.details['metadata'][source]))

            contents_layout.addSpacing(40)

        tech_details_grid = DetailsTable('Technical Details')
        tech_details_grid.set_details(self.get_technical_details())
        contents_layout.addLayout(tech_details_grid)

        contents_layout.addSpacing(40)

        history_grid = DetailsTable('History & Version Control')
        history_grid.set_details(self.get_history_details())
        contents_layout.addLayout(history_grid)

        contents_layout.addStretch()

        # contents_layout.addStretch(1)

        contents_widget = QFrame()
        contents_widget.setLayout(contents_layout)
        contents_widget.setStyleSheet("QFrame{ background: transparent; }")
        scroll_area.setWidget(contents_widget)
        scroll_area.setWidgetResizable(True)

        scroll_area_layout.addWidget(scroll_area)
        scroll_area.viewport().setStyleSheet("#qt_scrollarea_viewport{ background: transparent; }")

        layout.addLayout(scroll_area_layout, 1)

        self.setLayout(layout)

    def dialog_css(self) -> str:
        return """
            <style>
            p {{
            font-family: {};
            color: rgb(50, 50, 50);
            font-size: {}pt;
            letter-spacing: 0.1px;
            line-height: 1.5;
            }}
            a {{
            color: rgb(50, 50, 50);
            }}
            strong {{
             font-weight: 500;
            }}
            </style>
        """.format(FONT_FAMILIES, self.description_font_size)

    @staticmethod
    def format_number(value):
        """
        Formats a number for localised display
        """
        return locale.format_string("%d", value, grouping=True)

    @staticmethod
    def format_date(value: datetime.date):
        """
        Formats a date value for display
        """
        return value.strftime("%d %b %Y")

    def get_technical_details(self) -> List[Tuple]:
        res = [
            ('Data type', DatasetGuiUtils.get_data_type(self.dataset_obj))
        ]

        crs = self.dataset_obj.crs
        crs_display = crs.name() if crs else ''
        crs_id = crs.id() if crs else ''
        if crs_display:
            res.append(('CRS', '{} • <a href="{}">{}</a>'.format(
                crs_display,
                crs.url_external(),
                crs_id
            )))

        feature_count = self.dataset.get("data", {}).get("feature_count", 0)
        empty_count = self.dataset.get("data", {}).get('empty_geometry_count', 0)
        feature_count_label = self.format_number(feature_count)
        if empty_count:
            feature_count_label += ' • {} with empty or null geometries'.format(
                self.format_number(empty_count))
            res.append(('Feature count', feature_count_label))

        fields = self.dataset.get('data', {}).get('fields', [])
        if fields:
            res.append(('_Attributes', ", ".join(
                [f.get("name", '') for f in fields])))

        primary_key_fields = self.dataset.get('data', {}).get('primary_key_fields', [])
        if primary_key_fields:
            res.append(('_Primary key', ", ".join(primary_key_fields)))

        return res

    def get_history_details(self) -> List[Tuple]:
        res = []

        first_published = self.dataset_obj.created_at_date()
        if first_published:
            res.append(('Date Added', self.format_date(first_published)))

        last_updated = self.dataset_obj.updated_at_date()
        if last_updated:
            res.append(('Last updated', self.format_date(last_updated)))

        if Capability.RevisionCount in self.dataset_obj.capabilities:
            data_revisions_count = \
                KoordinatesClient.instance().data_revisions_count(
                    self.dataset_obj.id)
            total_revisions_count = \
                KoordinatesClient.instance().total_revisions_count(
                    self.dataset_obj.id)

            if data_revisions_count is not None or total_revisions_count is not None:
                res.append(
                    ('Revisions',
                     '{} data revisions • {} total revisions'.format(
                         data_revisions_count,
                         total_revisions_count
                     )))

        return res

    def setThumbnail(self, img):
        image_size = self.thumbnail_label.size()
        scale_factor = self.window().screen().devicePixelRatio()
        if scale_factor > 1:
            image_size *= scale_factor

        target = QImage(image_size, QImage.Format_ARGB32)
        target.fill(Qt.transparent)

        painter = QPainter(target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawRoundedRect(0, 0, image_size.width(), image_size.height(), 9, 9)

        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.setBrush(QBrush(QColor('#dddddd')))
        painter.drawRect(0, 0, image_size.width(), image_size.height())

        if img is not None:
            if img.size() != image_size:
                if image_size.width() != img.width() and image_size.height() != img.height():
                    resized = img.scaled(image_size.width(),
                                         image_size.height(),
                                         Qt.KeepAspectRatioByExpanding,
                                         Qt.SmoothTransformation)
                else:
                    resized = img

                if resized.width() > image_size.width():
                    left = int((resized.width() - image_size.width()) / 2)
                else:
                    left = 0
                if resized.height() > image_size.height():
                    top = int((resized.height() - image_size.height()) / 2)
                else:
                    top = 0

                if left > 0 or top > 0:
                    cropped = resized.copy(QRect(left, top, image_size.width(), image_size.height()))
                    painter.drawImage(0, 0, cropped)
                else:
                    painter.drawImage(int((image_size.width() - resized.width()) / 2),
                                      int((image_size.height() - resized.height()) / 2),
                                      resized)
            else:
                painter.drawImage(0, 0, img)
        else:
            painter.setBrush(QBrush(QColor('#cccccc')))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, 600, 600)

        painter.end()

        thumbnail = QPixmap.fromImage(target)
        thumbnail.setDevicePixelRatio(scale_factor)

        self.thumbnail_label.setPixmap(thumbnail)
