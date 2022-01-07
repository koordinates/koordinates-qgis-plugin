import os

from qgis.utils import iface

from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
)
from qgis.PyQt.QtWebKitWidgets import QWebView, QWebInspector
from qgis.PyQt.QtWebKit import QWebSettings

URL = QUrl(
    f"file:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')}"
)


class TestExplorer(QDialog):
    def __init__(self):
        super(QDialog, self).__init__(iface.mainWindow())
        self.txtUrl = QLineEdit()
        self.btnLoad = QPushButton("Load")
        self.btnLoad.clicked.connect(self.loadClicked)
        hlayout = QHBoxLayout()
        hlayout.setMargin(0)
        hlayout.addWidget(self.txtUrl)
        hlayout.addWidget(self.btnLoad)
        self.webView = QWebView()
        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.addLayout(hlayout)
        layout.addWidget(self.webView)
        self.inspector = QWebInspector()
        layout.addWidget(self.inspector)
        self.setLayout(layout)
        self.webView.page().settings().setAttribute(
            QWebSettings.JavascriptEnabled, True
        )
        self.txtUrl.setText(URL.toString())
        self.loadClicked()
        self.setWindowFlags(Qt.Window)

    def loadClicked(self):
        url = QUrl(self.txtUrl.text())
        self.webView.page().settings().setAttribute(
            QWebSettings.DeveloperExtrasEnabled, True
        )
        self.webView.load(url)
        self.inspector.setPage(self.webView.page())
