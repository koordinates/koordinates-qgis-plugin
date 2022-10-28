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
    QWidgetItem,
    QLayout
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


class DatasetItemLayout(QLayout):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.thumbnail_widget = None
        self.thumbnail_item = None
        self.title_container = None
        self.details_container = None
        self.button_container = None

        self.use_narrow_cards = False

    def set_thumbnail_widget(self, widget):
        self.thumbnail_widget = widget
        self.thumbnail_item = QWidgetItem(widget)
        self.addChildWidget(widget)
        self.invalidate()

    def set_title_layout(self, layout):
        self.title_container = layout
        self.addChildLayout(layout)
        self.invalidate()

    def set_details_layout(self, layout):
        self.details_container = layout
        self.addChildLayout(layout)
        self.invalidate()

    def set_button_layout(self, layout):
        self.button_container = layout
        self.addChildLayout(layout)
        self.invalidate()

    def addItem(self, item):
        pass

    def count(self):
        res = 0
        if self.thumbnail_item:
            res += 1
        if self.title_container:
            res += 1
        if self.details_container:
            res += 1
        if self.button_container:
            res += 1
        return res

    def itemAt(self, index):
        if index == 0:
            return self.thumbnail_item
        elif index == 1:
            return self.title_container
        elif index == 2:
            return self.details_container
        elif index == 3:
            return self.button_container

    def takeAt(self, index: int):
        if index == 0:
            res = self.thumbnail_item
            self.thumbnail_item = None
            self.thumbnail_widget.deleteLater()
            self.thumbnail_widget = None
            return res
        elif index == 1:
            res = self.title_container
            self.title_container = None
            return res
        elif index == 2:
            res = self.details_container
            self.details_container = None
            return res
        elif index == 3:
            res = self.button_container
            self.button_container = None
            return res
        return None

    def expandingDirections(self):
        return Qt.Orientations()  # Qt.Orientation.Horizontal)

    def hasHeightForWidth(self):
        return False

    def set_use_narrow_cards(self, narrow):
        self.use_narrow_cards = narrow

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        if self.use_narrow_cards:
            return QSize(330, DatasetItemWidgetBase.CARD_HEIGHT_TALL)
        else:
            return QSize(330, DatasetItemWidgetBase.CARD_HEIGHT)

    def setGeometry(self, rect):
        super().setGeometry(rect)

        if self.use_narrow_cards:
            if self.thumbnail_item:
                self.thumbnail_widget.show()
                self.thumbnail_item.setGeometry(
                    QRect(
                        0, 0,
                        rect.width() + 1, DatasetItemWidgetBase.THUMBNAIL_SIZE
                    )
                )
            if self.title_container:
                self.title_container.setGeometry(
                    QRect(
                        17, 155,
                        rect.width() - 17 * 2,
                        60
                    )
                )

            if self.details_container:
                self.details_container.setGeometry(
                    QRect(
                        17, 200,
                        rect.width() - 17 * 2,
                        56
                    )
                )

            if self.button_container:
                self.button_container.setGeometry(
                    QRect(
                        16, 280,
                        rect.width() - 12 * 2,
                        32
                    )
                )
        else:
            has_thumbnail = False
            if self.thumbnail_item:
                if rect.width() < 440:
                    self.thumbnail_widget.hide()
                else:
                    self.thumbnail_widget.show()
                    has_thumbnail = True
                    self.thumbnail_item.setGeometry(
                        QRect(
                            0, 0,
                            DatasetItemWidgetBase.THUMBNAIL_SIZE + 1,
                            DatasetItemWidgetBase.THUMBNAIL_SIZE + 1
                        )
                    )

            left = 160 if has_thumbnail else 16
            if self.title_container:
                self.title_container.setGeometry(
                    QRect(
                        left, 15,
                        rect.width() - left - 10,
                        60
                    )
                )

            if self.details_container:
                self.details_container.setGeometry(
                    QRect(
                        left, 80,
                        105,
                        61
                    )
                )

            if self.button_container:
                self.button_container.setGeometry(
                    QRect(
                        left + 103, 103,
                        rect.width() - left - 103 - 10,
                        38
                    )
                )


class DatasetItemWidgetBase(QFrame):
    """
    Base class for dataset items
    """

    THUMBNAIL_CORNER_RADIUS = 5
    THUMBNAIL_SIZE = 150

    CARD_HEIGHT = THUMBNAIL_SIZE + 2  # +2 for 2x1px border
    CARD_HEIGHT_TALL = THUMBNAIL_SIZE + 170 + 2  # +2 for 2x1px border

    def __init__(self, parent=None):
        super().__init__(parent)
        self.column_count = 1
        self.setStyleSheet(
            """DatasetItemWidgetBase {{
               border: 1px solid #dddddd;
               border-radius: {}px; background: white;
            }}""".format(self.THUMBNAIL_CORNER_RADIUS)
        )
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(self.CARD_HEIGHT)
        self.setLayout(DatasetItemLayout())

    def set_column_count(self, count: int):
        use_narrow_cards = count > 1
        is_using_narrow_cards = self.column_count > 1

        if self.column_count >= 1 and use_narrow_cards == is_using_narrow_cards:
            return

        self.column_count = count

        self.layout().set_use_narrow_cards(use_narrow_cards)

        if use_narrow_cards:
            self.setFixedHeight(self.CARD_HEIGHT_TALL)

        else:
            self.setFixedHeight(self.CARD_HEIGHT)
            self.setMinimumWidth(1)


class Label(QLabel):
    def __init__(self):
        super(Label, self).__init__()
        self.setMaximumSize(150, 200)
        self.setMinimumSize(150, 200)


class EmptyDatasetItemWidget(DatasetItemWidgetBase):
    """
    Shows an 'empty' dataset item
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.thumbnail = QFrame()
        self.thumbnail.setStyleSheet(
            """background: #e6e6e6; border-radius: {}px""".format(
                self.THUMBNAIL_CORNER_RADIUS
            )
        )
        self.layout().set_thumbnail_widget(self.thumbnail)

        self.title_layout = QHBoxLayout()
        self.title_frame = QFrame()
        self.title_frame.setStyleSheet(
            """background: #f6f6f6; border-radius: {}px""".format(
                self.THUMBNAIL_CORNER_RADIUS
            )
        )
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_layout.addWidget(self.title_frame)

        self.layout().set_title_layout(self.title_layout)

        self.details_layout = QHBoxLayout()
        self.details_frame = QFrame()
        self.details_frame.setStyleSheet(
            """background: #f6f6f6; border-radius: {}px""".format(
                self.THUMBNAIL_CORNER_RADIUS
            )
        )
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_layout.addWidget(self.details_frame)

        self.layout().set_details_layout(self.details_layout)


class DatasetItemWidget(DatasetItemWidgetBase):
    """
    Shows details for a dataset item
    """

    def __init__(self, dataset, column_count, parent):
        super().__init__(parent)

        self.setMouseTracking(True)
        self.dataset = dataset
        self.raw_thumbnail = None

        self.dataset_type: DataType = ApiUtils.data_type_from_dataset_response(self.dataset)

        self.thumbnail_label = Label()
        self.thumbnail_label.setFixedHeight(150)
        self.layout().set_thumbnail_widget(self.thumbnail_label)

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        thumbnail_url = self.dataset.get('thumbnail_url')
        if thumbnail_url:
            downloadThumbnail(thumbnail_url, self)

        is_starred = self.dataset.get('is_starred', False)
        self.star_button = StarButton(dataset_id=self.dataset['id'], checked=is_starred)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.addWidget(self.title_label, 1)
        title_layout.addWidget(self.star_button)
        self.layout().set_title_layout(title_layout)

        main_title_size = 11
        title_font_size = 11
        detail_font_size = 9
        if platform.system() == 'Darwin':
            # fonts looks smaller on a mac, where things "just work" :P
            main_title_size = 14
            title_font_size = 14
            detail_font_size = 10

        self.title_label.setText(
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

        details_layout = QVBoxLayout()
        details_layout.addStretch()
        details_layout.setContentsMargins(0, 0, 0, 0)
        if self.license_label:
            details_layout.addWidget(self.license_label)

        updated_layout = QHBoxLayout()
        updated_layout.setContentsMargins(0, 0, 0, 0)

        updated_layout.addWidget(self.labelUpdatedIcon)
        updated_layout.addWidget(self.labelUpdated)
        details_layout.addLayout(updated_layout)

        self.layout().set_details_layout(details_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.addStretch()

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
            buttons_layout.addWidget(self.btnClone)
        else:
            self.btnClone = None

        if Capability.Add in capabilities:
            self.btnAdd = AddButton(self.dataset)
            buttons_layout.addWidget(self.btnAdd)
        else:
            self.btnAdd = None

        self.layout().set_button_layout(buttons_layout)

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

        super().set_column_count(count)
        self.update_thumbnail()

    def setThumbnail(self, img: Optional[QImage]):
        self.raw_thumbnail = img
        self.update_thumbnail()

    def update_thumbnail(self):
        thumbnail = self.process_thumbnail(self.raw_thumbnail)
        self.thumbnail_label.setFixedSize(thumbnail.size())
        self.thumbnail_label.setPixmap(QPixmap.fromImage(thumbnail))

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

        if self.column_count > 1:
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
