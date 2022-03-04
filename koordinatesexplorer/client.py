import json
import requests

from qgis.PyQt.QtCore import pyqtSignal, QObject

from koordinatesexplorer.utils import waitcursor

PAGE_SIZE = 20

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

        self.layers = {}

        with open("c:\\temp\\layers.json") as f:
            self.layers = json.load(f)

        self.apiKey = None
        self.headers = None
        self._datasets = None

    @waitcursor
    def login(self, apiKey):
        oldKey = self.apiKey
        self.apiKey = apiKey

        self.headers = {"Authorization": f"key {apiKey}"}

        try:
            self.userEMail()
        except Exception:
            raise LoginException()

        if oldKey != apiKey:
            self.loginChanged.emit(self.isLoggedIn())

    def logout(self):
        oldKey = self.apiKey

        self.apiKey = None

        if oldKey != self.apiKey:
            self.loginChanged.emit(self.isLoggedIn())

    def isLoggedIn(self):
        return self.apiKey is not None

    def datasets(self, page=1):
        headers = {"Expand": "list,list.publisher,list.styles,list.data.source_summary"}
        params = {"page_size": PAGE_SIZE, "page": page}
        return self._get("data", headers, params)

    def userEMail(self):
        return self._get("users/me")["email"]

    def dataset(self, datasetid):
        if str(datasetid) not in self.layers:
            self.layers[str(datasetid)] = self._get(f"layers/{datasetid}")
        return self.layers[str(datasetid)]

    @waitcursor
    def _get(self, url, headers=None, params=None):
        headers = headers or {}
        headers.update(self.headers)
        params = params or {}
        ret = requests.get(
                f"https://koordinates.com/services/api/v1/{url}",
                headers=headers,
                params=params
            )
        ret.raise_for_status()
        return ret.json()
