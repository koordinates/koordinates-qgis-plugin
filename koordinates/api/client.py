import json
from enum import Enum
from typing import (
    Optional,
    Tuple,
    Dict,
    Set
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

from koordinates.utils import waitcursor
from .data_browser import DataBrowserQuery
from .utils import ApiUtils
from .repo import Repo
from .enums import (
    DataType,
    PublisherType
)
from .dataset import Dataset

PAGE_SIZE = 20


class LoginException(Exception):
    pass


class UserCapability(Enum):
    EnableKartClone = 0


class KoordinatesClient(QObject):
    loginChanged = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    BASE64_ENCODED_SVG_HEADER = 'data:image/svg+xml;base64,'

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
        self._dataset_details = {}
        self._categories = None

        self.reset_domain()

        self.apiKey = None
        self.headers = {}
        self._datasets = None
        self._user_details = None

    def reset_domain(self):
        self.domain = 'koordinates.com'

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
        headers = {"Expand": "list,list.publisher,list.styles,list.data.source_summary"}

        if query:
            params = query.build_query()
        else:
            params = {}

        if not is_facets:
            params.update({"page_size": PAGE_SIZE, "page": page})
        else:
            params['facets'] = True

        context = context or {"type": "site", "domain": "all"}

        if context["type"] == "site":
            endpoint = "data/"
            if not query.publisher:
                params["from"] = context["domain"]
        else:
            endpoint = "users/me/data/"

        return endpoint, headers, params

    def _build_explore_sections_request(self,
                                        context=None) -> Tuple[str, Dict[str, str], dict]:
        """
        Builds the parameters used for a datasets request
        """
        headers = {"Expand": "list,list.publisher,list.styles,list.data.source_summary"}

        params = {}

        endpoint = "explore-sections/"

        return endpoint, headers, params

    def _build_explore_request(self,
                               section_slug: str,
                               context=None) -> Tuple[str, Dict[str, str], dict]:
        """
        Builds the parameters used for a datasets request
        """
        headers = {"Expand": "list,list.publisher,list.styles,list.data.source_summary"}

        params = {}
        params.update({"page_size": PAGE_SIZE})

        endpoint = "explore-sections/"
        if section_slug not in ('browse', 'publishers'):
            endpoint += section_slug + "/"

        params["item_type"] = ['layer.*']

        return endpoint, headers, params

    def _build_publishers_request(self,
                                  publisher_type: Optional[PublisherType],
                                  filter_string: Optional[str] = None,
                                  page=1,
                                  context=None,
                                  is_facets: bool = False) -> Tuple[str, Dict[str, str], dict]:
        """
        Builds the parameters used for a publishers request
        """
        headers = {"Expand": "list,list.publisher,list.styles,list.data.source_summary"}

        params = {
                  'public': 'true',
                  'sort': 'popularity'
                  }

        if filter_string:
            params['q'] = filter_string

        if not is_facets:
            if publisher_type == PublisherType.Publisher:
                params['type'] = 'site'
            elif publisher_type == PublisherType.User:
                params['type'] = 'user'
            elif publisher_type == PublisherType.Mirror:
                params['type'] = 'mirror'
            params.update({"page_size": PAGE_SIZE, "page": page})
        else:
            params['facets'] = True
        endpoint = "publishers/"

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

    def explore_sections_async(self,
                               context=None) -> QNetworkReply:
        """
        Retrieve explore sections asynchronously
        """
        endpoint, headers, params = self._build_explore_sections_request(context)
        network_request = self._build_request(endpoint, headers, params)
        network_request.setAttribute(
            QNetworkRequest.CacheLoadControlAttribute,
            QNetworkRequest.PreferCache)
        network_request.setAttribute(
            QNetworkRequest.CacheSaveControlAttribute,
            True
        )
        return QgsNetworkAccessManager.instance().get(network_request)

    def explore_async(self,
                      section_slug: str,
                      context=None) -> QNetworkReply:
        """
        Retrieve datasets asynchronously
        """
        endpoint, headers, params = self._build_explore_request(
            section_slug, context)
        network_request = self._build_request(endpoint, headers, params)

        return QgsNetworkAccessManager.instance().get(network_request)

    def publishers_async(self,
                         publisher_type: Optional[PublisherType],
                         page=1,
                         filter_string: Optional[str] = None,
                         context=None,
                         is_facets: bool = False) -> QNetworkReply:
        """
        Retrieve publishers asynchronously
        """
        endpoint, headers, params = self._build_publishers_request(
            publisher_type=publisher_type,
            filter_string=filter_string,
            page=page,
            context=context,
            is_facets=is_facets)
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

    def data_revisions_count(self, id) -> Optional[int]:
        """
        Retrieve data revisions blocking
        """
        params = {}

        endpoint = "layers/{}/versions/".format(id)
        headers = {}
        headers.update(self.headers)

        ret = self._get(endpoint, headers, params)

        tokens = ret['reply'].rawHeader(b"X-Resource-Range").data().decode().split("/")
        try:
            total = int(tokens[-1])
        except ValueError:
            return None

        return total

    def total_revisions_count(self, id) -> Optional[int]:
        """
        Retrieve total revisions blocking
        """
        params = {'data_import': True}

        endpoint = "layers/{}/versions/".format(id)
        headers = {}
        headers.update(self.headers)

        ret = self._get(endpoint, headers, params)

        tokens = ret['reply'].rawHeader(b"X-Resource-Range").data().decode().split("/")
        try:
            total = int(tokens[-1])
        except ValueError:
            return None
        return total

    def retrieve_repository(self, url) -> Optional[Repo]:
        """
        Retrieve repository details blocking
        """
        res = self.get_json(url)
        if res:
            return Repo(res)

        return None

    def user_details(self) -> dict:
        """
        Returns a diction of user details
        """
        return self._user_details

    def user_capabilities(self) -> Set[UserCapability]:
        """
        Returns the user capabilities
        """
        res = set()
        if self._user_details.get('capabilities', {}).get('enable_kart_clone', False):
            res.add(UserCapability.EnableKartClone)

        return res

    def dataset_details(self, dataset: Dataset) -> Dict:
        """
        Retrieve dataset details
        """
        str_id = str(dataset.id)
        if str_id not in self._dataset_details:
            if dataset.datatype == DataType.PointClouds:
                endpoint = f"datasets/{str_id}/"
            elif dataset.datatype == DataType.Tables:
                endpoint = f"tables/{str_id}/"
            else:
                endpoint = f"layers/{str_id}/"
            self._dataset_details[str_id] = self._get(endpoint)['json']

        return self._dataset_details[str_id]

    def categories(self):
        if self._categories is None:
            self._categories = self._get("categories")['json']
        return self._categories

    @waitcursor
    def star(self, dataset_id, is_starred: bool):
        """
        Stars or unstars a dataset
        """
        url = QUrl(f"https://{self.domain}/services/api/v1.x/layers/{dataset_id}/star/")
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
        url = QUrl(f"https://{self.domain}/services/api/v1.x/{endpoint}")

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

    @waitcursor
    def get_json(self, url: str):
        url = QUrl(url)
        network_request = QNetworkRequest(url)
        headers = {}
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

        return reply_json
