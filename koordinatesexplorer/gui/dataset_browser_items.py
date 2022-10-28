import json
import platform
from typing import Optional

from dateutil import parser
from qgis.PyQt.QtCore import (
    Qt,
    QPointF,
    QRect,
    QRectF,
    QSize
)
from qgis.PyQt.QtGui import (
    QColor,
    QPixmap,
    QCursor,
    QPainter,
    QPainterPath,
    QImage,
    QBrush,
    QFont,
    QPen
)
from qgis.PyQt.QtSvg import QSvgWidget
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QFrame,
    QLabel,
    QVBoxLayout,
    QSizePolicy,
    QWidget
)
from qgis.core import (
    QgsProject,
    QgsGeometry,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsFields,
    QgsJsonUtils
)
from qgis.utils import iface

from koordinatesexplorer.gui.dataset_dialog import DatasetDialog
from koordinatesexplorer.gui.thumbnails import downloadThumbnail
from .action_button import (
    CloneButton,
    AddButton
)
from .dataset_utils import (
    DatasetGuiUtils,
    IconStyle
)
from .gui_utils import GuiUtils
from .star_button import StarButton
from ..api import (
    ApiUtils,
    DataType,
    Capability
)


class DatasetItemWidgetBase(QFrame):
    """
    Base class for dataset items
    """

    THUMBNAIL_CORNER_RADIUS = 5
    THUMBNAIL_SIZE = 150

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            """DatasetItemWidgetBase {{
               border: 1px solid #dddddd;
               border-radius: {}px; background: white;
            }}""".format(self.THUMBNAIL_CORNER_RADIUS)
        )
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    def set_column_count(self, count):
        pass


class Label(QLabel):
    def __init__(self):
        super(Label, self).__init__()
        self.setMaximumSize(150, 200)
        self.setMinimumSize(150, 200)


class EmptyDatasetItemWidget(DatasetItemWidgetBase):
    """
    Shows an 'empty' dataset item
    """

    TOP_LABEL_HEIGHT = 40
    TOP_LABEL_MARGIN = 15
    TOP_LABEL_WIDTH = 300
    BOTTOM_LABEL_HEIGHT = 20
    BOTTOM_LABEL_MARGIN = 40
    BOTTOM_LABEL_WIDTH = 130

    def __init__(self, parent=None):
        super().__init__(parent)

        # self.setThumbnail(None)

        self.labelMap = Label()
        self.labelMap.setFixedHeight(150)

        self.labelName = QLabel()
        self.labelName.setWordWrap(True)
        self.labelName.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.vlayout = QVBoxLayout()
        self.vlayout.setContentsMargins(11, 17, 15, 15)

        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.addWidget(self.labelName, 1)

        self.vlayout.addLayout(self.top_layout)

        self.buttonsLayout = QHBoxLayout()
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)

        self.vlayout.addLayout(self.buttonsLayout)

        layout = QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.labelMap)
        layout.addLayout(self.vlayout)

        self.setLayout(layout)

        target = QPixmap(self.TOP_LABEL_WIDTH,
                         self.TOP_LABEL_HEIGHT + self.TOP_LABEL_MARGIN)
        target.fill(Qt.transparent)

        painter = QPainter(target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        painter.setBrush(QBrush(QColor('#e6e6e6')))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, self.TOP_LABEL_MARGIN,
                                self.TOP_LABEL_WIDTH, self.TOP_LABEL_HEIGHT,
                                4, 4)

        painter.end()

        self.labelName.setPixmap(target)
        self.vlayout.addStretch()

        target = QPixmap(self.BOTTOM_LABEL_WIDTH,
                         self.BOTTOM_LABEL_HEIGHT + self.BOTTOM_LABEL_MARGIN)
        target.fill(Qt.transparent)

        painter = QPainter(target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        painter.setBrush(QBrush(QColor('#e6e6e6')))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0,
                                self.BOTTOM_LABEL_MARGIN,
                                self.BOTTOM_LABEL_WIDTH,
                                self.BOTTOM_LABEL_HEIGHT,
                                4,
                                4)

        painter.end()

        bottom_label = QLabel()
        bottom_label.setPixmap(target)
        self.vlayout.addWidget(bottom_label)
        self.vlayout.addStretch()


class DatasetItemWidget(DatasetItemWidgetBase):
    """
    Shows details for a dataset item
    """

    CARD_HEIGHT = DatasetItemWidgetBase.THUMBNAIL_SIZE + 2  # +2 for 2x1px border
    CARD_HEIGHT_TALL = DatasetItemWidgetBase.THUMBNAIL_SIZE + 170 + 2  # +2 for 2x1px border

    def __init__(self, dataset, column_count, parent):
        super().__init__(parent)

        self.setMouseTracking(True)
        self.dataset = dataset
        self.raw_thumbnail = None

        self.layout_widget = None
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self.column_count = -1

        self.dataset_type: DataType = ApiUtils.data_type_from_dataset_response(self.dataset)

        self.setFixedHeight(self.CARD_HEIGHT)

        self.labelMap = Label()
        self.labelMap.setFixedHeight(150)

        self.labelName = QLabel()
        self.labelName.setWordWrap(True)
        self.labelName.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        thumbnail_url = self.dataset.get('thumbnail_url')
        if thumbnail_url:
            downloadThumbnail(thumbnail_url, self)

        main_title_size = 11
        title_font_size = 11
        detail_font_size = 9
        if platform.system() == 'Darwin':
            # fonts looks smaller on a mac, where things "just work" :P
            main_title_size = 14
            title_font_size = 14
            detail_font_size = 10

        self.labelName.setText(
            f"""<p style="line-height: 130%;
                font-size: {main_title_size}pt;
                font-family: Arial, Sans"><b>{self.dataset.get("title", 'Layer')}</b><br>"""
            f"""<span style="color: #868889;
            font-size: {title_font_size}pt;
            font-family: Arial, Sans">{self.dataset.get("publisher", {}).get("name")}</span></p>"""
        )

        license = self.dataset.get('license')
        self.license_label = None
        if license:
            license_type = license.get('type')
            if license_type:
                license_type = license_type.upper()
                self.license_label = QLabel()
                self.license_label.setText(
                    f"""<span style="color: #868889;
                        font-family: Arial, Sans;
                        font-size: {detail_font_size}pt">{license_type}</span>"""
                )

        self.labelUpdatedIcon = QSvgWidget(GuiUtils.get_icon_svg("history_gray.svg"))
        self.labelUpdatedIcon.setFixedSize(13, 12)
        self.labelUpdated = QLabel()

        published_at_date_str: Optional[str] = self.dataset.get("published_at")
        if published_at_date_str:
            date = parser.parse(published_at_date_str)
            self.labelUpdated.setText(
                f"""<span style="color: #868889;
                    font-family: Arial, Sans;
                    font-size: {detail_font_size}pt">{date.strftime("%d %b %Y")}</span>"""
            )

        is_starred = self.dataset.get('is_starred', False)
        self.star_button = StarButton(dataset_id=self.dataset['id'], checked=is_starred)

        base_style = self.styleSheet()
        base_style += """
            DatasetItemWidget:hover {
                border: 1px solid rgb(180, 180, 180);
                background: #fcfcfc;
            }
        """
        self.setStyleSheet(base_style)

        capabilities = ApiUtils.capabilities_from_dataset_response(self.dataset)

        if Capability.Clone in capabilities:
            self.btnClone = CloneButton(self.dataset)
        else:
            self.btnClone = None

        if Capability.Add in capabilities:
            self.btnAdd = AddButton(self.dataset)
        else:
            self.btnAdd = None

        self.bbox: Optional[QgsGeometry] = self._geomFromGeoJson(
            self.dataset.get("data", {}).get("extent"))
        # if self.bbox:
        #     self.footprint = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        #     self.footprint.setWidth(2)
        #     self.footprint.setColor(QColor(255, 0, 0, 200))
        #     self.footprint.setFillColor(QColor(255, 0, 0, 40))
        # else:
        #     self.footprint = None

        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.set_column_count(column_count)

    def set_column_count(self, count: int):
        use_narrow_cards = count > 1
        is_using_narrow_cards = self.column_count > 1

        if self.column_count >= 1 and use_narrow_cards == is_using_narrow_cards:
            return

        self.column_count = count

        if use_narrow_cards:
            self.setFixedHeight(self.CARD_HEIGHT_TALL)

            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.labelMap)

            details_layout = QVBoxLayout()
            details_layout.setContentsMargins(16, 12, 16, 16)
            title_layout = QHBoxLayout()
            title_layout.setContentsMargins(0, 0, 0, 0)
            title_layout.addWidget(self.labelName, 1)
            title_layout.addWidget(self.star_button)
            title_layout.addStretch()
            details_layout.addLayout(title_layout)
            details_layout.addStretch()

            if self.license_label:
                details_layout.addWidget(self.license_label)

            updated_layout = QHBoxLayout()
            updated_layout.setContentsMargins(0, 0, 0, 0)

            updated_layout.addWidget(self.labelUpdatedIcon)
            updated_layout.addWidget(self.labelUpdated)
            details_layout.addLayout(updated_layout)

            buttonsLayout = QHBoxLayout()
            buttonsLayout.setContentsMargins(0, 0, 0, 0)
            buttonsLayout.addStretch()

            details_layout.addLayout(buttonsLayout)

            if self.btnClone:
                buttonsLayout.addWidget(self.btnClone)
            if self.btnAdd:
                buttonsLayout.addWidget(self.btnAdd)
            layout.addLayout(details_layout)
        else:
            self.setFixedHeight(self.CARD_HEIGHT)
            self.setMinimumWidth(1)

            vlayout = QVBoxLayout()
            vlayout.setContentsMargins(11, 17, 15, 15)

            top_layout = QHBoxLayout()
            top_layout.setContentsMargins(0, 0, 0, 0)
            top_layout.addWidget(self.labelName, 1)

            vlayout.addLayout(top_layout)

            buttonsLayout = QHBoxLayout()
            buttonsLayout.setContentsMargins(0, 0, 0, 0)

            vlayout.addLayout(buttonsLayout)

            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.labelMap)
            layout.addLayout(vlayout)

            details_layout = QVBoxLayout()
            details_layout.setContentsMargins(0, 0, 0, 0)
            if self.license_label:
                details_layout.addWidget(self.license_label)

            updated_layout = QHBoxLayout()
            updated_layout.setContentsMargins(0, 0, 0, 0)

            updated_layout.addWidget(self.labelUpdatedIcon)
            updated_layout.addWidget(self.labelUpdated)
            details_layout.addLayout(updated_layout)

            buttonsLayout.addLayout(details_layout)
            buttonsLayout.addStretch()

            star_layout = QVBoxLayout()
            star_layout.setContentsMargins(0, 0, 0, 0)
            star_layout.addWidget(self.star_button)
            star_layout.addStretch()
            top_layout.addLayout(star_layout)
            buttonsLayout.addStretch()

            if self.btnClone:
                buttonsLayout.addWidget(self.btnClone)
            if self.btnAdd:
                buttonsLayout.addWidget(self.btnAdd)

        self.layout_widget = QWidget()
        self.layout_widget.setLayout(layout)
        self._layout.takeAt(0)
        self._layout.addWidget(self.layout_widget)
        self.update_thumbnail()

    def setThumbnail(self, img: Optional[QImage]):
        self.raw_thumbnail = img
        self.update_thumbnail()

    def update_thumbnail(self):
        thumbnail = self.process_thumbnail(self.raw_thumbnail)
        self.labelMap.setFixedSize(thumbnail.size())
        self.labelMap.setPixmap(QPixmap.fromImage(thumbnail))

    def process_thumbnail(self, img: Optional[QImage]) -> QImage:
        if self.column_count == 1:
            size = QSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE)
        else:
            size = QSize(self.width() - 2, self.THUMBNAIL_SIZE)

        target = QImage(size, QImage.Format_ARGB32)
        target.fill(Qt.transparent)

        painter = QPainter(target)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 0, 0)))

        path = QPainterPath()
        if self.column_count == 1:
            path.moveTo(self.THUMBNAIL_CORNER_RADIUS, 0)
            path.lineTo(size.width(), 0)
            path.lineTo(size.width(), size.height())
            path.lineTo(self.THUMBNAIL_CORNER_RADIUS, size.height())
            path.arcTo(0,
                       size.height() - self.THUMBNAIL_CORNER_RADIUS * 2,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       270, -90
                       )
            path.lineTo(0, self.THUMBNAIL_CORNER_RADIUS)
            path.arcTo(0,
                       0,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       180, -90
                       )
        else:
            path.moveTo(self.THUMBNAIL_CORNER_RADIUS, 0)
            path.lineTo(size.width() - self.THUMBNAIL_CORNER_RADIUS, 0)
            path.arcTo(size.width() - self.THUMBNAIL_CORNER_RADIUS * 2,
                       0,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       90, -90
                       )
            path.lineTo(size.width(), size.height())
            path.lineTo(0, size.height())
            path.lineTo(0, self.THUMBNAIL_CORNER_RADIUS)
            path.arcTo(0,
                       0,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       self.THUMBNAIL_CORNER_RADIUS * 2,
                       180, -90
                       )

        painter.drawPath(path)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)

        if img is not None:
            rect = QRect(300, 15, 600, 600)
            thumbnail = QPixmap(img)
            cropped = thumbnail.copy(rect)

            thumb = cropped.scaled(
                size.width(), size.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, thumb)
        else:
            painter.setBrush(QBrush(QColor('#cccccc')))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, 600, 600)

        painter.end()

        scale_factor = self.screen().devicePixelRatio()

        scaled_image = target.scaled(int(scale_factor * target.width()),
                                     int(scale_factor * target.height()))

        scaled_image.setDevicePixelRatio(self.screen().devicePixelRatio())
        scaled_image.setDotsPerMeterX(
            int(scaled_image.dotsPerMeterX() * scale_factor))
        scaled_image.setDotsPerMeterY(int(
            scaled_image.dotsPerMeterY() * scale_factor))
        base = scaled_image

        painter = QPainter(base)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRoundedRect(QRectF(15, 100, 117, 32), 4, 4)

        icon = DatasetGuiUtils.get_icon_for_dataset(self.dataset, IconStyle.Light)
        if icon:
            painter.drawImage(QRectF(21, 106, 20, 20),
                              GuiUtils.get_svg_as_image(icon,
                                                        int(20 * scale_factor),
                                                        int(20 * scale_factor)))

        description = DatasetGuiUtils.get_type_description(self.dataset)
        if description:
            font = QFont('Arial')
            font.setPixelSize(int(10 / scale_factor))
            font.setBold(True)
            painter.setFont(font)

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(QPointF(47, 113), description)

        subtitle = DatasetGuiUtils.get_subtitle(self.dataset)
        if subtitle:
            font = QFont('Arial')
            font.setPixelSize(int(10 / scale_factor))
            font.setBold(False)
            painter.setFont(font)

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(QPointF(47, 127), subtitle)

        painter.end()
        return base

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.width() < 440 and self.column_count == 1:
            self.labelMap.hide()
        else:
            self.labelMap.show()
            self.update_thumbnail()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.showDetails()
        else:
            super().mousePressEvent(event)

    def showDetails(self):
        dataset = (
            self.dataset
        )
        dlg = DatasetDialog(self, dataset)
        dlg.exec()

    def _geomFromGeoJson(self, geojson) -> Optional[QgsGeometry]:
        try:
            feats = QgsJsonUtils.stringToFeatureList(
                json.dumps(geojson), QgsFields(), None
            )
            geom = feats[0].geometry()
        except Exception:
            geom = QgsGeometry()

        if geom.isNull() or geom.isEmpty():
            return None

        return geom

    # def enterEvent(self, event):
    #     if self.footprint is not None:
    #         self.showFootprint()

    # def leaveEvent(self, event):
    #     if self.footprint is not None:
    #         self.hideFootprint()

    def _bboxInProjectCrs(self):
        geom = QgsGeometry(self.bbox)
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:4326"),
            QgsProject.instance().crs(),
            QgsProject.instance(),
        )
        geom.transform(transform)
        return geom

    # def showFootprint(self):
    #     self.footprint.setToGeometry(self._bboxInProjectCrs())

    # def hideFootprint(self):
    #     self.footprint.reset(QgsWkbTypes.PolygonGeometry)

    def zoomToBoundingBox(self):
        rect = self.bbox.boundingBox()
        rect.scale(1.05)
        iface.mapCanvas().setExtent(rect)
        iface.mapCanvas().refresh()
