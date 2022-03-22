import os

from qgis.core import (
    QgsApplication,
    Qgis,
)
from qgis.utils import iface

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QDate, QDateTime, QThread
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout, QApplication
from qgis.PyQt.QtGui import QPixmap

from koordinatesexplorer.client import KoordinatesClient
from koordinatesexplorer.gui.datasetsbrowserwidget import DatasetsBrowserWidget
from koordinatesexplorer.auth import OAuthWorkflow


pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, BASE = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "koordinatesexplorer.ui")
)

SETTINGS_NAMESPACE = "Koordinates"
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

        self.btnLogin.clicked.connect(self.loginClicked)
        self.btnLogout.clicked.connect(self.logoutClicked)

        self.groupBox.collapsedStateChanged.connect(self.groupCollapseStateChanged)

        self.btnSearch.clicked.connect(self.search)
        self.comboDatatype.currentIndexChanged.connect(self.datatypeChanged)
        self.comboCategory.currentIndexChanged.connect(self.categoryChanged)

        self.comboContext.currentIndexChanged.connect(self.filtersChanged)
        self.dateCreatedBefore.dateChanged.connect(self.filtersChanged)
        self.dateUpdatedBefore.dateChanged.connect(self.filtersChanged)
        self.dateCreatedAfter.dateChanged.connect(self.filtersChanged)
        self.dateUpdatedAfter.dateChanged.connect(self.filtersChanged)
        self.chkPoints.stateChanged.connect(self.filtersChanged)
        self.chkLines.stateChanged.connect(self.filtersChanged)
        self.chkPolygons.stateChanged.connect(self.filtersChanged)
        self.chkHasZ.stateChanged.connect(self.filtersChanged)
        self.chkHasDataRepository.stateChanged.connect(self.filtersChanged)
        self.chkHasPrimaryKey.stateChanged.connect(self.filtersChanged)
        self.chkIncludeRepos.stateChanged.connect(self.filtersChanged)
        self.comboDatatype.currentIndexChanged.connect(self.filtersChanged)
        self.comboCategory.currentIndexChanged.connect(self.filtersChanged)
        self.txtSearch.textChanged.connect(self.filtersChanged)
        self.radioRGB.toggled.connect(self.filtersChanged)
        self.radioGrayscale.toggled.connect(self.filtersChanged)
        self.radioAerial.toggled.connect(self.filtersChanged)
        self.radioNoAerial.toggled.connect(self.filtersChanged)
        self.chkOnlyAlpha.stateChanged.connect(self.filtersChanged)

        KoordinatesClient.instance().loginChanged.connect(self._loginChanged)

        self.setForLogin(False)

    def backToBrowser(self):
        self.stackedWidget.setCurrentWidget(self.pageBrowser)

    def filtersChanged(self):
        self.btnSearch.setEnabled(True)

    def search(self):
        params = {}
        datatypeName = self.comboDatatype.currentText()
        datatype = {"Data Repository": "repo"}.get(datatypeName, datatypeName.lower())
        if datatype != "all":
            params["kind"] = datatype
        if datatype == "vector":
            geomtype = []
            if self.chkPoints.isChecked():
                geomtype.append("point")
            if self.chkLines.isChecked():
                geomtype.append("linestring")
            if self.chkPolygons.isChecked():
                geomtype.append("polygon")
            geomtype = geomtype or ["point", "linestring", "polygon"]
            params["data.geometry_type"] = geomtype
            if self.chkHasZ.isChecked():
                params["has_z"] = True
            if self.chkHasPrimaryKey.isChecked():
                params["has_pk"] = True
            if self.chkHasDataRepository.isChecked():
                params["has_repo"] = True
        if datatype == "raster":
            bands = []
            if self.radioRGB.isChecked():
                bands.extend(["red", "green", "blue"])
            if self.radioGrayscale.isChecked():
                bands.append("gray")
            if self.chkOnlyAlpha.isChecked():
                bands.append("alpha")
            if bands:
                params["raster_band"] = bands
            if self.radioAerial.isChecked():
                params["is_imagery"] = True
            if self.radioNoAerial.isChecked():
                params["is_imagery"] = False
        if datatype == "repo":
            if self.chkIncludeRepos.isChecked():
                params["kind"] = ["vector", "repo", "table"]
                params["has_repo"] = True
        category = self.comboCategory.currentData()
        if category is not None:
            if self.comboSubcategory.isVisible():
                params["category"] = self.comboSubcategory.currentData()
            else:
                params["category"] = category

        params["created_at.before"] = QDateTime(self.dateCreatedBefore.date()).toString(
            Qt.ISODate
        )
        params["created_at.after"] = QDateTime(self.dateCreatedAfter.date()).toString(
            Qt.ISODate
        )
        params["updated_at.before"] = QDateTime(self.dateUpdatedBefore.date()).toString(
            Qt.ISODate
        )
        params["updated_at.after"] = QDateTime(self.dateUpdatedAfter.date()).toString(
            Qt.ISODate
        )

        text = self.txtSearch.text().strip("")
        if text:
            params["q"] = text

        self.btnSearch.setEnabled(False)

        context = self.comboContext.currentData()

        self.browser.populate(params, context)

    def groupCollapseStateChanged(self):
        self.datatypeChanged()
        self.categoryChanged()
        self.comboContext.setVisible(self.comboContext.count() > 1)
        self.labelContext.setVisible(self.comboContext.count() > 1)

    def setDefaultParameters(self):
        self.groupBox.setCollapsed(True)
        self.stackedWidgetDatatype.setVisible(False)
        self.dateCreatedBefore.setDate(QDate.currentDate())
        self.dateUpdatedBefore.setDate(QDate.currentDate())
        self.chkPoints.setChecked(True)
        self.chkLines.setChecked(True)
        self.chkPolygons.setChecked(True)
        self.chkHasZ.setChecked(False)
        self.chkHasDataRepository.setChecked(False)
        self.chkHasPrimaryKey.setChecked(False)
        self.chkIncludeRepos.setChecked(True)

    def categoryChanged(self):
        category = self.comboCategory.currentText()
        if category == "All":
            self.comboSubcategory.setVisible(False)
            self.labelSubcategory.setVisible(False)
            return
        categories = {c["name"]: c for c in KoordinatesClient.instance().categories()}
        children = categories.get(category, {}).get("children", [])
        if children:
            self.comboSubcategory.setVisible(True)
            self.labelSubcategory.setVisible(True)
            self.comboSubcategory.clear()
            for c in children:
                self.comboSubcategory.addItem(c["name"], c["key"])
        else:
            self.comboSubcategory.setVisible(False)
            self.labelSubcategory.setVisible(False)

    def datatypeChanged(self):
        datatype = self.comboDatatype.currentText()
        self.stackedWidgetDatatype.setVisible(
            datatype in ["Vector", "Raster", "Data Repository"]
        )
        if datatype == "Vector":
            self.stackedWidgetDatatype.setCurrentWidget(self.pageVector)
        if datatype == "Raster":
            self.stackedWidgetDatatype.setCurrentWidget(self.pageRaster)
        if datatype == "Data Repository":
            self.stackedWidgetDatatype.setCurrentWidget(self.pageRepos)

    def _loginChanged(self, loggedIn):
        if not loggedIn:
            self.removeApiKey()
        self.setForLogin(loggedIn)

    def setForLogin(self, loggedIn):
        if loggedIn:
            self.stackedWidget.setCurrentWidget(self.pageBrowser)
            email = KoordinatesClient.instance().userEMail()
            self.labelLoggedAs.setText(f"Logged as <b>{email}</b>")
            if self.comboCategory.count() == 0:
                self.comboCategory.addItem("All")
                for c in KoordinatesClient.instance().categories():
                    self.comboCategory.addItem(c["name"], c["key"])
            contexts = KoordinatesClient.instance().userContexts()
            self.comboContext.clear()
            self.comboContext.addItem("All", {"type": "site", "domain": "all"})
            for context in contexts:
                self.comboContext.addItem(context.get("name", "user"), context)
            self.comboContext.setVisible(self.comboContext.count() > 1)
            self.labelContext.setVisible(self.comboContext.count() > 1)
            self.setDefaultParameters()
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
            self.oauth.finished.connect(self.objThread.quit)
            self.objThread.started.connect(self.oauth.doAuth)
            self.objThread.start()

    def _authFinished(self, apiKey):
        if apiKey:
            self.labelWaiting.setText("Logging in and retrieving datasets...")
            self.labelWaiting.setVisible(True)
            QApplication.processEvents()
            try:
                KoordinatesClient.instance().login(apiKey)
                self.storeApiKey()
                self.labelWaiting.setVisible(False)
            except Exception:
                iface.messageBar().pushMessage(
                    "Could not log in. Check your connection and your API Key value",
                    Qgis.Warning,
                    duration=5,
                )
                self.labelWaiting.setVisible(False)
        else:
            self.labelWaiting.setVisible(False)
            iface.messageBar().pushMessage(
                "Authorization worflow failed or was canceled",
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
