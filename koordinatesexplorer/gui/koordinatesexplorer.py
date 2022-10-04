import os
from typing import Optional

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QThread
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import QVBoxLayout, QApplication
from qgis.core import (
    QgsApplication,
    Qgis,
)
from qgis.gui import QgsDockWidget
from qgis.utils import iface

from koordinatesexplorer.auth import OAuthWorkflow
from koordinatesexplorer.gui.datasetsbrowserwidget import DatasetsBrowserWidget
from .filter_widget import FilterWidget
from .gui_utils import GuiUtils
from ..api import (
    KoordinatesClient
)

pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('koordinatesexplorer.ui'))

SETTINGS_NAMESPACE = "Koordinates"
AUTH_CONFIG_ID = "koordinates_auth_id"


class KoordinatesExplorer(QgsDockWidget, WIDGET):
    def __init__(self):
        super(QgsDockWidget, self).__init__(iface.mainWindow())
        self.setupUi(self)

        self.button_home.setIcon(GuiUtils.get_icon('home.svg'))
        self.button_home.setToolTip('Home')

        self.button_starred.setIcon(GuiUtils.get_icon('star_filled.svg'))
        self.button_starred.setToolTip('Starred')

        self.button_browse.setText('Browse')
        self.button_browse.setToolTip('Browse')

        self.button_help.setIcon(GuiUtils.get_icon('help.svg'))
        self.button_help.setToolTip('Help')

        self.button_user.setIcon(GuiUtils.get_icon('user.svg'))
        self.button_user.setToolTip('User')

        # a QToolButton with an icon will appear smaller by default vs one with text, so
        # force the advanced button to match the Clear All button size
        for b in (self.button_home,
                  self.button_starred,
                  self.button_help,
                  self.button_user):
            b.setFixedHeight(self.comboContext.sizeHint().height())
            b.setFixedWidth(self.button_home.height())

        self.button_browse.setFixedHeight(self.comboContext.sizeHint().height())

        self.button_starred.setCheckable(True)

        self.browser = DatasetsBrowserWidget()
        self.oauth: Optional[OAuthWorkflow] = None

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)
        self.browserFrame.setLayout(layout)

        pixmap = QPixmap(os.path.join(pluginPath, "img", "koordinates.png"))
        self.labelHeader.setPixmap(pixmap)

        self.btnLogin.clicked.connect(self.loginClicked)
        self.btnLogout.clicked.connect(self.logoutClicked)

        self.filter_widget = FilterWidget(self)
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(self.filter_widget)
        self.filter_frame.setLayout(filter_layout)

        self.filter_widget.filters_changed.connect(self.search)

        self.button_starred.toggled.connect(self.filter_widget.set_starred)
        self.filter_widget.clear_all.connect(self._clear_all_filters)

        #  self.comboContext.currentIndexChanged.connect(self.filtersChanged)

        KoordinatesClient.instance().loginChanged.connect(self._loginChanged)
        KoordinatesClient.instance().error_occurred.connect(self._client_error_occurred)

        self.setForLogin(False)

    def _clear_all_filters(self):
        """
        Called when the filter widget Clear All action is triggered
        """
        self.button_starred.setChecked(False)

    def backToBrowser(self):
        self.stackedWidget.setCurrentWidget(self.pageBrowser)

    def search(self):
        browser_query = self.filter_widget.build_query()

        context = self.comboContext.currentData()

        self.browser.populate(browser_query, context)

    def _loginChanged(self, loggedIn):
        if not loggedIn:
            self.removeApiKey()
        self.setForLogin(loggedIn)

    def setForLogin(self, loggedIn):
        if loggedIn:
            self.stackedWidget.setCurrentWidget(self.pageBrowser)
            email = KoordinatesClient.instance().userEMail()
            self.labelLoggedAs.setText(f"Logged as <b>{email}</b>")

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

    def logoutClicked(self):
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
