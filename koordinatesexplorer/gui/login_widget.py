from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QThread,
    QSize
)
from qgis.PyQt.QtSvg import (
    QSvgWidget
)
from qgis.PyQt.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget
)
from qgis.core import (
    Qgis,
    QgsApplication
)
from qgis.utils import iface

from .action_button import ActionButton
from .gui_utils import GuiUtils
from ..api import KoordinatesClient
from ..auth import (
    OAuthWorkflow,
    AuthState
)

AUTH_CONFIG_ID = "koordinates_auth_id"


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
            self.setText('Login with your Koordinates ID')
        elif state == AuthState.LoggingIn:
            self.setText('Authorizing')
        elif state == AuthState.LoggedIn:
            self.setText('Login with your Koordinates ID')

        if state == AuthState.LoggedOut:
            self.setStyleSheet(self.BASE_STYLE.format(
                self.BUTTON_COLOR,
                self.BUTTON_OUTLINE,
                self.BUTTON_TEXT,
                self.BUTTON_HOVER))
            self.setEnabled(True)
        else:
            self.setStyleSheet(self.BASE_STYLE.format(
                self.BUTTON_DISABLED_COLOR,
                self.BUTTON_DISABLED_OUTLINE,
                self.BUTTON_DISABLED_TEXT,
                self.BUTTON_DISABLED_HOVER))
            self.setEnabled(False)


class LoginWidget(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.oauth = None
        self.auth_thread = None

        self.setFrameShape(QFrame.NoFrame)

        self.setStyleSheet("""LoginWidget {
         background-color: white;
         border: 1px solid rgb(180, 180, 180);
          }""")

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)

        top_frame = QFrame()
        top_frame.setFrameShape(QFrame.NoFrame)
        top_frame.setStyleSheet("""
         background-color: #323233;
        """)
        top_frame.setFixedHeight(270)

        top_frame_layout = QVBoxLayout()
        top_frame_layout.setContentsMargins(38, 0, 0, 25)
        top_frame_layout.addStretch(1)
        koordinates_logo_widget = QSvgWidget(GuiUtils.get_icon_svg('koordinates_logo_white.svg'))
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
        self.login_label.setText("""<style>
        p { line-height: 1.3; }
        </style><p>Login to your Koordinates account to get started.</p>
        <p>The next step will open a web browser and might require you to sign in to your
        Koordinates account.</p>""")
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
            href="https://id.koordinates.com/signup">Sign Up</a></span>""")
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
            href="https://koordinates.com/terms-of-use/">Terms of Use</a></span>""")
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

    def login_clicked(self):
        key = self.retrieve_api_key()
        if key is not None:
            self._auth_finished(key)
        else:
            self.login_button.set_state(AuthState.LoggingIn)

            self.oauth = OAuthWorkflow()

            self.open_login_window_label.setText(
                '<a href="{}" style="color: black;">Open the login window</a>'.format(
                    self.oauth.authorization_url
                )
            )
            self.open_login_window_label.show()

            self.auth_thread = QThread(self)
            self.oauth.setParent(self.auth_thread)
            self.oauth.moveToThread(self.auth_thread)
            self.oauth.finished.connect(self._auth_finished)
            self.oauth.error_occurred.connect(self._auth_error_occurred)
            self.auth_thread.started.connect(self.oauth.doAuth)
            self.auth_thread.start()

    def _login_changed(self, logged_in: bool):
        if not logged_in:
            self.remove_api_key()
            self.login_button.set_state(AuthState.LoggedOut)
            self.open_login_window_label.hide()

    def _auth_finished(self, key):
        self.oauth = None

        if self.auth_thread and not sip.isdeleted(self.auth_thread):
            self.auth_thread.quit()
            self.auth_thread.deleteLater()
        self.auth_thread = None

        if not key:
            return

        try:
            KoordinatesClient.instance().login(key)
            self.store_api_key()
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
        QgsApplication.authManager().removeAuthSetting(AUTH_CONFIG_ID)

    def store_api_key(self) -> bool:
        """
        Stores the API key in the secure QGIS password store, IF available

        Returns True if the key could be stored
        """
        if not QgsApplication.authManager().masterPasswordHashInDatabase():
            return False

        key = KoordinatesClient.instance().apiKey
        QgsApplication.authManager().storeAuthSetting(AUTH_CONFIG_ID, key, True)

    def retrieve_api_key(self) -> Optional[str]:
        """
        Retrieves a previously stored API key, if available

        Returns None if no stored key is available
        """
        if not QgsApplication.authManager().masterPasswordHashInDatabase():
            return None

        api_key = (
                QgsApplication.authManager().authSetting(
                    AUTH_CONFIG_ID, defaultValue="", decrypt=True
                )
                or None
        )
        return api_key
