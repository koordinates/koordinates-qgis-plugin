import os

from qgis.core import (
    QgsApplication,
    Qgis,
)
from qgis.gui import QgsMessageBar
from qgis.utils import iface

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings, QUrl
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout, QSizePolicy
from qgis.PyQt.QtGui import QPixmap

from koordinatesexplorer.client import KoordinatesClient, LoginException
from koordinatesexplorer.gui.datasetsbrowserwidget import DatasetsBrowserWidget


pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, BASE = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "koordinatesexplorer.ui")
)

SETTINGS_NAMESPACE = "Koordinates"
SAVE_API_KEY = "SaveApiKey"

AUTH_CONFIG_ID = "koordinates_auth_id"


class KoordinatesExplorer(BASE, WIDGET):
    def __init__(self):
        super(QDockWidget, self).__init__(iface.mainWindow())
        self.setupUi(self)
        self.browser = DatasetsBrowserWidget()
        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.browser)
        self.browserFrame.setLayout(layout)

        pixmap = QPixmap(os.path.join(pluginPath, "img", "koordinates.png"))
        self.labelHeader.setPixmap(pixmap)

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().addWidget(self.bar)

        self.btnLogin.clicked.connect(self.loginClicked)
        self.btnLogout.clicked.connect(self.logoutClicked)
        self.chkSaveApiKey.stateChanged.connect(self.saveApiKeyChanged)

        self.saveApiKey = bool(
            QSettings().value(f"{SETTINGS_NAMESPACE}/{SAVE_API_KEY}")
        )

        self.setApiKeyField()

        KoordinatesClient.instance().loginChanged.connect(self.setForLogin)

        self.setForLogin(KoordinatesClient.instance().isLoggedIn())

    def backToBrowser(self):
        self.stackedWidget.setCurrentWidget(self.pageBrowser)

    def setForLogin(self, loggedIn):
        if loggedIn:
            self.stackedWidget.setCurrentWidget(self.pageBrowser)
            email = KoordinatesClient.instance().userEMail()
            self.labelLoggedAs.setText(f"Logged as <b>{email}</b>")
            self.browser.populate()
            '''
            QgsProject.instance().layerWillBeRemoved.connect(self.layerRemoved)
            QgsProject.instance().layerWasAdded.connect(self.layerAdded)
            '''
        else:
            self.stackedWidget.setCurrentWidget(self.pageAuth)
            try:
                '''
                QgsProject.instance().layerWillBeRemoved.disconnect(self.layerRemoved)
                QgsProject.instance().layerWasAdded.disconnect(self.layerAdded)
                '''
            except Exception:  # signal might not be connected
                pass

    def loginClicked(self):
        apiKey = self.txtApiKey.text()
        if apiKey:
            try:
                KoordinatesClient.instance().login(apiKey)
            except (LoginException, ValueError):
                self.bar.pushMessage("Invalid API Key", Qgis.Warning, duration=5)
                return
            except Exception:
                self.bar.pushMessage(
                    "Could not log in. Check your connection and your API Key value",
                    Qgis.Warning,
                    duration=5,
                )
                return

            if self.saveApiKey:
                self.storeApiKey()
        else:
            self.bar.pushMessage("Invalid API Key", Qgis.Warning, duration=5)

    def logoutClicked(self):
        KoordinatesClient.instance().logout()

    def saveApiKeyChanged(self, state):
        if state == 0:
            self.removeApiKey()
        self.saveApiKey = state > 0
        QSettings().setValue(f"{SETTINGS_NAMESPACE}/{SAVE_API_KEY}", self.saveApiKey)

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

    def setApiKeyField(self):
        self.txtApiKey.setPasswordVisibility(False)
        if not self.saveApiKey:
            self.txtApiKey.setText("")
            self.chkSaveApiKey.setChecked(False)
        else:
            self.chkSaveApiKey.setChecked(True)
            apiKey = self.retrieveApiKey()
            self.txtApiKey.setText(apiKey)

    def removeApiKey(self):
        QgsApplication.authManager().removeAuthSetting(AUTH_CONFIG_ID)
