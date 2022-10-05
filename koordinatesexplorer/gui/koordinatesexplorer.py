import json
import os
from functools import partial
from typing import Optional

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
    QMenu
)
from qgis.core import (
    QgsApplication,
    Qgis,
)
from qgis.gui import QgsDockWidget
from qgis.utils import iface

from koordinatesexplorer.auth import OAuthWorkflow
from koordinatesexplorer.gui.datasetsbrowserwidget import DatasetsBrowserWidget
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
        super(QgsDockWidget, self).__init__(iface.mainWindow())
        self.setupUi(self)

        self._facets = {}
        self._current_facets_reply = None
        self._visible_count = 0
        self._total_count = 0

        # self.button_home.setIcon(GuiUtils.get_icon('home.svg'))
        # self.button_home.setToolTip('Home')

        self.button_starred.setIcon(GuiUtils.get_icon('star_filled.svg'))
        self.button_starred.setToolTip('Starred')
        self.button_starred.setCheckable(True)

        self.button_browse.setText('Browse')
        self.button_browse.setToolTip('Browse')
        self.button_browse.setCheckable(True)
        self.button_browse.setChecked(True)

        self.button_help.setIcon(GuiUtils.get_icon('help.svg'))
        self.button_help.setToolTip('Help')
        self.button_help.clicked.connect(self._show_help)

        self.button_user.setIcon(GuiUtils.get_icon('user.svg'))
        self.button_user.setToolTip('User')

        # a QToolButton with an icon will appear smaller by default vs one with text, so
        # force the advanced button to match the Clear All button size
        for b in (self.button_starred,
                  self.button_help,
                  # self.button_home,
                  self.button_user):
            b.setFixedHeight(self.comboContext.sizeHint().height())
            b.setFixedWidth(b.height())

        self.button_browse.setFixedHeight(self.comboContext.sizeHint().height())

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
        smaller_font.setPointSize(smaller_font.pointSize() - 2)
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

        #  self.comboContext.currentIndexChanged.connect(self.filtersChanged)

        KoordinatesClient.instance().loginChanged.connect(self._loginChanged)
        KoordinatesClient.instance().error_occurred.connect(self._client_error_occurred)

        self.setForLogin(False)

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

        context = self.comboContext.currentData()

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
        if reply != self._current_facets_reply or \
                reply.error() == QNetworkReply.OperationCanceledError:
            # an old reply we don't care about anymore
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
        if not self._total_count or not self._visible_count:
            self.label_count.clear()
        else:
            self.label_count.setText('Showing {} of {} results'.format(self._visible_count, self._total_count))

    def _loginChanged(self, loggedIn):
        if not loggedIn:
            self.removeApiKey()
        self.setForLogin(loggedIn)

    def setForLogin(self, loggedIn):
        if loggedIn:
            self.stackedWidget.setCurrentWidget(self.pageBrowser)

            user = KoordinatesClient.instance().user_details()
            self.user_country_action.set_country_code(user['country'])

            contexts = KoordinatesClient.instance().userContexts()
            self.comboContext.clear()
            self.comboContext.addItem("All", {"type": "site", "domain": "all"})
            for context in contexts:
                self.comboContext.addItem(context.get("name", "user"), context)
            self.comboContext.setVisible(self.comboContext.count() > 1)

            self.filter_widget.set_logged_in(True)

            self.search()
        else:
            self.labelWaiting.setVisible(False)
            self.stackedWidget.setCurrentWidget(self.pageAuth)

    def loginClicked(self):
        key = self.retrieveApiKey()
        if key:
            self._authFinished(key)
        else:
            self.labelWaiting.setText("Waiting for OAuth authentication response...")
            self.labelWaiting.setVisible(True)
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
        QApplication.processEvents()
        try:
            KoordinatesClient.instance().login(apiKey)
            self.storeApiKey()
            self.labelWaiting.setVisible(False)
        except FileExistsError:
            iface.messageBar().pushMessage(
                "Could not log in. Check your connection and your API Key value",
                Qgis.Warning,
                duration=5,
            )
            self.labelWaiting.setVisible(False)

    def _auth_error_occurred(self, error: str):
        self.labelWaiting.setVisible(False)
        iface.messageBar().pushMessage(
            "Authorization failed: {}".format(error),
            Qgis.Warning,
            duration=5,
        )

    def _client_error_occurred(self, error: str):
        self.labelWaiting.setVisible(False)
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

    def storeApiKey(self):
        key = KoordinatesClient.instance().apiKey
        QgsApplication.authManager().storeAuthSetting(AUTH_CONFIG_ID, key, True)

    def retrieveApiKey(self):
        apiKey = (
                QgsApplication.authManager().authSetting(
                    AUTH_CONFIG_ID, defaultValue="", decrypt=True
                )
                or ""
        )
        return apiKey

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
