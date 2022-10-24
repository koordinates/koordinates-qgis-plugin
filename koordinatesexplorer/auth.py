import json
import urllib
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from random import choice
from string import ascii_lowercase
from urllib.parse import parse_qs, urlsplit

from qgis.PyQt.QtCore import (
    QObject,
    pyqtSignal,
    QUrl
)
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import (
    QgsBlockingNetworkRequest
)

from .pkce import generate_pkce_pair

AUTH_HANDLER_REDIRECT = ""

AUTH_HANDLER_RESPONSE = """\
<html>
  <head>
    <title>Authentication Status</title>
  </head>
  <body>
    <p>The authentication flow has completed.</p>
  </body>
</html>
""".encode(
    "utf-8"
)

AUTH_URL = "https://id.koordinates.com/o/authorize/"
TOKEN_URL = "https://id.koordinates.com/o/token/"
API_TOKEN_URL = "https://koordinates.com/services/api/v1.x/tokens/"
CLIENT_ID = "hqQUoglBFNlb5xJevSvGlqobqOasPsCZYOA5xeuh"
REDIRECT_PORT = 8989
REDIRECT_URL = f"http://127.0.0.1:{REDIRECT_PORT}/"
SCOPE = "read"
SCOPE_KX = (
    "query tiles catalog users:read sets:read layers:read repos:read viewers:read"
    " viewers:write wxs:wfs exports:write notifications:read"
)


class AuthState(Enum):
    """
    Authentication states
    """
    LoggedOut = 0
    LoggingIn = 1
    LoggedIn = 2


class _Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        params = parse_qs(urlsplit(self.path).query)
        code = params.get("code")

        if not code:
            self.server.error = 'Authorization canceled'
            self._send_response()
            return

        body = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code_verifier": self.server.code_verifier,
            "code": code[0],
            "redirect_uri": REDIRECT_URL,
        }

        request = QgsBlockingNetworkRequest()
        token_body = urllib.parse.urlencode(body).encode()

        network_request = QNetworkRequest(QUrl(TOKEN_URL))
        network_request.setHeader(QNetworkRequest.ContentTypeHeader,
                                  'application/x-www-form-urlencoded')

        if request.post(network_request,
                        data=token_body,
                        forceRefresh=True) != QgsBlockingNetworkRequest.NoError:
            self.server.error = request.reply().content().data().decode() \
                                or request.reply().errorString()
            self._send_response()
            return

        resp = json.loads(request.reply().content().data().decode())

        access_token = resp.get("access_token")
        expires_in = resp.get("expires_in")

        if not access_token or not expires_in:
            if not access_token:
                self.server.error = 'Could not find access_token in reply'
            elif not expires_in:
                self.server.error = 'Could not find expires_in in reply'

            self._send_response()
            return

        body = {
            "scope": SCOPE_KX,
            "name": "koordinates-qgis-plugin-token",
            "site": "*",
        }
        api_token_body = urllib.parse.urlencode(body).encode()

        network_request = QNetworkRequest(QUrl(API_TOKEN_URL))
        network_request.setHeader(QNetworkRequest.ContentTypeHeader,
                                  'application/x-www-form-urlencoded')
        network_request.setRawHeader(b"Authorization", f"Bearer {access_token}".encode())

        if request.post(network_request,
                        data=api_token_body,
                        forceRefresh=True) != QgsBlockingNetworkRequest.NoError:
            self.server.error = request.reply().content().data().decode() \
                                or request.reply().errorString()
            self._send_response()
            return

        resp = json.loads(request.reply().content().data().decode())

        self.server.apikey = resp["key"]
        self._send_response()

    def _send_response(self):
        if AUTH_HANDLER_REDIRECT:
            self.send_response(302)
            self.send_header("Location", AUTH_HANDLER_REDIRECT)
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(AUTH_HANDLER_RESPONSE)


class OAuthWorkflow(QObject):
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        code_verifier, code_challenge = generate_pkce_pair()

        state = "".join(choice(ascii_lowercase) for i in range(10))
        self.authorization_url = (
            f"{AUTH_URL}?"
            f"scope={SCOPE}&"
            f"response_type=code&"
            f"response_mode=query&"
            f"client_id={CLIENT_ID}&"
            f"code_challenge={code_challenge}&"
            f"state={state}&"
            f"code_challenge_method=S256&"
            f"redirect_uri={REDIRECT_URL}"
        )
        self.code_verifier, self.code_challenge = generate_pkce_pair()
        self.authorization_url = f"{self.authorization_url}&code_challenge={self.code_challenge}&code_challenge_method=S256"  # noqa: E501

    def doAuth(self):
        server = HTTPServer(("127.0.0.1", REDIRECT_PORT), _Handler)
        server.code_verifier = self.code_verifier
        server.apikey = None
        server.error = None
        QDesktopServices.openUrl(QUrl(self.authorization_url))

        server.handle_request()

        if server.error:
            self.error_occurred.emit(server.error)

        self.finished.emit(server.apikey)
