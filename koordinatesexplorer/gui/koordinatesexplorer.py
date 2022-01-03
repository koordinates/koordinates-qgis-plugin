import os

from qgis.core import (
    QgsApplication,
    Qgis,
    QgsProject,
    QgsWkbTypes,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsGeometry,
    QgsRectangle
)
from qgis.gui import QgsMessageBar, QgsRubberBand
from qgis.utils import iface

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QObject, QSettings, QUrl, pyqtSlot, Qt
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout, QSizePolicy
from qgis.PyQt.QtWebKitWidgets import QWebView, QWebInspector
from qgis.PyQt.QtWebKit import QWebSettings
from qgis.PyQt.QtGui import QPixmap, QColor

from koordinatesexplorer.client import KoordinatesClient, LoginException
from koordinatesexplorer.utils import cloneKartRepo, KartNotInstalledException

pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, BASE = uic.loadUiType(os.path.join(os.path.dirname(__file__), "koordinatesexplorer.ui"))

URL = QUrl(f"file:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')}")
#URL = QUrl("https://koordinates.com/uivx")

SETTINGS_NAMESPACE = "Koordinates"
SAVE_API_KEY = "SaveApiKey"

AUTH_CONFIG_ID = "koordinates_auth_id"


class KoordinatesExplorer(BASE, WIDGET):
    def __init__(self):
        super(QDockWidget, self).__init__(iface.mainWindow())
        self.setupUi(self)
        self.webView = QWebView()
        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.webView)
        self.pageBrowser.setLayout(layout)
        self.webView.page().mainFrame().javaScriptWindowObjectCleared.connect(self._addToJavaScript)
        self.webView.page().settings().setAttribute(QWebSettings.JavascriptEnabled, True)

        pixmap = QPixmap(os.path.join(pluginPath, "img", "koordinates.png"))
        self.labelHeader.setPixmap(pixmap)

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().addWidget(self.bar)

        self.btnLogin.clicked.connect(self.loginClicked)
        self.chkSaveApiKey.stateChanged.connect(self.saveApiKeyChanged)

        self.saveApiKey = bool(
            QSettings().value(f"{SETTINGS_NAMESPACE}/{SAVE_API_KEY}")
        )

        self.setApiKeyField()

        KoordinatesClient.instance().loginChanged.connect(self.setForLogin)

        self.setForLogin(KoordinatesClient.instance().isLoggedIn())

    def layerAdded(self, layer):
        js = f'setLayerIsInProject("{layer.name()}", true)'
        self.webView.page().mainFrame().evaluateJavaScript(js)

    def layerRemoved(self, layerid):
        layer = QgsProject.instance().mapLayers()[layerid]
        self.webView.page().mainFrame().evaluateJavaScript(f'setLayerIsInProject("{layer.name()}", false)')

    def setForLogin(self, loggedIn):
        if loggedIn:
            self.jsObject = JSObject(self)
            #self.webView.page().settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
            self.webView.load(URL)
            #inspector = QWebInspector(self.webView)
            #inspector.setPage(self.webView.page())
            self.stackedWidget.setCurrentWidget(self.pageBrowser)
            QgsProject.instance().layerWillBeRemoved.connect(self.layerRemoved)
            QgsProject.instance().layerWasAdded.connect(self.layerAdded)
        else:
            self.stackedWidget.setCurrentWidget(self.pageAuth)
            try:
                QgsProject.instance().layerWillBeRemoved.disconnect(self.layerRemoved)
                QgsProject.instance().layerWasAdded.disconnect(self.layerAdded)
                self.jsObject.hideBoundingBox()
            except Exception:  # signal might not be connected
                pass

    def _addToJavaScript(self):
        self.webView.page().mainFrame().addToJavaScriptWindowObject("qgisPlugin", self.jsObject)

    def loginClicked(self):
        apiKey = self.txtApiKey.text()
        if apiKey:
            try:
                KoordinatesClient.instance().login(apiKey)
            except (LoginException, ValueError):
                self.bar.pushMessage("Invalid API Key", Qgis.Warning, duration=5)
                return
            except Exception:
                self.bar.pushMessage("Could not log in. Check your connection and your API Key value", Qgis.Warning, duration=5)
                return

            if self.saveApiKey:
                self.storeApiKey()
        else:
            self.bar.pushMessage("Invalid API Key", Qgis.Warning, duration=5)

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
            QgsApplication.authManager().authSetting(AUTH_CONFIG_ID, defaultValue="", decrypt=True)
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


class JSObject(QObject):

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.aoi = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.aoi.setFillColor(QColor(0, 0, 0, 0))
        self.aoi.setStrokeColor(QColor(255, 0, 0))
        self.aoi.setWidth(2)
        self.aoi.setLineStyle(Qt.DashLine)

    @pyqtSlot(str)
    def clone(self, url):
        try:
            if cloneKartRepo(url, self.parent()):
                self.parent().bar.pushMessage("Repository correctly cloned", Qgis.Information, duration=5)
        except KartNotInstalledException:
            self.parent().bar.pushMessage("Kart plugin must be installed to clone repositories", Qgis.Warning, duration=5)

    @pyqtSlot(str)
    def addWms(self, url):
        print(url)
        pass

    @pyqtSlot(str)
    def addWfs(self, url):
        print(url)
        pass

    @pyqtSlot()
    def logout(self):
        KoordinatesClient.instance().logout()

    def _geom_in_project_crs(self, coords):
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:4326"),
            QgsProject.instance().crs(),
            QgsProject.instance(),
        )
        rect = QgsRectangle(*coords)
        geom = QgsGeometry.fromRect(rect)
        geom.transform(transform)
        return geom

    @pyqtSlot(list)
    def showBoundingBox(self, coords):
        geom = self._geom_in_project_crs(coords)
        self.aoi.setToGeometry(geom)
        for layer in QgsProject.instance().mapLayers().values():
            print(layer.name())
            self.parent().layerAdded(layer)

    @pyqtSlot()
    def hideBoundingBox(self):
        self.aoi.reset(QgsWkbTypes.PolygonGeometry)
