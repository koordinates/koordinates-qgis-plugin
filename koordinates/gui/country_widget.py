from typing import Optional
import platform

from qgis.PyQt.QtCore import (
    QSize,
    QRect,
    Qt
)
from qgis.PyQt.QtGui import (
    QFontMetrics,
    QPainter,
    QFont,
    QFontDatabase,
    QIcon,
    QImage,
    QPixmap
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QWidgetAction
)


from .gui_utils import GuiUtils
from ..external import flag

COUNTRY_NAMES = {'AF': 'Afghanistan',
                 'AL': 'Albania',
                 'DZ': 'Algeria',
                 'AS': 'American Samoa',
                 'AD': 'Andorra',
                 'AO': 'Angola', 'AI': 'Anguilla', 'AQ': 'Antarctica', 'AG': 'Antigua and Barbuda',
                 'AR': 'Argentina',
                 'AM': 'Armenia', 'AW': 'Aruba', 'AU': 'Australia', 'AT': 'Austria',
                 'AZ': 'Azerbaijan',
                 'BS': 'Bahamas', 'BH': 'Bahrain', 'BD': 'Bangladesh', 'BB': 'Barbados',
                 'BY': 'Belarus',
                 'BE': 'Belgium', 'BZ': 'Belize', 'BJ': 'Benin', 'BM': 'Bermuda', 'BT': 'Bhutan',
                 'BO': 'Bolivia, Plurinational State of', 'BQ': 'Bonaire, Sint Eustatius and Saba',
                 'BA': 'Bosnia and Herzegovina', 'BW': 'Botswana', 'BV': 'Bouvet Island',
                 'BR': 'Brazil',
                 'IO': 'British Indian Ocean Territory', 'BN': 'Brunei Darussalam',
                 'BG': 'Bulgaria',
                 'BF': 'Burkina Faso', 'BI': 'Burundi', 'KH': 'Cambodia', 'CM': 'Cameroon',
                 'CA': 'Canada',
                 'CV': 'Cape Verde', 'KY': 'Cayman Islands', 'CF': 'Central African Republic',
                 'TD': 'Chad',
                 'CL': 'Chile', 'CN': 'China', 'CX': 'Christmas Island',
                 'CC': 'Cocos (Keeling) Islands',
                 'CO': 'Colombia', 'KM': 'Comoros', 'CG': 'Congo',
                 'CD': 'Congo, the Democratic Republic of the',
                 'CK': 'Cook Islands', 'CR': 'Costa Rica', 'Code': 'Country name', 'HR': 'Croatia',
                 'CU': 'Cuba',
                 'CW': 'Curaçao', 'CY': 'Cyprus', 'CZ': 'Czech Republic', 'CI': "Côte d'Ivoire",
                 'DK': 'Denmark',
                 'DJ': 'Djibouti', 'DM': 'Dominica', 'DO': 'Dominican Republic', 'EC': 'Ecuador',
                 'EG': 'Egypt',
                 'SV': 'El Salvador', 'GQ': 'Equatorial Guinea', 'ER': 'Eritrea', 'EE': 'Estonia',
                 'ET': 'Ethiopia',
                 'FK': 'Falkland Islands (Malvinas)', 'FO': 'Faroe Islands', 'FJ': 'Fiji',
                 'FI': 'Finland',
                 'FR': 'France', 'GF': 'French Guiana', 'PF': 'French Polynesia',
                 'TF': 'French Southern Territories',
                 'GA': 'Gabon', 'GM': 'Gambia', 'GE': 'Georgia', 'DE': 'Germany', 'GH': 'Ghana',
                 'GI': 'Gibraltar',
                 'GR': 'Greece', 'GL': 'Greenland', 'GD': 'Grenada', 'GP': 'Guadeloupe',
                 'GU': 'Guam',
                 'GT': 'Guatemala', 'GG': 'Guernsey', 'GN': 'Guinea', 'GW': 'Guinea-Bissau',
                 'GY': 'Guyana',
                 'HT': 'Haiti', 'HM': 'Heard Island and McDonald Islands',
                 'VA': 'Holy See (Vatican City State)',
                 'HN': 'Honduras', 'HK': 'Hong Kong', 'HU': 'Hungary', '(.uk)': 'ISO 3166-2:GB',
                 'IS': 'Iceland',
                 'IN': 'India', 'ID': 'Indonesia', 'IR': 'Iran, Islamic Republic of', 'IQ': 'Iraq',
                 'IE': 'Ireland',
                 'IM': 'Isle of Man', 'IL': 'Israel', 'IT': 'Italy', 'JM': 'Jamaica',
                 'JP': 'Japan', 'JE': 'Jersey',
                 'JO': 'Jordan', 'KZ': 'Kazakhstan', 'KE': 'Kenya', 'KI': 'Kiribati',
                 'KP': "Korea, Democratic People's Republic of", 'KR': 'Korea, Republic of',
                 'KW': 'Kuwait',
                 'KG': 'Kyrgyzstan', 'LA': "Lao People's Democratic Republic", 'LV': 'Latvia',
                 'LB': 'Lebanon',
                 'LS': 'Lesotho', 'LR': 'Liberia', 'LY': 'Libya', 'LI': 'Liechtenstein',
                 'LT': 'Lithuania',
                 'LU': 'Luxembourg', 'MO': 'Macao',
                 'MK': 'Macedonia, the former Yugoslav Republic of',
                 'MG': 'Madagascar', 'MW': 'Malawi', 'MY': 'Malaysia', 'MV': 'Maldives',
                 'ML': 'Mali', 'MT': 'Malta',
                 'MH': 'Marshall Islands', 'MQ': 'Martinique', 'MR': 'Mauritania',
                 'MU': 'Mauritius', 'YT': 'Mayotte',
                 'MX': 'Mexico', 'FM': 'Micronesia, Federated States of',
                 'MD': 'Moldova, Republic of', 'MC': 'Monaco',
                 'MN': 'Mongolia', 'ME': 'Montenegro', 'MS': 'Montserrat', 'MA': 'Morocco',
                 'MZ': 'Mozambique',
                 'MM': 'Myanmar', 'NA': 'Namibia', 'NR': 'Nauru', 'NP': 'Nepal',
                 'NL': 'Netherlands',
                 'NC': 'New Caledonia', 'NZ': 'New Zealand', 'NI': 'Nicaragua', 'NE': 'Niger',
                 'NG': 'Nigeria',
                 'NU': 'Niue', 'NF': 'Norfolk Island',
                 'MP': 'Northern Mariana Islands', 'NO': 'Norway', 'OM': 'Oman',
                 'PK': 'Pakistan', 'PW': 'Palau', 'PS': 'Palestine, State of', 'PA': 'Panama',
                 'PG': 'Papua New Guinea',
                 'PY': 'Paraguay', 'PE': 'Peru', 'PH': 'Philippines', 'PN': 'Pitcairn',
                 'PL': 'Poland',
                 'PT': 'Portugal', 'PR': 'Puerto Rico', 'QA': 'Qatar', 'RO': 'Romania',
                 'RU': 'Russian Federation',
                 'RW': 'Rwanda', 'RE': 'Réunion',
                 'BL': 'Saint Barthélemy',
                 'SH': 'Saint Helena, Ascension and Tristan da Cunha',
                 'KN': 'Saint Kitts and Nevis',
                 'LC': 'Saint Lucia', 'MF': 'Saint Martin (French part)',
                 'PM': 'Saint Pierre and Miquelon',
                 'VC': 'Saint Vincent and the Grenadines', 'WS': 'Samoa', 'SM': 'San Marino',
                 'ST': 'Sao Tome and Principe', 'SA': 'Saudi Arabia', 'SN': 'Senegal',
                 'RS': 'Serbia',
                 'SC': 'Seychelles', 'SL': 'Sierra Leone', 'SG': 'Singapore',
                 'SX': 'Sint Maarten (Dutch part)',
                 'SK': 'Slovakia', 'SI': 'Slovenia', 'SB': 'Solomon Islands', 'SO': 'Somalia',
                 'ZA': 'South Africa',
                 'GS': 'South Georgia and the South Sandwich Islands',
                 'SS': 'South Sudan', 'ES': 'Spain',
                 'LK': 'Sri Lanka', 'SD': 'Sudan', 'SR': 'Suriname',
                 'SJ': 'Svalbard and Jan Mayen', 'SZ': 'Swaziland',
                 'SE': 'Sweden', 'CH': 'Switzerland', 'SY': 'Syrian Arab Republic',
                 'TW': 'Taiwan, Province of China',
                 'TJ': 'Tajikistan', 'TZ': 'Tanzania, United Republic of', 'TH': 'Thailand',
                 'TL': 'Timor-Leste',
                 'TG': 'Togo', 'TK': 'Tokelau', 'TO': 'Tonga', 'TT': 'Trinidad and Tobago',
                 'TN': 'Tunisia',
                 'TR': 'Turkey', 'TM': 'Turkmenistan', 'TC': 'Turks and Caicos Islands',
                 'TV': 'Tuvalu',
                 'UG': 'Uganda',
                 'UA': 'Ukraine', 'AE': 'United Arab Emirates', 'GB': 'United Kingdom',
                 'US': 'United States',
                 'UM': 'United States Minor Outlying Islands', 'UY': 'Uruguay', 'UZ': 'Uzbekistan',
                 'VU': 'Vanuatu',
                 'VE': 'Venezuela, Bolivarian Republic of', 'VN': 'Viet Nam',
                 'VG': 'Virgin Islands, British',
                 'VI': 'Virgin Islands, U.S.',
                 'WF': 'Wallis and Futuna', 'EH': 'Western Sahara',
                 'YE': 'Yemen',
                 'ZM': 'Zambia',
                 'ZW': 'Zimbabwe',
                 'AX': 'Åland Islands'}

STANDARD_EMOJI_FONTS = (
    'Apple Color Emoji',
    'Segoe UI Emoji',
    'Noto Color Emoji',
)

class EmojiToIconRenderer:
    """
    Renders emoji to Icons
    """

    EMOJI_FONT = None

    @staticmethod
    def _init_font():
        if EmojiToIconRenderer.EMOJI_FONT:
            return

        families = set(QFontDatabase().families())

        found = False
        for candidate in STANDARD_EMOJI_FONTS:
            if candidate in families:
                EmojiToIconRenderer.EMOJI_FONT = QFont(candidate)
                found = True
                break

        if not found:
            # load from the embedded Noto Emoji subset, which doesn't always work cross-platform...
            EmojiToIconRenderer.EMOJI_FONT = GuiUtils.get_embedded_font('NotoEmojiSubset.ttf')

        EmojiToIconRenderer.EMOJI_FONT.setPointSize(50)

    @staticmethod
    def render_flag_to_icon(code: str) -> QIcon:
        """
        Renders a flag to a icon
        """
        return EmojiToIconRenderer.render_emoji_to_icon(flag.flag(code))

    @staticmethod
    def render_emoji_to_icon(char: str) -> QIcon:
        """
        Renders an emoji to a icon
        """
        if platform.system() == 'Windows':
            return QIcon()

        EmojiToIconRenderer._init_font()
        fm = QFontMetrics(EmojiToIconRenderer.EMOJI_FONT)

        image = QImage(fm.boundingRect(char).width(),
                       fm.boundingRect(char).height(),
                       QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        painter.setFont(EmojiToIconRenderer.EMOJI_FONT)
        painter.drawText(0, 0, image.width(), image.height(), 0, char)

        painter.end()

        return QIcon(QPixmap.fromImage(image))


class CountryWidget(QWidget):
    """
    Shows a styled country flag and name
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        families = set(QFontDatabase().families())

        found = False
        for candidate in STANDARD_EMOJI_FONTS:
            if candidate in families:
                self._emoji_font = QFont(candidate)
                found = True
                break

        if not found:
            # load from the embedded Noto Emoji subset, which doesn't always work cross-platform...
            self._emoji_font = GuiUtils.get_embedded_font('NotoEmojiSubset.ttf')

        self._emoji_font.setPointSize(10)
        self._country: Optional[str] = None

    def set_country_code(self, code: str):
        """
        Sets the country code for the country to show
        """
        self._country = code

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        return QSize(fm.width('x') * 30, int(fm.height() * 1.5))

    def paintEvent(self, event):
        if not self._country:
            return

        fm = QFontMetrics(self.font())
        left_space = int(fm.width('x') * 4.5)

        if platform.system() != 'Windows':
            icon_space = int(QFontMetrics(self._emoji_font).width(self._country) * 1.5)
        else:
            icon_space = 0

        bottom_pad = int(fm.height() * 0.5)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if platform.system() != 'Windows':
            painter.setFont(self._emoji_font)
            painter.drawText(
                QRect(
                    left_space, 0,
                    icon_space, self.height() - bottom_pad
                ), Qt.AlignLeft | Qt.AlignVCenter,
                flag.flag(self._country))

        name_font = self.font()
        name_font.setPointSizeF(10)
        painter.setFont(name_font)
        pen = painter.pen()
        color = pen.color()
        color.setAlphaF(0.5)
        pen.setColor(color)
        painter.setPen(pen)

        text_left = left_space + icon_space
        painter.drawText(QRect(text_left, 0, self.width() - text_left, self.height() - bottom_pad),
                         Qt.AlignLeft | Qt.AlignVCenter, COUNTRY_NAMES[self._country])
        painter.end()


class CountryWidgetAction(QWidgetAction):
    """
    A widget action for showing a styled country flag
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._country_widget = CountryWidget(parent)
        self.setDefaultWidget(self._country_widget)

    def set_country_code(self, code: str):
        """
        Sets the country code for the country to show
        """
        self._country_widget.set_country_code(code)
