import json
from typing import (
    Optional,
    Tuple,
    Dict
)

from qgis.PyQt.QtCore import (
    pyqtSignal,
    QObject,
    QUrl
)
from qgis.PyQt.QtNetwork import (
    QNetworkRequest,
    QNetworkReply
)
from qgis.core import (
    QgsBlockingNetworkRequest,
    QgsNetworkAccessManager
)

from koordinatesexplorer.utils import waitcursor
from .data_browser import DataBrowserQuery
from .utils import ApiUtils

PAGE_SIZE = 20


class LoginException(Exception):
    pass


class KoordinatesClient(QObject):
    loginChanged = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    __instance = None

    @staticmethod
    def instance() -> 'KoordinatesClient':
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
        self._user_details = None

    @waitcursor
    def login(self, apiKey):
        self.headers = {"Authorization": f"key {apiKey}"}

        try:
            self._user_details = self._get("users/me/")['json']
        except Exception:
            self._user_details = None

        if self._user_details is None:
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

    def _build_datasets_request(self,
                                page=1,
                                query: Optional[DataBrowserQuery] = None,
                                context=None,
                                is_facets: bool = False) -> Tuple[str, Dict[str, str], dict]:
        """
        Builds the parameters used for a datasets request
        """
        context = context or {"type": "site", "domain": "all"}
        headers = {"Expand": "list,list.publisher,list.styles,list.data.source_summary"}

        if query:
            params = query.build_query()
        else:
            params = {}

        if not is_facets:
            params.update({"page_size": PAGE_SIZE, "page": page})
        else:
            params['facets'] = True

        if context["type"] == "site":
            endpoint = "data/"
            params["from"] = context["domain"]
        else:
            endpoint = "users/me/data/"

        return endpoint, headers, params

    def datasets_async(self,
                       page=1,
                       query: Optional[DataBrowserQuery] = None,
                       context=None) -> QNetworkReply:
        """
        Retrieve datasets asynchronously
        """
        endpoint, headers, params = self._build_datasets_request(page, query, context)
        network_request = self._build_request(endpoint, headers, params)

        return QgsNetworkAccessManager.instance().get(network_request)

    def facets_async(self,
                     page=1,
                     query: Optional[DataBrowserQuery] = None,
                     context=None) -> QNetworkReply:
        """
        Retrieve dataset facets asynchronously
        """
        endpoint, headers, params = self._build_datasets_request(page, query, context,
                                                                 is_facets=True)
        network_request = self._build_request(endpoint, headers, params)

        return QgsNetworkAccessManager.instance().get(network_request)

    def datasets(self, page=1, query: Optional[DataBrowserQuery] = None, context=None):
        """
        Retrieve datasets blocking
        """
        endpoint, headers, params = self._build_datasets_request(page, query, context)
        ret = self._get(endpoint, headers, params)

        tokens = ret['reply'].rawHeader(b"X-Resource-Range").data().decode().split("/")
        total = tokens[-1]
        last = tokens[0].split("-")[-1]
        return ret['json'], last == total

    def user_details(self) -> dict:
        """
        Returns a diction of user details
        """
        return self._user_details

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
    def star(self, dataset_id, is_starred: bool):
        """
        Stars or unstars a dataset
        """
        url = QUrl(f"https://koordinates.com/services/api/v1.x/layers/{dataset_id}/star/")
        network_request = QNetworkRequest(url)

        for header, value in self.headers.items():
            network_request.setRawHeader(header.encode(),
                                         value.encode())

        request = QgsBlockingNetworkRequest()
        if is_starred:
            if request.post(network_request, b'') != QgsBlockingNetworkRequest.NoError:
                self.error_occurred.emit(request.reply().errorString())
        else:
            if request.deleteResource(network_request) != QgsBlockingNetworkRequest.NoError:
                self.error_occurred.emit(request.reply().errorString())

    def _build_request(self, endpoint: str, headers=None, params=None) -> QNetworkRequest:
        """
        Builds a network request
        """
        url = QUrl(f"https://koordinates.com/services/api/v1.x/{endpoint}")

        if params:
            url.setQuery(ApiUtils.to_url_query(params))

        network_request = QNetworkRequest(url)

        headers = headers or {}
        headers.update(self.headers)
        for header, value in headers.items():
            network_request.setRawHeader(header.encode(),
                                         value.encode())

        return network_request

    @waitcursor
    def _get(self, endpoint, headers=None, params=None):
        network_request = self._build_request(endpoint, headers, params)

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
