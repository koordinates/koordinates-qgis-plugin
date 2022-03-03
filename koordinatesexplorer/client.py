import json
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

        ret = requests.get(
            "https://koordinates.com/services/api/v1/layers?kind=raster",
            headers=self.headers,
        )
        if not ret.ok:
            raise LoginException()

        self._datasets = ret.json()

        if oldKey != apiKey:
            self.loginChanged.emit(self.isLoggedIn())

    def logout(self):
        oldKey = self.apiKey

        self.apiKey = None

        if oldKey != self.apiKey:
            self.loginChanged.emit(self.isLoggedIn())

    def isLoggedIn(self):
        return self.apiKey is not None

    def datasets(self):
        return self._datasets

    def dataset(self, datasetid):
        if str(datasetid) not in self.layers:
            ret = requests.get(
                f"https://koordinates.com/services/api/v1/layers/{datasetid}",
                headers=self.headers,
            )
            self.layers[str(datasetid)] = ret.json()
        '''
        with open("c:\\temp\\layers.json", "w") as f:
            json.dump(self.layers, f)
        '''
        return self.layers[str(datasetid)]
