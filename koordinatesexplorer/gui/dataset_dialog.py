import locale
import os
import platform
from typing import Dict, List, Tuple

from dateutil import parser
from qgis.PyQt import uic
from qgis.PyQt.QtCore import (
    Qt,
    QSize,
    QRect,
    pyqtSignal
)
from qgis.PyQt.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QBrush,
    QColor,
    QFontMetrics,
    QFont
)
from qgis.PyQt.QtWidgets import (
    QFrame,
    QLabel,
    QHBoxLayout,
    QApplication,
    QSizePolicy,
    QDialog,
    QVBoxLayout,
    QScrollArea,
    QGridLayout,
    QWidget
)

from .action_button import (
    AddButton,
    CloneButton
)
from .dataset_utils import (
    DatasetGuiUtils,
    IconStyle
)
from .gui_utils import GuiUtils
from .star_button import StarButton
from .svg_label import SvgLabel
from .thumbnails import downloadThumbnail
from ..api import (
    ApiUtils,
    DataType,
    Capability
)

pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, BASE = uic.loadUiType(GuiUtils.get_ui_file_path("datasetdialog.ui"))

FONT_FAMILIES = "KxMetric, -apple-system, BlinkMacSystemFont," \
                "'avenir next', avenir, helvetica, 'helvetica neue', ubuntu," \
                "roboto, noto, 'segoe ui', arial, sans-serif"
MONOSPACE_FONT_FAMILIES = "SFMono-Regular, Menlo, Monaco, Consolas, " \
                          "'Liberation Mono', 'Courier New', monospace"


class HorizontalLine(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background-color: #eaeaea;")


class ThumbnailLabel(QLabel):

    def __init__(self, url, width, height, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(width, height))

        downloadThumbnail(url, self)

    def setThumbnail(self, image: QImage):
        image = image.convertToFormat(QImage.Format_ARGB32)
        if image.width() > self.width():
            image = image.scaled(self.width(), int(image.height() * self.width() / image.width()),
                                 transformMode=Qt.SmoothTransformation)
            self.setFixedHeight(image.height())

        if image.height() > self.height():
            image = image.scaled(int(image.width() * self.height() / image.height()),
                                 self.height(),
                                 transformMode=Qt.SmoothTransformation)
            self.setFixedWidth(image.width())

        self.setPixmap(QPixmap.fromImage(image))


class SvgFramedButton(QFrame):
    clicked = pyqtSignal()

    def __init__(self, icon_name: str, width: int, height: int,
                 icon_width: int, icon_height: int, parent=None,
                 border_color=None, hover_border_color=None):
        super().__init__(parent)

        self.setFixedSize(width, height)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if hover_border_color:
            self.setMouseTracking(True)

        if border_color:
            self.setStyleSheet(
                """
            SvgFramedButton {{ background-color: none; border-radius: 3px; border: 1px solid {}; }}
            SvgFramedButton:hover {{ border-color: {}}}
            """.format(
                    border_color,
                    hover_border_color if hover_border_color else border_color
                )
            )

        svg_label = SvgLabel(icon_name, icon_width, icon_height)
        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)
        vl.addStretch()
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addStretch()
        hl.addWidget(svg_label)
        hl.addStretch()
        vl.addLayout(hl)
        vl.addStretch()
        self.setLayout(vl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        else:
            super().mousePressEvent(event)


class StatisticWidget(QWidget):

    def __init__(self, title: str, icon_name: str, value: str, parent=None):
        super().__init__(parent)

        gl = QGridLayout()
        gl.setContentsMargins(0, 0, 0, 0)

        font_size = 9
        if platform.system() == 'Darwin':
            font_size = 11

        title_label = QLabel(
            '<b style="font-family: {}; font-size: {}pt">{}</b>'.format(
                FONT_FAMILIES,
                font_size,
                title))
        gl.addWidget(title_label, 0, 0, 1, 2)

        icon = SvgLabel(icon_name, 16, 16)
        gl.addWidget(icon, 1, 0, 1, 1)

        value_label = QLabel(
            '<span style="font-family: {}; font-size: {}pt">{}</span>'.format(
                FONT_FAMILIES,
                font_size, value))
        gl.addWidget(value_label, 1, 1, 1, 1)

        self.setLayout(gl)


class HeaderWidget(QFrame):

    def __init__(self, dataset: Dict, parent=None):
        super().__init__(parent)
        self.dataset = dataset

        self.setFixedHeight(72)
        self.setFrameShape(QFrame.NoFrame)

        background_color = self.dataset.get('publisher', {}).get('theme', {}).get(
            'background_color') or '555657'
        self.setStyleSheet(
            'HeaderWidget {{ background-color: #{}; }}'.format(background_color))

        hl = QHBoxLayout()
        hl.setContentsMargins(15, 0, 15, 0)

        logo = self.dataset.get('publisher', {}).get('theme', {}).get('logo')
        if logo:
            logo = 'https:{}'.format(logo)
            logo_widget = ThumbnailLabel(logo, 145, 35)
            hl.addWidget(logo_widget)

        url_frame = QFrame()
        url_frame.setFrameShape(QFrame.NoFrame)
        if background_color:
            url_frame.setStyleSheet(
                'QFrame { border-radius: 6px; background-color: rgba(255,255,255,0.1); }')
        url_frame.setFixedHeight(35)
        url_layout = QHBoxLayout()
        url_layout.setContentsMargins(12, 7, 12, 7)

        url_label = QLabel(self.dataset.get('url_canonical', ''))
        if background_color:
            url_label.setStyleSheet(
                'QLabel {background-color: none; color: rgba(255,255,255,0.3)}')
        url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        url_label.setCursor(Qt.CursorShape.IBeamCursor)
        url_label.setMinimumWidth(10)
        url_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        url_layout.addWidget(url_label, 1)

        url_copy = SvgFramedButton(
            'copy.svg', 19, 19, 11, 14,
            border_color='rgba(255,255,255,0.3)' if background_color else None,
            hover_border_color='rgba(255,255,255,0.5)' if background_color else None
        )

        url_copy.clicked.connect(self._copy_url)
        url_layout.addWidget(url_copy)
        url_frame.setLayout(url_layout)

        hl.addWidget(url_frame, 1)

        org_details_label = QLabel()
        org_details_label.setStyleSheet('padding-left: 10px;')
        org_details_label.setText(
            f"""<p style="line-height: 130%;
            font-size: 10pt;
            color: rgba(255,255,255,0.7);
            font-family: {FONT_FAMILIES}"><b>{self.dataset.get('publisher', {}).get('name')}</b><br>"""
            f"""<span style="
        font-size: 10pt;
        font-family: {FONT_FAMILIES}"
        >via {self.dataset.get("publisher").get('site', {}).get("name")}</span></p>"""
        )

        hl.addWidget(org_details_label)

        self.setLayout(hl)

    def _copy_url(self):
        url = self.dataset.get('url_canonical', '')
        QApplication.clipboard().setText(url)


class DetailsTable(QGridLayout):

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setVerticalSpacing(13)
        self.font_size = 10
        if platform.system() == 'Darwin':
            self.font_size = 14

        heading = QLabel(
            """<b style="font-family: {}; font-size: {}pt; color: black">{}</b>""".format(
                FONT_FAMILIES,
                self.font_size,
                title))
        self.addWidget(heading, 0, 0, 1, 2)
        self.setColumnStretch(1, 1)

    def push_row(self, title: str, value: str):
        if self.rowCount() > 1:
            self.addWidget(HorizontalLine(), self.rowCount(), 0, 1, 2)

        is_monospace = title.startswith('_')
        if is_monospace:
            title = title[1:]

        row = self.rowCount()
        title_label = QLabel(
            """<span style="font-family: {};
            font-size: {}pt;
            color: #868889">{}</span>""".format(FONT_FAMILIES,
                                                self.font_size,
                                                title))
        title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        fm = QFontMetrics(QFont())
        title_label.setFixedWidth(fm.width('x') * 30)
        title_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.addWidget(title_label, row, 0, 1, 1)
        font_family = FONT_FAMILIES if not is_monospace else MONOSPACE_FONT_FAMILIES
        value_label = QLabel(
            """<span style="font-family: {}; font-size: {}pt; color: black">{}</span>""".format(
                font_family,
                self.font_size,
                value))
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        value_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        value_label.setWordWrap(True)
        self.addWidget(value_label, row, 1, 1, 1)

    def finalize(self):
        self.addWidget(HorizontalLine(), self.rowCount(), 0, 1, 2)

    def set_details(self, details: List[Tuple]):
        for title, value in details:
            self.push_row(title, value)
        self.finalize()


class DatasetDialog(QDialog):
    def __init__(self, parent, dataset):
        super().__init__(parent)

        self.dataset = dataset
        self.dataset_type: DataType = ApiUtils.data_type_from_dataset_response(self.dataset)

        self.setWindowTitle('Dataset Details - {}'.format(dataset.get('title', 'layer')))

        self.setStyleSheet('DatasetDialog {background-color: white; }')

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 20)

        self.header_widget = HeaderWidget(dataset)
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
            font-weight: bold;
            font-size: {title_font_size}pt;">{dataset.get('title', '')}</span>"""
        )
        title_hl.addWidget(self.label_title, 1)

        is_starred = self.dataset.get('is_starred', False)
        self.star_button = StarButton(dataset_id=self.dataset['id'], checked=is_starred)
        title_hl.addWidget(self.star_button)

        capabilities = ApiUtils.capabilities_from_dataset_response(self.dataset)

        if Capability.Clone in capabilities:
            self.clone_button = CloneButton(dataset, close_parent_on_clone=True)
            title_hl.addWidget(self.clone_button)
        else:
            self.clone_button = None

        if Capability.Add in capabilities:
            self.add_button = AddButton(dataset)
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
        thumbnail_url = dataset.get('thumbnail_url')
        if thumbnail_url:
            downloadThumbnail(thumbnail_url, self)

        contents_layout = QVBoxLayout()
        contents_layout.setContentsMargins(0, 0, 15, 15)

        base_details_layout = QHBoxLayout()
        base_details_layout.setContentsMargins(0, 0, 0, 0)
        base_details_layout.addWidget(self.thumbnail_label)

        base_details_right_pane_layout = QHBoxLayout()
        base_details_right_pane_layout.setContentsMargins(12, 0, 0, 0)
        icon_name = DatasetGuiUtils.get_icon_for_dataset(self.dataset, IconStyle.Dark)
        icon_label = SvgLabel(icon_name, 24, 24)
        base_details_right_pane_layout.addWidget(icon_label)

        summary_label = QLabel()
        summary_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        description = DatasetGuiUtils.get_type_description(self.dataset)
        subtitle = DatasetGuiUtils.get_subtitle(self.dataset)

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
        base_details_right_pane_layout_vl.addStretch()

        base_details_layout.addLayout(base_details_right_pane_layout_vl)

        contents_layout.addLayout(base_details_layout)

        contents_layout.addSpacing(7)
        contents_layout.addWidget(HorizontalLine())
        contents_layout.addSpacing(7)

        statistics_layout = QHBoxLayout()
        statistics_layout.setContentsMargins(0, 0, 0, 0)

        first_published = dataset.get('first_published_at')
        if first_published:
            statistics_layout.addWidget(StatisticWidget('Date Added', 'add.svg', parser.parse(
                first_published).strftime("%d %b %Y")))

        last_updated = dataset.get("published_at")
        if last_updated:
            statistics_layout.addWidget(StatisticWidget('Last Updated', 'history.svg',
                                                        parser.parse(last_updated).strftime(
                                                            "%d %b %Y")))

        num_downloads = dataset.get("num_downloads", 0)
        statistics_layout.addWidget(StatisticWidget('Exports', 'arrow-down.svg',
                                                    DatasetGuiUtils.format_count(
                                                        num_downloads)))

        num_views = dataset.get('num_views', 0)
        statistics_layout.addWidget(StatisticWidget('Views', 'eye.svg',
                                                    DatasetGuiUtils.format_count(
                                                        num_views)))
        statistics_layout.addWidget(StatisticWidget('Layer ID', 'layers.svg', str(dataset["id"])))

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
            self.dialog_css() + self.dataset.get("description_html", ''))

        contents_layout.addWidget(self.description_label, 1)

        contents_layout.addSpacing(40)

        tech_details_grid = DetailsTable('Technical Details')
        tech_details_grid.set_details(self.get_technical_details())
        contents_layout.addLayout(tech_details_grid)

        contents_layout.addSpacing(40)

        history_grid = DetailsTable('History')
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
            </style>
        """.format(FONT_FAMILIES, self.description_font_size)

    def format_number(self, value):
        return locale.format_string("%d", value, grouping=True)

    def format_date(self, value):
        return parser.parse(value).strftime("%d %b %Y")

    def get_technical_details(self) -> List[Tuple]:
        res = [
            ('Data type', DatasetGuiUtils.get_data_type(self.dataset))
        ]

        crs_display = self.dataset.get('data', {}).get('crs_display')
        crs = self.dataset.get('data', {}).get('crs')
        if crs_display:
            res.append(('CRS', '{} • {}'.format(crs_display,
                                                crs
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

        first_published = self.dataset.get("first_published_at")
        if first_published:
            res.append(('Added', self.format_date(first_published)))

        last_updated = self.dataset.get("published_at")
        if last_updated:
            res.append(('Last updated', self.format_date(last_updated)))

        res.append(('Revisions', 'xxx'))
        return res

    def setThumbnail(self, img):
        target = QImage(self.thumbnail_label.size(), QImage.Format_ARGB32)
        target.fill(Qt.transparent)

        painter = QPainter(target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawRoundedRect(0, 0, target.width(), target.height(), 9, 9)

        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)

        if img is not None:
            rect = QRect(300, 87, 600, 457)
            thumbnail = QPixmap(img)
            cropped = thumbnail.copy(rect)

            thumb = cropped.scaled(
                target.width(), target.height(), Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, thumb)
        else:
            painter.setBrush(QBrush(QColor('#cccccc')))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, 600, 600)

        painter.end()

        thumbnail = QPixmap.fromImage(target)
        self.thumbnail_label.setPixmap(thumbnail)
