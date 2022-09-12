import json
from typing import (
    Optional,
    List
)

from qgis.PyQt.QtCore import (
    pyqtSignal,
    QObject,
    QUrl,
    QUrlQuery
)
from qgis.PyQt.QtNetwork import QNetworkRequest

from qgis.core import QgsBlockingNetworkRequest



from koordinatesexplorer.utils import waitcursor

PAGE_SIZE = 20


class LoginException(Exception):
    pass


class KoordinatesClient(QObject):

    loginChanged = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

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

        email = None
        try:
            email = self.userEMail()
        except Exception:
            pass

        if email is None:
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

    def datasets(self, page=1, params=None, context=None):
        params = params or {}
        context = context or {"type": "site", "domain": "all"}
        headers = {"Expand": "list,list.publisher,list.styles,list.data.source_summary"}
        params.update({"page_size": PAGE_SIZE, "page": page})
        if context["type"] == "site":
            url = "data/"
            params["from"] = context["domain"]
        else:
            url = "users/me/data/"
        ret = self._get(url, headers, params)

        tokens = ret['reply'].rawHeader(b"X-Resource-Range").data().decode().split("/")
        total = tokens[-1]
        last = tokens[0].split("-")[-1]
        return ret['json'], last == total

    def userEMail(self) -> Optional[str]:
        return self._get("users/me/")['json'].get("email")

    def userContexts(self) -> List[str]:
        return self._get("users/me/")['json'].get("contexts", [])

    def dataset(self, datasetid):
        if str(datasetid) not in self.layers:
            self.layers[str(datasetid)] = self._get(f"data/{datasetid}/")['json']
        return self.layers[str(datasetid)]

    def table(self, tableid):
        if str(tableid) not in self.layers:
            self.tables[str(tableid)] = self._get(f"tables/{tableid}/")['json']
        return self.layers[str(tableid)]

    def categories(self):
        if self._categories is None:
            self._categories = self._get("categories")['json']
        return self._categories

    @waitcursor
    def _get(self, url, headers=None, params=None):

        url = QUrl(f"https://koordinates.com/services/api/v1.x/{url}")

        params = params or {}
        query = QUrlQuery()
        for name, value in params.items():
            query.addQueryItem(name, str(value))
        url.setQuery(query)

        network_request = QNetworkRequest(url)

        headers = headers or {}
        headers.update(self.headers)
        for header, value in headers.items():
            network_request.setRawHeader(header.encode(),
                                         value.encode())

        request = QgsBlockingNetworkRequest()
        if request.get(network_request) != QgsBlockingNetworkRequest.NoError:
            self.error_occurred.emit(request.reply().errorString())
            reply_json = {}
        else:
            reply_json = json.loads(request.reply().content().data().decode())

        return {
            'json': reply_json,
            'reply': request.reply()
        }
