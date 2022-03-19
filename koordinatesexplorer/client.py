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
        self._categories = None

        self.apiKey = None
        self.headers = {}
        self._datasets = None

    @waitcursor
    def login(self, apiKey):
        self.headers = {"Authorization": f"key {apiKey}"}

        try:
            self.userEMail()
        except Exception:
            raise LoginException()

        self.apiKey = apiKey
        self.loginChanged.emit(True)

    def logout(self):
        oldKey = self.apiKey

        self.apiKey = None

        if oldKey != self.apiKey:
            self.loginChanged.emit(self.isLoggedIn())

    def isLoggedIn(self):
        return self.apiKey is not None

    def datasets(self, page=1, params=None):
        params = params or {}
        headers = {"Expand": "list,list.publisher,list.styles,list.data.source_summary"}
        params.update({"page_size": PAGE_SIZE, "page": page})
        ret = self._get("data", headers, params)
        tokens = ret.headers.get("X-Resource-Range", "").split("/")
        total = tokens[-1]
        last = tokens[0].split("-")[-1]
        return ret.json(), last == total

    def userEMail(self):
        return self._get("users/me").json()["email"]

    def dataset(self, datasetid):
        if str(datasetid) not in self.layers:
            self.layers[str(datasetid)] = self._get(f"data/{datasetid}").json()
        return self.layers[str(datasetid)]

    def table(self, tableid):
        if str(tableid) not in self.layers:
            self.tables[str(tableid)] = self._get(f"tables/{tableid}").json()
        return self.layers[str(tableid)]

    def categories(self):
        if self._categories is None:
            self._categories = self._get("categories").json()
        return self._categories

    @waitcursor
    def _get(self, url, headers=None, params=None):
        headers = headers or {}
        headers.update(self.headers)
        params = params or {}
        ret = requests.get(
            f"https://koordinates.com/services/api/v1/{url}",
            headers=headers,
            params=params,
        )
        ret.raise_for_status()
        return ret
