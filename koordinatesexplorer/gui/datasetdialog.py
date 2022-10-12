import os
from typing import Dict

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
    QColor
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
from qgis.utils import iface

from koordinatesexplorer.gui.thumbnails import downloadThumbnail
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

pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, BASE = uic.loadUiType(GuiUtils.get_ui_file_path("datasetdialog.ui"))


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
            image = image.scaled(self.width(), int(image.height() * self.width() / image.width()))

        if image.height() > self.height():
            image = image.scaled(int(image.width() * self.height() / image.height()),
                                 self.height())

        self.setPixmap(QPixmap.fromImage(image))


class SvgLabel(QLabel):

    def __init__(self, icon_name: str, width, height,
                 icon_width, icon_height, parent=None):
        super().__init__(parent)

        self.setFixedSize(QSize(width, height))
        icon = GuiUtils.get_svg_as_image(icon_name, icon_width, icon_height)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setPixmap(QPixmap.fromImage(icon))


class SvgFramedButton(SvgLabel):
    clicked = pyqtSignal()

    def __init__(self, icon_name: str, width, height,
                 icon_width, icon_height, parent=None,
                 border_color=None, hover_border_color=None):
        super().__init__(icon_name, width, height,
                         icon_width, icon_height, parent)

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

        title_label = QLabel(
            '<b style="font-family: Arial, Sans; font-size: 9pt">{}</b>'.format(title))
        gl.addWidget(title_label, 0, 0, 1, 2)

        icon = SvgLabel(icon_name, 16, 16, 16, 16)
        gl.addWidget(icon, 1, 0, 1, 1)

        value_label = QLabel(
            '<span style="font-family: Arial, Sans; font-size: 9pt">{}</span>'.format(value))
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
            logo_widget = ThumbnailLabel(logo, 145, 70)
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

        url_copy = SvgFramedButton('copy.svg', 19, 19, 11, 14,
                                   border_color='rgba(255,255,255,0.3)' if background_color else None,
                                   hover_border_color='rgba(255,255,255,0.5)' if background_color else None)

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
            font-family: Arial, Sans"><b>{self.dataset.get('publisher', {}).get('name')}</b><br>"""
            f"""<span style="
        font-size: 10pt;
        font-family: Arial, Sans">via {self.dataset.get("publisher").get('site', {}).get("name")}</span></p>"""
        )

        hl.addWidget(org_details_label)

        self.setLayout(hl)

    def _copy_url(self):
        url = self.dataset.get('url_canonical', '')
        QApplication.clipboard().setText(url)


class DatasetDialog(QDialog):
    def __init__(self, dataset):
        super().__init__(iface.mainWindow())
        # self.setupUi(self)

        self.dataset = dataset

        self.setWindowTitle('Dataset Details - {}'.format(dataset['title']))

        self.setStyleSheet('DatasetDialog {background-color: white; }')

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 20)

        self.header_widget = HeaderWidget(dataset)
        layout.addWidget(self.header_widget)

        title_hl = QHBoxLayout()
        title_hl.setContentsMargins(20, 25, 20, 25)

        self.label_title = QLabel()
        self.label_title.setText(
            '<span style="font-family: Arial, Sans; font-weight: bold; font-size: 18pt;">{}</span>'.format(
                dataset['title']))
        title_hl.addWidget(self.label_title, 1)

        is_starred = self.dataset.get('is_starred', False)
        self.star_button = StarButton(dataset_id=self.dataset['id'], checked=is_starred)
        title_hl.addWidget(self.star_button)

        self.clone_button = CloneButton(dataset)
        title_hl.addWidget(self.clone_button)

        self.add_button = AddButton(dataset)
        title_hl.addWidget(self.add_button)

        layout.addLayout(title_hl)

        scroll_area_layout = QHBoxLayout()
        scroll_area_layout.setContentsMargins(20, 0, 20, 0)
        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)

        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(256, 195)
        downloadThumbnail(dataset["thumbnail_url"], self)

        contents_layout = QVBoxLayout()
        contents_layout.setContentsMargins(0, 0, 15, 15)

        base_details_layout = QHBoxLayout()
        base_details_layout.setContentsMargins(0, 0, 0, 0)
        base_details_layout.addWidget(self.thumbnail_label)

        base_details_right_pane_layout = QHBoxLayout()
        base_details_right_pane_layout.setContentsMargins(12, 0, 0, 0)
        icon_name = DatasetGuiUtils.get_icon_for_dataset(self.dataset, IconStyle.Dark)
        icon_label = SvgLabel(icon_name, 24, 44, 24, 24)
        base_details_right_pane_layout.addWidget(icon_label)

        summary_label = QLabel()
        summary_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        description = DatasetGuiUtils.get_type_description(self.dataset)
        subtitle = DatasetGuiUtils.get_subtitle(self.dataset)

        summary_label.setText("""<p style="line-height: 130%; font-family: Arial, Sans; font-size: 10pt"><b>Data type</b><br>
        {},<br>{}</p>""".format(description, subtitle))

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

        statistics_layout.addWidget(StatisticWidget('Date Added', 'add.svg', parser.parse(
            dataset["first_published_at"]).strftime("%d %b %Y")))
        statistics_layout.addWidget(StatisticWidget('Last Updated', 'history.svg',
                                                    parser.parse(dataset["published_at"]).strftime(
                                                        "%d %b %Y")))
        statistics_layout.addWidget(StatisticWidget('Exports', 'arrow-down.svg',
                                                    DatasetGuiUtils.format_count(
                                                        dataset["num_downloads"])))
        statistics_layout.addWidget(StatisticWidget('Views', 'eye.svg',
                                                    DatasetGuiUtils.format_count(
                                                        dataset["num_views"])))
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
        self.description_label.setText(self.dataset["description_html"])

        contents_layout.addWidget(self.description_label, 1)
        contents_layout.addStretch()

        # contents_layout.addStretch(1)

        contents_widget = QFrame()
        contents_widget.setLayout(contents_layout)
        contents_widget.setStyleSheet("QFrame{ background: transparent; }")
        scroll_area.setWidget(contents_widget)

        scroll_area_layout.addWidget(scroll_area)
        scroll_area.viewport().setStyleSheet("#qt_scrollarea_viewport{ background: transparent; }")

        layout.addLayout(scroll_area_layout, 1)

        self.setLayout(layout)

    def _html(self):
        if self.dataset["data"].get("fields") is not None:
            extra = f"""
                </tr><tr>
                <td>Data type</td> <td>{self.dataset["data"]["geometry_type"]}</td>
                </tr><tr>
                <td> Feature count </td><td> {self.dataset["data"]["feature_count"]} </td>
                </tr><tr>
                  <td> Attributes </td><td>{", ".join(
                [f["name"] for f in self.dataset["data"]["fields"]]
            )}</td>
            """

        elif "feature_count" in self.dataset["data"]:
            extra = f"""
                </tr><tr>
                <td> Tile count </td><td> {self.dataset["data"]["feature_count"]} </td>
            """
        else:
            extra = ""
        html = f"""
            <p>{self.dataset["description_html"]}</p>
            <h3>Koordinates categories</h3>
            {"<br>".join([cat["name"] for cat in self.dataset["categories"]])}
            <h3>Tags</h3>
            {" | ".join(self.dataset["tags"])}
            <h3>Details</h3>
            <p>
            <table>
              <tbody>
                <tr>
                  <td> Layer ID </td><td> {self.dataset["id"]}</td>
                  {extra}
                </tr><tr>
                  <td> Stored CRS </td><td>{self.dataset["data"]["crs_display"]}</td>
                </tr>
              </tbody>
            </table>
            </p>
        """
        return html

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
