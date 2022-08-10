import requests
from random import choice
from string import ascii_lowercase
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit
from webbrowser import open as web_open

from .pkce import generate_pkce_pair

from PyQt5.QtCore import QObject, pyqtSignal


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


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        params = parse_qs(urlsplit(self.path).query)
        code = params.get("code")

        if not code:
            self._send_response()
            return

        body = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code_verifier": self.server.code_verifier,
            "code": code,
            "redirect_uri": REDIRECT_URL,
        }

        resp = requests.post(TOKEN_URL, data=body).json()

        access_token = resp.get("access_token")
        expires_in = resp.get("expires_in")

        if not access_token or not expires_in:
            self._send_response()
            return

        headers = {"Authorization": f"Bearer {access_token}"}
        body = {
            "scope": SCOPE_KX,
            "name": "koordinates-qgis-plugin-token",
            "expires_at": None,
            "referrers": [],
            "site": "*",
        }
        resp = requests.post(API_TOKEN_URL, headers=headers, data=body).json()

        self.server.apikey = resp["key"]

        self._send_response()

    def _send_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(AUTH_HANDLER_RESPONSE)


class OAuthWorkflow(QObject):

    finished = pyqtSignal(str)

    def doAuth(self):
        code_verifier, code_challenge = generate_pkce_pair()

        state = "".join(choice(ascii_lowercase) for i in range(10))
        authorization_url = (
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
        code_verifier, code_challenge = generate_pkce_pair()
        authorization_url = f"{authorization_url}&code_challenge={code_challenge}&code_challenge_method=S256"  # noqa: E501

        server = HTTPServer(("127.0.0.1", REDIRECT_PORT), _Handler)
        server.code_verifier = code_verifier
        server.apikey = None
        web_open(authorization_url)

        server.handle_request()

        self.finished.emit(server.apikey)
        # print(self.server.apikey)
