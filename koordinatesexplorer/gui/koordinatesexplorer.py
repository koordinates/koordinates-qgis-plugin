import os
from typing import Optional

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QDate, QDateTime, QThread
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
from ..api import (
    KoordinatesClient,
    DataBrowserQuery,
    DataType,
    VectorFilter,
    RasterFilter,
    RasterFilterOptions,
    RasterBandFilter
)

from .gui_utils import GuiUtils

pluginPath = os.path.split(os.path.dirname(__file__))[0]

WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('koordinatesexplorer.ui'))

SETTINGS_NAMESPACE = "Koordinates"
AUTH_CONFIG_ID = "koordinates_auth_id"


class KoordinatesExplorer(QgsDockWidget, WIDGET):
    def __init__(self):
        super(QgsDockWidget, self).__init__(iface.mainWindow())
        self.setupUi(self)
        self.browser = DatasetsBrowserWidget()
        self.oauth: Optional[OAuthWorkflow] = None

        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.browser)
        self.browserFrame.setLayout(layout)

        pixmap = QPixmap(os.path.join(pluginPath, "img", "koordinates.png"))
        self.labelHeader.setPixmap(pixmap)

        self.btnLogin.clicked.connect(self.loginClicked)
        self.btnLogout.clicked.connect(self.logoutClicked)

        self.filter_widget = FilterWidget(self)
        filter_layout = QVBoxLayout()
        filter_layout.addWidget(self.filter_widget)
        self.filter_group_box.setLayout(filter_layout)

        self.groupBox.collapsedStateChanged.connect(self.groupCollapseStateChanged)

        self.comboDatatype.addItem(self.tr('All'))
        self.comboDatatype.addItem(self.tr('Vector'), DataType.Vectors)
        self.comboDatatype.addItem(self.tr('Raster'), DataType.Rasters)
        self.comboDatatype.addItem(self.tr('Grid'), DataType.Grids)
        self.comboDatatype.addItem(self.tr('Table'), DataType.Tables)
        self.comboDatatype.addItem(self.tr('Set'), DataType.Sets)
        self.comboDatatype.addItem(self.tr('Data Repository'), DataType.Repositories)
        self.comboDatatype.addItem(self.tr('Document'), DataType.Documents)

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
        KoordinatesClient.instance().error_occurred.connect(self._client_error_occurred)

        self.setForLogin(False)

    def backToBrowser(self):
        self.stackedWidget.setCurrentWidget(self.pageBrowser)

    def filtersChanged(self):
        self.btnSearch.setEnabled(True)

    def search(self):
        browser_query = DataBrowserQuery()

        if self.comboDatatype.currentData() is not None:
            browser_query.data_types = {self.comboDatatype.currentData()}

        if DataType.Vectors in browser_query.data_types:
            if self.chkPoints.isChecked():
                browser_query.vector_filters.add(VectorFilter.Point)
            if self.chkLines.isChecked():
                browser_query.vector_filters.add(VectorFilter.Line)
            if self.chkPolygons.isChecked():
                browser_query.vector_filters.add(VectorFilter.Polygon)
            if self.chkHasZ.isChecked():
                browser_query.vector_filters.add(VectorFilter.HasZ)
            if self.chkHasPrimaryKey.isChecked():
                browser_query.vector_filters.add(VectorFilter.HasPrimaryKey)
            # if self.chkHasDataRepository.isChecked():
            #    params["has_repo"] = True
        if DataType.Rasters in browser_query.data_types:
            if self.radioAerial.isChecked():
                browser_query.raster_filters.add(RasterFilter.AerialSatellitePhotos)
            elif self.radioNoAerial.isChecked():
                browser_query.raster_filters.add(RasterFilter.NotAerialSatellitePhotos)
            elif self.radioRGB.isChecked():
                browser_query.raster_filters.add(RasterFilter.ByBand)
                browser_query.raster_band_filters.add(RasterBandFilter.RGB)
            elif self.radioGrayscale.isChecked():
                browser_query.raster_filters.add(RasterFilter.ByBand)
                browser_query.raster_band_filters.add(RasterBandFilter.BlackAndWhite)

            if self.chkOnlyAlpha.isChecked():
                browser_query.raster_filter_options.add(RasterFilterOptions.WithAlphaChannel)
        # if datatype == "repo":
        #    if self.chkIncludeRepos.isChecked():
        #        params["kind"] = ["vector", "repo", "table"]
        #        params["has_repo"] = True
        category = self.comboCategory.currentData()
        if category is not None:
            if self.comboSubcategory.isVisible():
                browser_query.category = self.comboSubcategory.currentData()
            else:
                browser_query.category = category

        browser_query.created_maximum = QDateTime(self.dateCreatedBefore.date())
        browser_query.created_minimum = QDateTime(self.dateCreatedAfter.date())
        browser_query.updated_maximum = QDateTime(self.dateUpdatedBefore.date())
        browser_query.updated_minimum = QDateTime(self.dateUpdatedAfter.date())

        text = self.txtSearch.text().strip("")
        if text:
            browser_query.search = text

        self.btnSearch.setEnabled(False)

        context = self.comboContext.currentData()

        self.browser.populate(browser_query, context)

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

            self.filter_widget.set_logged_in(True)

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
