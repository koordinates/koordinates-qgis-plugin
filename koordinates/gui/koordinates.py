import json
import locale
import os
from functools import partial
from typing import (
    Dict,
    Optional,
    List
)

from qgis.PyQt import sip
from qgis.PyQt import uic
from qgis.PyQt.QtCore import (
    QUrl,
    QRect,
    Qt,
    QSize,
    QObject,
    QEvent,
    QUrlQuery,
    pyqtSignal
)
from qgis.PyQt.QtGui import (
    QDesktopServices,
    QPalette,
    QColor,
    QIcon
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.PyQt.QtWidgets import (
    QVBoxLayout,
    QAction,
    QMenu,
    QHBoxLayout,
    QComboBox,
    QSizePolicy,
    QFrame,
    QTabBar,
    QWidget,
    QLabel,
    QStylePainter,
    QStyleOptionTab,
    QStyleOptionTabBarBase,
    QStyle,
    QLayout,
    QWidgetItem,
    QToolButton,
    QButtonGroup,
    QWidgetAction,
    QRadioButton
)
from qgis.gui import (
    QgsDockWidget,
    QgsFilterLineEdit
)

from .colored_frame import ColoredFrame
from .context_widget import (
    ContextItemMenuAction,
    ContextLogo,
    NoMouseReleaseMenu
)
from .country_widget import CountryWidgetAction
from .results_panel import ResultsPanel
from .filter_widget import FilterWidget
from .gui_utils import GuiUtils
from .login_widget import LoginWidget
from .svg_label import SvgLabel
from .thumbnails import downloadThumbnail
from ..api import (
    KoordinatesClient,
    SortOrder,
    DataBrowserQuery,
    Publisher,
    DataType
)
from .enums import (
    StandardExploreModes
)
from .country_widget import EmojiToIconRenderer

from ..auth import OAuthWorkflow

pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('koordinates.ui'))

SETTINGS_NAMESPACE = "Koordinates"


class CustomTab(QTabBar):

    def paintEvent(self, event):

        painter = QStylePainter(self)
        tab_overlap = QStyleOptionTab()
        tab_overlap.shape = self.shape()

        option = QStyleOptionTabBarBase()
        option.initFrom(self)
        option.shape = self.shape()
        option.documentMode = self.documentMode()
        option.rect = QRect(0, self.height() - 2, self.width(), 2)
        painter.drawPrimitive(QStyle.PE_FrameTabBarBase, option)

        for i in range(self.count()):
            option = QStyleOptionTab()
            self.initStyleOption(option, i)

            if i == Koordinates.TAB_STARRED_INDEX:
                painter.drawControl(QStyle.CE_TabBarTabShape, option)
                painter.drawPixmap(option.rect.center().x() - 7, option.rect.center().y() - 8,
                                   GuiUtils.get_icon_pixmap('star_filled.svg'))
            elif i == Koordinates.TAB_CONTEXT_SWITCHER_INDEX:
                painter.drawControl(QStyle.CE_TabBarTabShape, option)
                painter.drawPixmap(option.rect.center().x() - 7, option.rect.center().y() - 8,
                                   GuiUtils.get_icon_pixmap('context_switcher.svg'))
            else:
                painter.drawControl(QStyle.CE_TabBarTab, option)


class ResponsiveLayout(QLayout):
    WIDE_MODE_WIDTH_THRESHOLD = 780

    def __init__(self, parent=None):
        super().__init__(parent)

        self.filter_widget: Optional[FilterWidget] = None
        self.filter_item: Optional[QWidgetItem] = None
        self.results_layout = None
        self.is_wide_mode = False

    def set_filter_widget(self, widget: FilterWidget):
        self.filter_widget = widget
        self.filter_item = QWidgetItem(widget)
        self.addChildWidget(widget)
        self.invalidate()

    def set_results_layout(self, layout):
        self.results_layout = layout
        self.addChildLayout(layout)
        self.invalidate()

    def addItem(self, item):
        pass

    def count(self):
        res = 0
        if self.filter_item:
            res += 1
        if self.results_layout:
            res += 1
        return res

    def itemAt(self, index):
        if index == 0:
            return self.filter_item
        elif index == 1:
            return self.results_layout

    def takeAt(self, index: int):
        if index == 0:
            res = self.filter_item
            self.filter_item = None
            self.filter_widget.deleteLater()
            self.filter_item = None
            return res
        elif index == 1:
            res = self.results_layout
            self.results_layout = None
            return res
        return None

    def expandingDirections(self):
        return Qt.Orientations()  # Qt.Orientation.Horizontal)

    def hasHeightForWidth(self):
        return False

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        return QSize(130, 130)

    def setGeometry(self, rect):
        super().setGeometry(rect)

        margins = self.contentsMargins()
        left = margins.left()
        top = margins.top()
        right = margins.right()
        bottom = margins.bottom()

        effective_rect = rect.adjusted(left, top, -right, -bottom)

        advanced_filter_item_rect_changed = False

        if effective_rect.width() < ResponsiveLayout.WIDE_MODE_WIDTH_THRESHOLD:
            # show advanced filters on top
            self.is_wide_mode = False

            top = effective_rect.top()

            if self.filter_item:
                self.filter_widget.set_wide_mode(False)
                height = self.filter_widget.sizeHint().height()

                new_geom = QRect(
                    effective_rect.left(), top,
                    effective_rect.width(),
                    height
                )
                advanced_filter_item_rect_changed = \
                    new_geom != self.filter_item.geometry()

                self.filter_item.setGeometry(
                    new_geom
                )

                top += height

            if self.results_layout:
                self.results_layout.setGeometry(
                    QRect(
                        effective_rect.left(), top,
                        effective_rect.width(),
                        effective_rect.height() - top
                    )
                )
        else:
            # show advanced filters on left
            self.is_wide_mode = True

            if self.filter_item:
                self.filter_widget.set_wide_mode(True)
                # self.filter_widget.show_advanced(True)
                self.filter_item.setGeometry(
                    QRect(
                        effective_rect.left(),
                        effective_rect.top(),
                        270,
                        effective_rect.height()
                    )
                )

            if self.results_layout:
                self.results_layout.setGeometry(
                    QRect(
                        effective_rect.left() + 270 + 8, effective_rect.top(),
                        effective_rect.width() - 270 - 8,
                        effective_rect.height()
                    )
                )

        if self.filter_widget and advanced_filter_item_rect_changed:
            self.filter_widget.layout().invalidate()
        else:
            self.filter_widget.update()


class CustomLabelWidgetAction(QWidgetAction):
    selected = pyqtSignal()

    def __init__(self, text: str,
                 enabled: bool = True,
                 checkable: bool = False,
                 indent: int = 0,
                 sub_text: Optional[str] = None,
                 icon: Optional[QIcon] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._text = text
        self._widget = None
        self._container = None
        self._enabled = enabled
        self._checkable = checkable
        self._action_group = None
        self._indent = indent
        self._sub_text = sub_text
        self._icon = icon

    def set_widget_checked(self, checked: bool):
        if self._checkable:
            self._widget.setChecked(checked)

    def eventFilter(self, obj, event):
        if not self._enabled:
            # swallow clicks, we don't want to user to dismiss the menu by clicking
            # disabled actions
            if event.type() in (QEvent.MouseButtonPress,
                                QEvent.MouseButtonDblClick,
                                QEvent.MouseButtonRelease):
                return True
        else:
            if event.type() == QEvent.HoverEnter:
                self.highlight(True)
            elif event.type() == QEvent.HoverLeave:
                self.highlight(False)

        return super().eventFilter(obj, event)

    def _on_radio_button_toggled(self):
        """
        Called when the radio button is ticked
        """
        if self._widget.isChecked():
            self.selected.emit()

    def createWidget(self, parent):
        if self._checkable:
            check_box = QRadioButton(self._text, parent)
            if self._icon:
                check_box.setIcon(self._icon)
            if self._enabled:
                check_box.setMouseTracking(True)
            else:
                self._action_group = QButtonGroup(self)
                self._action_group.setExclusive(False)
                self._action_group.addButton(check_box)
            check_box.installEventFilter(self)
            check_box.setStyleSheet(
                """margin-top: 8px; margin-right:30px;
                 margin-bottom:{}px; margin-left:{}px;""".format(
                    8 if not self._sub_text else 0,
                    15 + self._indent * 20
                ))
            check_box.toggled.connect(self._on_radio_button_toggled)
            self._widget = check_box

            if self._sub_text:
                vl = QVBoxLayout()
                vl.setContentsMargins(0, 0, 0, 0)
                vl.addWidget(self._widget)
                sub_text_label = QLabel(self._sub_text)
                sub_text_label.setStyleSheet(
                    """margin-top: 0px; margin-right:20px;
                     margin-bottom: 8px; margin-left:{}px;""".format(
                        35 + self._indent * 20
                    ))
                palette = sub_text_label.palette()
                text_color = palette.color(QPalette.WindowText)
                text_color.setAlphaF(0.7)
                palette.setColor(QPalette.WindowText, text_color)
                sub_text_label.setPalette(palette)
                font = sub_text_label.font()
                font.setPointSizeF(font.pointSizeF() * 0.85)
                sub_text_label.setFont(font)

                vl.addWidget(sub_text_label)
                self._container = QWidget(parent)
                self._container.setLayout(vl)
                return self._container
            else:
                self._container = self._widget
                return self._widget
        else:
            label = QLabel(self._text, parent)
            if self._enabled:
                label.setMouseTracking(True)
            label.installEventFilter(self)

            palette = label.palette()
            text_color = palette.color(QPalette.WindowText)
            text_color.setAlphaF(0.7)
            palette.setColor(QPalette.WindowText, text_color)
            label.setPalette(palette)
            label.setStyleSheet('margin: 10px;')
            font = label.font()
            font.setPointSizeF(font.pointSizeF() * 0.9)
            label.setFont(font)
            self._widget = label
            self._container = self._widget

            return self._widget

    def highlight(self, enabled: bool):
        self._container.setBackgroundRole(QPalette.Highlight if enabled else QPalette.Window)
        self._container.setAutoFillBackground(enabled)


class WidgetActionMenuHoverEventFilter(QObject):

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._last_widget_action = None

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.MouseMove:
            action = obj.actionAt(event.pos())
            if isinstance(action, CustomLabelWidgetAction) and action._enabled:
                if self._last_widget_action and action != self._last_widget_action:
                    self._last_widget_action.highlight(False)

                action.highlight(True)
                self._last_widget_action = action
            else:
                if self._last_widget_action:
                    self._last_widget_action.highlight(False)
                    self._last_widget_action = None

        return super().eventFilter(obj, event)


class Koordinates(QgsDockWidget, WIDGET):
    TAB_STARRED_INDEX = 1
    TAB_EXPLORE_INDEX = 0
    TAB_CONTEXT_SWITCHER_INDEX = 3

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

        self._block_searching = 0
        self._facets = {}
        self._current_facets_reply = None
        self._visible_count = -1
        self._total_count = -1
        self._contexts = []
        self._current_context = None
        self._prev_tab = -1

        # self.button_home.setIcon(GuiUtils.get_icon('home.svg'))
        # self.button_home.setToolTip('Home')

        self.logo_widget = SvgLabel('koordinates_logo.svg', 110, ContextLogo.LOGO_HEIGHT)
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.logo_widget)
        self.logo_frame.setLayout(hl)

        self.context_tab_container = QWidget(self.context_container)
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addSpacing(11)

        self.context_tab = CustomTab()
        hl.addWidget(self.context_tab)
        hl.addSpacing(11)
        self.context_tab_container.setLayout(hl)

        self.context_tab_container.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.context_tab.setExpanding(False)
        # self.context_tab.setFixedSize(100,100)
        self.context_tab.addTab('')
        self.context_tab.addTab('')
        self.context_tab.setTabIcon(self.TAB_STARRED_INDEX, GuiUtils.get_icon('star_filled.svg'))
        self.context_tab.setTabToolTip(self.TAB_STARRED_INDEX, 'Starred')
        self.context_tab.setDrawBase(True)
        self.context_tab_container.setFixedHeight(self.context_tab.sizeHint().height())

        self.context_frame = ColoredFrame()
        self.context_frame.set_color(QColor())
        self.context_frame.setObjectName('context_frame')
        context_frame_layout = QVBoxLayout()
        context_frame_layout.setContentsMargins(0, 0, 0, 0)

        context_layout = QVBoxLayout()
        context_layout.setContentsMargins(0, self.context_tab.sizeHint().height() - 2, 0, 0)
        context_layout.setSpacing(0)
        self.context_header = QWidget()
        hl = QHBoxLayout()
        hl.setContentsMargins(11, 0, 0, 0)
        self.context_logo_label = ContextLogo()
        self.context_logo_label.setContentsMargins(0, 8, 0, 0)
        hl.addWidget(self.context_logo_label)
        self.context_name_label = QLabel()
        self.context_name_label.setContentsMargins(11, 14, 11, 10)
        hl.addWidget(self.context_name_label)
        hl.addStretch(1)

        self.context_header.setLayout(hl)

        context_frame_layout.addWidget(self.context_header)

        self.filter_top_frame = QFrame()
        context_frame_layout.addWidget(self.filter_top_frame)

        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 16, 0, 0)

        self.context_header.hide()

        self.filter_top_frame.setLayout(filter_layout)

        self.context_frame.setLayout(context_frame_layout)
        context_layout.addWidget(self.context_frame)

        self.context_container.setLayout(context_layout)

        self.context_tab.show()

        self.context_tab.setTabText(self.TAB_EXPLORE_INDEX, self.tr('Explore'))
        self.context_tab.setTabToolTip(self.TAB_EXPLORE_INDEX, self.tr('Explore'))

        self.context_tab.setCurrentIndex(self.TAB_EXPLORE_INDEX)

        # self.context_container.setFixedHeight(self.context_tab.sizeHint().height() + 100)

        self.button_help.setIcon(GuiUtils.get_icon('help.svg'))
        self.button_help.setToolTip('Help')

        self.button_user.setIcon(GuiUtils.get_icon('user.svg'))
        self.button_user.setToolTip('User')

        # a QToolButton with an icon will appear smaller by default vs one with text, so
        # force the advanced button to match the Clear All button size
        temp_combo = QComboBox()
        for b in (self.button_help,
                  # self.button_home,
                  self.button_user):
            b.setFixedHeight(temp_combo.sizeHint().height())
            b.setFixedWidth(b.height())

        self.results_panel = ResultsPanel()
        self.results_panel.visible_count_changed.connect(self._visible_count_changed)
        self.results_panel.total_count_changed.connect(self._total_count_changed)
        self.results_panel.publisher_selected.connect(
            self._publisher_selected)
        self.oauth: Optional[OAuthWorkflow] = None

        self.login_widget = LoginWidget(self)
        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)
        vl.addWidget(self.login_widget)
        self.pageAuth.setLayout(vl)

        results_layout = QVBoxLayout()

        self.label_count = QLabel()
        self.button_sort_order = QToolButton()
        self.button_sort_order.setText('...')
        self.button_sort_order.setPopupMode(QToolButton.InstantPopup)
        self.button_sort_order.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.button_sort_order.setAutoRaise(True)

        self.browse_header_widget = QWidget()
        self.browse_header_widget.setSizePolicy(QSizePolicy.Ignored,
                                                QSizePolicy.Fixed)
        results_top_layout = QHBoxLayout()
        results_top_layout.setContentsMargins(0, 0, 0, 0)
        results_top_layout.addWidget(self.label_count)
        results_top_layout.addStretch()
        results_top_layout.addWidget(self.button_sort_order)
        self.browse_header_widget.setLayout(results_top_layout)
        results_layout.addWidget(self.browse_header_widget)

        results_layout.addWidget(self.results_panel)

        self.responsive_layout = ResponsiveLayout()
        self.responsive_layout.setContentsMargins(11, 0, 11, 0)
        self.responsive_layout.set_results_layout(results_layout)

        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(11, 0, 11, 0)

        self.search_line_edit = QgsFilterLineEdit()
        self.search_line_edit.setShowClearButton(True)
        self.search_line_edit.setShowSearchIcon(True)
        self.search_line_edit.setPlaceholderText('Search')
        self.search_line_edit.setFixedHeight(
            int(self.search_line_edit.sizeHint().height() * 1.2)
        )
        filter_layout.addWidget(self.search_line_edit)

        self.filter_widget = FilterWidget(self)
        self.filter_widget.set_search_line_edit(self.search_line_edit)
        filter_layout.addSpacing(6)

        self.filter_widget.publisher_changed.connect(
            self.results_panel.set_publisher
        )

        self.horizontal_filter_container.setLayout(filter_layout)

        self.responsive_layout.set_filter_widget(self.filter_widget)

        self.browserFrame.setLayout(self.responsive_layout)

        self.context_frame.color_height = int(self.filter_widget.height() / 2)

        self.filter_widget.filters_changed.connect(self.search)
        self.filter_widget.explore.connect(self.explore)
        self.filter_widget.explore_publishers.connect(self.explore_publishers)

        self.context_tab.currentChanged.connect(self._context_tab_changed)
        self.context_tab.tabBarClicked.connect(self._tab_bar_clicked)

        self.filter_widget.clear_all.connect(self._clear_all_filters)
        self.results_panel.publisher_cleared.connect(
            self.filter_widget.remove_publisher_filter)

        self.button_sort_order.setStyleSheet(
            """QToolButton::menu-indicator { image: none }
            QToolButton { margin-top: 2px; }
            """
        )
        self.sort_menu = QMenu(self.button_sort_order)
        self.sort_by_popular_action: Optional[QAction] = None
        self._sort_menu_event_filter = WidgetActionMenuHoverEventFilter(self.sort_menu)
        self.sort_menu.installEventFilter(self._sort_menu_event_filter)

        self.button_sort_order.setMenu(self.sort_menu)
        smaller_font = self.button_sort_order.font()
        smaller_font_size = max(smaller_font.pointSize() - 1, 7)
        smaller_font.setPointSize(smaller_font_size)
        self.button_sort_order.setFont(smaller_font)

        self.label_count.setFont(smaller_font)
        active_color = self.palette().color(QPalette.WindowText)
        active_color.setAlphaF(0.6)
        p = QPalette(self.palette())
        p.setColor(QPalette.WindowText, active_color)
        self.label_count.setPalette(p)

        self._set_count_label()

        self.sort_menu.aboutToShow.connect(self._sort_order_menu_about_to_show)
        self._set_sort_order_button_text()

        self.help_menu = QMenu(self.button_help)
        self.help_action = QAction('Koordinates Help', self.help_menu)
        self.help_action.triggered.connect(self._show_help)
        self.help_menu.addAction(self.help_action)
        self.report_action = QAction('Report a Bug or Issue', self.help_menu)
        self.report_action.triggered.connect(self._report_bug)
        self.help_menu.addAction(self.report_action)

        self.button_help.setMenu(self.help_menu)

        self.user_menu = QMenu(self.button_user)
        self.current_user_action = QAction('Current User', self.user_menu)
        self.user_menu.addAction(self.current_user_action)
        self.user_country_action = CountryWidgetAction(self.user_menu)
        self.user_menu.addAction(self.user_country_action)
        self.user_menu.addSeparator()
        self.edit_profile_action = QAction('Edit Profile', self.user_menu)
        self.edit_profile_action.triggered.connect(self._edit_profile)
        self.user_menu.addAction(self.edit_profile_action)
        self.logout_action = QAction('Logout', self.user_menu)
        self.logout_action.triggered.connect(self.logout)
        self.user_menu.addAction(self.logout_action)
        self.user_menu.aboutToShow.connect(self._user_menu_about_to_show)

        self.button_user.setMenu(self.user_menu)

        self.context_tab_container.setFixedWidth(self.context_container.width())

        KoordinatesClient.instance().loginChanged.connect(self._loginChanged)
        self._data_options: Optional[Dict] = None
        KoordinatesClient.instance().data_options_retrieved.connect(
            self._data_options_retrieved
        )

        self.setMinimumWidth(430)

        self._loginChanged(False)

    def cancel_active_requests(self):
        """
        Cancels any active request
        """
        self.login_widget.cancel_active_requests()

        if self._current_facets_reply is not None and \
                not sip.isdeleted(self._current_facets_reply):
            self._current_facets_reply.abort()

        self._current_facets_reply = None

        self.results_panel.cancel_active_requests()

    def _clear_all_filters(self):
        """
        Called when the filter widget Clear All action is triggered
        """
        self.filter_widget.sort_order = SortOrder.Popularity
        self._set_sort_order_button_text()

    def _sort_order_menu_about_to_show(self):
        """
        Called when the sort order menu is about to show
        """
        for action in self.sort_menu.actions():
            if action == self.sort_by_popular_action:
                action.set_widget_checked(
                    isinstance(self.filter_widget.sort_order, str)
                    or self.filter_widget.sort_order == SortOrder.Popularity
                )
            else:
                is_checked = (action.data() == self.filter_widget.sort_order or
                              (self.filter_widget.sort_order == SortOrder.Popularity and
                               not action.data()))
                if isinstance(action, CustomLabelWidgetAction):
                    action.set_widget_checked(is_checked)

    def _set_sort_order(self, order: SortOrder):
        """
        Triggered when the sort order is changed
        """
        self.sort_menu.close()
        if self.filter_widget.sort_order == order:
            return

        self.filter_widget.sort_order = order
        self._set_sort_order_button_text()
        self.search()

    def _set_popular_sort_order(self, code: str):
        """
        Triggered when the popular sort order is selected
        """
        self.sort_menu.close()
        if self.filter_widget.sort_order == code:
            return

        self.filter_widget.sort_order = code
        self._set_sort_order_button_text()
        self.search()

    def _set_sort_order_button_text(self):
        """
        Sets the correct text for the sort order button
        """
        if isinstance(self.filter_widget.sort_order, str):
            region_string = {
                'AU': 'AU',
                'NZ': 'NZ',
                'GB': 'UK',
                'US': 'US'
            }.get(self.filter_widget.sort_order)
            if region_string:
                self.button_sort_order.setText(
                    'Popular for {}'.format(region_string)
                )
            else:
                self.button_sort_order.setText(
                    'Popular'
                )
        else:
            self.button_sort_order.setText(
                self.filter_widget.sort_order.to_button_text()
            )

    def _show_context_switcher_menu(self):
        # because this menu will be shown in a fix location (center of tab), we
        # don't allow it to be dismissed via a mouse release event
        # otherwise the menu may pop up under the mouse location and so the initial
        # click to show will cause the menu to immediately get dismissed when the click
        # is released
        menu = NoMouseReleaseMenu()

        tab_rect = self.context_tab.tabRect(3)

        tab_center = self.context_tab.mapToGlobal(tab_rect.center())

        current_context_tab = self.context_tab.tabData(self.context_tab.count() - 2)

        def on_selected(c):
            menu.deleteLater()
            self._set_visible_context(c)

        for idx, c in enumerate(self._contexts):
            w = ContextItemMenuAction(c, c['name'] == current_context_tab,
                                      idx == 0, menu)
            w.selected.connect(partial(on_selected, c))

            menu.addAction(w)

        menu.exec_(tab_center)

    def _set_visible_context(self, details):
        self.context_tab.setTabText(self.context_tab.count() - 2,
                                    'My data' if details['type'] == 'user' else details['name'])
        self.context_tab.setTabData(self.context_tab.count() - 2, details['name'])
        self._prev_tab = -1
        self.context_tab.setCurrentIndex(self.context_tab.count() - 2)
        self._context_tab_changed(self.context_tab.currentIndex())

    def _tab_bar_clicked(self, target: int):
        if self.context_tab.tabData(target) == 'CONTEXT_SWITCHER':
            self._show_context_switcher_menu()

    def _context_tab_changed(self, current: int):
        """
        Called when the context tab is changed
        """
        if current == self._prev_tab:
            return

        if current in (self.TAB_EXPLORE_INDEX, self.TAB_STARRED_INDEX):
            self._current_context = {"type": "site", "domain": "all"}
            self.filter_top_frame.layout().setContentsMargins(0, 16, 0, 0)
            self.context_frame.set_color(QColor())
            self.context_frame.color_height = int(self.filter_widget.height() / 2)
            self.context_header.setVisible(False)
        elif self.context_tab.tabData(current) == 'CONTEXT_SWITCHER':
            self.context_tab.setCurrentIndex(self._prev_tab)
            return
        else:
            self.filter_top_frame.layout().setContentsMargins(0, 0, 0, 0)
            self._current_context = \
                [c for c in self._contexts if c['name'] == self.context_tab.tabData(current)][0]

            if self._current_context['type'] == 'user':
                KoordinatesClient.instance().reset_domain()
                if KoordinatesClient.instance().user_details()["avatar_url"]:
                    self.context_logo_label.circle = True
                    downloadThumbnail(KoordinatesClient.instance().user_details()["avatar_url"],
                                      self.context_logo_label)
                    self.context_logo_label.show()
                else:
                    self.context_logo_label.hide()
                self.context_frame.color_height = int(
                    self.filter_widget.height() / 2) + ContextLogo.LOGO_HEIGHT + 15

                self.context_name_label.setText(
                    '<b style="color: white; font-size: 10pt">{}</b>'.format(
                        self._current_context['name']))
                self.context_name_label.show()
                self.context_frame.set_color(QColor('#323233'))
                self.context_header.setVisible(True)
            else:
                self.context_logo_label.circle = False
                KoordinatesClient.instance().domain = \
                    self._current_context.get('domain')
                downloadThumbnail(self._current_context.get("logo"),
                                  self.context_logo_label)
                self.context_logo_label.show()
                self.context_frame.color_height = int(
                    self.filter_widget.height() / 2) + ContextLogo.LOGO_HEIGHT + 15

                background_color_text = self._current_context["org"].get("background_color")
                if background_color_text and not background_color_text.startswith('#'):
                    background_color_text = '#' + background_color_text

                background_color = QColor(background_color_text)
                if not background_color.isValid():
                    background_color = QColor('#323233')

                self.context_frame.set_color(background_color)

                if not self._current_context.get("logo"):
                    self.context_name_label.setText(
                        '<b style="color: white; font-size: 10pt">{}</b>'.format(
                            self._current_context['name']))
                    self.context_name_label.show()
                    self.context_logo_label.hide()
                else:
                    self.context_name_label.hide()
                    self.context_logo_label.show()

                self.context_header.setVisible(True)

        self._prev_tab = current

        self._block_searching += 1
        self.filter_widget.set_starred(current == self.TAB_STARRED_INDEX)

        is_explore_tab = current == self.TAB_EXPLORE_INDEX
        self.filter_widget.set_is_browse_tab(
            is_explore_tab
        )
        self.filter_widget._clear_all()

        self._block_searching -= 1
        if not is_explore_tab:
            # force browse tab
            self.filter_widget.set_explore_mode(StandardExploreModes.Browse)
        else:
            if self.filter_widget.explore_mode() == \
                    StandardExploreModes.Browse:
                self.search()
            else:
                self.explore()

    def _user_menu_about_to_show(self):
        """
        Called when the user menu is about to show
        """
        user = KoordinatesClient.instance().user_details()
        self.current_user_action.setText(
            '{} {}'.format(user.get('first_name'), user.get('last_name')).strip()
        )

    def search(self):
        if self._block_searching:
            return

        browser_query = self.filter_widget.build_query()
        context = self._current_context
        self.browse_header_widget.show()
        self._fetch_facets(browser_query, context)

        self.results_panel.populate(browser_query, context)

    def explore(self, section_slug: str = StandardExploreModes.Popular):
        context = self._current_context
        self.browse_header_widget.hide()
        self.results_panel.explore(section_slug, context)

    def explore_publishers(self):
        context = self._current_context
        self.browse_header_widget.hide()
        self.results_panel.show_publishers(context)

    def _fetch_facets(self,
                      query: Optional[DataBrowserQuery] = None,
                      context: Optional[str] = None):
        if self._current_facets_reply is not None and not sip.isdeleted(
                self._current_facets_reply):
            self._current_facets_reply.abort()
            self._current_facets_reply = None

        self._current_facets_reply = KoordinatesClient.instance().facets_async(
            query=query,
            context=context
        )
        self._current_facets_reply.finished.connect(
            partial(self._facets_reply_finished, self._current_facets_reply))

    def _facets_reply_finished(self, reply: QNetworkReply):
        if sip.isdeleted(self):
            return

        if reply != self._current_facets_reply:
            # an old reply we don't care about anymore
            return

        self._current_facets_reply = None
        if reply.error() == QNetworkReply.OperationCanceledError:
            return

        if reply.error() != QNetworkReply.NoError:
            print('error occurred :(')
            return
        #            self.error_occurred.emit(request.reply().errorString())

        # inject context into facets, so that this is accessible to widgets
        request_url = reply.request().url()
        from_context = QUrlQuery(request_url.query()).queryItemValue('from')

        self._facets = json.loads(reply.readAll().data().decode())
        self._facets['from'] = from_context
        self.filter_widget.set_facets(self._facets)

    def _visible_count_changed(self, count):
        self._visible_count = count
        self._set_count_label()

    def _total_count_changed(self, count):
        self._total_count = count
        self._set_count_label()

    def _set_count_label(self):
        if self._total_count < 0 or self._visible_count < 0:
            self.label_count.clear()
        elif self._total_count == 0:
            self.label_count.setText(
                'Showing 0 of 0 results'
            )
        else:
            self.label_count.setText(
                'Showing {} of {} results'.format(
                    locale.format_string("%d", self._visible_count, grouping=True),
                    locale.format_string("%d", self._total_count, grouping=True))
            )

    def _publisher_selected(self, publisher: Publisher):
        query = DataBrowserQuery()
        query.data_types = {DataType.Vectors, DataType.Rasters, DataType.Grids}
        query.publisher = publisher

        self.filter_widget.set_from_query(query)
        self.filter_widget.set_explore_mode(StandardExploreModes.Browse)
        context = self._current_context

        self.results_panel.populate(query, context)

    def _loginChanged(self, logged_in: bool):
        if logged_in:
            self.stackedWidget.setCurrentWidget(self.pageBrowser)

            user = KoordinatesClient.instance().user_details()
            self.user_country_action.set_country_code(user['country'])

            self._build_sort_menu()

            self._create_context_tabs(user.get('contexts', []))

            self.filter_widget.set_logged_in(True)
        else:
            self.stackedWidget.setCurrentWidget(self.pageAuth)

    def _data_options_retrieved(self, options: dict):
        """
        Called when the data options request is finished
        """
        self._data_options = options
        self._build_sort_menu()

    def _build_sort_menu(self):
        """
        Builds the dataset sorting options menu.

        This can only be done after a login event
        """
        user_details = KoordinatesClient.instance().user_details()
        if not user_details or not self._data_options:
            return

        self.sort_menu.clear()

        country_choices = (self._data_options
                           .get('filters', {})
                           .get('country', {})
                           .get('choices', []))

        user_country_code = user_details['country']

        sort_by_action = CustomLabelWidgetAction(
            self.tr('Sort by'), enabled=False,
            parent=self.sort_menu)
        self.sort_menu.addAction(sort_by_action)

        self.sort_by_popular_action = CustomLabelWidgetAction(self.tr('Popular'),
                                                              enabled=False,
                                                              checkable=True,
                                                              parent=self.sort_menu)
        self.sort_menu.addAction(self.sort_by_popular_action)
        for country_choice in country_choices:
            country = country_choice['display_name']
            code = country_choice['value']

            if code == 'global':
                code = ''

            if not code:
                sub_text = self.tr("Don't bias results by location")
            elif user_country_code == code:
                sub_text = "Your Koordinates ID country"
            else:
                sub_text = None

            if code:
                icon = EmojiToIconRenderer.render_flag_to_icon(code)
            else:
                icon = EmojiToIconRenderer.render_emoji_to_icon('🌎')
            sort_by_action = CustomLabelWidgetAction(country,
                                                     enabled=True,
                                                     checkable=True,
                                                     indent=1,
                                                     sub_text=sub_text,
                                                     icon=icon,
                                                     parent=self.sort_menu)

            self.sort_menu.addAction(sort_by_action)
            sort_by_action.setData(code)
            sort_by_action.selected.connect(partial(self._set_popular_sort_order, code))

        for order in (
                SortOrder.RecentlyAdded,
                SortOrder.RecentlyUpdated,
                SortOrder.AlphabeticalAZ,
                SortOrder.AlphabeticalZA,
                SortOrder.Oldest):
            sort_by_action = CustomLabelWidgetAction(SortOrder.to_text(order),
                                                     enabled=True,
                                                     checkable=True,
                                                     parent=self.sort_menu)
            self.sort_menu.addAction(sort_by_action)
            sort_by_action.selected.connect(partial(self._set_sort_order, order))
            sort_by_action.setData(order)

        self.filter_widget.sort_order = ''
        self._set_sort_order_button_text()

    def _create_context_tabs(self, contexts: List):
        """
        Sets the context information
        """
        self._contexts = contexts[:]

        for i in range(self.context_tab.count() - 1, 0, -1):
            if i in (self.TAB_EXPLORE_INDEX, self.TAB_STARRED_INDEX):
                continue

            self.context_tab.removeTab(i)

        if self._contexts:
            tab_text = self._contexts[0]['name'] if self._contexts[0][
                                                        'type'] != 'user' else 'My data'
            idx = self.context_tab.addTab(tab_text)
            self.context_tab.setTabData(idx, self._contexts[0]['name'])
            if len(self._contexts) > 1:
                idx = self.context_tab.addTab('')
                self.context_tab.setTabIcon(idx, GuiUtils.get_icon('context_switcher.svg'))
                self.context_tab.setTabData(idx, 'CONTEXT_SWITCHER')
        else:
            pass

    def logout(self):
        """
        Logs the user out
        """
        KoordinatesClient.instance().logout()

    def _edit_profile(self):
        """
        Opens the edit profile page
        """
        QDesktopServices.openUrl(QUrl('https://id.koordinates.com/profile/'))

    def _show_help(self):
        """
        Shows the help web page
        """
        QDesktopServices.openUrl(
            QUrl(
                'https://help.koordinates.com/plugins/qgis-koordinates-plugin/'
            )
        )

    def _report_bug(self):
        """
        Shows the report bug page
        """
        QDesktopServices.openUrl(
            QUrl(
                'https://github.com/koordinates/koordinates-qgis-plugin/issues'
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.context_tab_container.setFixedWidth(self.context_container.width())
