import requests

from qgis.PyQt.QtCore import pyqtSignal, QObject

from koordinatesexplorer.utils import waitcursor


class LoginException(Exception):
    pass


class KoordinatesClient(QObject):

    loginChanged = pyqtSignal(bool)

    __instance = None

    @staticmethod
    def instance():
        if KoordinatesClient.__instance is None:
            KoordinatesClient()

        return KoordinatesClient.__instance

    def __init__(self):
        if KoordinatesClient.__instance is not None:
            raise Exception("Singleton class")

        QObject.__init__(self)

        KoordinatesClient.__instance = self

        self.apiKey = None
        self.client = None

    @waitcursor
    def login(self, apiKey):
        oldKey = self.apiKey
        self.apiKey = apiKey

        headers = {"Authorization": f"key {apiKey}"}

        ret = requests.get(
            "https://koordinates.com//services/api/v1/data",
            headers=headers,
        )
        if not ret.ok:
            raise LoginException()

        if oldKey != apiKey:
            self.loginChanged.emit(self.isLoggedIn())

    def logout(self):
        oldKey = self.apiKey

        self.apiKey = None
        self.client = None

        if oldKey != self.apiKey:
            self.loginChanged.emit(self.isLoggedIn())

    def isLoggedIn(self):
        return self.apiKey is not None
