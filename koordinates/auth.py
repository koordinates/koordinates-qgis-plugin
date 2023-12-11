import json
import platform
import urllib
from typing import Optional
from enum import Enum
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from random import choice
from string import ascii_lowercase
from urllib.parse import parse_qs, urlsplit

import requests
from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QThread,
    pyqtSignal,
    QUrl,
    QUrlQuery
)
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtNetwork import (
    QNetworkRequest,
    QNetworkReply
)
from qgis.core import (
    QgsBlockingNetworkRequest,
    QgsNetworkAccessManager
)

from .pkce import generate_pkce_pair

AUTH_HANDLER_REDIRECT = "https://id.koordinates.com/o/authorize/qgis/"
AUTH_HANDLER_REDIRECT_CANCELLED = "https://id.koordinates.com/o/authorize/qgis/cancelled/"

AUTH_HANDLER_RESPONSE = """\
<html>
  <head>
    <title>Authentication Status</title>
  </head>
  <body>
    <p>The authentication flow has completed.</p>
  </body>
</html>
"""

AUTH_HANDLER_RESPONSE_ERROR = """\
<html>
  <head>
    <title>Authentication Status</title>
  </head>
  <body>
    <p>The authentication flow encountered an error: {}.</p>
  </body>
</html>
"""

AUTH_URL = "https://id.koordinates.com/o/authorize/"
TOKEN_URL = "https://id.koordinates.com/o/token/"
API_TOKEN_URL = "https://koordinates.com/services/api/v1.x/tokens/"

if platform.system() == "Darwin":
    CLIENT_ID = "AQDurhawOJKKmMcczxpwhFpMElUyz8FkxLHVsRse"
else:
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

    def log_request(self, format, *args):
        pass

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
        refresh_token = resp.get("refresh_token")

        if not access_token or not expires_in or not refresh_token:
            if not access_token:
                self.server.error = 'Could not find access_token in reply'
            elif not expires_in:
                self.server.error = 'Could not find expires_in in reply'
            elif not refresh_token:
                self.server.error = 'Could not find refresh_token in reply'

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
        self.server.refresh_token = refresh_token
        self.server.expires_in = expires_in
        self._send_response()

    def _send_response(self):
        if AUTH_HANDLER_REDIRECT and self.server.error is None:
            self.send_response(302)
            self.send_header("Location", AUTH_HANDLER_REDIRECT)
            self.end_headers()
        elif AUTH_HANDLER_REDIRECT_CANCELLED and self.server.error:
            self.send_response(302)
            self.send_header("Location", AUTH_HANDLER_REDIRECT_CANCELLED)
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            if self.server.error is not None:
                self.wfile.write(
                    AUTH_HANDLER_RESPONSE_ERROR.format(self.server.error).encode("utf-8"))
            else:
                self.wfile.write(AUTH_HANDLER_RESPONSE.encode("utf-8"))


class OAuthWorkflow(QThread):
    finished = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    EXPIRY_DURATION_SECONDS = 0

    def __init__(self):
        super().__init__()

        self.server = None

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
        self._refresh_reply: Optional[QNetworkReply] = None
        self._refresh_kx_key_reply: Optional[QNetworkReply] = None

    def refresh(self, refresh_token: str):
        query = QUrlQuery()
        query.addQueryItem('grant_type', 'refresh_token')
        query.addQueryItem('client_id', CLIENT_ID)
        query.addQueryItem('refresh_token', refresh_token)

        network_request = QNetworkRequest(QUrl(TOKEN_URL))
        network_request.setHeader(QNetworkRequest.ContentTypeHeader,
                                  'application/x-www-form-urlencoded')
        self._refresh_reply = QgsNetworkAccessManager.instance().post(
            network_request,
            query.toString(QUrl.FullyEncoded).encode()
        )
        self._refresh_reply.finished.connect(
            partial(self._refresh_oauth_finished, self._refresh_reply))

    def _refresh_oauth_finished(self, reply: QNetworkReply):
        if (self._refresh_reply is None or
                reply != self._refresh_reply or
                sip.isdeleted(self._refresh_reply)):
            return

        result = json.loads(self._refresh_reply.readAll().data())
        self._refresh_reply = None

        if 'error' in result:
            # assume refresh token is expired
            self.run()
            return

        access_token = result['access_token']
        refresh_token = result['refresh_token']
        expires_in = result['expires_in']

        body = {
            "scope": SCOPE_KX,
            "name": "koordinates-qgis-plugin-token",
            "site": "*",
        }
        api_token_body = urllib.parse.urlencode(body).encode()

        network_request = QNetworkRequest(QUrl(API_TOKEN_URL))
        network_request.setHeader(QNetworkRequest.ContentTypeHeader,
                                  'application/x-www-form-urlencoded')
        network_request.setRawHeader(b"Authorization",
                                     f"Bearer {access_token}".encode())

        self._refresh_kx_key_reply = QgsNetworkAccessManager.instance().post(
            network_request,
            api_token_body)
        self._refresh_kx_key_reply.finished.connect(
            partial(self._refresh_kx_key_finished,
                    self._refresh_kx_key_reply,
                    refresh_token,
                    expires_in))

    def _refresh_kx_key_finished(self,
                                 reply: QNetworkReply,
                                 refresh_token: str,
                                 expires_in: int):
        if (reply != self._refresh_kx_key_reply or
                sip.isdeleted(self._refresh_kx_key_reply)):
            return

        result = json.loads(self._refresh_kx_key_reply.readAll().data())
        self._refresh_kx_key_reply = None

        if 'error' in result:
            # assume refresh token is expired
            self.run()
            return

        kx_key = result['key']
        OAuthWorkflow.EXPIRY_DURATION_SECONDS = expires_in
        self.finished.emit(kx_key, refresh_token)

    def force_stop(self):
        # we have to dummy a dummy request in order to abort the blocking handle_request() loop
        requests.get("http://127.0.0.1:{}".format(REDIRECT_PORT))

    def close_server(self):
        if not self.server:
            return

        self.server.server_close()

        del self.server
        self.server = None

    def run(self):
        self.server = HTTPServer(("127.0.0.1", REDIRECT_PORT), _Handler)
        self.server.code_verifier = self.code_verifier
        self.server.apikey = None
        self.server.refresh_token = None
        self.server.expires_in = None
        self.server.error = None
        QDesktopServices.openUrl(QUrl(self.authorization_url))

        self.server.handle_request()

        err = self.server.error
        apikey = self.server.apikey
        refresh_token = self.server.refresh_token
        OAuthWorkflow.EXPIRY_DURATION_SECONDS = self.server.expires_in or 0

        if err:
            self.error_occurred.emit(err)

        self.finished.emit(apikey, refresh_token)
