import json
import platform
from enum import (
    Enum,
    auto
)
from typing import (
    Optional,
    Dict
)

from qgis.PyQt.QtCore import (
    Qt,
    QPointF,
    QRect,
    QRectF,
    QSize,
    QTimer
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

from koordinates.gui.dataset_dialog import DatasetDialog
from koordinates.gui.thumbnails import downloadThumbnail
from .action_button import (
    CloneButton,
    AddButton
)
from .dataset_utils import (
    DatasetGuiUtils,
    IconStyle
)
from .enums import ExploreMode
from .gui_utils import GuiUtils
from .star_button import StarButton
from ..api import (
    DataType,
    Capability,
    PublicAccessType,
    Dataset
)


class CardLayout(Enum):
    """
    Dataset card layout arrangements
    """
    Tall = auto()
    Wide = auto()
    Compact = auto()
    Empty = auto()


class DatasetItemLayout(QLayout):

    COMPACT_WIDTH_THRESHOLD = 430

    def __init__(self, parent=None):
        super().__init__(parent)

        self.thumbnail_widget = None
        self.thumbnail_item = None
        self.title_container = None
        self.details_container = None
        self.button_container = None
        self.star_button = None
        self.star_button_item = None

        self.private_icon = None
        self.private_icon_item = None

        self._columns: int = 1

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

    def set_star_button(self, widget):
        self.star_button = widget
        self.star_button_item = QWidgetItem(widget)
        self.addChildWidget(widget)
        self.invalidate()

    def set_private_icon(self, widget):
        self.private_icon = widget
        self.private_icon_item = QWidgetItem(widget)
        self.addChildWidget(widget)
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
        if self.star_button:
            res += 1
        if self.private_icon:
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
        elif index == 4:
            return self.star_button_item
        elif index == 5:
            return self.private_icon_item

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
        elif index == 4:
            res = self.star_button_item
            self.star_button_item = None
            self.star_button.deleteLater()
            self.star_button = None
            return res
        elif index == 5:
            res = self.private_icon_item
            self.private_icon_item = None
            self.private_icon.deleteLater()
            self.private_icon = None
            return res
        return None

    def expandingDirections(self):
        return Qt.Orientations()  # Qt.Orientation.Horizontal)

    def hasHeightForWidth(self):
        return False

    def set_table_column_count(self, columns: int):
        """
        Sets the number of columns shown in the parent table
        """
        self._columns = columns

    def sizeHint(self):
        return self.minimumSize()

    def arrangement(self, rect: Optional[QRect] = None) -> CardLayout:
        """
        Returns the arrangement of cards
        """
        if rect is None:
            rect = self.geometry()

        if self._columns > 1:
            return CardLayout.Tall
        elif not rect.width():
            return CardLayout.Empty
        elif rect.width() < DatasetItemLayout.COMPACT_WIDTH_THRESHOLD:
            return CardLayout.Compact
        else:
            return CardLayout.Wide

    @staticmethod
    def fixed_height_for_arrangement(arrangement: CardLayout) -> int:
        """
        Returns the fixed height for an arrangement
        """
        if arrangement == CardLayout.Tall:
            return DatasetItemWidgetBase.CARD_HEIGHT_TALL
        else:
            return DatasetItemWidgetBase.CARD_HEIGHT

    def thumbnail_size_for_rect(self, rect: Optional[QRect] = None) -> QSize:
        """
        Returns the thumbnail size for the given item rect
        """
        if rect is None:
            rect = self.geometry()
        _arrangement = self.arrangement(rect)

        if _arrangement == CardLayout.Wide:
            # sizes here account for borders, hence height is + 2
            size = QSize(DatasetItemWidgetBase.THUMBNAIL_SIZE,
                         DatasetItemWidgetBase.THUMBNAIL_SIZE + 2)
        elif _arrangement == CardLayout.Tall:
            size = QSize(rect.width(), DatasetItemWidgetBase.THUMBNAIL_SIZE)
        else:
            size = QSize(111, rect.height())

        return size

    def minimumSize(self):
        return QSize(150, DatasetItemWidgetBase.CARD_HEIGHT)

    def setGeometry(self, rect):
        super().setGeometry(rect)

        new_arrangement = self.arrangement(rect)
        if new_arrangement is None:
            return

        if new_arrangement == CardLayout.Tall:
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
                        17, 165,
                        rect.width() - 17 * 2 - 20 -
                        (24 if self.private_icon_item else 0),
                        60
                    )
                )

            if self.private_icon_item:
                self.private_icon_item.widget().show()
                self.private_icon_item.setGeometry(
                    QRect(
                        rect.width() - 64, 162,
                        30,
                        20
                    )
                )

            if self.star_button_item:
                self.star_button_item.setGeometry(
                    QRect(
                        rect.width() - 40, 162,
                        30,
                        20
                    )
                )

            if self.details_container:
                self.details_container.setGeometry(
                    QRect(
                        17, 213,
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
        elif new_arrangement == CardLayout.Wide:
            has_thumbnail = False
            if self.thumbnail_item:
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
                        rect.width() - left - 40 -
                        (24 if self.private_icon_item else 0),
                        90
                    )
                )

            if self.private_icon_item:
                self.private_icon_item.widget().show()
                self.private_icon_item.setGeometry(
                    QRect(
                        rect.width() - 64, 12,
                        30,
                        20
                    )
                )

            if self.star_button_item:
                self.star_button_item.setGeometry(
                    QRect(
                        rect.width() - 40, 12,
                        30,
                        20
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
        elif new_arrangement == CardLayout.Compact:
            has_thumbnail = False
            left = 11
            if self.thumbnail_item:
                self.thumbnail_widget.show()
                has_thumbnail = True
                size = self.thumbnail_size_for_rect(rect)
                self.thumbnail_item.setGeometry(
                    QRect(
                        0, 0,
                        size.width(),
                        size.height()
                    )
                )
                left += size.width()

            if self.title_container:
                self.title_container.setGeometry(
                    QRect(
                        left, 15,
                        rect.width() - left - 40 -
                        (24 if self.private_icon_item else 0),
                        90
                    )
                )

            if self.private_icon_item:
                self.private_icon_item.widget().hide()

            if self.star_button_item:
                self.star_button_item.setGeometry(
                    QRect(
                        rect.width() - 40, 12,
                        30,
                        20
                    )
                )

            if self.details_container:
                self.details_container.setGeometry(
                    QRect(
                        left, 35,
                        105,
                        61
                    )
                )

            if self.button_container:
                self.button_container.setGeometry(
                    QRect(
                        left, 103,
                        rect.width() - left - 10,
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

    def __init__(self,
                 parent=None,
                 mode: ExploreMode = ExploreMode.Browse):
        super().__init__(parent)
        self.column_count = None
        self._mode = mode
        if self._mode == ExploreMode.Browse:
            self.setStyleSheet(
                """DatasetItemWidgetBase {{
                   border: 1px solid #dddddd;
                   border-radius: {}px; background: white;
                }}""".format(self.THUMBNAIL_CORNER_RADIUS)
            )
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(self.CARD_HEIGHT)
        self.dataset_layout = DatasetItemLayout()
        self.setLayout(self.dataset_layout)

    def set_column_count(self, count: int):
        """
        Sets the number of table columns in the parent table, so that
        the item can rearrange layout accordingly
        """
        # if self.column_count >= 1 and \
        # use_narrow_cards == is_using_narrow_cards:
        #    return

        self.column_count = count

        self.dataset_layout.set_table_column_count(count)

        arrangement = self.dataset_layout.arrangement()
        if arrangement is None:
            return

        self.setFixedHeight(self.dataset_layout.fixed_height_for_arrangement(
            arrangement
        ))

        # might not be needed anymore...
        if arrangement != CardLayout.Tall:
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
        self.dataset_layout.set_thumbnail_widget(self.thumbnail)

        self.title_layout = QHBoxLayout()
        self.title_frame = QFrame()
        self.title_frame.setStyleSheet(
            """background: #f6f6f6; border-radius: {}px""".format(
                self.THUMBNAIL_CORNER_RADIUS
            )
        )
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_layout.addWidget(self.title_frame)

        self.dataset_layout.set_title_layout(self.title_layout)

        self.details_layout = QHBoxLayout()
        self.details_frame = QFrame()
        self.details_frame.setStyleSheet(
            """background: #f6f6f6; border-radius: {}px""".format(
                self.THUMBNAIL_CORNER_RADIUS
            )
        )
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_layout.addWidget(self.details_frame)

        self.dataset_layout.set_details_layout(self.details_layout)


class DatasetItemWidget(DatasetItemWidgetBase):
    """
    Shows details for a dataset item
    """

    def __init__(self,
                 dataset: Dict,
                 column_count,
                 parent,
                 mode: ExploreMode = ExploreMode.Browse):
        super().__init__(parent, mode)

        self.setMouseTracking(True)
        self.dataset = Dataset(dataset)

        self.old_arrangement = None

        self.raw_thumbnail = None
        self.timer = None

        try:
            font_scale = self.screen().logicalDotsPerInch() / 92
        except AttributeError:
            # requires Qt 5.14+
            font_scale = 1

        self.thumbnail_label = Label()
        self.thumbnail_label.setFixedHeight(150)
        self.dataset_layout.set_thumbnail_widget(self.thumbnail_label)

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        thumbnail_svg = DatasetGuiUtils.thumbnail_icon_for_dataset(
            self.dataset
        )
        if thumbnail_svg:
            self.setThumbnail(GuiUtils.get_svg_as_image(thumbnail_svg,
                                                        150, 150))
        else:
            thumbnail_url = self.dataset.thumbnail_url()
            if thumbnail_url:
                downloadThumbnail(thumbnail_url, self)

        if self.dataset.access == PublicAccessType.none:
            private_icon = QSvgWidget(GuiUtils.get_icon_svg('private.svg'))
            private_icon.setFixedSize(QSize(24, 24))
            private_icon.setToolTip(self.tr('Private'))
            self.dataset_layout.set_private_icon(private_icon)

        self.star_button = StarButton(self.dataset)
        self.dataset_layout.set_star_button(self.star_button)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.addWidget(self.title_label, 1)
        self.dataset_layout.set_title_layout(title_layout)

        detail_font_size = 9
        if platform.system() == 'Darwin':
            # fonts looks smaller on a mac, where things "just work" :P
            detail_font_size = 10
        elif font_scale > 1:
            detail_font_size = int(10 / font_scale)

        self._update_title()

        self.labelUpdatedIcon = QSvgWidget(
            GuiUtils.get_icon_svg("history_gray.svg"))
        self.labelUpdatedIcon.setFixedSize(13, 12)
        self.labelUpdated = QLabel()

        license = self.dataset.details.get('license')
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

        changed_date = self.dataset.updated_at_date()
        if changed_date is not None:
            self.labelUpdated.setText(
                f"""<span style="color: #868889;
                    font-family: Arial, Sans;
                    font-size: {detail_font_size}pt">{changed_date.strftime("%d %b %Y")}</span>"""
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

        self.dataset_layout.set_details_layout(details_layout)

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

        if Capability.Clone in self.dataset.capabilities:
            self.btnClone = CloneButton(self.dataset)
            buttons_layout.addWidget(self.btnClone)
        else:
            self.btnClone = None

        if Capability.Add in self.dataset.capabilities:
            self.btnAdd = AddButton(self.dataset)
            buttons_layout.addWidget(self.btnAdd)
        else:
            self.btnAdd = None

        self.dataset_layout.set_button_layout(buttons_layout)

        self.bbox: Optional[QgsGeometry] = self._geomFromGeoJson(
            self.dataset.details.get("data", {}).get("extent"))
        # if self.bbox:
        #     self.footprint = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        #     self.footprint.setWidth(2)
        #     self.footprint.setColor(QColor(255, 0, 0, 200))
        #     self.footprint.setFillColor(QColor(255, 0, 0, 40))
        # else:
        #     self.footprint = None

        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.set_column_count(column_count)

    def _update_title(self):
        arrangement = self.dataset_layout.arrangement()
        try:
            font_scale = self.screen().logicalDotsPerInch() / 92
        except AttributeError:
            # requires Qt 5.14+
            font_scale = 1

        main_title_size = 11 if arrangement != CardLayout.Compact else 10
        title_font_size = 11 if arrangement != CardLayout.Compact else 10
        if platform.system() == 'Darwin':
            # fonts looks smaller on a mac, where things "just work" :P
            main_title_size = 14 if arrangement != CardLayout.Compact else 12
            title_font_size = 14 if arrangement != CardLayout.Compact else 12
        elif font_scale > 1:
            main_title_size = int(
                12 / font_scale) if arrangement != CardLayout.Compact else int(
                11 / font_scale)
            title_font_size = int(
                12 / font_scale) if arrangement != CardLayout.Compact else int(
                11 / font_scale)

        publisher_name = self.dataset.publisher().name() if \
            self.dataset.publisher() else ''
        self.title_label.setText(
            f"""<p style="line-height: 130%;
                font-size: {main_title_size}pt;
                font-family: Arial, Sans"><b>{self.dataset.title()}</b><br>"""
            f"""<span style="color: #868889;
            font-size: {title_font_size}pt;
            font-family: Arial, Sans">{publisher_name}</span></p>"""
        )

    def _update_arrangement(self):
        self._update_title()
        arrangement = self.dataset_layout.arrangement()
        if arrangement in (CardLayout.Tall, CardLayout.Wide):
            self.labelUpdated.show()
            self.labelUpdatedIcon.show()
        else:
            self.labelUpdated.hide()
            self.labelUpdatedIcon.hide()

    def set_column_count(self, count: int):
        if count == self.column_count:
            return

        super().set_column_count(count)

        arrangement = self.dataset_layout.arrangement()
        if arrangement != self.old_arrangement:
            self.defer_update_thumbnail()

        self.old_arrangement = arrangement
        self._update_arrangement()

    def defer_update_thumbnail(self):
        if self.timer is not None:
            return

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update_thumbnail)
        self.timer.start(10)

    def setThumbnail(self, img: Optional[QImage]):
        self.raw_thumbnail = img
        # defer updating thumbnail, as we need the widget to be initially
        # sized first
        self.defer_update_thumbnail()

    def update_thumbnail(self):
        self.timer = None
        thumbnail_svg = DatasetGuiUtils.thumbnail_icon_for_dataset(
            self.dataset
        )
        if thumbnail_svg:
            size = 150
            self.raw_thumbnail = GuiUtils.get_svg_as_image(
                thumbnail_svg, size, size)

        thumbnail = self.process_thumbnail(self.raw_thumbnail)
        if not thumbnail:
            return

        try:
            dpi_ratio = self.window().screen().devicePixelRatio()
        except AttributeError:
            # requires Qt 5.14
            dpi_ratio = 1
        width = int(thumbnail.width() / dpi_ratio)
        height = int(thumbnail.height() / dpi_ratio)
        self.thumbnail_label.setFixedSize(QSize(width, height))
        self.thumbnail_label.setPixmap(QPixmap.fromImage(thumbnail))

    def process_thumbnail(self, img: Optional[QImage]) -> QImage:
        size = self.dataset_layout.thumbnail_size_for_rect()
        if size.width() == 0 or size.height() == 0:
            return

        arrangement = self.dataset_layout.arrangement()

        image_size = size
        try:
            scale_factor = self.window().screen().devicePixelRatio()
        except AttributeError:
            # requires Qt 5.14+
            scale_factor = 1

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

        path = QPainterPath()
        if arrangement in (CardLayout.Wide, CardLayout.Compact):
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
            resized = img.scaled(image_size.width(),
                                 image_size.height(),
                                 Qt.KeepAspectRatioByExpanding,
                                 Qt.SmoothTransformation)

            if resized.width() > image_size.width():
                left = int((resized.width() - image_size.width()) / 2)
            else:
                left = 0
            if resized.height() > image_size.height():
                top = int((resized.height() - image_size.height()) / 2)
            else:
                top = 0

            cropped = resized.copy(
                QRect(left, top, image_size.width(), image_size.height()))
            painter.drawImage(0, 0, cropped)
        else:
            painter.setBrush(QBrush(QColor('#cccccc')))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, 600, 600)

        painter.end()

        target.setDevicePixelRatio(scale_factor)
        target.setDotsPerMeterX(
            int(target.dotsPerMeterX() * scale_factor))
        target.setDotsPerMeterY(int(
            target.dotsPerMeterY() * scale_factor))
        base = target

        if arrangement == CardLayout.Compact:
            return base

        painter = QPainter(base)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRoundedRect(QRectF(15, 100, 117, 32), 4, 4)

        icon = DatasetGuiUtils.get_icon_for_dataset(self.dataset,
                                                    IconStyle.Light)
        if icon:
            painter.drawImage(QRectF(21, 106, 20, 20),
                              GuiUtils.get_svg_as_image(icon,
                                                        int(20 * scale_factor),
                                                        int(20 * scale_factor)))

        description = DatasetGuiUtils.get_type_description(
            self.dataset
        )

        try:
            font_scale = self.screen().logicalDotsPerInch() / 92
        except AttributeError:
            # requires Qt 5.14 +
            font_scale = 1

        overlay_font_size = 7.5
        if platform.system() == 'Darwin':
            overlay_font_size = 9
        elif font_scale > 1:
            overlay_font_size = 7.5 / font_scale

        if description:
            font = QFont('Arial')
            font.setPointSizeF(overlay_font_size / scale_factor)
            font.setBold(True)
            painter.setFont(font)

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(QPointF(47, 112), description)

        subtitle = DatasetGuiUtils.get_subtitle(self.dataset,
                                                short_format=True)
        if subtitle:
            font = QFont('Arial')
            font.setPointSizeF(overlay_font_size / scale_factor)
            font.setBold(False)
            painter.setFont(font)

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(QPointF(47, 126), subtitle)

        painter.end()
        return base

    def resizeEvent(self, event):
        super().resizeEvent(event)

        arrangement = self.dataset_layout.arrangement()
        if arrangement != self.old_arrangement or \
                arrangement == CardLayout.Tall:
            self.defer_update_thumbnail()

        self.old_arrangement = arrangement
        self._update_arrangement()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.show_details()
        else:
            super().mousePressEvent(event)

    def show_details(self):
        """
        Shows the details dialog for the item
        """
        if self.dataset.datatype == DataType.Repositories:
            # dlg = RepositoryDialog(self, self.dataset)
            return
        else:
            dlg = DatasetDialog(self, self.dataset)
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
