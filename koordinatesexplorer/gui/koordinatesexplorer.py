import json
import os
import locale
from functools import partial
from typing import Optional, Dict

from qgis.PyQt import sip
from qgis.PyQt import uic
from qgis.PyQt.QtCore import (
    QThread,
    QUrl
)
from qgis.PyQt.QtGui import (
    QPixmap,
    QDesktopServices,
    QPalette
)
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.PyQt.QtWidgets import (
    QVBoxLayout,
    QApplication,
    QAction,
    QMenu,
    QLabel,
    QHBoxLayout,
    QComboBox
)
from qgis.core import (
    QgsApplication,
    Qgis,
)
from qgis.gui import QgsDockWidget
from qgis.utils import iface

from koordinatesexplorer.auth import OAuthWorkflow
from koordinatesexplorer.gui.datasetsbrowserwidget import DatasetsBrowserWidget
from .context_widget import ContextWidget
from .country_widget import CountryWidgetAction
from .filter_widget import FilterWidget
from .gui_utils import GuiUtils
from ..api import (
    KoordinatesClient,
    SortOrder,
    DataBrowserQuery
)

pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('koordinatesexplorer.ui'))

SETTINGS_NAMESPACE = "Koordinates"
AUTH_CONFIG_ID = "koordinates_auth_id"


class KoordinatesExplorer(QgsDockWidget, WIDGET):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self._facets = {}
        self._current_facets_reply = None
        self._visible_count = -1
        self._total_count = -1

        # self.button_home.setIcon(GuiUtils.get_icon('home.svg'))
        # self.button_home.setToolTip('Home')

        label = QLabel()
        default_font = label.font()

        self.context_widget = ContextWidget(self)
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.context_widget)
        self.context_frame.setLayout(hl)

        self.button_starred.setIcon(GuiUtils.get_icon('star_filled.svg'))
        self.button_starred.setToolTip('Starred')
        self.button_starred.setCheckable(True)

        self.button_browse.setText('Browse')
        self.button_browse.setToolTip('Browse')
        self.button_browse.setCheckable(True)
        self.button_browse.setChecked(True)
        self.button_browse.setFont(default_font)

        self.button_help.setIcon(GuiUtils.get_icon('help.svg'))
        self.button_help.setToolTip('Help')
        self.button_help.clicked.connect(self._show_help)

        self.button_user.setIcon(GuiUtils.get_icon('user.svg'))
        self.button_user.setToolTip('User')

        # a QToolButton with an icon will appear smaller by default vs one with text, so
        # force the advanced button to match the Clear All button size
        temp_combo = QComboBox()
        for b in (self.button_starred,
                  self.button_help,
                  # self.button_home,
                  self.button_user):
            b.setFixedHeight(temp_combo.sizeHint().height())
            b.setFixedWidth(b.height())

        self.button_browse.setFixedHeight(temp_combo.sizeHint().height())

        self.browser = DatasetsBrowserWidget()
        self.browser.visible_count_changed.connect(self._visible_count_changed)
        self.browser.total_count_changed.connect(self._total_count_changed)
        self.oauth: Optional[OAuthWorkflow] = None

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)
        self.browserFrame.setLayout(layout)

        pixmap = QPixmap(os.path.join(pluginPath, "img", "koordinates.png"))
        self.labelHeader.setPixmap(pixmap)

        self.btnLogin.clicked.connect(self.loginClicked)

        self.filter_widget = FilterWidget(self)
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(self.filter_widget)
        self.filter_frame.setLayout(filter_layout)

        self.filter_widget.filters_changed.connect(self.search)

        self.button_starred.toggled.connect(self._set_starred)
        self.button_browse.clicked.connect(self._browse)
        self.filter_widget.clear_all.connect(self._clear_all_filters)

        self.sort_menu = QMenu(self.button_sort_order)
        for order in (
                SortOrder.Popularity,
                SortOrder.RecentlyAdded,
                SortOrder.RecentlyUpdated,
                SortOrder.AlphabeticalAZ,
                SortOrder.AlphabeticalZA,
                SortOrder.Oldest):
            action = QAction(SortOrder.to_text(order), self.sort_menu)
            action.setData(order)
            action.triggered.connect(partial(self._set_sort_order, order))
            self.sort_menu.addAction(action)

        self.button_sort_order.setMenu(self.sort_menu)
        smaller_font = self.button_sort_order.font()
        smaller_font.setPointSize(smaller_font.pointSize() - 1)
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

        self.context_widget.context_changed.connect(self._context_changed)

        KoordinatesClient.instance().loginChanged.connect(self._loginChanged)
        KoordinatesClient.instance().error_occurred.connect(self._client_error_occurred)

        self.setForLogin(False)

    def cancel_active_requests(self):
        """
        Cancels any active request
        """
        if self._current_facets_reply is not None and \
                not sip.isdeleted(self._current_facets_reply):
            self._current_facets_reply.abort()

        self._current_facets_reply = None

        self.browser.cancel_active_requests()

    def _clear_all_filters(self):
        """
        Called when the filter widget Clear All action is triggered
        """
        self.button_starred.setChecked(False)
        self.filter_widget.sort_order = SortOrder.Popularity
        self._set_sort_order_button_text()

    def _sort_order_menu_about_to_show(self):
        """
        Called when the sort order menu is about to show
        """
        for action in self.sort_menu.actions():
            is_checked = action.data() == self.filter_widget.sort_order
            action.setCheckable(is_checked)
            if is_checked:
                action.setChecked(True)

    def _set_sort_order(self, order: SortOrder):
        """
        Triggered when the sort order is changed
        """
        if self.filter_widget.sort_order == order:
            return

        self.filter_widget.sort_order = order
        self._set_sort_order_button_text()
        self.search()

    def _set_sort_order_button_text(self):
        """
        Sets the correct text for the sort order button
        """
        self.button_sort_order.setText(
            'Sort by {}'.format(SortOrder.to_text(self.filter_widget.sort_order))
        )

    def _set_starred(self, starred: bool):
        """
        Called when the starred button is checked
        """
        if starred:
            self.button_browse.setChecked(False)
        else:
            self.button_browse.setChecked(True)
        self.filter_widget.set_starred(starred)

    def _browse(self):
        """
        Switches back to browse mode
        """
        self.button_starred.setChecked(False)
        self.button_browse.setChecked(True)

    def _user_menu_about_to_show(self):
        """
        Called when the user menu is about to show
        """
        user = KoordinatesClient.instance().user_details()
        self.current_user_action.setText(
            '{} {}'.format(user.get('first_name'), user.get('last_name')).strip()
        )

    def backToBrowser(self):
        self.stackedWidget.setCurrentWidget(self.pageBrowser)

    def search(self):
        browser_query = self.filter_widget.build_query()

        context = self.context_widget.current_context()

        self._fetch_facets(browser_query, context)
        self.browser.populate(browser_query, context)

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

        self._facets = json.loads(reply.readAll().data().decode())
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

    def _context_changed(self, context: Dict):
        self.filter_widget.update()
        self.update()
        self.search()

    def _loginChanged(self, loggedIn):
        if not loggedIn:
            self.removeApiKey()
        self.setForLogin(loggedIn)

    def setForLogin(self, loggedIn):
        if loggedIn:
            self.stackedWidget.setCurrentWidget(self.pageBrowser)

            user = KoordinatesClient.instance().user_details()
            self.user_country_action.set_country_code(user['country'])

            self.context_widget.set_contexts(user.get('contexts', []))
            self.context_widget.setVisible(self.context_widget.count() > 1)

            self.filter_widget.set_logged_in(True)

            self.search()
        else:
            self.labelWaiting.setVisible(False)
            self.btnLogin.setEnabled(True)
            self.stackedWidget.setCurrentWidget(self.pageAuth)

    def loginClicked(self):
        key = self.retrieve_api_key()
        if key is not None:
            self._authFinished(key)
        else:
            self.labelWaiting.setText("Waiting for OAuth authentication response...")
            self.labelWaiting.setVisible(True)
            self.btnLogin.setEnabled(False)
            QApplication.processEvents()
            self.oauth = OAuthWorkflow()

            self.objThread = QThread()
            self.oauth.moveToThread(self.objThread)
            self.oauth.finished.connect(self._authFinished)
            self.oauth.error_occurred.connect(self._auth_error_occurred)
            self.oauth.finished.connect(self.objThread.quit)
            self.objThread.started.connect(self.oauth.doAuth)
            self.objThread.start()

    def _authFinished(self, apiKey):
        if not apiKey:
            return

        self.labelWaiting.setText("Logging in and retrieving datasets...")
        self.labelWaiting.setVisible(True)
        self.btnLogin.setEnabled(False)
        QApplication.processEvents()
        try:
            KoordinatesClient.instance().login(apiKey)
            self.store_api_key()
            self.labelWaiting.setVisible(False)
            self.btnLogin.setEnabled(True)
        except FileExistsError:
            iface.messageBar().pushMessage(
                "Could not log in. Check your connection and your API Key value",
                Qgis.Warning,
                duration=5,
            )
            self.labelWaiting.setVisible(False)
            self.btnLogin.setEnabled(True)

    def _auth_error_occurred(self, error: str):
        self.labelWaiting.setVisible(False)
        self.btnLogin.setEnabled(True)
        iface.messageBar().pushMessage(
            "Authorization failed: {}".format(error),
            Qgis.Warning,
            duration=5,
        )

    def _client_error_occurred(self, error: str):
        self.labelWaiting.setVisible(False)
        self.btnLogin.setEnabled(True)
        iface.messageBar().pushMessage(
            "Request failed: {}".format(error),
            Qgis.Warning,
            duration=5,
        )

    def logout(self):
        """
        Logs the user out
        """
        KoordinatesClient.instance().logout()

    def store_api_key(self) -> bool:
        """
        Stores the API key in the secure QGIS password store, IF available

        Returns True if the key could be stored
        """
        if not QgsApplication.authManager().masterPasswordHashInDatabase():
            return False

        key = KoordinatesClient.instance().apiKey
        QgsApplication.authManager().storeAuthSetting(AUTH_CONFIG_ID, key, True)

    def retrieve_api_key(self) -> Optional[str]:
        """
        Retrieves a previously stored API key, if available

        Returns None if no stored key is available
        """
        if not QgsApplication.authManager().masterPasswordHashInDatabase():
            return None

        api_key = (
                QgsApplication.authManager().authSetting(
                    AUTH_CONFIG_ID, defaultValue="", decrypt=True
                )
                or None
        )
        return api_key

    def removeApiKey(self):
        QgsApplication.authManager().removeAuthSetting(AUTH_CONFIG_ID)

    def _edit_profile(self):
        """
        Opens the edit profile page
        """
        QDesktopServices.openUrl(QUrl('https://id.koordinates.com/profile/'))

    def _show_help(self):
        """
        Shows the help web page
        """
        QDesktopServices.openUrl(QUrl('https://help.koordinates.com/'))
