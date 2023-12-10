from typing import (
    Optional,
    Tuple
)
import platform

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QSize, QTimer
from qgis.PyQt.QtSvg import QSvgWidget
from qgis.PyQt.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from qgis.core import Qgis, QgsApplication, QgsSettings
from qgis.utils import iface

from .action_button import ActionButton
from .gui_utils import GuiUtils
from ..api import KoordinatesClient
from ..auth import OAuthWorkflow, AuthState

AUTH_CONFIG_ID = "koordinates_auth_id"
AUTH_CONFIG_REFRESH_TOKEN = "koordinates_refresh_token"


class LoginButton(ActionButton):
    BUTTON_COLOR = "#0a9b46"
    BUTTON_OUTLINE = "#076d31"
    BUTTON_TEXT = "#ffffff"
    BUTTON_HOVER = "#1a8c49"

    BUTTON_DISABLED_COLOR = "#f5f5f7"
    BUTTON_DISABLED_OUTLINE = "#c4c4c6"
    BUTTON_DISABLED_TEXT = "#c4c4c6"
    BUTTON_DISABLED_HOVER = "#f5f5f7"

    def __init__(self, parent=None):
        super().__init__(parent)

        self._state = AuthState.LoggedOut
        self.setFixedSize(233, self.BUTTON_HEIGHT)
        self.set_state(AuthState.LoggedOut)

    def set_state(self, state: AuthState):
        self._state = state

        if state == AuthState.LoggedOut:
            self.setText("Login with your Koordinates ID")
        elif state == AuthState.LoggingIn:
            self.setText("Authorizing")
        elif state == AuthState.LoggedIn:
            self.setText("Login with your Koordinates ID")

        if state == AuthState.LoggedOut:
            self.setStyleSheet(
                self.BASE_STYLE.format(
                    self.BUTTON_COLOR,
                    self.BUTTON_OUTLINE,
                    self.BUTTON_TEXT,
                    self.BUTTON_HOVER,
                )
            )
            self.setEnabled(True)
        else:
            self.setStyleSheet(
                self.BASE_STYLE.format(
                    self.BUTTON_DISABLED_COLOR,
                    self.BUTTON_DISABLED_OUTLINE,
                    self.BUTTON_DISABLED_TEXT,
                    self.BUTTON_DISABLED_HOVER,
                )
            )
            self.setEnabled(False)


class LoginWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.oauth = None
        self.oauth_close_timer = None

        self.setFrameShape(QFrame.NoFrame)

        self.setStyleSheet(
            """LoginWidget {
         background-color: white;
         border: 1px solid rgb(180, 180, 180);
          }"""
        )

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)

        top_frame = QFrame()
        top_frame.setFrameShape(QFrame.NoFrame)
        top_frame.setStyleSheet(
            """
         background-color: #323233;
        """
        )
        top_frame.setFixedHeight(270)

        top_frame_layout = QVBoxLayout()
        top_frame_layout.setContentsMargins(38, 0, 0, 25)
        top_frame_layout.addStretch(1)
        koordinates_logo_widget = QSvgWidget(
            GuiUtils.get_icon_svg("koordinates_logo_white.svg")
        )
        koordinates_logo_widget.setFixedSize(QSize(182, 52))

        top_frame_layout.addWidget(koordinates_logo_widget)
        top_frame.setLayout(top_frame_layout)

        vl.addWidget(top_frame)

        contents_widget = QWidget()
        contents_layout = QVBoxLayout()
        contents_layout.setContentsMargins(40, 35, 40, 0)

        self.login_label = QLabel()
        self.login_label.setWordWrap(True)
        font = self.font()
        font.setPointSize(10)
        self.login_label.setText(
            """<style>
        p { line-height: 1.3; }
        </style><p>Login to your Koordinates account to get started.</p>
        <p>The next step will open a web browser and might require you to sign in to your
        Koordinates account.</p>"""
        )
        self.login_label.setFont(font)
        contents_layout.addWidget(self.login_label)
        contents_layout.addSpacing(18)

        self.login_button = LoginButton()

        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.login_button)

        self.open_login_window_label = QLabel()
        self.open_login_window_label.setFont(font)
        self.open_login_window_label.setOpenExternalLinks(True)
        hl.addSpacing(10)
        hl.addWidget(self.open_login_window_label)
        self.open_login_window_label.hide()
        hl.addStretch(1)

        contents_layout.addLayout(hl)

        contents_layout.addSpacing(21)
        signup_label = QLabel()
        signup_label.setWordWrap(True)
        signup_label.setText(
            """<style>
            a {color: #868889;}
            </style><span
            style="color: #868889;">Need to create a Koordinates ID? <a
            href="https://id.koordinates.com/signup">Sign Up</a></span>"""
        )
        signup_label.setFont(font)
        signup_label.setOpenExternalLinks(True)
        contents_layout.addWidget(signup_label)

        contents_layout.addStretch(1)

        tos_label = QLabel()
        tos_label.setWordWrap(True)
        tos_label.setText(
            """<style>
            a {color: #868889; text-decoration: none}
            </style><span
            style="color: #868889;"><a
            href="https://koordinates.com/privacy-policy/">Privacy Policy</a> • <a
            href="https://koordinates.com/terms-of-use/">Terms of Use</a></span>"""
        )
        tos_label.setFont(font)
        tos_label.setOpenExternalLinks(True)
        contents_layout.addWidget(tos_label)

        contents_layout.addSpacing(50)

        contents_widget.setLayout(contents_layout)

        self.login_button.clicked.connect(self.login_clicked)

        vl.addWidget(contents_widget, 1)

        self.setLayout(vl)

        KoordinatesClient.instance().loginChanged.connect(self._login_changed)
        KoordinatesClient.instance().error_occurred.connect(self._client_error_occurred)

    def cancel_active_requests(self):
        self._close_auth_server(force_close=True)

    def login_clicked(self):
        key, refresh_token = self.retrieve_api_key()

        if refresh_token:
            if self.oauth is not None:
                self._close_auth_server()

            self.oauth = OAuthWorkflow()
            self.oauth.finished.connect(self._auth_finished)
            self.oauth.error_occurred.connect(self._auth_error_occurred)

            self.oauth.refresh(refresh_token)

            return

        if key is not None:
            self._auth_finished(key, refresh_token)
        else:
            self.login_button.set_state(AuthState.LoggingIn)

            if self.oauth is not None:
                self._close_auth_server()

            self.oauth = OAuthWorkflow()

            self.open_login_window_label.setText(
                '<a href="{}" style="color: black;">Open the login window</a>'.format(
                    self.oauth.authorization_url
                )
            )
            self.open_login_window_label.show()

            self.oauth.finished.connect(self._auth_finished)
            self.oauth.error_occurred.connect(self._auth_error_occurred)
            self.oauth.start()

    def _login_changed(self, logged_in: bool):
        if not logged_in:
            self.remove_api_key()
            self.login_button.set_state(AuthState.LoggedOut)
            self.open_login_window_label.hide()

    def _close_auth_server(self, force_close=False):
        if self.oauth_close_timer and not sip.isdeleted(self.oauth_close_timer):
            self.oauth_close_timer.timeout.disconnect(self._close_auth_server)
            self.oauth_close_timer.deleteLater()
        self.oauth_close_timer = None

        if self.oauth and not sip.isdeleted(self.oauth):
            if force_close:
                self.oauth.force_stop()

            self.oauth.close_server()
            self.oauth.quit()
            self.oauth.wait()
            self.oauth.deleteLater()

        self.oauth = None

    def _auth_finished(self, key: str, refresh_token: Optional[str]):
        if self.oauth and not sip.isdeleted(self.oauth):
            self.oauth_close_timer = QTimer(self)
            self.oauth_close_timer.setSingleShot(True)
            self.oauth_close_timer.setInterval(1000)
            self.oauth_close_timer.timeout.connect(self._close_auth_server)
            self.oauth_close_timer.start()

        if not key:
            return

        try:
            KoordinatesClient.instance().login(key)
            self.store_api_key(key, refresh_token)
            self.login_button.set_state(AuthState.LoggedIn)
            self.open_login_window_label.hide()
        except FileExistsError:
            iface.messageBar().pushMessage(
                "Could not log in. Check your connection and your API Key value",
                Qgis.Warning,
                duration=5,
            )
            self.login_button.set_state(AuthState.LoggedOut)
            self.open_login_window_label.hide()

    def _auth_error_occurred(self, error: str):
        self.login_button.set_state(AuthState.LoggedOut)
        self.open_login_window_label.hide()
        iface.messageBar().pushMessage(
            "Authorization failed: {}".format(error),
            Qgis.Warning,
            duration=5,
        )

    def _client_error_occurred(self, error: str):
        self.login_button.set_state(AuthState.LoggedOut)
        self.open_login_window_label.hide()
        self.open_login_window_label.hide()
        iface.messageBar().pushMessage(
            "Request failed: {}".format(error),
            Qgis.Warning,
            duration=5,
        )

    def remove_api_key(self):
        if platform.system() == "Darwin":
            # remove stored plain text tokens on MacOS
            QgsSettings().remove("koordinates/token", QgsSettings.Plugins)
            QgsSettings().remove("koordinates/refresh_token",
                                 QgsSettings.Plugins)
        else:
            QgsApplication.authManager().removeAuthSetting(AUTH_CONFIG_ID)
            QgsApplication.authManager().removeAuthSetting(
                AUTH_CONFIG_REFRESH_TOKEN)

    def store_api_key(self, key: str, refresh_token: Optional[str]) -> bool:
        """
        Stores the API key in the secure QGIS password store, IF available

        Returns True if the key could be stored
        """
        if platform.system() == "Darwin":
            # store tokens in plain text on MacOS as keychain isn't available due to MacOS security
            QgsSettings().setValue("koordinates/token", key,
                                   QgsSettings.Plugins)
            if refresh_token:
                QgsSettings().setValue("koordinates/refresh_token",
                                       refresh_token,
                                       QgsSettings.Plugins)
        else:
            QgsApplication.authManager().storeAuthSetting(
                AUTH_CONFIG_ID, key, True)
            QgsApplication.authManager().storeAuthSetting(
                AUTH_CONFIG_REFRESH_TOKEN, refresh_token or '', True)
        return True

    def retrieve_api_key(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieves a previously stored API key and refresh token, if available

        Returns None if no stored key is available
        """
        if platform.system() == "Darwin":
            api_key = QgsSettings().value(
                "koordinates/token", None, str, QgsSettings.Plugins
            ) or None
            refresh_token = QgsSettings().value(
                "koordinates/refresh_token", None, str, QgsSettings.Plugins
            ) or None
        else:
            api_key = (
                QgsApplication.authManager().authSetting(
                    AUTH_CONFIG_ID, defaultValue="", decrypt=True
                )
                or None
            )
            refresh_token = (
                    QgsApplication.authManager().authSetting(
                        AUTH_CONFIG_REFRESH_TOKEN, defaultValue="", decrypt=True
                    )
                    or None
            )
        return api_key, refresh_token
