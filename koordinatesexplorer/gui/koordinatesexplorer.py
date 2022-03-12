import os

from qgis.core import (
    QgsApplication,
    Qgis,
)
from qgis.utils import iface

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings, Qt, QDate, QDateTime
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout
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

        self.btnLogin.clicked.connect(self.loginClicked)
        self.btnLogout.clicked.connect(self.logoutClicked)
        self.chkSaveApiKey.stateChanged.connect(self.saveApiKeyChanged)

        self.groupBox.collapsedStateChanged.connect(self.groupCollapseStateChanged)

        self.btnSearch.clicked.connect(self.search)
        self.comboDatatype.currentIndexChanged.connect(self.datatypeChanged)
        self.comboCategory.currentIndexChanged.connect(self.categoryChanged)

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
        self.radioNoAerial.toggle.connect(self.filtersChanged)
        self.chkOnlyAlpha.stateChanged.connect(self.filtersChanged)

        self.saveApiKey = bool(
            QSettings().value(f"{SETTINGS_NAMESPACE}/{SAVE_API_KEY}")
        )

        self.setApiKeyField()

        KoordinatesClient.instance().loginChanged.connect(self.setForLogin)

        self.setForLogin(KoordinatesClient.instance().isLoggedIn())

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

        self.browser.populate(params)

    def groupCollapseStateChanged(self):
        self.datatypeChanged()
        self.categoryChanged()

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

    def setForLogin(self, loggedIn):
        if loggedIn:
            self.stackedWidget.setCurrentWidget(self.pageBrowser)
            email = KoordinatesClient.instance().userEMail()
            self.labelLoggedAs.setText(f"Logged as <b>{email}</b>")
            if self.comboCategory.count() == 0:
                self.comboCategory.addItem("All")
                for c in KoordinatesClient.instance().categories():
                    self.comboCategory.addItem(c["name"], c["key"])
            self.setDefaultParameters()
            self.search()
            """
            QgsProject.instance().layerWillBeRemoved.connect(self.layerRemoved)
            QgsProject.instance().layerWasAdded.connect(self.layerAdded)
            """
        else:
            self.stackedWidget.setCurrentWidget(self.pageAuth)
            try:
                """
                QgsProject.instance().layerWillBeRemoved.disconnect(self.layerRemoved)
                QgsProject.instance().layerWasAdded.disconnect(self.layerAdded)
                """
            except Exception:  # signal might not be connected
                pass

    def loginClicked(self):
        apiKey = self.txtApiKey.text()
        if apiKey:
            try:
                KoordinatesClient.instance().login(apiKey)
            except (LoginException, ValueError):
                raise
                iface.messageBar().pushMessage(
                    "Invalid API Key", Qgis.Warning, duration=5
                )
                return
            except Exception:
                iface.messageBar().pushMessage(
                    "Could not log in. Check your connection and your API Key value",
                    Qgis.Warning,
                    duration=5,
                )
                return

            if self.saveApiKey:
                self.storeApiKey()
        else:
            print(1)
            iface.messageBar().pushMessage("Invalid API Key", Qgis.Warning, duration=5)

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
